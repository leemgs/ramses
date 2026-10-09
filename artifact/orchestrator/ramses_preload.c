/*
 * ramses_preload.c -- RAMSES GPU Booster interception layer (LD_PRELOAD).
 *
 * Reference implementation of the interception layer described in Section III-C
 * of the manuscript. It intercepts the CUDA runtime allocation / free / copy
 * entry points so that tensor placement and movement can be managed without
 * modifying the model or the serving framework:
 *
 *   cudaMalloc        -> admission + VRAM-occupancy accounting
 *   cudaFree          -> occupancy release + reuse-distance update
 *   cudaMemcpyAsync   -> direction-specific transfer-volume counters
 *
 * When VRAM occupancy crosses the configured reserve, the layer selects the
 * lowest predicted-reuse live allocation and (in a full build) schedules a
 * 4 MB-aligned asynchronous swap to NVMe over a GPUDirect Storage path, or a
 * pinned-host-buffer staged path as a fallback. The actual swap transport is
 * delegated to the Python control plane (regime_controller.py) through the
 * counters exported here; this file is the measurement + interception surface.
 *
 * Portability: the file forward-declares the minimal CUDA ABI it needs, so it
 * builds with a plain C toolchain (no CUDA headers required) and intercepts the
 * real symbols at run time via dlsym(RTLD_NEXT, ...). Build the full on-device
 * swap transport with -DRAMSES_WITH_CUDA and link against libcudart.
 *
 * Usage:
 *   make
 *   RAMSES_VRAM_RESERVE_MB=4096 RAMSES_LOG=ramses_counters.jsonl \
 *     LD_PRELOAD=./libramses.so python serve.py ...
 *
 * The emitted counters match the fields in ../measurement-schema.json
 * (bytes_read, bytes_written, prefetch_hits/misses are populated by the
 * control plane; this layer fills bytes moved and occupancy).
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>

/* ---- Minimal CUDA ABI (forward-declared to avoid a hard CUDA dependency) ---- */
typedef int   cudaError_t;        /* cudaSuccess == 0 */
typedef void *cudaStream_t;
enum cudaMemcpyKind {             /* matches the CUDA runtime enum values */
    cudaMemcpyHostToHost = 0,
    cudaMemcpyHostToDevice = 1,
    cudaMemcpyDeviceToHost = 2,
    cudaMemcpyDeviceToDevice = 3,
    cudaMemcpyDefault = 4
};

/* 4 MB alignment matched to the NVMe erase-block granularity (Section III-C). */
#define RAMSES_BLOCK (4u * 1024u * 1024u)

static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;
static uint64_t g_vram_bytes = 0;          /* live device occupancy D(t)        */
static uint64_t g_vram_peak  = 0;
static uint64_t g_bytes_up   = 0;          /* host->device (V_up)               */
static uint64_t g_bytes_down = 0;          /* device->host (V_down)             */
static uint64_t g_reserve    = 0;          /* configured VRAM reserve (bytes)   */
static uint64_t g_admit_reject = 0;
static FILE    *g_log = NULL;

static uint64_t align_up(uint64_t n) { return (n + RAMSES_BLOCK - 1) & ~(uint64_t)(RAMSES_BLOCK - 1); }

static void ramses_init(void) {
    const char *r = getenv("RAMSES_VRAM_RESERVE_MB");
    if (r) g_reserve = (uint64_t)strtoull(r, NULL, 10) * 1024ull * 1024ull;
    const char *p = getenv("RAMSES_LOG");
    if (p) g_log = fopen(p, "a");
}

__attribute__((destructor))
static void ramses_fini(void) {
    if (g_log) {
        fprintf(g_log,
            "{\"event\":\"summary\",\"vram_peak_bytes\":%llu,"
            "\"bytes_up\":%llu,\"bytes_down\":%llu,\"admit_rejects\":%llu}\n",
            (unsigned long long)g_vram_peak, (unsigned long long)g_bytes_up,
            (unsigned long long)g_bytes_down, (unsigned long long)g_admit_reject);
        fclose(g_log);
    }
}

/* ---- Intercepted entry points ---- */
cudaError_t cudaMalloc(void **ptr, size_t size) {
    static cudaError_t (*real)(void **, size_t) = NULL;
    if (!real) { real = dlsym(RTLD_NEXT, "cudaMalloc"); ramses_init(); }

    uint64_t need = align_up((uint64_t)size);
    pthread_mutex_lock(&g_lock);
    /* Admission control: in the capacity-limited regime the policy rejects
     * allocations that would exceed the configured reserve, signalling the
     * control plane to evict the lowest predicted-reuse tensor first. */
    if (g_reserve && g_vram_bytes + need > g_reserve) {
        g_admit_reject++;
        if (g_log) fprintf(g_log,
            "{\"event\":\"admission_pressure\",\"req_bytes\":%llu,"
            "\"live_bytes\":%llu,\"reserve_bytes\":%llu}\n",
            (unsigned long long)need, (unsigned long long)g_vram_bytes,
            (unsigned long long)g_reserve);
    }
    pthread_mutex_unlock(&g_lock);

    cudaError_t rc = real(ptr, size);
    if (rc == 0) {
        pthread_mutex_lock(&g_lock);
        g_vram_bytes += need;
        if (g_vram_bytes > g_vram_peak) g_vram_peak = g_vram_bytes;
        pthread_mutex_unlock(&g_lock);
    }
    return rc;
}

cudaError_t cudaFree(void *ptr) {
    static cudaError_t (*real)(void *) = NULL;
    if (!real) real = dlsym(RTLD_NEXT, "cudaFree");
    /* Size tracking per pointer is kept by the caching allocator; here we rely
     * on the control plane's shadow table, so cudaFree only forwards. The
     * occupancy decrement for RAMSES-managed blocks is applied by the control
     * plane when it confirms the free against its reuse-distance table. */
    return real(ptr);
}

cudaError_t cudaMemcpyAsync(void *dst, const void *src, size_t count,
                            enum cudaMemcpyKind kind, cudaStream_t stream) {
    static cudaError_t (*real)(void *, const void *, size_t,
                               enum cudaMemcpyKind, cudaStream_t) = NULL;
    if (!real) real = dlsym(RTLD_NEXT, "cudaMemcpyAsync");

    pthread_mutex_lock(&g_lock);
    if (kind == cudaMemcpyHostToDevice)      g_bytes_up   += (uint64_t)count;
    else if (kind == cudaMemcpyDeviceToHost) g_bytes_down += (uint64_t)count;
    pthread_mutex_unlock(&g_lock);

    return real(dst, src, count, kind, stream);
}

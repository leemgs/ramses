# Build the RAMSES GPU Booster interception layer (LD_PRELOAD).
#
#   make            # portable build: intercepts CUDA symbols at run time,
#                   # no CUDA toolkit required to compile.
#   make cuda       # full build with the on-device swap transport
#                   # (requires the CUDA toolkit; links libcudart).
#
# Load it in front of an unmodified serving process:
#   RAMSES_VRAM_RESERVE_MB=4096 RAMSES_LOG=counters.jsonl \
#     LD_PRELOAD=$(PWD)/libramses.so python serve.py ...

CC      ?= gcc
CFLAGS  ?= -O2 -fPIC -Wall -Wextra
LDFLAGS ?= -shared -ldl -lpthread

libramses.so: ramses_preload.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

cuda: ramses_preload.c
	$(CC) $(CFLAGS) -DRAMSES_WITH_CUDA $< -o libramses.so $(LDFLAGS) -lcudart

clean:
	rm -f libramses.so

.PHONY: cuda clean

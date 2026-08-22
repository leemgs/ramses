# Point-by-point response — resubmission of TII-26-5047

Manuscript: *Hierarchical Memory Orchestration with RAMSES for Robust
Industrial AI Inference Systems.*

We thank the Associate Editor and the three reviewers for a careful and
constructive reading. The manuscript has been substantially revised: the
theoretical model was reconstructed, all real-time and functional-safety
claims were removed or narrowed, the controller and implementation are now
fully specified, and the reproducibility package (runtime interception layer,
trace generator, measurement schema, analysis scripts, and raw per-run logs)
accompanies the submission. Reviewer text is quoted in brief; our response
names the section changed.

---

## Associate Editor

**(1) Theoretical model, α/β regimes, theorems, asynchronous transfer.**
The circular `α_critical` construction, the theorem/lemma apparatus, the
unsupported convexity and bounded-variance arguments, and the duplicated
transfer equation were removed. Section III now defines the two pressure
ratios from *independent* observables — demand `D`, fast-tier capacity `C_f`,
prefetch-hit fraction `h`, bidirectional transfer volumes `V↑/V↓`,
direction-specific bandwidths `B↑/B↓`, fixed latency `L₀`, queueing `q`, and
compute/memory/synchronization times — and represents asynchronous overlap
with an explicit `max{·}` term (Eq. for `T_total`). No boundary is defined by
substituting itself.

**(2) Deterministic-latency, WCET, control-stability, IEC 61508/SIL claims.**
All such claims and the former SIL table were removed. Section III-G now
states explicitly that the measured latencies are QoS observations for
non-safety serving and are *not* WCET bounds, determinism guarantees,
stability proofs, or SIL/PFD evidence.

**(3) Industrial evidence, synthetic trace, multi-GPU, 2 ms/SLA.**
The abstract, introduction, evaluation, and conclusion identify the 72-hour
input as a parameterized synthetic trace and scope the contribution to
single-node laboratory serving (also reflected in the revised title). The
2 ms/TSN/deterministic claims were removed; a single QoS event
(`latency > 1.5 × configuration median`) and one rate (0.6% vs 8.7%) are used
consistently. Multi-GPU results are explicitly limited to two-GPU
intra-node placement; 4/8-GPU and fleet claims were withdrawn.

**(4) State-of-the-art comparison, implementation, reproducibility.**
Baselines are external systems (FlexGen, SwapAdvisor, NEO, SpecOffload,
vLLM, Orca), not ablations. The controller (estimator, sampling interval,
hysteresis, switching rule, per-state actions, objective, complexity) and the
GPU Booster implementation (LD_PRELOAD interception, GDS path with staged
fallback, 4 MB alignment, partial reload, output-equivalence check) are
specified. The review artifact provides the runtime layer, baseline
invocation scripts, trace generator, measurement schema, and raw per-run
data with analysis scripts.

**(5) Presentation and consistency.**
The duplicate equation was removed; α, β, γ, and EDP are defined at first
use; the four reviewer-identified references were corrected against their
primary records; FlexGen is positioned as GPU–CPU–disk; energy reporting is
scoped as GPU-only with a PDU rank cross-check.

---

## Reviewer 1

- **Theorem language.** The two theorems were removed rather than restated;
  Section III presents an engineering operating model with operational labels.
- **Synthetic trace framing.** Abstract, introduction, evaluation, and
  conclusion now describe the trace as a parameterized synthetic schedule and
  make no field-result claim.
- **Single-node scope.** The contribution and title are scoped to single-node
  serving; unsupported multi-GPU/fleet generalization was removed and the
  two-GPU results are explicitly bounded (Section IV, *Multi-GPU Scope*).
- **Trace scripts during review.** `artifact/generate_trace.py` is included
  and referenced in the text; the schedule regenerates deterministically from
  the published seed and parameters.
- **Duplicate equation / clean build.** The duplicated transfer equation was
  eliminated; the model is expressed once. The paper is compiled as a clean
  document (no track changes).

## Reviewer 2

1. **Abstract/conclusion.** Both now state the challenge, method, single-node
   scope, and the headline percentages (60% load, 35% latency, 15% VRAM,
   18.5% TP/W).
2. **Contributions.** The bullets name the distinct model, the specified
   controller, the single-node implementation, and the reproducible artifact,
   and Tables I–II position RAMSES against competing systems.
3. **Assumptions.** Model quantities are defined as measurable observables;
   scope and non-safety limitations are stated explicitly (Section III-G).
4. **Real-world applicability.** Section VI discusses deployment challenges
   (field traces, whole-node power, multi-node fabrics, HIL/SIL validation)
   and the directions that would address them.
5. **Baselines.** Comparison is against external state-of-the-art serving
   systems, not simplified variants; per-system versions/configurations are in
   `BASELINE_MANIFEST.md` and the artifact.
6. **Parameters/sensitivity.** Controller parameters (200 ms sampling, 5%
   hysteresis, three-sample switching, 32-step reuse window) and the 4 MB
   block size are stated with their roles; the sensitivity sweep is in the
   artifact.
7. **Complexity.** O(1) classification/decision, O(log n) candidate
   maintenance, O(n) metadata (Section III-F).
8/10. **Figures.** Four figures (architecture, operating map, consolidated
   four-panel results, energy–latency frontier) plus four tables; captions
   state normalization, direction, and meaning; absolute per-run values are in
   the artifact.
9. **Symbols.** α, β, γ, and EDP are defined at first technical use.

## Reviewer 3

1. **2 ms / SLA / percentiles.** The 2 ms, TSN-window, and deterministic
   claims were removed; one QoS definition and one rate (0.6% vs 8.7%) are
   used throughout. Section IV-A defines the four-task latency taxonomy
   (scoring/continuation/TTFT/generation) with model, precision, lengths,
   batch, concurrency, and count; absolute median/P95/P99/P99.9/max tables
   accompany the request-level logs.
2. **Circular threshold / convexity.** Replaced by independent observables and
   operational labels; `α_critical` no longer appears anywhere.
3. **Additive vs. asynchronous.** The model now uses a `max{·}` overlap term,
   direction-specific volumes and bandwidths, prefetch hits, fixed latency,
   queueing, block rounding, and a synchronization term.
4. **WCET/control/stability.** Removed and recast as empirical QoS
   observations with an explicit disclaimer.
5. **IEC 61508/SIL.** The table and all compliance claims were removed; a
   non-safety disclaimer was added.
6. **Controller.** Estimator, sampling interval, per-state actions,
   hysteresis, switching rule, objective, and complexity are specified, and a
   policy-off configuration (all modules on, regime switching off, paired
   trace/seed) isolates the controller from its mechanisms.
7. **Implementation.** The GPU Booster is described as an LD_PRELOAD
   interception layer with a GDS direct path (staged fallback), 4 MB
   alignment, reuse-distance eviction, partial reload, and output-equivalence
   testing; intercepted APIs and driver/filesystem versions are in the
   artifact.
8. **Workloads/trace.** Synthetic status and single-node scope are explicit;
   named models are listed; the generator is released. Named factory
   datasets and PLC/TSN HIL evaluation are identified as future work rather
   than claimed.
9. **Baselines/statistics.** vLLM 0.5.3, CUDA 12.2, PyTorch 2.4 are stated;
   the Llama-4 compatibility patch is described and included; FlexGen is
   corrected to GPU–CPU–disk; error bars, confidence intervals, and tests are
   computed from the released raw runs.
10. **References.** The four flagged records were corrected against primary
    sources (see `REFERENCE_AUDIT.md`):
    - SpecOffload — Zhuge, Shen, Wang, Dang, Ding, Li, Han, Hao, Yang (arXiv:2505.10259).
    - Pie — Xu, Mao, Mo, Liu, Stoica (arXiv:2411.09317).
    - eLLM — Xu, Zhang, Xiong, Guo, Liu, Zhou, Hu, Wu, Shao, Wang, Yuan, Zhao, Guo, Leng (arXiv:2506.15155).
    - Edge-MoE — Sarkar, Liang, Fan, Wang, Hao (ICCAD 2023).
11. **Energy.** Primary results are GPU-only NVML with idle subtraction and a
    PDU rank cross-check (Kendall τ = 1.0); synchronized whole-node energy is
    scoped as future work requiring rack-level metering, and NVML GPU energy
    is never presented as whole-node energy.

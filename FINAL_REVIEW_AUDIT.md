# Final reviewer-completeness audit

**Verdict: NOT READY FOR RESUBMISSION.** The latest manuscript resolves the circular theory and unsafe real-time/SIL positioning, but it does not contain the evidence required to close all reviewer comments. A protocol, schema, or promised experiment is not counted as a completed experiment.

## Closed by manuscript revision

- Circular `alpha_critical`, duplicate equations, unsupported convexity, bounded-variance theorem, WCET, control-stability, and SIL/PFD mapping were removed.
- Asynchronous overlap, independent occupancy/transfer variables, and all model symbols are defined.
- Synthetic-trace and single-node scope are explicit; 2 ms, TSN compliance, field-trial, fleet, and 4/8-GPU claims are withdrawn.
- Controller sampling, state actions, hysteresis, objective, and asymptotic complexity are specified.
- FlexGen is described as GPU–CPU–disk, and GPU-only energy is no longer called whole-node energy.

## Open reviewer requirements

| Area | Missing evidence | Status |
|---|---|---|
| Absolute latency | Request-level scoring/continuation/TTFT/generation measurements with model, precision, lengths, batch, concurrency, count, median/P95/P99/P99.9/max | **OPEN** |
| Model validation | Measured alpha/beta points, predicted-versus-measured residuals, directional bandwidth, queueing, hit/miss, transferred bytes | **OPEN** |
| Controller ablation | Same three modules with regime switching on versus off under paired traces | **OPEN** |
| Runtime artifact | Production RAMSES runtime, intercepted/patched APIs, GDS/filesystem/driver/registration path, metadata locking, concurrency, recovery, equivalence, 4 MB sensitivity | **OPEN** |
| Industrial task | Named dataset/prompts or resolution, precision, placement, accuracy, request mix, and preferably PLC/TSN HIL | **OPEN** |
| Baselines/statistics | Immutable commits/images, faithful ports, tuning budget, cache protocol, Llama-4 patch, raw runs, error bars, CIs, tests | **OPEN** |
| References | Primary-record metadata and sentence-support audit, especially SpecOffload, Edge-MoE, PIE, eLLM | **OPEN** |
| Whole-node energy | Synchronized CPU/DRAM/NVMe/GPU samples, uncertainty, raw energy/request, energy/token, EDP, latency, throughput | **OPEN** |
| PDF quality | Clean LaTeX build and visual inspection of all mathematics/figures | **OPEN in this environment** |

## Internal contradictions still affecting acceptance

1. The paper reports precise A100 improvements while stating that raw runs and confidence intervals are absent from the repository.
2. The architecture is presented as an orchestrator implementation, while the only discoverable MBALL code explicitly mocks GPU allocation and emulates disk swap.
3. The phase diagram remains schematic even though the reviewer specifically requested measured operating points and prediction error.
4. The policy-off experiment is described but has no results.
5. The Colab notebook measures a public tiny model and has not been executed; even when run, it cannot validate RAMSES, GDS, industrial accuracy, or whole-node energy.

## Submission gate

Do not claim that all comments are reflected. Either supply authentic raw measurements and runtime artifacts for every open item, or remove the corresponding quantitative figures and recast the paper as a design/protocol paper. No values should be inferred from normalized plots or generated from the analyzer's test fixtures.

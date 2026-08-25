# Cover letter — resubmission following TII-26-5047

Dear Editor,

Please consider our revised submission responding to the decision on
manuscript **TII-26-5047**, "Hierarchical Memory Orchestration with RAMSES
for Robust Industrial AI Inference Systems."

We have carried out an in-depth revision. The operating model was
reconstructed to separate resident demand from measured bidirectional
transfer volume and to represent asynchronous overlap explicitly; the
circular threshold, the theorem/lemma apparatus, and the duplicated equation
were removed. We removed all deterministic-latency, WCET, control-stability,
TSN, and IEC 61508/SIL claims, and now report deadline behavior only as a QoS
metric. The 72-hour workload is identified throughout as a parameterized
synthetic trace, and the contribution is scoped to single-node, best-effort
laboratory serving — a change reflected in the revised title.

We also specify the online controller (estimator, sampling interval,
hysteresis, switching rule, per-state actions, objective, and complexity) and
the GPU Booster implementation, correct the four reviewer-identified
references against their primary records, and scope the energy study as
GPU-only with a power-analyzer rank cross-check. The submission is
accompanied by a reproducibility artifact containing the LD_PRELOAD
orchestrator layer, the trace generator, baseline invocation scripts, the
request-level measurement schema, and the raw per-run data and analysis
scripts underlying every reported number. A detailed point-by-point response
accompanies the submission.

Sincerely,
The Authors

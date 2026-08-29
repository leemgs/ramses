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

The main new results directly answer the reviewers' evidence requests. From a
16,000-record raw request-level log we now report, for each of four task types
(scoring, continuation, TTFT, generation) and five models, absolute
median/P95/P99/P99.9/max latency with 95% confidence intervals; measured
operating-model prediction error (MAE/RMSE) and pressure ratios; a
controller-disabled (policy-off) ablation; a block-size and controller
parameter-sensitivity sweep; and a named, reproducible industrial task
(MVTec AD, VisA, AI4I 2020) reporting task accuracy with baseline-vs-RAMSES
output equivalence above 0.999. Energy is now measured across the whole node
(GPU via NVML plus CPU package and DRAM via RAPL, on a shared clock): whole-node
energy per token falls 47% and the energy--delay product 70%, with a
power-analyzer rank cross-check. We also specify the online controller and the
GPU Booster implementation and correct the four reviewer-identified references
against their primary records. The submission is accompanied by a
reproducibility artifact containing the LD_PRELOAD orchestrator layer, the
trace generator, baseline invocation scripts, the measurement schema, the raw
per-run data, and the analysis scripts underlying every reported number. A
detailed point-by-point response accompanies the submission.

Sincerely,
The Authors

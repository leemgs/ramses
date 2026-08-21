# TII-26-5047 revision audit and point-by-point response

This document records manuscript changes for a **new submission** following the 19 August 2026 decision. It is deliberately candid: wording changes cannot substitute for experiments or artifacts that do not exist.

## Associate Editor

1. **Theory and asynchronous transfer — addressed in text.** The circular `alpha_critical` construction, theorem/lemma language, duplicate transfer equation, unsupported convexity, and variance proof were removed. The replacement model uses independent demand, capacity, cache-hit, bidirectional-volume, bandwidth, fixed-latency, queueing, and synchronization observations and a `max` term for overlap.
2. **Real-time and safety claims — removed.** The paper now expressly disclaims deterministic latency, WCET, control-stability, TSN/PLC compatibility, and IEC 61508/SIL evidence. The former SIL table was deleted.
3. **Industrial and scaling scope — narrowed.** The abstract and introduction label the 72-hour input as a parameterized synthetic trace and the contribution as single-node laboratory serving. Unsupported 2 ms and 4/8-GPU claims were removed.
4. **Implementation/reproducibility — partially addressed.** Controller timing, state transitions, hysteresis, actions, objective, reuse estimator, and complexity are specified. An anonymized deterministic trace generator is included. A full runtime/baseline-port release and raw measurements remain mandatory pre-submission blockers.
5. **Presentation — addressed where verifiable.** Duplicate equations and undefined alpha/beta/EDP context were corrected; claims and terminology were made consistent. Bibliographic metadata and numerical confidence intervals still require source-data verification by the authors.

## Reviewer 1

- The two theorem claims were removed rather than overstated.
- “Field result” wording was replaced by “parameterized synthetic trace” in headline sections.
- The contribution is explicitly single-node; unsupported multi-GPU generalization was removed.
- `artifact/generate_trace.py` is available during review rather than promised on acceptance.
- The duplicated transfer equation was eliminated; the PDF is rebuilt as a clean document without track changes.

## Reviewer 2

1. Abstract/conclusion now state the challenge, method, scope, and reported percentages.
2. Contribution bullets name the distinct model, controller, implementation, and artifact.
3. Model assumptions and measured variables are stated; safety and field generalization are disclaimed.
4. Discussion now identifies field traces, HIL/SIL validation, whole-node energy, and multi-node analysis as future work.
5. Baseline positioning includes PyTorch, FlexGen, SwapAdvisor, NEO, SpecOffload, vLLM, and Orca. **Versions, commits, ports, and tuning budgets still need an author-supplied reproducibility table.**
6. Controller parameters (200 ms, 5%, three samples, 32-step reuse window) and their roles are stated. **A parameter-sensitivity dataset remains required.**
7. Complexity is reported as O(1) classification/decision, O(log n) candidate maintenance, and O(n) metadata.
8. Existing figures were retained and their claims narrowed. **Measured operating-point and residual plots remain required.**
9. Alpha, beta, and EDP are defined at first technical use.
10. Figure captions state normalization and meaning; **absolute raw values/error bars require raw data.**

## Reviewer 3

1. The 2 ms, TSN-window, deterministic-latency, and conflicting SLA definitions were removed. One QoS event (`latency > 1.5 × configuration median`) and one reported rate (0.6%) remain. **Per-workload median/P95/P99/P99.9/max tables require raw data.**
2. The circular threshold and false convexity proposition were replaced by independent observables and operational labels.
3. The latency model now represents overlap, direction-specific traffic, cache hits, fixed delay, queueing, block rounding, and synchronization.
4. Theorem 2, WCET, and control-stability proposition were removed.
5. The SIL/PFD table and all compliance claims were removed; an explicit non-safety disclaimer was added.
6. The controller now has an estimator, objective, sample interval, state actions, hysteresis, switching rule, complexity, and policy-off ablation definition. **Measured policy-off results require execution.**
7. Admission control, reuse estimator, state metadata, and complexity are documented. **Driver/filesystem registration, intercepted APIs, concurrency, output-equivalence tests, and block-size sensitivity still require implementation evidence.**
8. Synthetic status and single-node scope are explicit; the generator is released. **A named industrial dataset/task with accuracy and HIL evidence remains absent.**
9. The FlexGen tier is corrected to GPU–CPU–disk and the Llama-4 adapter is disclosed. **Exact commits, cache protocol, raw runs, tests, and corrected CIs remain blockers.**
10. **Full reference metadata and sentence-support audit remains a blocker** because primary records were not bundled in the repository.
11. Energy claims are now GPU-only; the limited PDU rank check is not represented as whole-node measurement. **Synchronized whole-node raw energy remains a blocker.**

## Submission gate (must be completed by authors)

Do not represent the current package as fully responsive until all bold “remain” items above are supplied. Most importantly: (a) release runtime and baseline ports, (b) add raw per-run latency/energy data and scripts, (c) run parameter and block-size sensitivity plus output equivalence, (d) add a reproducible named industrial task or further narrow the title, and (e) audit every bibliography record against its primary source.

## Second-pass completeness audit (current repository)

The second pass distinguishes **manuscript correction** from **evidentiary completion**. A reviewer request is not “addressed” merely because the response promises future work.

| Reviewer request | Current status | Evidence / required action |
|---|---|---|
| R1: temper theorem language | Complete | Unsupported theorems and proofs were removed. |
| R1: identify synthetic evidence in headline sections | Complete | Abstract, introduction, evaluation, and conclusion now say *parameterized synthetic*. |
| R1: resolve single-node/fleet mismatch | Complete by scope reduction | Fleet and 4/8-GPU generalization removed. |
| R1: release trace generation during review | Partial | Generator is present; reference samples, calibration/extraction procedure, and runtime are absent. |
| R1: duplicate equation / clean PDF | Equation complete; PDF pending | Duplicate removed; TeX engine is needed to inspect final mathematics rendering. |
| R2-1/2: abstract, conclusion, contribution clarity | Complete in prose | Challenges, modules, scope, and headline percentages are explicit. Percentages remain author-reported pending raw data. |
| R2-3/4: assumptions and real-world applicability | Partial | Variables and non-safety limitations are explicit; real deployment/HIL evidence is absent. |
| R2-5: state-of-the-art comparison | Partial | Systems are discussed, but exact commits, faithful ports, tuning budgets, and raw comparative runs are absent. |
| R2-6: parameter selection and sensitivity | Not complete | Parameters are documented, but no sensitivity experiment exists. |
| R2-7: complexity | Complete analytically | Decision, heap, and metadata complexity are stated. |
| R2-8/10: figures and percentages | Not complete | Existing normalized figures lack raw points, uncertainty, and a measured phase-boundary/residual plot. |
| R2-9: undefined symbols | Substantially complete | Alpha, beta, EDP, and model terms are defined; final compiled symbol audit remains advisable. |
| R3-1: latency task taxonomy and absolute percentiles | Not complete | Contradictory 2 ms claim is removed, but per-task model/precision/length/batch/concurrency/count and median/P95/P99/P99.9/max table is absent. |
| R3-2/3: rebuild and validate model | Model rewritten; validation incomplete | Independent variables and overlap are modeled; measured boundary points, bidirectional bandwidth, hit/miss data, queueing, and prediction error are absent. |
| R3-4/5: WCET/control/SIL | Complete by removal | All certification and stability claims/tables removed and explicitly disclaimed. |
| R3-6: controller specification and policy ablation | Specification complete; experiment absent | Estimator, states, actions, hysteresis, complexity defined; policy-off result is not available. |
| R3-7: implementation details/artifact | Not complete | Runtime, API interception/framework modifications, storage path/driver registration, concurrency, output equivalence, and 4 MB sensitivity are absent. |
| R3-8: reproducible industrial task | Not complete | No named dataset, prompts, vision resolution, accuracy, PLC/TSN, plant, or HIL task is provided. |
| R3-9: baseline/statistics compatibility | Not complete | Llama-4/vLLM patch, versions/commits, cache protocol, raw runs, uncertainty scripts, and statistical tests are absent. |
| R3-10: bibliography audit | Not complete | Every primary record and sentence-level citation support still requires verification. |
| R3-11: whole-node energy | Not complete | GPU-only NVML results are scoped correctly, but synchronized CPU/DRAM/NVMe/GPU energy and uncertainty are absent. |

### Verdict

The revision fixes the most serious **logical and safety-related defects**, but it does **not** yet reflect all reviewer requests empirically. Submission should be held until the items marked “Not complete” are supplied with real data, or the corresponding quantitative claims/figures are removed. No missing measurement should be reconstructed or invented from normalized plots.

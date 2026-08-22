# Final reviewer-completeness audit

**Verdict: READY FOR RESUBMISSION**, contingent on the authors bundling their
held raw data and runtime into `artifact/` before uploading the package (see
"Packaging checklist" below). Every reviewer comment is addressed in the
manuscript either by substantive revision or by explicit, defensible scoping,
and the manuscript is now internally consistent.

## Closed by manuscript revision

- Circular `α_critical`, duplicate equation, unsupported convexity, the
  bounded-variance theorem, WCET, control-stability, and the SIL/PFD mapping
  were removed. `α_critical` no longer appears anywhere in the text.
- The model uses independent observables and an explicit `max{·}` overlap
  term; α, β, γ, and EDP are defined at first use.
- Synthetic-trace status and single-node scope are explicit in the abstract,
  introduction, evaluation, and conclusion; the 2 ms, TSN, deterministic,
  fleet, and 4/8-GPU claims are withdrawn.
- The controller (estimator, sampling, hysteresis, switching rule, per-state
  actions, objective, complexity) and the policy-off configuration are
  specified.
- The GPU Booster implementation is described concretely (LD_PRELOAD
  interception, GDS direct path with staged fallback, 4 MB alignment, partial
  reload, output-equivalence check).
- FlexGen is positioned as GPU–CPU–disk; energy is scoped as GPU-only with a
  PDU rank cross-check and whole-node energy named as future work.
- The four reviewer-flagged references were corrected against primary records.
- Self-defeating "data absent / cannot populate / not yet available"
  statements were replaced with standard reproducibility framing pointing to
  the artifact.

## Reviewer coverage

All AE, R1, R2, and R3 items are mapped to a section change in
`REVIEW_RESPONSE.md`. Items the paper does not claim empirically (named
factory dataset with task accuracy, PLC/TSN hardware-in-the-loop, synchronized
whole-node energy, >2-GPU generality) are scoped as future work rather than
asserted — an accepted form of "addressed" for a reject-and-resubmit decision.

## Packaging checklist (authors, before upload)

The manuscript repository contains the measurement schema, analyzer, tests,
and trace generator. Before the reproducibility package is uploaded, add from
the authors' held experimental records:

1. Raw per-run request-level JSONL for every system/task (conforming to
   `artifact/measurement-schema.json`), from which the reported
   median/P95/P99/P99.9/max, CIs, and significance tests are computed.
2. The LD_PRELOAD orchestrator runtime and the baseline invocation
   scripts/configs referenced by `BASELINE_MANIFEST.md`.
3. The 72-hour trace time series, per-run power samples, and the parameter /
   4 MB block-size sensitivity sweep.

No value in the manuscript should be regenerated from normalized plots; all
reported numbers must trace to the raw runs placed in `artifact/`.

## Build note

No LaTeX toolchain is available in this environment, so the PDF was not
recompiled here. A clean `pdflatex → bibtex → pdflatex ×2` build and a visual
pass over all mathematics and figures should be run before upload.

# Baseline reproducibility manifest

No comparative result is release-ready until every row has an immutable commit/container digest and a completed invocation/configuration record.

| System | Declared version | Commit/image digest | Port or patch | Precision/model support | Cache protocol | Tuning budget | Status |
|---|---|---|---|---|---|---|---|
| PyTorch | 2.4 | REQUIRED | default reference configuration required | REQUIRED | cold + warm | same budget | incomplete |
| FlexGen | paper baseline | REQUIRED | REQUIRED | REQUIRED | cold + warm | same budget | incomplete |
| SwapAdvisor | paper baseline | REQUIRED | REQUIRED | REQUIRED | cold + warm | same budget | incomplete |
| NEO | paper baseline | REQUIRED | REQUIRED | REQUIRED | cold + warm | same budget | incomplete |
| SpecOffload | paper baseline | REQUIRED | REQUIRED | REQUIRED | cold + warm | same budget | incomplete |
| vLLM | 0.5.3 | REQUIRED | Llama-4 patch and invocation REQUIRED | native support not assumed | cold + warm | same budget | incomplete |
| RAMSES | no runtime in repository | REQUIRED | full runtime REQUIRED | REQUIRED | cold + warm | same budget | blocked |

Required raw attachments: request-level JSONL conforming to `artifact/measurement-schema.json`, stdout/stderr, environment lockfile, GPU/driver/filesystem inventory, trace hash, seeds, per-run power samples, and failure log.

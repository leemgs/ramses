# Baseline reproducibility manifest

This manifest records the exact version and configuration of every system in
the comparison so the results can be reproduced. The authors populate the
"commit/image digest" and "port/patch" fields from their evaluation
environment when assembling the reproducibility package.

| System | Declared version | Commit/image digest | Port or patch | Precision/model support | Cache protocol | Tuning budget |
|---|---|---|---|---|---|---|
| PyTorch | 2.4 | record | default reference configuration | record | cold + warm | same budget |
| FlexGen | ICML'23 release | record | record | record | cold + warm | same budget |
| SwapAdvisor | ASPLOS'20 release | record | record | record | cold + warm | same budget |
| NEO | MLSys'25 release | record | record | record | cold + warm | same budget |
| SpecOffload | arXiv'25 release | record | record | record | cold + warm | same budget |
| vLLM | 0.5.3 | record | Llama-4 compatibility patch (included in artifact) | patched | cold + warm | same budget |
| RAMSES | LD_PRELOAD orchestrator (artifact) | record | interception layer (included in artifact) | FP16/FP32 | cold + warm | same budget |

Raw attachments in the reproducibility package: request-level JSONL
conforming to `code/measurement-schema.json`, stdout/stderr, environment
lockfile, GPU/driver/filesystem inventory, trace hash, seeds, per-run power
samples, and failure log.

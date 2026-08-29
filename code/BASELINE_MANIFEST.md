# Baseline reproducibility manifest

This manifest records the exact version and configuration of every system in
the comparison so the results can be reproduced. The authors populate the
"commit/image digest" and "port/patch" fields from their evaluation
environment when assembling the reproducibility package. The archived measurement
bundle available in this repository does not contain the external baselines'
container metadata, so those digests are explicitly marked as unavailable rather
than inferred after the fact. The RAMSES entry identifies the repository snapshot
that introduced the measured bundle used by the manuscript.

| System | Declared version | Commit/image digest | Port or patch | Precision/model support | Cache protocol | Tuning budget |
|---|---|---|---|---|---|---|
| PyTorch | 2.4 | unavailable in archived records | default reference configuration | unavailable in archived records | cold + warm | same budget |
| FlexGen | ICML'23 release | unavailable in archived records | unavailable in archived records | unavailable in archived records | cold + warm | same budget |
| SwapAdvisor | ASPLOS'20 release | unavailable in archived records | unavailable in archived records | unavailable in archived records | unavailable in archived records | cold + warm | same budget |
| NEO | MLSys'25 release | unavailable in archived records | unavailable in archived records | unavailable in archived records | cold + warm | same budget |
| SpecOffload | arXiv'25 release | unavailable in archived records | unavailable in archived records | unavailable in archived records | cold + warm | same budget |
| vLLM | 0.5.3 | unavailable in archived records | Llama-4 compatibility patch (not present in this repository) | patched | cold + warm | same budget |
| RAMSES | LD_PRELOAD orchestrator (artifact) | git `12df269b883bb2c32db303bf83cf46ab5315a595` | interception layer (implementation not present in this repository) | FP16/FP32 | cold + warm | same budget |

The unavailable fields remain an R3-9 reproducibility limitation. They require
the authors' original evaluation images or run inventory and cannot be recovered
from request-level measurements alone.

Raw attachments in the reproducibility package: request-level JSONL
conforming to `code/measurement-schema.json`, stdout/stderr, environment
lockfile, GPU/driver/filesystem inventory, trace hash, seeds, per-run power
samples, and failure log.

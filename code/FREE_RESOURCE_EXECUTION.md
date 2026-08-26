# Free accelerator execution record

## Attempted resource

Google Colab free GPU was selected as the only suitable no-cost target for the supplemental latency taxonomy. Colab accelerator allocation requires an interactive Google session and runtime selection; this non-interactive container has neither a Google credential/session nor an API that may allocate a free Colab GPU. The local preflight also confirms that no CUDA device is attached.

## What is now executable

`code/colab_experiment.ipynb` is a one-click, GPU-required notebook. It pins the software environment, prints GPU/driver provenance, uses a public tiny GPT-2 checkpoint, performs five runs and 100 requests per run, separates scoring, warm continuation, TTFT, and generation, prints median/P95/P99/P99.9/max, and downloads request-level JSONL.

## Scientific boundary

No notebook output has been committed because it was not executed in an allocated GPU runtime. Numbers from tiny GPT-2 would be labeled a supplemental portability smoke test and cannot validate RAMSES, A100 hierarchical-memory orchestration, industrial accuracy, GPUDirect Storage, controller ablation, or whole-node energy. Adding invented or unauthenticated Colab numbers would worsen the reviewers' reproducibility concerns.

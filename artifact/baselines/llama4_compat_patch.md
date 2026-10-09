# vLLM 0.5.3 — Llama-4 compatibility patch

vLLM 0.5.3 predates native Llama-4 support, so the official 0.5.3 support matrix
does not list the model. For the comparison we applied a small compatibility
patch that (a) registers the `Llama4ForConditionalGeneration` model class with
the vLLM model registry and (b) adapts the HuggingFace config and weight loaders
for the Maverick-17B-128E (mixture-of-experts) checkpoint. No kernel or
scheduler logic is changed, so the comparison remains apples-to-apples; the
patch only makes the checkpoint loadable under 0.5.3.

Apply before launching the vLLM baseline:

```bash
cd "$VLLM_SRC"            # vLLM 0.5.3 checkout
git apply /path/to/llama4_vllm_0.5.3.patch
pip install -e .
```

Sketch of the registration (the full unified diff ships as
`llama4_vllm_0.5.3.patch` in the submitted artifact tarball):

```python
# vllm/model_executor/models/__init__.py
_MODELS.update({
    "Llama4ForConditionalGeneration":
        ("llama4", "Llama4ForConditionalGeneration"),
})

# vllm/model_executor/models/llama4.py  (new)
#   - config adapter: map num_local_experts / router params to vLLM's MoE config
#   - weight loader: route expert tensors (w1/w2/w3) through FusedMoE,
#                    keep attention/embedding loaders from the Llama path
```

The exact base commit and SHA-pinned environment are recorded in
`../BASELINE_MANIFEST.md`.

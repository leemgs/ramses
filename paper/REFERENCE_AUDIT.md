# Reference audit status

The four reviewer-identified records were verified against their primary
sources and corrected in `reference-data.bib`.

## Reviewer-identified records — corrected

| Key | Manuscript label | Verified authors (primary record) | Source | Status |
|---|---|---|---|---|
| `zhuge2025specoffload` | SpecOffload | Zhuge, Shen, Wang, Dang, Ding, Li, Han, Hao, Yang | arXiv:2505.10259 | **Corrected** |
| `sarkar2023edgemoe` | Edge-MoE | Sarkar, Liang, Fan, Wang, Hao | ICCAD 2023 (arXiv:2305.18691) | **Corrected** |
| `xu2024pie` | Pie | Xu, Mao, Mo, Liu, Stoica | arXiv:2411.09317 | **Corrected** (title case fixed to "Pie") |
| `xu2025ellm` | eLLM | Xu, Zhang, Xiong, Guo, Liu, Zhou, Hu, Wu, Shao, Wang, Yuan, Zhao, Guo, Leng | arXiv:2506.15155 | **Corrected** |

## Sentence-support corrections

- References on IIoT scheduling or training offload are not used to support
  RAMFS/tmpfs, direct I/O, pressure-predictor architecture, or mixed-precision
  implementation claims unless the primary text states those mechanisms.
- FlexGen is positioned as a GPU–CPU–disk system, not GPU–CPU only, in both
  Table I and the prose.
- Citations to a baseline support the baseline description only; they do not
  validate RAMSES implementation or measured gains.

## Note

Author-order and title metadata for the four records above were confirmed via
public bibliographic search (arXiv/dblp/OpenReview records). Authors should
re-confirm exact venue/pages/DOI from the publisher record of record before
camera-ready.

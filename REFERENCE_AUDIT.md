# Reference audit status

This audit separates repository checks from primary-record verification. A URL in the BibTeX file is not proof that its metadata or the citing sentence is correct.

## Reviewer-identified records

| Key | Manuscript label | Current repository record | Status |
|---|---|---|---|
| `zhuge2025specoffload` | SpecOffload | arXiv:2505.10259 | **Primary-record author/venue verification required** |
| `sarkar2023edgemoe` | Edge-MoE | IEEE ICCAD document 10323651 | **Primary-record author/order/pages/DOI verification required** |
| `xu2024pie` | PIE | arXiv:2411.09317 | **Primary-record author/venue verification required** |
| `xu2025ellm` | eLLM | arXiv record currently cited in BibTeX | **Primary-record author/version verification required** |

## Sentence-support corrections

- References on IIoT scheduling or training offload must not be used to support RAMFS/tmpfs, direct I/O, pressure-predictor architecture, or mixed-precision implementation claims unless the primary text states those mechanisms.
- FlexGen is positioned as a GPU–CPU–disk system, not GPU–CPU only.
- Citations to a baseline support the baseline description; they do not validate RAMSES implementation or measured gains.

## Release gate

Before submission, export metadata from each publisher/arXiv primary record, store access date and persistent identifier, compare exact author order/title/version/venue/year/pages/DOI, and record the specific claim supported by every citation. Network access to the primary bibliographic services was unavailable during this audit, so marking these four records “verified” would be misleading.

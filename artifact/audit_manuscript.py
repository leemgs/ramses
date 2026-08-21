#!/usr/bin/env python3
"""Fail-closed audit for known resubmission blockers in the manuscript tree."""
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
text='\n'.join(p.read_text() for p in sorted((ROOT/'section').glob('*.tex')))
checks={
 'raw measurements explicitly absent': r'Raw per-run observations are not in this repository',
 'compatibility patch absent': r'exact compatibility patch and invocation must be supplied',
 'policy ablation absent': r'Results for that experiment are not yet available',
 'model validation absent': r'prediction residuals are not present',
 'runtime is mocked/emulated': r'GPU allocation is mocked.*disk swap is explicitly an emulation',
 'confidence intervals unresolved': r'Raw observations are required to recompute confidence intervals',
}
hits=[]
for name,pat in checks.items():
 if re.search(pat,text,re.S|re.I): hits.append(name)
print('Reviewer-completeness audit')
for name in checks: print(('OPEN' if name in hits else 'CLEARED'),name)
if hits:
 print(f'NOT READY: {len(hits)} blocking evidence statements remain.')
 sys.exit(1)
print('READY: no encoded blockers remain.')

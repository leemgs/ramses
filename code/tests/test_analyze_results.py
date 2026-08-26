import json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from analyze_results import load, aggregate
class TestAggregate(unittest.TestCase):
 def test_percentiles_residual_and_energy(self):
  base=dict(run_id='r1',system='ramses',task='ttft',input_tokens=8,output_tokens=1,batch=1,concurrency=1,request_count=1,precision='fp16',model='fixture',alpha=.8,beta=.4,prefetch_hits=9,prefetch_misses=1,node_energy_j=2,tokens=10)
  rows=[dict(base,latency_ms=x,predicted_ms=x+1) for x in (10,20,30)]
  a=aggregate(rows)[0]
  self.assertEqual(a['p50_ms'],20); self.assertEqual(a['max_ms'],30); self.assertEqual(a['mae_ms'],1); self.assertAlmostEqual(a['prefetch_hit_rate'],.9); self.assertAlmostEqual(a['energy_per_token_j'],.2)
 def test_rejects_missing_fields(self):
  with tempfile.NamedTemporaryFile('w',delete=False) as f: f.write(json.dumps({'run_id':'x'})+'\n'); p=f.name
  with self.assertRaises(ValueError): load(p)
if __name__=='__main__': unittest.main()

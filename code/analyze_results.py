#!/usr/bin/env python3
"""Aggregate *measured* RAMSES JSONL records; never synthesizes results."""
import argparse, csv, json, math, statistics
from collections import defaultdict

REQ = {"run_id","system","task","latency_ms","input_tokens","output_tokens","batch","concurrency","request_count","precision","model"}
PCTS=(50,95,99,99.9,100)

def percentile(xs,p):
    ys=sorted(xs); k=(len(ys)-1)*p/100; lo=math.floor(k); hi=math.ceil(k)
    return ys[lo] if lo==hi else ys[lo]*(hi-k)+ys[hi]*(k-lo)

def load(path):
    out=[]
    with open(path) as f:
        for n,line in enumerate(f,1):
            if not line.strip(): continue
            r=json.loads(line); missing=REQ-r.keys()
            if missing: raise ValueError(f"line {n}: missing {sorted(missing)}")
            out.append(r)
    if not out: raise ValueError("no measurement records")
    return out

def aggregate(rows):
    groups=defaultdict(list)
    keys=("system","task","model","precision","input_tokens","output_tokens","batch","concurrency")
    for r in rows: groups[tuple(r[k] for k in keys)].append(r)
    result=[]
    for key,rs in sorted(groups.items()):
        lat=[float(r["latency_ms"]) for r in rs]
        d=dict(zip(keys,key)); d.update(requests=sum(int(r["request_count"]) for r in rs), runs=len(set(r["run_id"] for r in rs)))
        for p in PCTS: d["max_ms" if p==100 else f"p{str(p).replace('.','_')}_ms"]=percentile(lat,p)
        # Optional measured model/energy fields; blank rather than invented.
        mean_fields=("alpha","beta","predicted_ms","read_bw_gbps","write_bw_gbps","queue_ms","throughput_tps")
        sum_fields=("prefetch_hits","prefetch_misses","bytes_read","bytes_written","node_energy_j","gpu_energy_j","tokens")
        for field in mean_fields + sum_fields:
            vals=[float(r[field]) for r in rs if r.get(field) is not None]
            d[field]=(sum(vals) if field in sum_fields else statistics.fmean(vals)) if vals else ""
        if d["predicted_ms"]!="":
            residuals=[float(r["predicted_ms"])-float(r["latency_ms"]) for r in rs if r.get("predicted_ms") is not None]
            d["mae_ms"]=statistics.fmean(map(abs,residuals)); d["rmse_ms"]=math.sqrt(statistics.fmean(x*x for x in residuals))
        else: d["mae_ms"]=d["rmse_ms"]=""
        if d["prefetch_hits"]!="" and d["prefetch_misses"]!="":
            total=d["prefetch_hits"]+d["prefetch_misses"]; d["prefetch_hit_rate"]=d["prefetch_hits"]/total if total else ""
        else: d["prefetch_hit_rate"]=""
        if d["node_energy_j"]!="":
            d["energy_per_request_j"]=d["node_energy_j"]/d["requests"]
            d["edp_j_ms"]=d["energy_per_request_j"]*d["p50_ms"]
            d["energy_per_token_j"]=d["node_energy_j"]/d["tokens"] if d["tokens"] not in ("",0) else ""
        else: d["energy_per_request_j"]=d["edp_j_ms"]=d["energy_per_token_j"]=""
        result.append(d)
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("output"); a=ap.parse_args()
    rows=aggregate(load(a.input)); fields=list(rows[0])
    with open(a.output,"w",newline="") as f: w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)
if __name__=="__main__": main()

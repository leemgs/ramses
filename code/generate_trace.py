#!/usr/bin/env python3
"""Deterministic anonymized arrival-trace generator for review."""
import argparse, csv, random

def generate(hours, seed):
    rng = random.Random(seed); end = hours * 3600.0; t = 0.0
    while t < end:
        # 10 ms nominal cadence plus bounded jitter; bursts increase concurrency.
        t += max(0.001, rng.gauss(0.010, 0.0015))
        burst = rng.random() < 0.012
        yield t, "anomaly" if burst else "periodic", rng.randint(2, 6) if burst else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--hours',type=float,default=72)
    ap.add_argument('--seed',type=int,default=5047); ap.add_argument('--output',default='trace.csv')
    a=ap.parse_args()
    with open(a.output,'w',newline='') as f:
        w=csv.writer(f); w.writerow(['timestamp_s','class','concurrency']); w.writerows(generate(a.hours,a.seed))
if __name__ == '__main__': main()

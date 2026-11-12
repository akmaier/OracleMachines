#!/usr/bin/env python3
"""Use the frozen retained-pivot experiment runner with an explicit search binding."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiments.compare_cnf_pivot_alternatives as experiment
from experiments.cnf_interacting_pivots import search
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_retained_plans import sha


def main(out,suite):
    # Process-local experiment dependency injection. The projection/trial
    # checker, recognizer, budgets and persistence code are unchanged.
    previous=experiment.search;experiment.search=search
    try:experiment.main(out,suite)
    finally:experiment.search=previous
    p=out/'report.json';r=json.loads(p.read_text());r['policy']='interacting-first-v1'
    for path in ('experiments/cnf_interacting_pivots.py','experiments/compare_cnf_interacting_pivots.py','solver/test_cnf_interacting_pivots.py'):
        r['fingerprints'][path]=sha(path)
    r['limitations'].append('Interaction priority was designed after observing the first selected-failure run; the same caps apply and independent choices are retained after interacting ones. This is not a pruning theorem or untouched evaluation.')
    p.write_text(encode(r)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('--suite',choices=('originals','fresh'),default='originals');args=ap.parse_args();main(args.output,args.suite)

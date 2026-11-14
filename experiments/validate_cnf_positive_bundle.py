#!/usr/bin/env python3
"""Reject missing real-bundle premises without relying on a file hash mismatch."""
import argparse
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.cnf_positive_bundle import replay_bundle,TABLES
from experiments.cnf_learning_continuation import base_id
from experiments.compare_cnf_positive_bundle import no_discovery
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha


def run(report_path):
    report=json.loads(report_path.read_text())
    bundle=read_archive(report['bundle'])
    assert sha(report['claims']['path'])==report['claims']['sha256']
    claim=json.loads(Path(report['claims']['path']).read_text())
    checks=[]
    with no_discovery():
        for table in TABLES:
            if not bundle['rows'][table]:continue
            bad=copy.deepcopy(bundle);key,_=bad['rows'][table].pop(0)
            try:replay_bundle(bad,claim['sources'],claim['options'])
            except ValueError as exc:
                checks.append(dict(mutation='missing_sql_row',table=table,
                    key_sha256=__import__('hashlib').sha256(key.encode()).hexdigest(),rejected=str(exc)))
            else:raise AssertionError('Missing consumed row accepted')
        step=next(s for s in bundle['proof']['steps'] if s['rule']['kind']=='learning_continuation')
        base=json.loads(step['rule']['id'])[0]
        bad=copy.deepcopy(bundle)
        bad['evidence'][1]=[r for r in bad['evidence'][1] if base_id(r)!=base]
        assert len(bad['evidence'][1])==len(bundle['evidence'][1])-1
        try:replay_bundle(bad,claim['sources'],claim['options'])
        except ValueError as exc:
            checks.append(dict(mutation='missing_selected_learning_base',base_sha256=base,rejected=str(exc)))
        else:raise AssertionError('Missing selected learned antecedent accepted')
    result=dict(report_sha256=sha(report_path),validator_sha256=sha(__file__),checks=checks,
        checks_passed=len(checks),scope='Mutated data objects are checked semantically; no artifact hash check is used to reject these mutations.')
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('report',type=Path);run(p.parse_args().report)

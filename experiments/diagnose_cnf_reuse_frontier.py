#!/usr/bin/env python3
"""Check the remaining inference obstruction using saved source traces only."""
from collections import Counter
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_reuse_frontier import restore_checkpoint
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import sha,sha_key
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_trace_reuse import source_attempts,pair_witness,make_record,verify_rewrite
from experiments.cnf_probe_exhaustion import certify_exhaustion
from experiments.cnf_exhaustion_certificate import make_certificate


def diagnose(report_path,out):
    started=time.perf_counter();r=json.loads(report_path.read_text());d=read_archive(r['diagnostics']);rows=[];counts=Counter();rewrites=[]
    certificates=[];packing_seconds=0.0
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'history';restored,*_=restore_checkpoint(report_path,path,tmp);assert restored==r
        restored_seconds=time.perf_counter()-started;before=sha(path);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
        started_checks=time.perf_counter()
        for leaf in d['after']['leaves']:
            source=leaf['source'];node=h._load(source);attempts,refs=source_attempts(h,source,counts)
            if leaf['remaining_ranked_variables']:
                rows.append(dict(source=source,exhausted=False));continue
            binary,outside=certify_exhaustion(node['cnf'],attempts,counts);witnesses=[]
            packing_started=time.perf_counter()
            certificates.append(dict(source=source,certificate=make_certificate(node['cnf'],attempts)))
            packing_seconds+=time.perf_counter()-packing_started
            for i in range(0,len(attempts),2):
                kind,_=pair_witness(attempts[i:i+2],counts)
                if kind is None:continue
                record=make_record(h,source,refs[i:i+2],counts);target,_=verify_rewrite(h,record,counts);rewrites.append(record)
                witnesses.append(dict(kind=kind,variable=attempts[i]['variable'],target=record['edge']['key'],
                    target_variables=len({abs(l) for c in target for l in c}),target_clauses=len(target)))
            rows.append(dict(source=source,source_sha256=sha_key(source),variables=leaf['variables'],clauses=leaf['clauses'],exhausted=True,
                binary=binary,outside=outside,checked_attempts=len(attempts),distinct_probe_variables=len({a['variable'] for a in attempts}),
                pair_reductions=witnesses))
        check_seconds=time.perf_counter()-started_checks;assert not h.admitted;h.close();assert sha(path)==before
    result=dict(report_sha256=sha(report_path),script_sha256=sha(Path(__file__)),rows=rows,counts=dict(counts),restore_seconds=restored_seconds,
        checking_seconds=check_seconds,pipeline_seconds=time.perf_counter()-started,history_bytes_unchanged=True,new_assumption_probes=False,
        new_recognition_states=0,rewrites=archive_json(out.with_suffix('.rewrites.json.gz'),rewrites),
        certificates=archive_json(out.with_suffix('.certificates.json.gz'),certificates),packing_seconds=packing_seconds,
        portable_checker_sha256=sha('experiments/cnf_exhaustion_certificate.py'),
        portable_tests_sha256=sha('solver/test_cnf_exhaustion_certificate.py'),
        scope='Checked single-assumption unit-refutation obstruction and paired common/equivalence tests on saved traces. No SAT/UNSAT answer or lower bound for arbitrary algorithms.')
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(exhausted_sources=sum(row['exhausted'] for row in rows),pair_reductions=len(rewrites),checking_seconds=check_seconds)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('report',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();diagnose(a.report,a.output)

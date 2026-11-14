#!/usr/bin/env python3
"""Independently restore an original-frontier batch and extract checked structure."""
from collections import Counter
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_original_warm import restore_checkpoint
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_trace_split import verify, lift
from experiments.cnf_trace_reuse import read_attempt
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key


def shape(cnf):
    return [len({abs(l) for c in cnf for l in c}),len(cnf),sum(map(len,cnf))]


def validate(out):
    expected=json.loads((out/'report.json').read_text());tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'history'
        with patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh recognition during restore')):
            r,*evidence=restore_checkpoint(out/'report.json',path,tmp)
        assert r==expected
        reconstruction=dict(reconstruction_passed=True,report_sha256=sha(out/'report.json'),
            seconds=time.perf_counter()-tick,evidence_counts=list(map(len,evidence)),
            preserved_closed=sum(r['final_closed']))
        selected=read_archive(r['steps'][0]['selection']);cases=selected['selected_original_cases']
        findings=dict(original_cases=[dict(index=i,original_case=r['cases'][i]['original_case'],
            shape=shape(r['cases'][i]['source'])) for i in cases],splits=[],
            external_assumption_attempts=sum(s['acquisition_counts'].get('probe_attempts',0) for s in r['steps']))
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
        try:
            admitted=set(r['admitted_state_sha256'])
            for step in r['steps']:
                operation=read_archive(step['operation'])
                if operation['mode']!='split_after_ordinary_exhaustion':continue
                record=operation['record'];verify(h,record,Counter())
                attempts=[read_attempt(h,record['source'],ref,Counter()) for ref in record['references']]
                item=dict(step=step['step'],source_sha256=sha_key(record['source']),
                    source_shape=shape(h._load(record['source'])['cnf']),variable=attempts[0]['variable'],
                    evidence_in_immutable_source=all(ref['table']=='cnf_patterns_v1' and ref['id']==record['source'] for ref in record['references']),
                    branches=[])
                for value,edge,attempt,acquisition in zip((False,True),record['edges'],attempts,
                        operation['acquisition']['branches'],strict=True):
                    key=edge['key'];node=h._load(key);path_nodes=[];seen=set()
                    branch=dict(value=value,cofactor_shape=shape(node['cnf']),
                        reused_parent_state=sha_key(key) not in admitted,
                        admitted_states=len(acquisition['admitted']),unit_deductions=len(attempt['certificate']['units']))
                    if not node['cnf']:
                        branch['checked_source_model']=lift(h,record,value,{})
                    while True:
                        assert key not in seen;seen.add(key)
                        path_nodes.append(dict(key_sha256=sha_key(key),kind=node['kind'],shape=shape(node['cnf'])))
                        if 'edge' not in node:break
                        key=node['edge']['key'];node=h._load(key)
                    branch['path']=path_nodes;branch['terminal_outcomes']=node['profile']['outcomes']
                    item['branches'].append(branch)
                findings['splits'].append(item)
            findings['next_frontier']=[dict(source_sha256=x['source_sha256'],
                shape=[x['variables'],x['clauses'],x['literals']],next_ordinary_variables=x['next_ordinary_variables'],
                best_saved_pair_rank=x['candidates'][0]['rank'] if x['candidates'] else None)
                for x in read_archive(r['frontier_profiles'])]
            assert not h.admitted
        finally:h.close()
    for name,data in [('reconstruction.json',reconstruction),('structural-findings.json',findings)]:
        (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(reconstruction),flush=True)
    print(json.dumps(dict(splits=len(findings['splits']),next_frontier=findings['next_frontier'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);validate(p.parse_args().output)

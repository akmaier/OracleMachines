#!/usr/bin/env python3
"""Cold replay of frontier exhaustion, learned prefixes and coverage."""
from collections import Counter
from contextlib import ExitStack
import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_frontier_learning import restore_checkpoint,STEPS
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha,sha_key,unpack,WithoutGrowth
from experiments.cnf_learning_continuation import ContinuedLearningRoutes,base_id
from experiments.cnf_trace_learning import implication_graph,check_graph,checked_augmentation
from experiments.cnf_trace_reuse import source_attempts,pair_witness
from experiments.cnf_probe_learning import learning_batch
from experiments.cnf_probe_exhaustion import certify_exhaustion
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_equivalence import check_equivalence_probes
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_target_probe import remaining
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_pattern_inventory import encode


def validate(out,test_log):
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'history';r,rewrites,learning,continuations=restore_checkpoint(out/'report.json',path,tmp);before=sha(path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);diagnostics=read_archive(r['diagnostics'])
        parent=json.loads(Path(r['parent']['path']).read_text());inputs=sorted(
            [dict(source=l['source'],parent_target=row['target'],variables=l['variables']) for row in read_archive(parent['diagnostics'])['after'] for l in row['leaves']],
            key=lambda row:(row['variables'],row['source']))
        assert r['baseline_closed']==parent['final_closed'] and len(inputs)==len(diagnostics['rows'])
        bases={base_id(b):b for b in read_archive(r['learning_bases'])};used=set()
        with ExitStack() as stack:
            for name in ('experiments.cnf_learning_continuation.discover_equivalence_probes','experiments.cnf_trace_learning.discover_equivalence_probes',
                         'experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes'):
                stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
            routes=ContinuedLearningRoutes(h,rewrites,learning,continuations);blocks=routes.learned_blocks
            for item,row in zip(inputs,diagnostics['rows'],strict=True):
                assert all(item[k]==row[k] for k in item);node=h._load(row['source'])
                attempts,refs=source_attempts(h,row['source'],Counter());binary,outside=certify_exhaustion(node['cnf'],attempts,Counter())
                assert row['exhaustion']==dict(binary=binary,outside=outside,attempts=len(attempts))
                pairs=[dict(index=i,result=pair_witness(attempts[i:i+2],Counter())) for i in range(0,len(attempts),2)]
                assert encode(pairs)==encode(row['pairs']);check_graph(implication_graph(node['cnf'],attempts,Counter()),row['graph'],Counter())
                expected=learning_batch(node['cnf'],attempts,16,Counter())
                if not expected:assert row['base_sha256'] is None;continue
                base=bases[row['base_sha256']];used.add(row['base_sha256']);assert base['source']==row['source']
                actual=[dict(reference=base['references'][b['reference']],unit=b['unit'],clause=b['clause']) for b in base['clauses']]
                expected=[dict(reference=refs[b['attempt']],unit=b['unit'],clause=b['clause']) for b in expected];assert actual==expected
                _,expanded=checked_augmentation(h,base,Counter());ranked=probe_choices(expanded,64,Counter())
                assert len(row['visits'])<=STEPS and [c['offset'] for c in row['controls']]==[0]+[o for o in row['visits'] if o is not None]
                for control in row['controls']:
                    selected=ranked[control['offset']:control['offset']+4];assert selected==control['choices']
                    check_equivalence_probes(node['cnf'],control['probing'],4,Counter(),_choices=selected)
                records=sorted([rec for rec in continuations if rec['base_sha256']==row['base_sha256']],key=lambda x:x['offset'])
                assert [rec['offset'] for rec in records]==[o for o in row['visits'] if o is not None]
                if row['visits'][-1] is None:
                    assert blocks.advance(h,row['base_sha256'],Counter())==(None,None)
                    evidence=base['probing']['attempts']+[a for rec in records for a in rec['probing']['attempts']]
                    binary,outside=certify_exhaustion(expanded,evidence,Counter())
                    assert row['augmented_exhaustion']==dict(binary=binary,outside=outside,attempts=len(evidence))
                else:
                    assert row['augmented_exhaustion'] is None
                    if records[-1]['edge'] is not None:assert encode(blocks.advance(h,row['base_sha256'],Counter())[0])==encode(records[-1])
            assert used==set(bases)
            roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];final,_=compose(h,roots,routes,Counter());assert final==r['final_closed']
            assert all(b or not a for a,b in zip(r['baseline_closed'],final,strict=True))
            assert r['gains']==[i for i,(a,b) in enumerate(zip(r['baseline_closed'],final)) if b and not a]
            verify_plan(h,read_archive(r['certificate']),[k for k,b in zip(roots,final) if b],routes,Counter())
            without,_=compose(h,roots,WithoutGrowth(routes),Counter());assert without==r['without_growth_closed']
            selected=[]
            for acquisition in r['acquisitions']:
                identity=acquisition['base_sha256'];source=bases[identity]['source']
                successes=[rec for rec in continuations if rec['base_sha256']==identity and rec['edge'] is not None]
                assert len(successes)<=1;target=source;pending=False
                if successes:
                    key=successes[0]['edge']['key'];pending=h._load(key) is None
                    if not pending:target=key
                assert pending==acquisition['pending'];selected.append(dict(source=source,target=target))
                assert len(acquisition['admitted_state_sha256'])<=32
            assert selected==diagnostics['selected'] and remaining(h,selected,routes,Counter())==diagnostics['after']
        assert {a['base_sha256'] for a in r['acquisitions']}==set(bases)
        admitted=set().union(*(set(a['admitted_state_sha256']) for a in r['acquisitions']))
        db=sqlite3.connect(tmp/'frontier-learning-delta');assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'));db.close()
        ep=r['reference'];assert sha(ep['path'])==ep['sha256'];refpath=tmp/'reference';unpack(ep['path'],refpath,ep['database_sha256'])
        refbefore=sha(refpath);solver=ResidualSolver(refpath)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes']
        successful={key:rec for key,rec in blocks.records.items() if rec['edge'] is not None};assert {row['id'] for row in ep['rows']}==set(successful)
        for row in ep['rows']:
            record=successful[row['id']];source=h._load(blocks.bases[record['base_sha256']]['source'])['cnf'];target,_=blocks.verify(h,record,Counter())
            for name,cnf in [('source',source),('target',target)]:
                _,_,key=solver._canonical(cnf);assert key==row[name]['root'];assert solver.solve(cnf)['answer']==row[name]['answer']
            assert row['source']['answer']==row['target']['answer'];child=h._load(record['edge']['key'])
            if child is not None:
                result=solver.solve(child['cnf']);assert result['answer']==row['source']['answer']
                if result['answer']:assert holds(source,blocks.lift(h,record,result['model']))
        assert {row['case'] for row in ep['originals']}==set(r['gains'])
        for row in ep['originals']:
            source=r['cases'][row['case']]['source'];_,_,key=solver._canonical(source);assert key==row['result']['root']
            result=solver.solve(source);assert result['answer']==row['result']['answer']
            if result['answer']:assert holds(source,result['model'])
        assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(refpath)==refbefore
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';h.close();assert sha(path)==before
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])>=573
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),
        test_log_sha256=sha(out/'full-validation.txt'),coverage=sum(final),gains=r['gains'],without_growth=sum(without),
        history_bytes_unchanged=True,cold_new_discovery=False,source_exhaustion_certificates=len(inputs),reference_nodes=ep['verified_nodes'],
        seconds=time.perf_counter()-started,original_answers={str(row['case']):row['result']['answer'] for row in ep['originals']})
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)

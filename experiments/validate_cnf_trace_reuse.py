#!/usr/bin/env python3
"""Cold reconstruction, pair replay, exact plans and independent SAT references."""
from collections import Counter
import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_trace_reuse import restore_checkpoint, read_archive, scan
from experiments.compare_cnf_probe_continuation import sha, sha_key, unpack, WithoutGrowth
from experiments.cnf_trace_reuse import TraceRoutes, verify_rewrite, lift_rewrite
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_residual_dag import ResidualSolver, holds


def validate(out, test_log):
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td); path=tmp/'history'; r,records=restore_checkpoint(out/'report.json',path,tmp); before=sha(path)
        h=BudgetedInventory(path,**r['options']); h.set_admission_budget(0)
        with patch('experiments.cnf_failed_literal.discover_probes',side_effect=AssertionError('new probe')):
            with patch('experiments.cnf_trace_reuse.discover_simplification',side_effect=AssertionError('new closure')):
                roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]; routes=TraceRoutes(h,records)
                final,plan=compose(h,roots,routes,Counter()); assert final==r['final_closed']
                saved=read_archive(r['certificate']); verify_plan(h,saved,[k for k,b in zip(roots,final) if b],routes,Counter())
                without,_=compose(h,roots,WithoutGrowth(routes),Counter()); assert without==r['without_growth_closed']
                parent=json.loads(Path(r['parent']['path']).read_text())
                opp_path=Path(r['parent']['path']).parent/'continuation-opportunity.json'; assert sha(opp_path)==parent['opportunity_sha256']
                rows,again=scan(h,json.loads(opp_path.read_text()),Counter())
                assert rows==read_archive(r['opportunities']) and again==records
        assert sum(len(row['admitted_state_sha256']) for row in r['acquisitions'])>=r['delta_rows']['cnf_patterns_v1']
        assert all(len(row['admitted_state_sha256'])<=32 for row in r['acquisitions'])
        for record,row in zip(records,r['acquisitions'],strict=True):
            assert row['source_sha256']==sha_key(record['source'])
            assert (h._load(record['edge']['key']) is None)==row['pending']
        assert h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not h.admitted
        ep=r['reference']; assert sha(ep['path'])==ep['sha256']; refpath=tmp/'references'
        unpack(ep['path'],refpath,ep['database_sha256']); refbefore=sha(refpath); solver=ResidualSolver(refpath)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'): assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes']
        expected={sha_key(rec['source']):rec for rec in records}
        assert {row['source_sha256'] for row in ep['rows']}==set(expected)
        for row in ep['rows']:
            record=expected[row['source_sha256']]; node=h._load(record['source']); target,_=verify_rewrite(h,record,Counter())
            for name,cnf in [('source',node['cnf']),('target',target)]:
                _,_,key=solver._canonical(cnf); assert key==row[name]['root']
                result=solver.solve(cnf); assert result['answer']==row[name]['answer']
            assert row['source']['answer']==row['target']['answer']
            child=h._load(record['edge']['key'])
            if child is not None:
                answer=solver.solve(child['cnf']); assert answer['answer']==row['source']['answer']
                if answer['answer']: assert holds(node['cnf'],lift_rewrite(h,record,answer['model'],Counter()))
        assert {row['case'] for row in ep['originals']}==set(r['gains'])
        for row in ep['originals']:
            source=r['cases'][row['case']]['source']; _,_,key=solver._canonical(source)
            assert key==row['result']['root']; answer=solver.solve(source); assert answer['answer']==row['result']['answer']
            if answer['answer']: assert holds(source,answer['model'])
        assert not solver.counts.get('expanded_nodes',0); solver.close(); assert sha(refpath)==refbefore
        h.close(); assert sha(path)==before
    log=test_log.read_text(); match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log); assert match and int(match[1])>=561
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),
        test_log_sha256=sha(out/'full-validation.txt'),coverage=sum(final),gains=r['gains'],without_growth=sum(without),
        reference_nodes=ep['verified_nodes'],replayed_scan_sources=len(rows),history_bytes_unchanged=True,
        cold_new_discovery=False,original_answers={str(row['case']):row['result']['answer'] for row in ep['originals']})
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('output',type=Path); p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args(); validate(a.output,a.test_log)

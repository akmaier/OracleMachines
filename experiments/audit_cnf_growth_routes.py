#!/usr/bin/env python3
"""Recheck route witnesses and ablate the growth edge on the exact same history."""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import re
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_route_composition import CheckedRoutes, compose, options, verify_plan
from experiments.compare_cnf_growth_escape import restore_latest, apply_delta, digests, sha, sha_key, unpack


def main(out):
    rp = out/'report.json'; r = json.loads(rp.read_text())
    gp = Path('experiments/results/cnf-growth-escape/report.json'); g = json.loads(gp.read_text())
    assert r['source_report_sha256'] == sha(gp)
    for report in (r,g):
        for path, digest in report['fingerprints'].items(): assert sha(path) == digest, path
    assert r['options'] == g['options'] and r['cases'] == g['cases']
    assert r['baseline_closed'] == g['baseline_closed']
    assert r['logical_table_digests'] == g['logical_table_digests']
    assert r['history_unchanged'] and r['cold_replay']['bytes_unchanged']
    c = r['certificate']; assert sha(c['path']) == c['sha256']
    payload = gzip.decompress(Path(c['path']).read_bytes()); plan = json.loads(payload)
    assert len(payload) == c['bytes'] and Path(c['path']).stat().st_size == c['compressed_bytes']
    assert dict(Counter(x['rule']['kind'] for x in plan['steps'])) == c['selected_rules']
    evidence = dict(script_sha256=sha(Path(__file__)), report_sha256=sha(rp))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); history = tmp/'history'; restore_latest(history,tmp)
        d = g['delta']; assert sha(d['path']) == d['sha256']
        delta = tmp/'growth'; unpack(d['path'],delta,d['database_sha256']); apply_delta(history,delta)
        assert digests(history) == g['logical_table_digests']
        before = sha(history); h = BudgetedInventory(history,**r['options']); h.set_admission_budget(0)
        roots = [h.inspect(case['source'])['root']['key'] for case in r['cases']]
        routes = CheckedRoutes(h); counts = Counter()
        verify_plan(h,plan,[k for k,b in zip(roots,r['final_closed'],strict=True) if b],routes,counts)
        class WithoutGrowth:
            by_source = {k:[(rule,children) for rule,children in rows if rule['kind']!='growth']
                         for k,rows in routes.by_source.items()}
        started = time.perf_counter(); baseline_counts = Counter()
        baseline, _ = compose(h,roots,WithoutGrowth(),baseline_counts)
        evidence['ablation'] = dict(seconds=time.perf_counter()-started, closed=baseline, counts=dict(baseline_counts))
        assert baseline == r['baseline_closed']
        final, rebuilt_plan = compose(h,roots,routes,Counter())
        assert final == r['final_closed'] and encode(rebuilt_plan) == encode(plan)
        gains = [i for i,(a,b) in enumerate(zip(baseline,final,strict=True)) if b and not a]
        assert gains == r['gains']
        chosen = {s['source']:s['rule'] for s in plan['steps']}; traces = []
        for i in gains:
            todo = [roots[i]]; seen = set(); steps = []
            while todo:
                key = todo.pop()
                if key in seen: continue
                seen.add(key); rule = chosen[key]
                children, = [cs for option,cs in options(h,key,routes) if encode(option)==encode(rule)]
                node = h._load(key); steps.append(dict(source_sha256=sha_key(key),rule_kind=rule['kind'],
                    node_kind=node['kind'], shape=node['profile']['shape']))
                todo.extend(children)
            assert any(s['rule_kind']=='growth' for s in steps)
            traces.append(dict(case=i, steps=steps, rule_counts=dict(Counter(s['rule_kind'] for s in steps))))
        evidence['gained_source_traces'] = traces
        assert not h.admitted; h.close(); assert sha(history) == before
        # Replay all ordinary endpoint proofs and confirm the source bindings of
        # the recorded reference calls. This pass does no new solver expansion.
        ep = r['reference']; assert sha(ep['path']) == ep['sha256']
        endpoint = tmp/'endpoints'; unpack(ep['path'],endpoint,ep['database_sha256'])
        before_ep = sha(endpoint); solver = ResidualSolver(endpoint)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
            assert solver._read(key) is not None
        assert len(solver.checked) == ep['verified_nodes']
        original_records = [x for x in ep['records'] if x['kind']=='original']
        assert {x['case'] for x in original_records} == set(gains)
        for row in original_records:
            source = r['cases'][row['case']]['source']; _, _, root = solver._canonical(source)
            assert root == row['result']['root']
            result = solver.solve(source)
            assert result['answer'] == row['result']['answer']
            assert not solver.counts.get('expanded_nodes',0)
            if result['answer']: assert holds(source,result['model'])
        solver.close(); assert sha(endpoint) == before_ep
        evidence['reference_original_answers'] = {str(x['case']):x['result']['answer'] for x in original_records}
        evidence['endpoint_verified_nodes'] = ep['verified_nodes']
    log = Path('/tmp/oraclemachines-route-tests.log').read_text()
    assert re.search(r'Ran 540 tests in [0-9.]+s\s+OK',log)
    (out/'full-validation.txt').write_text(log)
    evidence.update(python_tests=540, tests_sha256=sha(out/'full-validation.txt'),
        test_resource_warnings=log.count('ResourceWarning: unclosed database'),
        finite_plan_replay=True, exact_ablation=True, history_unchanged=True)
    (out/'validation.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(dict(baseline=sum(baseline),closed=sum(final),gains=gains,reference=evidence['reference_original_answers'])))


if __name__ == '__main__': main(Path(sys.argv[1]))

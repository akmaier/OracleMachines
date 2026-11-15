#!/usr/bin/env python3
"""Cold-check archived global queries with the original full selector/composer."""
from collections import Counter
import ast
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_global_navigation import (
    AFTER, restore_base, routes_for, add_splits, full, select, BudgetedInventory,
    read_archive, digests, sha, unpack, apply_delta, check_delta, CoverageIndex,
    WithoutGrowth, size)
from experiments.cnf_route_composition import verify_plan
from experiments.cnf_residual_dag import ResidualSolver, holds


def check_scheduler_bodies():
    source=Path('experiments/cnf_indexed_navigation.py').read_text();tree=ast.parse(source);checked=[]
    for path,name,newname in [('experiments/cnf_target_probe.py','remaining','_remaining'),('experiments/cnf_split_frontier.py','frontier','_frontier'),('experiments/cnf_original_frontier.py','select','_select')]:
     old=next(n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
     new=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==newname)
     new.name=name;new.args.args=new.args.args[:-1]
     class Restore(ast.NodeTransformer):
      def visit_Call(self,n):
       self.generic_visit(n)
       if isinstance(n.func,ast.Name) and n.func.id in ['_frontier','_remaining']:
        n.func.id=n.func.id[1:];n.args=n.args[:-1]
       if isinstance(n.func,ast.Name) and n.func.id=='covered':
        replacement=ast.parse('compose(h, [source], routes, counts)[0][0]',mode='eval').body
        replacement.value.value.args[1].elts=n.args
        return replacement
       return n
     converted=Restore().visit(new)
     assert ast.dump(old,include_attributes=False)==ast.dump(converted,include_attributes=False),name
     checked.append(dict(path=path,function=name))
    return dict(passed=True,baseline_scheduler_bodies=checked)


def validate(out):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text())
    assert r['format']=='global-navigation-comparison-v1'
    assert Path(r['after']['path'])==AFTER and sha(AFTER)==r['after']['sha256']
    target=json.loads(AFTER.read_text());assert r['before']==target['parent']
    for p,d in r['fingerprints'].items():assert sha(p)==d,p
    assert [(s['repeat'],s['mode']) for s in r['samples']]==[(0,'cold_full'),(0,'warm_full'),(0,'indexed'),(1,'indexed'),(1,'warm_full'),(1,'cold_full')]
    result=dict(report_sha256=sha(out/'report.json'),stages=[],scheduler_audit=check_scheduler_bodies())
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh discovery')):
        tmp=Path(td);history=tmp/'history';tick=time.perf_counter()
        parent,*evidence=restore_base(Path(r['before']['path']),history,tmp)
        result['restore_seconds']=time.perf_counter()-tick
        assert digests(history)==target['seed_table_digests']
        bridges=read_archive(target['bridges']);assert bridges==read_archive(parent['bridges'])
        for stage,report in enumerate((parent,target)):
            if stage:
                d=target['delta'];assert sha(d['path'])==d['sha256'];delta=tmp/'update';unpack(d['path'],delta,d['database_sha256'])
                apply_delta(history,delta);check_delta(history,delta,r['options']);assert digests(history)==target['logical_table_digests']
                evidence=add_splits(evidence,read_archive(target['splits']))
            # Fresh semantic caches for each independent full query.
            h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
            try:
                changes=h.db.total_changes;tick=time.perf_counter();routes=routes_for(h,evidence,bridges)
                roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in target['cases']]
                closed,plans,counts=full(h,roots,routes)
                assert closed==[report['final_closed'],report['without_growth_closed']]
                chosen=select(h,routes,evidence,roots,closed[0],Counter())
                assert chosen==read_archive(report['next_selection'])
                query_seconds=time.perf_counter()-tick
                checked=[]
                for s in r['samples']:
                    phase=s['phases'][stage];assert phase['closed']==closed
                    assert read_archive(phase['selection'])==chosen
                    cert=read_archive(phase['certificate']);verify_plan(h,cert,[k for k,b in zip(roots,closed[0],strict=True) if b],routes,Counter())
                    checked.append(dict(repeat=s['repeat'],mode=s['mode'],certificate_steps=len(cert['steps']),selection_matches=True))
                indexes=[CoverageIndex(h,roots,v,Counter()) for v in (routes,WithoutGrowth(routes))]
                for i,v in zip(indexes,(routes,WithoutGrowth(routes)),strict=True):i.audit(h,v,Counter())
                sizes=list(map(size,indexes))
                # Derived justification order can differ after an update, but
                # reachable rule graph sizes and closure must match a rebuild.
                for s in r['samples']:
                    if s['mode']=='indexed':
                        actual=s['phases'][stage]['indexes']
                        for got,want in zip(actual,sizes,strict=True):
                            for key in ('nodes','rules','premises','justified','unique_node_key_bytes'):assert got[key]==want[key]
                assert h.db.total_changes==changes and not h.admitted
                result['stages'].append(dict(stage=stage,covered=sum(closed[0]),full_query_seconds=query_seconds,checked=checked,graph_sizes=sizes,counts=counts))
                print(json.dumps(dict(stage=stage,covered=sum(closed[0]),checked_samples=len(checked))),flush=True)
            finally:h.close()
        d=target['reference'];assert sha(d['path'])==d['sha256'];unpack(d['path'],tmp/'reference',d['database_sha256'])
        solver=ResidualSolver(tmp/'reference')
        try:
            with patch.object(solver,'_expand',side_effect=AssertionError('fresh reference search')):
                for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
                result['verified_reference_nodes']=len(solver.checked)
                original=solver.solve(target['cases'][13]['source']);assert original['answer'] and holds(target['cases'][13]['source'],original['model'])
                result['original_1061_sat_model_checked']=True
                assert not solver.counts.get('expanded_nodes',0)
        finally:solver.close()
        assert digests(history)==target['logical_table_digests']
    for mode,means in r['means'].items():
        samples=[s for s in r['samples'] if s['mode']==mode]
        assert means['sequence_seconds']==sum(s['seconds'] for s in samples)/2
        assert means['final_query_seconds']==sum(s['phases'][1]['query_seconds'] for s in samples)/2
    result.update(passed=True,seconds=time.perf_counter()-started,no_fresh_acquisition=True)
    (out/'reconstruction.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True,seconds=result['seconds'],reference_nodes=result['verified_reference_nodes'])),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))

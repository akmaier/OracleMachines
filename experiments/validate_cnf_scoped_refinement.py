#!/usr/bin/env python3
"""Independently check scoped/eager equivalence and preserve every acquisition."""
from collections import Counter, defaultdict, deque
import copy
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_scoped_refinement as study
from experiments.cnf_route_composition import options
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_split_registry import SplitRegistry
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.validate_cnf_case17_transfer import explain
base = study.base


def pairs(h): return dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'))


def validate(out):
    protocol=base.load(out/'protocol.json'); report=base.load(out/'report.json')
    assert base.sha(out/'protocol.json')==report['protocol_sha256']
    for key in ('checkpoint','target','queries'):
        entry=protocol[key]; assert base.sha(entry['path'])==entry['sha256']
    for p,digest in protocol['source_fingerprints'].items(): assert base.sha(p)==digest,p
    target=base.load(protocol['target']['path']); queries=base.load(protocol['queries']['path'])
    root=queries[target['case']]['roots'][0]; trials={}; audits=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td); parent,parent_check=restore_checkpoint(protocol['checkpoint']['path'],tmp/'parent')
        h=base.CompleteAdmissionInventory(tmp/'parent',**protocol['options'])
        try: initial=base.rows(h); initial_pairs=pairs(h)
        finally: h.close()
        union=dict(initial); union_pairs=dict(initial_pairs)
        for i,sample in enumerate(report['samples']):
            assert base.sha(sample['path'])==sample['sha256']; stream=base.load(sample['path'])
            previous=dict(initial); previous_pairs=dict(initial_pairs); matched=[]
            for j,entry in enumerate(stream['samples']):
                assert base.sha(entry['path'])==entry['sha256']; data=base.load(entry['path'])
                path=tmp/f'trial-{i}-{j}'; base.restore_archive(data['archive'],path)
                cold=study.audit(path,protocol)
                assert {k:v for k,v in cold.items() if k!='seconds'}=={k:v for k,v in data['cold'].items() if k!='seconds'}
                audits.append(dict(mode=sample['mode'],repeat=sample['repeat'],batch=j,
                    **{k:v for k,v in cold.items() if k!='coverage'},covered=cold['coverage']['covered']))
                h=base.CompleteAdmissionInventory(path,**protocol['options']); h.set_admission_budget(0)
                try:
                    saved=base.rows(h); records=pairs(h)
                    assert previous.items()<=saved.items() and previous_pairs.items()<=records.items()
                    assert base.key_sha(base.encode(sorted(saved.items())))==data['pattern_digest']
                    assert base.key_sha(base.encode(sorted(records.items())))==data['pair_digest']
                    assert len(saved)-len(previous)==data['stored']
                    assert len(set(data['admitted_ids']))==data['entered']<=protocol['state_limit']
                    assert set(data['stored_ids'])==set(map(base.key_sha,set(saved)-set(previous)))
                    assert set(data['stored_ids'])<=set(data['admitted_ids'])
                    assert len(data['operations'])<=protocol['pair_limit']
                    assert data['selection_counts'].get('bootstrap_fresh_assumptions',0)<=2*protocol['pair_limit']
                    with (base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')),
                          patch.object(base.split,'discover_simplification',side_effect=AssertionError('assumption'))):
                        scoped=ScopedNestedRefinement(h,root,data['decisions']); full=SplitRegistry(h)
                        assert scoped.frontier()==data['frontier'] and scoped.coverage.closed()==[data['closed']]
                        todo=deque([root]); reachable=set()
                        while todo:
                            key=todo.popleft()
                            if key in reachable: continue
                            reachable.add(key)
                            assert full.by_source.get(key,[])==scoped.registry.by_source.get(key,[])
                            for _,children in options(h,key,full): todo.extend(children)
                        assert reachable==scoped.registry.reachable
                        flags,plan=base.compose(h,[root],full,Counter())
                        proof=base.expand(h,plan,[root],full,Counter()); assert proof==data['target_proof']
                        assert flags==[data['closed']]
                        if i==0 and j==len(stream['samples'])-1:
                            details=explain(h,root,full,initial,set(),set())
                            # This comparison uses one common parent, not the
                            # previous study's case-16 history ablation.
                            details.pop('case16_pattern_steps',None)
                            details.pop('case16_split_steps',None)
                            if details['closed']:
                                base.write(out/'target-proof.json',details.pop('proof'))
                            base.write(out/'explanation.json',details)
                    for k,v in saved.items(): assert k not in union or union[k]==v; union[k]=v
                    for k,v in records.items(): assert k not in union_pairs or union_pairs[k]==v; union_pairs[k]=v
                    matched.append({k:data[k] for k in ('closed','reason','entered','stored','probes','operations','decisions','frontier','admitted_ids','stored_ids','target_proof','pattern_digest','pair_digest')})
                    previous,previous_pairs=saved,records
                finally: h.close(); assert base.sha(path)==data['archive']['database_sha256']
            trials[(sample['mode'],sample['repeat'])]=matched
        reference=trials[('eager',0)]
        assert all(data==reference for data in trials.values())
        path=tmp/'union'; base.restore_archive(parent['archive'],path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']); h.set_admission_budget(0)
        try:
            with h.db:
                h.db.executemany('INSERT INTO cnf_patterns_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
                h.db.executemany(f'INSERT INTO {base.split.TABLE} VALUES (?,?)',[(k,v) for k,v in union_pairs.items() if k not in initial_pairs])
            evidence=[base.load_json(p) for p in union_pairs.values()]; routes=base.routes_for(h,evidence)
            coverage=study.nested.all_coverage(h,routes,queries)
            base.split.verify_positive(h,coverage['proof'],coverage['roots'],evidence,Counter())
            new_queries=copy.deepcopy(queries)
            for q,depth in zip(new_queries,coverage['selected_depths'],strict=True):
                q['selected_depth']=depth
                q['closed_by_depth']=[h._load(k) is not None and base.compose(h,[k],routes,Counter())[0][0] for k in q['roots']]
            pending=[dict(source=r['source'],variable=r['variable'],value=v,target=b['edge']['key'])
                for r in evidence for v,b in zip((False,True),r['branches']) if h._load(b['edge']['key']) is None]
        finally: h.close()
        for name,value in [('queries',new_queries),('proof',coverage['proof']),('pending',pending)]: base.write(out/f'{name}.json',value)
        previous_protocol=base.load(parent['protocol']['path'])
        base.write(out/'checkpoint-protocol.json',dict(options=protocol['options'],cases=previous_protocol['cases'],
            parent_protocol=parent['protocol'],continuation_protocol=study.binding(out/'protocol.json')))
        dest=out/'union'; dest.mkdir(exist_ok=True); archive=base.archive(path,dest)
        sources=dict(protocol['source_fingerprints']); sources['experiments/validate_cnf_scoped_refinement.py']=base.sha(__file__)
        cp=dict(format='bootstrap-coverage-union-v1',source_fingerprints=sources,archive=archive,roots=coverage['roots'],
            report=study.binding(out/'report.json'),protocol=study.binding(out/'checkpoint-protocol.json'),
            queries=study.binding(out/'queries.json'),proof=study.binding(out/'proof.json'),pending=study.binding(out/'pending.json'),
            coverage=coverage['covered'],uncovered_originals=[q['case'] for q in new_queries if q['selected_depth'] is None],
            initial_patterns=len(initial),new_patterns=len(union)-len(initial),patterns=len(union),pairs=len(union_pairs))
        base.write(out/'checkpoint.json',cp); _,union_check=restore_checkpoint(out/'checkpoint.json',tmp/'cold-union')
        means=defaultdict(list); history_path=Path('experiments/results/cnf-split-registry/report.json')
        for sample in base.load(history_path)['samples']:
            if sample['mode']=='incremental':
                assert base.sha(sample['path'])==sample['sha256']
                for row in base.load(sample['path'])['records']: means[row['case']].append(row['seconds'])
        case=target['case'] if target['case'] in cp['uncovered_originals'] else min(cp['uncovered_originals'],key=lambda c:(-sum(means[c])/len(means[c]),c))
        seed_path=Path('experiments/results/cnf-bootstrap-conditioning/seed.json')
        source=base.load(seed_path)['records'][case]['leaf']; h=base.CompleteAdmissionInventory(tmp/'cold-union',**protocol['options'])
        try:
            routes=base.routes_for(h,evidence); node=h._load(source); assert node is not None
            assert not any(base.compose(h,[k],routes,Counter())[0][0] for k in new_queries[case]['roots'])
            prior_pairs=[]
            for r in evidence:
                if r['source']!=source: continue
                branches=[]
                for v,b in zip((False,True),r['branches']):
                    key=b['edge']['key'];child=h._load(key)
                    branches.append(dict(value=v,child=key,key_sha256=base.key_sha(key),present=child is not None,
                        closed=base.compose(h,[key],routes,Counter())[0][0] if child else False,
                        kind=child['kind'] if child else None,shape=child['profile']['shape'] if child else None))
                prior_pairs.append(dict(variable=r['variable'],branches=branches))
            pointer=dict(case=case,group=previous_protocol['cases'][case]['group'],checkpoint=study.binding(out/'checkpoint.json'),
                source_seed=study.binding(seed_path),original_source=previous_protocol['cases'][case]['source'],source=source,
                source_sha256=base.key_sha(source),shape=node['profile']['shape'],prior_pairs=prior_pairs,
                selection_measurement=dict(**study.binding(history_path),mean_query_seconds=sum(means[case])/len(means[case]),scope='Historical enumeration timings, not a new union measurement.'),
                resume_decisions=reference[-1]['decisions'] if case==target['case'] else {},
                rationale='Resume unfinished target, otherwise transfer the unchanged policy to the largest historical remaining query.')
            base.write(out/'next-discovery.json',pointer)
        finally: h.close(); assert base.sha(tmp/'cold-union')==cp['archive']['database_sha256']
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),
        validator_sha256=base.sha(__file__),parent_check=parent_check,archives=audits,union_check=union_check,
        same_acquisitions_operations_and_proofs=True,complete_reachable_catalogs=True,pending_children=len(pending),next_case=case)
    base.write(out/'reconstruction.json',result)
    print(base.encode({k:v for k,v in result.items() if k in ('passed','union_check','same_acquisitions_operations_and_proofs','complete_reachable_catalogs','pending_children','next_case')}))


if __name__=='__main__': validate(Path(sys.argv[1]))

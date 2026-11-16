#!/usr/bin/env python3
"""Replay committed and pilot refinement, including cold scheduler recovery."""
from collections import Counter, defaultdict, deque
import copy
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_pilot_refinement as study
from experiments.cnf_pilot_refinement import PilotRefinement
from experiments import compare_cnf_scoped_refinement as frozen
from experiments.cnf_query_checkpoint import check_query
from experiments.validate_cnf_grouped_checkpoints import explanation
from experiments.cnf_route_composition import options
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_split_registry import SplitRegistry
from experiments.validate_cnf_bootstrap import restore_checkpoint
base = study.base


def pairs(h): return dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'))


def validate(out):
    started=time.perf_counter(); protocol=base.load(out/'protocol.json'); report=base.load(out/'report.json')
    assert base.sha(out/'protocol.json')==report['protocol_sha256']
    for key in ('checkpoint','target','queries'):
        entry=protocol[key]; assert base.sha(entry['path'])==entry['sha256']
    for p,digest in protocol['source_fingerprints'].items(): assert base.sha(p)==digest,p
    target=base.load(protocol['target']['path']); queries=base.load(protocol['queries']['path'])
    root=queries[target['case']]['roots'][0]; trials={}; audits=[];deltas={};proofs={};pilot_states={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td); parent,parent_check=restore_checkpoint(protocol['checkpoint']['path'],tmp/'parent')
        h=base.CompleteAdmissionInventory(tmp/'parent',**protocol['options'])
        try:initial=base.rows(h);initial_pairs=pairs(h)
        finally:h.close()
        union=dict(initial); union_pairs=dict(initial_pairs)
        for i,sample in enumerate(report['samples']):
            assert base.sha(sample['path'])==sample['sha256']; stream=base.load(sample['path'])
            mode=sample['mode'];previous=dict(initial);previous_pairs=dict(initial_pairs);matched=[];old_events=[]
            for j,entry in enumerate(stream['samples']):
                assert base.sha(entry['path'])==entry['sha256']; data=base.load(entry['path'])
                path=tmp/f'trial-{i}-{j}'; base.restore_archive(data['archive'],path)
                cold=frozen.audit(path,protocol)
                assert {k:v for k,v in cold.items() if k!='seconds'}=={k:v for k,v in data['cold'].items() if k not in ('seconds','canonical','normalization_counts')}
                assert data['cold']['canonical'] is True
                query_check=check_query(path,protocol['options'],target['original_source'],root,data['target_proof'],data['closed'])
                assert {k:v for k,v in query_check.items() if k!='seconds'}=={k:v for k,v in data['query_check'].items() if k!='seconds'}
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
                        scoped=(PilotRefinement(h,root,target['source'],data['pilot_state']) if mode=='pilot' else ScopedNestedRefinement(h,root,data['decisions']));full=SplitRegistry(h)
                        assert scoped.frontier()==data['frontier'] and scoped.coverage.closed()==[data['closed']]
                        if mode=='pilot':
                            assert scoped.state()==data['pilot_state'] and scoped.decisions==data['decisions']
                            events=data['pilot_state']['events'];assert events[:len(old_events)]==old_events
                            fresh_events=events[len(old_events):]
                            assert len(fresh_events)<=len(data['operations'])
                            for event,op in zip(fresh_events,data['operations']):
                                assert event['source_sha256']==base.key_sha(op['source']) and event['variable']==op['variable']
                                assert event['record_sha256']==base.key_sha(op['record']) and event['pending']==any(op['pending'])
                            for metric,limit in [('entered',data['entered']),('probes',data['probes']),('assumptions',data['selection_counts'].get('bootstrap_fresh_assumptions',0))]:
                                assert all(type(e[metric]) is int and e[metric]>=0 for e in fresh_events)
                                assert sum(e[metric] for e in fresh_events)<=limit
                            old_events=events
                        else:assert data['pilot_state'] is None
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
                        if j==len(stream['samples'])-1:
                            details,proof=explanation(h,root,full,initial,initial,target['case'],target['group'])
                            split_ids={s['rule']['id'] for s in data['target_proof']['steps'] if s['rule']['kind']==base.split.KIND}
                            details['prior_split_steps']=len(split_ids & set(initial_pairs))
                            details['new_split_steps']=len(split_ids-set(initial_pairs))
                            keys={step['source'] for step in data['target_proof']['steps']}
                            details['unused_new_pattern_rows']=len((set(saved)-set(initial))-keys)
                            choice_step=next((step for step in data['target_proof']['steps'] if step['source']==target['source']),None)
                            details['proof_source_pivot']=base.load_json(choice_step['rule']['id'])[1] if choice_step and choice_step['rule']['kind']==base.split.KIND else None
                            pilot_states[(mode,sample['repeat'])]=data['pilot_state']
                            if sample['repeat']==0:
                                if proof:base.write(out/f'{mode}-target-proof.json',proof)
                                base.write(out/f'{mode}-explanation.json',details)
                            proofs[(mode,sample['repeat'])]=data['target_proof']
                            deltas[(mode,sample['repeat'])]=(set(saved)-set(initial),set(records)-set(initial_pairs))
                    for k,v in saved.items(): assert k not in union or union[k]==v; union[k]=v
                    for k,v in records.items(): assert k not in union_pairs or union_pairs[k]==v; union_pairs[k]=v
                    matched.append({k:data[k] for k in ('closed','reason','entered','stored','probes','operations','decisions','frontier','admitted_ids','stored_ids','target_proof','pattern_digest','pair_digest','recognition_counts','selection_counts','pilot_state')})
                    matched[-1]['database_sha256']=data['archive']['database_sha256']
                    matched[-1]['archive_sha256']=data['archive']['sha256']
                    previous,previous_pairs=saved,records
                finally: h.close(); assert base.sha(path)==data['archive']['database_sha256']
            trials[(sample['mode'],sample['repeat'])]=matched
        assert set(trials)=={(mode,repeat) for repeat,order in enumerate(protocol['orders']) for mode in order}
        for mode in study.MODES:
            assert all(trials[(mode,repeat)]==trials[(mode,0)] for repeat in range(len(protocol['orders'])))
        a,b=(deltas[(mode,0)] for mode in study.MODES)
        pa,pb=({s['source'] for s in proofs[(mode,0)]['steps']} for mode in study.MODES)
        intersection=sorted((pa&pb)-set(initial));shared=[]
        for key in intersection:
            node=base.load_json(union[key]);shared.append(dict(source_sha256=base.key_sha(key),kind=node['kind'],shape=node['profile']['shape']))
        comparison=dict(identical_continuations=trials[('committed',0)]==trials[('pilot',0)],
            added_patterns={m:len(deltas[(m,0)][0]) for m in study.MODES},
            shared_new_patterns=len(a[0]&b[0]),distinct_new_patterns=len(a[0]|b[0]),
            shared_new_split_records=len(a[1]&b[1]),distinct_new_split_records=len(a[1]|b[1]),
            shared_new_proof_nodes=shared,shared_parent_proof_steps=len(pa&pb&set(initial)),
            note='Overlap is between alternative continuations of the same original, not cross-input reuse or a counterfactual acquisition saving.')
        base.write(out/'comparison.json',comparison)
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
        sources=dict(protocol['source_fingerprints']); sources['experiments/validate_cnf_pilot_refinement.py']=base.sha(__file__)
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
        assert cp['uncovered_originals'], 'No unresolved original: omit next-discovery pointer'
        case=target['case'] if target['case'] in cp['uncovered_originals'] else min(cp['uncovered_originals'],key=lambda c:(-sum(means[c])/len(means[c]),c))
        seed_path=Path('experiments/results/cnf-bootstrap-conditioning/seed.json')
        source=base.load(seed_path)['records'][case]['leaf']; h=base.CompleteAdmissionInventory(tmp/'cold-union',**protocol['options'])
        try:
            routes=base.routes_for(h,evidence); node=h._load(source); assert node is not None
            root_presence=[h._load(k) is not None for k in new_queries[case]['roots']]
            assert not any(present and base.compose(h,[k],routes,Counter())[0][0] for k,present in zip(new_queries[case]['roots'],root_presence,strict=True))
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
                source_sha256=base.key_sha(source),shape=node['profile']['shape'],prior_pairs=prior_pairs,root_presence=root_presence,
                selection_measurement=dict(**study.binding(history_path),mean_query_seconds=sum(means[case])/len(means[case]),scope='Historical enumeration timings, not a new union measurement.'),
                resume_decisions=trials[('committed',0)][-1]['decisions'] if case==target['case'] else {},
                resume_pilot_state=pilot_states[('pilot',0)] if case==target['case'] else None,
                rationale='Resume unfinished target, otherwise transfer the unchanged policy to the largest historical remaining query.')
            base.write(out/'next-discovery.json',pointer)
        finally: h.close(); assert base.sha(tmp/'cold-union')==cp['archive']['database_sha256']
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),
        validator_sha256=base.sha(__file__),parent_check=parent_check,archives=audits,union_check=union_check,
        identical_within_mode_repetitions=True,complete_reachable_catalogs=True,cold_pilot_resume_checked=True,shared_batch_budget_checked=True,comparison=study.binding(out/'comparison.json'),pending_children=len(pending),next_case=case,seconds=time.perf_counter()-started)
    base.write(out/'reconstruction.json',result)
    print(base.encode({k:v for k,v in result.items() if k in ('passed','union_check','identical_within_mode_repetitions','complete_reachable_catalogs','pending_children','next_case')}))


if __name__=='__main__': validate(Path(sys.argv[1]))

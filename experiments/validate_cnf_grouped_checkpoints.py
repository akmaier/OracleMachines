#!/usr/bin/env python3
"""Retrospectively check every group prefix, proof, and preserved record."""
from collections import Counter,defaultdict,deque
import copy
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_grouped_checkpoints as study
from experiments.cnf_query_checkpoint import check_query
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_split_registry import SplitRegistry
from experiments.cnf_route_composition import options
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.validate_cnf_case17_transfer import explain
base=study.base


def pair_rows(h):return dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'))
def without_time(value):return {k:v for k,v in value.items() if k!='seconds'}


def explanation(h,root,full,initial,case_start,case,group):
    details=explain(h,root,full,initial,set(),set())
    details.pop('case16_pattern_steps',None);details.pop('case16_split_steps',None)
    details.update(case=case,group=group,original_shape=h._load(root)['profile']['shape'])
    if not details['closed']:return details,None
    proof=details.pop('proof');keys={s['source'] for s in proof['steps']}
    details['earlier_query_steps']=len(keys & (set(case_start)-set(initial)))
    details['current_query_new_steps']=len(keys-set(case_start))
    assert details['prior_pattern_steps']+details['earlier_query_steps']+details['current_query_new_steps']==len(keys)
    depth={root:0};decompositions=[];splits=[]
    for step in reversed(proof['steps']):
        for child in step['children']:
            depth[child]=max(depth.get(child,0),depth[step['source']]+(step['rule']['kind']==base.split.KIND))
    for step in proof['steps']:
        kind=step['rule']['kind']
        if kind not in ('components',base.split.KIND):continue
        node=base.owner(h,step['source'])._load(step['source'])
        row=dict(source_sha256=base.key_sha(step['source']),shape=node['profile']['shape'],external_depth=depth[step['source']],
            children=[dict(key_sha256=base.key_sha(k),kind=base.owner(h,k)._load(k)['kind'],shape=base.owner(h,k)._load(k)['profile']['shape']) for k in step['children']])
        if kind=='components':decompositions.append(row)
        else:
            record=base.load_json(h.db.execute(f'SELECT payload FROM {base.split.TABLE} WHERE id=?',(step['rule']['id'],)).fetchone()[0])
            row['variable']=record['variable'];splits.append(row)
    details['decompositions']=decompositions;details['conditioning_sources']=splits
    return details,proof


def validate(out):
    started=time.perf_counter();protocol=base.load(out/'protocol.json');report=base.load(out/'report.json')
    assert base.sha(out/'protocol.json')==report['protocol_sha256']
    for key in ('checkpoint','queries','selection_measurement'):
        e=protocol[key];assert base.sha(e['path'])==e['sha256']
    for p,digest in protocol['source_fingerprints'].items():assert base.sha(p)==digest,p
    queries=base.load(protocol['queries']['path']);trials={};audits=[];final_decisions={};observed_queries=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);parent,parent_check=restore_checkpoint(protocol['checkpoint']['path'],tmp/'parent')
        parent_protocol=base.load(parent['protocol']['path']);h=base.CompleteAdmissionInventory(tmp/'parent',**protocol['options'])
        try:initial=base.rows(h);initial_pairs=pair_rows(h)
        finally:h.close()
        union=dict(initial);union_pairs=dict(initial_pairs)
        for i,sample in enumerate(report['samples']):
            assert base.sha(sample['path'])==sample['sha256'];stream=base.load(sample['path']);matched=[]
            prior=dict(initial);prior_pairs=dict(initial_pairs);current_case=None;case_start=None;case_order=[];batch_number=0
            for j,entry in enumerate(stream['samples']):
                assert base.sha(entry['path'])==entry['sha256'];data=base.load(entry['path']);case=data['case'];root=queries[case]['roots'][0]
                if case!=current_case:
                    current_case=case;case_start=dict(prior);case_order.append(case);batch_number=0
                assert data['batch']==batch_number;batch_number+=1;assert batch_number<=protocol['max_batches_per_case']
                path=tmp/f'prefix-{i}-{j}';base.restore_archive(data['archive'],path)
                cold=study.previous.audit(path,protocol)
                if data['full_cold'] is not None:assert without_time(cold)==without_time(data['full_cold'])
                assert (data['full_cold'] is not None)==(sample['mode']=='each_batch' or j==len(stream['samples'])-1)
                query_check=check_query(path,protocol['options'],queries[case]['source'],root,data['target_proof'],data['closed'])
                assert without_time(query_check)==without_time(data['query_cold'])
                audits.append(dict(mode=sample['mode'],repeat=sample['repeat'],case=case,batch=data['batch'],
                    **{k:v for k,v in cold.items() if k!='coverage'},covered=cold['coverage']['covered'],
                    positive_query_steps=query_check['positive_steps'],query_check_seconds=query_check['seconds']))
                h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
                try:
                    saved=base.rows(h);records=pair_rows(h)
                    assert prior.items()<=saved.items() and prior_pairs.items()<=records.items()
                    assert base.key_sha(base.encode(sorted(saved.items())))==data['pattern_digest']
                    assert base.key_sha(base.encode(sorted(records.items())))==data['pair_digest']
                    assert len(saved)-len(prior)==data['stored']
                    assert len(set(data['admitted_ids']))==data['entered']<=protocol['state_limit']
                    assert set(data['stored_ids'])==set(map(base.key_sha,set(saved)-set(prior)))
                    assert set(data['stored_ids'])<=set(data['admitted_ids']) and len(data['operations'])<=protocol['pair_limit']
                    assert data['selection_counts'].get('bootstrap_fresh_assumptions',0)<=2*protocol['pair_limit']
                    with (base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')),
                          patch.object(base.split,'discover_simplification',side_effect=AssertionError('assumption'))):
                        scoped=ScopedNestedRefinement(h,root,data['decisions']);full=SplitRegistry(h)
                        assert scoped.frontier()==data['frontier'] and scoped.coverage.closed()==[data['closed']]
                        todo=deque([root]);reachable=set()
                        while todo:
                            key=todo.popleft()
                            if key in reachable:continue
                            reachable.add(key);assert full.by_source.get(key,[])==scoped.registry.by_source.get(key,[])
                            for _,children in options(h,key,full):todo.extend(children)
                        assert reachable==scoped.registry.reachable
                        flags,plan=base.compose(h,[root],full,Counter())
                        assert flags==[data['closed']] and base.expand(h,plan,[root],full,Counter())==data['target_proof']
                        last_for_case=(j==len(stream['samples'])-1 or base.load(stream['samples'][j+1]['path'])['case']!=case)
                        if last_for_case:
                            assert data['closed'] or batch_number==protocol['max_batches_per_case']
                        if i==0 and last_for_case:
                            details,proof=explanation(h,root,full,initial,case_start,case,parent_protocol['cases'][case]['group'])
                            base.write(out/f'case-{case}-explanation.json',details)
                            if proof:base.write(out/f'case-{case}-proof.json',proof)
                            final_decisions[case]=data['decisions'];observed_queries.append(dict(case=case,closed=data['closed'],proof_steps=details.get('unique_steps',0)))
                    for k,v in saved.items():assert k not in union or union[k]==v;union[k]=v
                    for k,v in records.items():assert k not in union_pairs or union_pairs[k]==v;union_pairs[k]=v
                    matched.append({k:data[k] for k in ('case','batch','closed','reason','entered','stored','probes','operations','decisions','frontier','admitted_ids','stored_ids','target_proof','pattern_digest','pair_digest','recognition_counts','selection_counts')})
                    matched[-1]['database_sha256']=data['archive']['database_sha256'];matched[-1]['archive_sha256']=data['archive']['sha256']
                    prior,prior_pairs=saved,records
                finally:h.close();assert base.sha(path)==data['archive']['database_sha256']
            assert case_order==protocol['cases'];trials[(sample['mode'],sample['repeat'])]=matched
        reference=trials[('each_batch',0)];assert all(data==reference for data in trials.values())
        path=tmp/'union';base.restore_archive(parent['archive'],path);h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        try:
            with h.db:
                h.db.executemany('INSERT INTO cnf_patterns_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
                h.db.executemany(f'INSERT INTO {base.split.TABLE} VALUES (?,?)',[(k,v) for k,v in union_pairs.items() if k not in initial_pairs])
            evidence=[base.load_json(p) for p in union_pairs.values()];routes=base.routes_for(h,evidence)
            coverage=study.previous.nested.all_coverage(h,routes,queries)
            base.split.verify_positive(h,coverage['proof'],coverage['roots'],evidence,Counter())
            new_queries=copy.deepcopy(queries)
            for q,depth in zip(new_queries,coverage['selected_depths'],strict=True):
                q['selected_depth']=depth;q['closed_by_depth']=[h._load(k) is not None and base.compose(h,[k],routes,Counter())[0][0] for k in q['roots']]
            pending=[dict(source=r['source'],variable=r['variable'],value=v,target=b['edge']['key']) for r in evidence for v,b in zip((False,True),r['branches']) if h._load(b['edge']['key']) is None]
        finally:h.close()
        for name,value in [('queries',new_queries),('proof',coverage['proof']),('pending',pending)]:base.write(out/f'{name}.json',value)
        base.write(out/'checkpoint-protocol.json',dict(options=protocol['options'],cases=parent_protocol['cases'],parent_protocol=parent['protocol'],continuation_protocol=study.binding(out/'protocol.json')))
        dest=out/'union';dest.mkdir(exist_ok=True);archive=base.archive(path,dest)
        sources=dict(protocol['source_fingerprints']);sources['experiments/validate_cnf_grouped_checkpoints.py']=base.sha(__file__)
        cp=dict(format='bootstrap-coverage-union-v1',source_fingerprints=sources,archive=archive,roots=coverage['roots'],
            report=study.binding(out/'report.json'),protocol=study.binding(out/'checkpoint-protocol.json'),queries=study.binding(out/'queries.json'),
            proof=study.binding(out/'proof.json'),pending=study.binding(out/'pending.json'),coverage=coverage['covered'],
            uncovered_originals=[q['case'] for q in new_queries if q['selected_depth'] is None],initial_patterns=len(initial),new_patterns=len(union)-len(initial),patterns=len(union),pairs=len(union_pairs))
        base.write(out/'checkpoint.json',cp);_,union_check=restore_checkpoint(out/'checkpoint.json',tmp/'cold-union')
        means=defaultdict(list);historical=Path(protocol['selection_measurement']['path'])
        for s in base.load(historical)['samples']:
            if s['mode']=='incremental':
                for row in base.load(s['path'])['records']:means[row['case']].append(row['seconds'])
        unfinished=[c for c in protocol['cases'] if c in cp['uncovered_originals']]
        case=unfinished[0] if unfinished else min(cp['uncovered_originals'],key=lambda c:(-sum(means[c])/len(means[c]),c))
        seed_path=Path('experiments/results/cnf-bootstrap-conditioning/seed.json');source=base.load(seed_path)['records'][case]['leaf']
        h=base.CompleteAdmissionInventory(tmp/'cold-union',**protocol['options'])
        try:
            routes=base.routes_for(h,evidence);node=h._load(source);assert node is not None
            assert not any(base.compose(h,[k],routes,Counter())[0][0] for k in new_queries[case]['roots'])
            prior_pairs=[]
            for r in evidence:
                if r['source']!=source:continue
                branches=[]
                for v,b in zip((False,True),r['branches']):
                    key=b['edge']['key'];child=h._load(key)
                    branches.append(dict(value=v,child=key,key_sha256=base.key_sha(key),present=child is not None,closed=base.compose(h,[key],routes,Counter())[0][0] if child else False,kind=child['kind'] if child else None,shape=child['profile']['shape'] if child else None))
                prior_pairs.append(dict(variable=r['variable'],branches=branches))
            base.write(out/'next-discovery.json',dict(case=case,group=parent_protocol['cases'][case]['group'],checkpoint=study.binding(out/'checkpoint.json'),source_seed=study.binding(seed_path),
                original_source=parent_protocol['cases'][case]['source'],source=source,source_sha256=base.key_sha(source),shape=node['profile']['shape'],prior_pairs=prior_pairs,
                selection_measurement=dict(**study.binding(historical),mean_query_seconds=sum(means[case])/len(means[case]),scope='Historical enumeration timings, not a new union measurement.'),
                resume_decisions=final_decisions.get(case,{}),rationale='Resume an unfinished group query, otherwise choose the historically costliest remaining original.'))
        finally:h.close();assert base.sha(tmp/'cold-union')==cp['archive']['database_sha256']
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),validator_sha256=base.sha(__file__),
        parent_check=parent_check,archives=audits,union_check=union_check,observed_queries=observed_queries,same_acquisitions_operations_proofs_and_snapshots=True,
        complete_reachable_catalogs=True,all_prefixes_append_only=True,pending_children=len(pending),next_case=case,validation_wall_seconds=time.perf_counter()-started)
    base.write(out/'reconstruction.json',result)
    print(base.encode({k:v for k,v in result.items() if k in ('passed','union_check','observed_queries','same_acquisitions_operations_proofs_and_snapshots','all_prefixes_append_only','pending_children','next_case','validation_wall_seconds')}))


if __name__=='__main__':validate(Path(sys.argv[1]))

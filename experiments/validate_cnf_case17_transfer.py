#!/usr/bin/env python3
"""Check target transfer, isolate history reuse, and preserve the full union."""
from collections import Counter
import copy
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_case17_transfer as study
from experiments.validate_cnf_bootstrap import restore_checkpoint
base=study.base


def table_pairs(h):return dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'))


def explain(h,root,routes,prior,case16_rows,case16_pairs):
    closed,plan=base.compose(h,[root],routes,Counter())
    if not closed[0]:return dict(closed=False)
    proof=base.expand(h,plan,[root],routes,Counter())
    evidence=[base.load_json(p) for p in table_pairs(h).values()]
    base.split.verify_positive(h,proof,[root],evidence,Counter())
    multiple=Counter({root:1});depth={root:0}
    for step in reversed(proof['steps']):
        for child in step['children']:
            multiple[child]+=multiple[step['source']]
            depth[child]=max(depth.get(child,0),depth[step['source']]+(step['rule']['kind']==base.split.KIND))
    kinds=Counter(s['rule']['kind'] for s in proof['steps']);reductions=Counter();families=[];shared=[]
    for step in proof['steps']:
        node=base.owner(h,step['source'])._load(step['source'])
        if step['rule']['kind']=='edge':reductions[node['kind']]+=1
        if step['rule']['kind']=='family':
            families.append(dict(source_sha256=base.key_sha(step['source']),shape=node['profile']['shape'],
                recognized=[k for k,v in node['profile']['outcomes'].items() if v=='recognized'],
                multiplicity=multiple[step['source']]))
        if multiple[step['source']]>1:
            shared.append(dict(source_sha256=base.key_sha(step['source']),kind=node['kind'],
                               multiplicity=multiple[step['source']],shape=node['profile']['shape']))
    keys={s['source'] for s in proof['steps']}
    split_ids={s['rule']['id'] for s in proof['steps'] if s['rule']['kind']==base.split.KIND}
    return dict(closed=True,proof=proof,unique_steps=len(keys),rule_counts=dict(kinds),reduction_counts=dict(reductions),
        max_external_depth=max(depth.values()),unfolded_step_occurrences=sum(multiple.values()),families=families,
        family_occurrences=sum(x['multiplicity'] for x in families),shared_nodes=shared,
        prior_pattern_steps=len(keys&set(prior)),case16_pattern_steps=len(keys&case16_rows),
        case16_split_steps=len(split_ids&case16_pairs),new_pattern_steps=len(keys-set(prior)-case16_rows))


def validate(out):
    report=base.load(out/'report.json');protocol=base.load(out/'protocol.json')
    assert report['protocol_sha256']==base.sha(out/'protocol.json')
    for binding in [protocol['target'],protocol['queries'],protocol['policy_binding'],*protocol['checkpoints'].values()]:
        assert base.sha(binding['path'])==binding['sha256']
    for p,digest in protocol['source_fingerprints'].items():assert base.sha(p)==digest,p
    target=base.load(protocol['target']['path']);queries=base.load(protocol['queries']['path'])
    root=queries[target['case']]['roots'][0];parents={};parent_checks={};audits=[];deltas={};target_proofs={};sample_records={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for mode,binding in protocol['checkpoints'].items():
            cp,checked=restore_checkpoint(binding['path'],tmp/f'parent-{mode}');parent_checks[mode]=checked
            h=base.CompleteAdmissionInventory(tmp/f'parent-{mode}',**protocol['options']);h.set_admission_budget(0)
            try:parents[mode]=dict(report=cp,rows=base.rows(h),pairs=table_pairs(h))
            finally:h.close()
        old=parents['before_case16'];full=parents['retained']
        assert old['rows'].items()<=full['rows'].items() and old['pairs'].items()<=full['pairs'].items()
        case16_rows=set(full['rows'])-set(old['rows']);case16_pairs=set(full['pairs'])-set(old['pairs'])
        union=dict(full['rows']);union_pairs=dict(full['pairs'])
        for i,sample in enumerate(report['samples']):
            assert base.sha(sample['path'])==sample['sha256'];stream=base.load(sample['path']);mode=sample['mode']
            parent=parents[mode];previous=dict(parent['rows']);previous_pairs=dict(parent['pairs']);steps=[]
            for j,entry in enumerate(stream['samples']):
                assert base.sha(entry['path'])==entry['sha256'];data=base.load(entry['path']);steps.append(data)
                path=tmp/f'check-{i}-{j}';base.restore_archive(data['archive'],path)
                cold=study.nested.replay(path,protocol,data);audits.append(dict(mode=mode,repeat=sample['repeat'],batch=j,**cold))
                h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
                try:
                    saved=base.rows(h);pairs=table_pairs(h)
                    assert previous.items()<=saved.items() and previous_pairs.items()<=pairs.items()
                    assert len(saved)-len(previous)==data['stored'] and data['entered']<=protocol['state_limit']
                    assert len(data['operations'])<=protocol['pair_limit']
                    assert data['selection_counts'].get('bootstrap_fresh_assumptions',0)<=2*protocol['pair_limit']
                    assert set(data['stored_ids'])<=set(data['admitted_ids']) and len(data['admitted_ids'])==data['entered']
                    added={k:v for k,v in saved.items() if k not in parent['rows']}
                    added_pairs={k:v for k,v in pairs.items() if k not in parent['pairs']}
                    assert base.key_sha(base.encode(sorted(added.items())))==data['added_pattern_digest']
                    assert base.key_sha(base.encode(sorted(added_pairs.items())))==data['added_pair_digest']
                    assert sorted(map(base.key_sha,added))==data['added_pattern_ids']
                    assert sorted(map(base.key_sha,added_pairs))==data['added_pair_ids']
                    with (base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')),
                          patch.object(base.split,'discover_simplification',side_effect=AssertionError('source assumption'))):
                        session=study.nested.NestedRefinement(h,root,data['decisions'])
                        assert session.frontier()==data['frontier'] and session.coverage.closed()[0]==data['closed']
                        if j==len(stream['samples'])-1:
                            details=explain(h,root,session.registry,old['rows'],case16_rows,case16_pairs)
                            if details['closed']:
                                proof=details.pop('proof');target_proofs[(mode,sample['repeat'])]=proof
                                if sample['repeat']==0:base.write(out/f'{mode}-target-proof.json',proof)
                            if sample['repeat']==0:base.write(out/f'{mode}-explanation.json',details)
                    for k,v in saved.items():assert k not in union or union[k]==v;union[k]=v
                    for k,v in pairs.items():assert k not in union_pairs or union_pairs[k]==v;union_pairs[k]=v
                    previous,previous_pairs=saved,pairs
                    deltas[(mode,sample['repeat'])]=(added,added_pairs)
                finally:h.close();assert base.sha(path)==data['archive']['database_sha256']
            sample_records[(mode,sample['repeat'])]=steps
        same_deltas=all(deltas[('retained',r)]==deltas[('before_case16',r)] for r in (0,1))
        same_operations=all([x['operations'] for x in sample_records[('retained',r)]]==
                            [x['operations'] for x in sample_records[('before_case16',r)]] for r in (0,1))
        same_proof=bool(target_proofs) and len(target_proofs)==len(report['samples']) and all(
            target_proofs[('retained',r)]==target_proofs[('before_case16',r)] for r in (0,1))
        path=tmp/'union';base.restore_archive(full['report']['archive'],path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        try:
            with h.db:
                h.db.executemany('INSERT INTO cnf_patterns_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in full['rows']])
                h.db.executemany(f'INSERT INTO {base.split.TABLE} VALUES (?,?)',[(k,v) for k,v in union_pairs.items() if k not in full['pairs']])
            evidence=[base.load_json(p) for p in union_pairs.values()];routes=base.routes_for(h,evidence)
            coverage=study.nested.all_coverage(h,routes,queries)
            base.split.verify_positive(h,coverage['proof'],coverage['roots'],evidence,base.Counter())
            new_queries=copy.deepcopy(queries)
            for q,depth in zip(new_queries,coverage['selected_depths'],strict=True):
                q['selected_depth']=depth
                q['closed_by_depth']=[h._load(k) is not None and base.compose(h,[k],routes,base.Counter())[0][0] for k in q['roots']]
            pending=[dict(source=r['source'],variable=r['variable'],value=value,target=b['edge']['key'])
                for r in evidence for value,b in zip((False,True),r['branches']) if h._load(b['edge']['key']) is None]
        finally:h.close()
        base.write(out/'queries.json',new_queries);base.write(out/'proof.json',coverage['proof']);base.write(out/'pending.json',pending)
        previous_protocol=base.load(full['report']['protocol']['path'])
        base.write(out/'checkpoint-protocol.json',dict(options=protocol['options'],cases=previous_protocol['cases'],
            parent_protocol=full['report']['protocol'],continuation_protocol=study.binding(out/'protocol.json')))
        dest=out/'union';dest.mkdir(exist_ok=True);archive=base.archive(path,dest)
        sources=dict(protocol['source_fingerprints']);sources['experiments/validate_cnf_case17_transfer.py']=base.sha(__file__)
        checkpoint=dict(format='bootstrap-coverage-union-v1',source_fingerprints=sources,archive=archive,roots=coverage['roots'],
            report=study.binding(out/'report.json'),protocol=study.binding(out/'checkpoint-protocol.json'),
            queries=study.binding(out/'queries.json'),proof=study.binding(out/'proof.json'),pending=study.binding(out/'pending.json'),
            coverage=coverage['covered'],uncovered_originals=[q['case'] for q in new_queries if q['selected_depth'] is None],
            initial_patterns=len(full['rows']),new_patterns=len(union)-len(full['rows']),patterns=len(union),pairs=len(union_pairs))
        base.write(out/'checkpoint.json',checkpoint);_,union_check=restore_checkpoint(out/'checkpoint.json',tmp/'cold-union')
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),
        validator_sha256=base.sha(__file__),parent_checks=parent_checks,archives=audits,union_check=union_check,
        same_acquisition_deltas=same_deltas,same_selected_operations=same_operations,same_target_proof=same_proof,
        excluded_case16_patterns=len(case16_rows),excluded_case16_pairs=len(case16_pairs),pending_children=len(pending),
        uncovered_originals=checkpoint['uncovered_originals'])
    base.write(out/'reconstruction.json',result)
    print(base.encode({k:result[k] for k in ('passed','union_check','same_acquisition_deltas','same_selected_operations','same_target_proof','pending_children','uncovered_originals')}))


if __name__=='__main__':validate(Path(sys.argv[1]))

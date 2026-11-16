#!/usr/bin/env python3
"""Cold-check every continuation and preserve their immutable union."""
from collections import Counter
import copy
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_nested_refinement as study
from experiments.validate_cnf_bootstrap import restore_checkpoint
base=study.base


def validate(out):
    report=base.load(out/'report.json');protocol=base.load(out/'protocol.json')
    assert report['protocol_sha256']==base.sha(out/'protocol.json')
    for key in ('target','checkpoint','queries'):
        entry=protocol[key];assert base.sha(entry['path'])==entry['sha256']
    for p,digest in protocol['source_fingerprints'].items():assert base.sha(p)==digest,p
    target=base.load(protocol['target']['path']);parent=base.load(protocol['checkpoint']['path'])
    queries=base.load(protocol['queries']['path']);root=queries[target['case']]['roots'][0]
    checks=[];mode_final={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);_,old_check=restore_checkpoint(protocol['checkpoint']['path'],tmp/'parent')
        h=base.CompleteAdmissionInventory(tmp/'parent',**protocol['options']);h.set_admission_budget(0)
        try:
            initial=base.rows(h);initial_pairs=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
            union=dict(initial);pairs=dict(initial_pairs);index=base.FrontierIndex(h);frontiers=[];unique=set()
            with base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')):
                for pair in target['prior_pairs']:
                    for branch in pair['branches']:
                        leaves=[]
                        for key,multiplicity in index.frontier(branch['child']).items():
                            unique.add(key);leaves.append(dict(source=key,source_sha256=base.key_sha(key),
                                multiplicity=multiplicity,shape=h._load(key)['profile']['shape']))
                        frontiers.append(dict(variable=pair['variable'],value=branch['value'],leaves=leaves))
        finally:h.close()
        base.write(out/'initial-frontiers.json',dict(target=protocol['target'],branches=frontiers,
            unique_leaves=len(unique),leaf_occurrences=sum(len(b['leaves']) for b in frontiers),
            scope='Selected internal reductions before nested acquisition; exact keys, not an isomorphism search.'))
        for i,sample in enumerate(report['samples']):
            assert base.sha(sample['path'])==sample['sha256'];stream=base.load(sample['path'])
            previous_rows=dict(initial);previous_pairs=dict(initial_pairs)
            for j,entry in enumerate(stream['samples']):
                assert base.sha(entry['path'])==entry['sha256'];data=base.load(entry['path'])
                path=tmp/f'sample-{i}-{j}';base.restore_archive(data['archive'],path)
                cold=study.replay(path,protocol,data);checks.append(dict(mode=sample['mode'],repeat=sample['repeat'],batch=j,**cold))
                h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
                try:
                    saved=base.rows(h);saved_pairs=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
                    assert previous_rows.items()<=saved.items() and previous_pairs.items()<=saved_pairs.items()
                    assert len(saved)-len(previous_rows)==data['stored'] and data['entered']<=protocol['state_limit']
                    assert len(data['operations'])<=protocol['pair_limit']
                    assert data['selection_counts'].get('bootstrap_fresh_assumptions',0)<=2*protocol['pair_limit']
                    assert set(data['stored_ids'])<=set(data['admitted_ids']) and len(data['admitted_ids'])==data['entered']
                    assert base.key_sha(base.encode(sorted(saved.items())))==data['pattern_digest']
                    assert base.key_sha(base.encode(sorted(saved_pairs.items())))==data['pair_digest']
                    with base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')):
                        session=study.NestedRefinement(h,root,data['decisions'])
                        if sample['mode']=='nested':assert session.frontier()==data['frontier']
                        assert session.coverage.closed()[0]==data['closed']
                    for key,value in saved.items():assert key not in union or union[key]==value;union[key]=value
                    for key,value in saved_pairs.items():assert key not in pairs or pairs[key]==value;pairs[key]=value
                    previous_rows,previous_pairs=saved,saved_pairs
                    mode_final[sample['mode']]=len(saved)-len(initial)
                finally:h.close();assert base.sha(path)==data['archive']['database_sha256']
        path=tmp/'union';base.restore_archive(parent['archive'],path);h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        try:
            with h.db:
                h.db.executemany('INSERT INTO cnf_patterns_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
                h.db.executemany(f'INSERT INTO {base.split.TABLE} VALUES (?,?)',[(k,v) for k,v in pairs.items() if k not in initial_pairs])
            evidence=[base.load_json(p) for p in pairs.values()];routes=base.routes_for(h,evidence)
            coverage=study.all_coverage(h,routes,queries)
            base.split.verify_positive(h,coverage['proof'],coverage['roots'],evidence,Counter())
            new_queries=copy.deepcopy(queries)
            for query,depth in zip(new_queries,coverage['selected_depths'],strict=True):
                query['selected_depth']=depth
                query['closed_by_depth']=[h._load(k) is not None and base.compose(h,[k],routes,Counter())[0][0] for k in query['roots']]
            pending=[dict(source=r['source'],variable=r['variable'],value=value,target=b['edge']['key'])
                for r in evidence for value,b in zip((False,True),r['branches']) if h._load(b['edge']['key']) is None]
        finally:h.close()
        base.write(out/'queries.json',new_queries);base.write(out/'proof.json',coverage['proof']);base.write(out/'pending.json',pending)
        checkpoint_protocol=base.load(parent['protocol']['path'])
        base.write(out/'checkpoint-protocol.json',dict(options=protocol['options'],cases=checkpoint_protocol['cases'],
            parent_protocol=parent['protocol'],continuation_protocol=dict(path=str(out/'protocol.json'),sha256=base.sha(out/'protocol.json'))))
        destination=out/'union';destination.mkdir(exist_ok=True);archive=base.archive(path,destination)
        sources=dict(protocol['source_fingerprints']);sources['experiments/validate_cnf_nested_refinement.py']=base.sha(__file__)
        binding=lambda p:dict(path=str(p),sha256=base.sha(p))
        checkpoint=dict(format='bootstrap-coverage-union-v1',source_fingerprints=sources,archive=archive,
            roots=coverage['roots'],report=binding(out/'report.json'),protocol=binding(out/'checkpoint-protocol.json'),
            queries=binding(out/'queries.json'),proof=binding(out/'proof.json'),pending=binding(out/'pending.json'),
            coverage=coverage['covered'],uncovered_originals=[q['case'] for q in new_queries if q['selected_depth'] is None],
            initial_patterns=len(initial),new_patterns=len(union)-len(initial),patterns=len(union),pairs=len(pairs))
        base.write(out/'checkpoint.json',checkpoint);_,union_check=restore_checkpoint(out/'checkpoint.json',tmp/'cold-union')
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),
        validator_sha256=base.sha(__file__),archives=checks,parent_check=old_check,union_check=union_check,
        overlap_between_workflows=sum(mode_final.values())-(len(union)-len(initial)),pending_children=len(pending),
        initial_unique_frontier=len(unique),initial_frontier_occurrences=sum(len(b['leaves']) for b in frontiers),
        uncovered_originals=checkpoint['uncovered_originals'])
    base.write(out/'reconstruction.json',result)
    print(base.encode({k:result[k] for k in ('passed','union_check','overlap_between_workflows','pending_children','uncovered_originals')}))


if __name__=='__main__':validate(Path(sys.argv[1]))

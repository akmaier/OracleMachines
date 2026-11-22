#!/usr/bin/env python3
"""Retain the replacement regression without assuming it loses earlier proofs."""
from collections import Counter
from pathlib import Path
import json,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_ranked_binary_targets as study
from experiments.cnf_clause_partition import branch_sources
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
base=study.base;NATIVE=study.TABLES[0]


def diagnose(out):
    p=base.load(out/'protocol.json');seed=study.read_zip(p['prefixes']['31']['archive']);census={};inputs={}
    for mode in study.MODES:
        report_path=out/f'fresh-31-{mode}-0/report.json';report=base.load(report_path);qs=study.bound(report['queries']);delta=study.read_zip(report['delta'])
        rows={**dict(seed[NATIVE]),**dict(delta[NATIVE])};earlier=set(qs[0]['new_ids'][NATIVE]);summaries=[]
        for i,b in enumerate(qs[1]['branches']):
            seen=set();todo=[b['result']['root']]
            while todo:
                key=todo.pop()
                if key in seen:continue
                seen.add(key);proof=json.loads(rows[key]).get('proof',{})
                todo.extend(proof[f] for f in ('child','low','high') if f in proof)
            summaries.append(dict(branch=i,expansions=b['metrics']['expanded_nodes'],
                seed_nodes=len(seen&dict(seed[NATIVE]).keys()),earlier_nodes=sorted(seen&earlier),
                current_nodes=len(seen-dict(seed[NATIVE]).keys()-earlier)))
        census[mode]=summaries;inputs[mode]=(report_path,report,qs,delta)
    # All policies use the same first-false regions. The previous-query record
    # occurs in the first cheap branch, not in the expensive third branch.
    roots=[[b['result']['root'] for b in inputs[m][2][1]['branches']] for m in study.MODES]
    assert roots[0]==roots[1]==roots[2]
    assert [census[m][2]['expansions'] for m in study.MODES]==[10,35,33]
    assert all(census[m][2]['seed_nodes']==0 and not census[m][2]['earlier_nodes'] for m in study.MODES)
    previous={k for r in census['baseline'] for k in r['earlier_nodes']};assert len(previous)==1
    candidate_before=set(dict(seed[NATIVE]))|set(inputs['binary1'][2][0]['new_ids'][NATIVE])
    assert previous<=candidate_before
    report_path,report,qs,delta=inputs['binary1'];q=qs[1];index=2
    count=q['probe']['metrics'].get('batch_committed_records',0)+q['preparation_counts'].get('inserted_nodes',0)
    count+=sum(b['metrics'].get('batch_committed_records',0) for b in q['branches'][:index])
    keys=qs[0]['new_ids'][NATIVE]+q['new_ids'][NATIVE][:count];assert len(keys)==len(set(keys))
    extra={t:[[k,v] for k,v in delta[t] if t==NATIVE and k in set(keys)] for t in study.TABLES}
    assert len(extra[NATIVE])==len(keys)
    case=next(c for c in study.bound(p['cases']) if (c['split'],c['case'],c['variant'])==('fresh',31,'replace'))
    source=branch_sources(case['source'],q['missing'])[1][index][2]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';study.restore(seed,path,extra);digest=base.sha(path);s=CanonicalVerifySnapshot(path)
        try:
            cnf,names,root=s._canonical(source);assert root==roots[0][index];assert s._read(root,cnf) is None
            for key in keys:assert s._read(key) is not None
            assert s._read(q['stronger_root'])['answer'] is False
            for b in q['branches'][:index]:assert s._read(b['result']['root'])['answer'] is False
            counts=dict(s.counts)
        finally:s.close()
        assert base.sha(path)==digest
    base.write(out/'next-target.json',dict(source=source,root=root,branch=index,prefix=p['prefixes']['31']['archive'],
        trial_report=study.binding(report_path),extra_ids=keys,extra_count=len(keys),reader_counts=counts,
        input_reports={m:study.binding(inputs[m][0]) for m in study.MODES},dependency_census=census,
        preceding_reused_node_available_under_binary1=True,
        limitations=[
        'Read-only posthoc diagnostic. The target is the third first-false branch in case31 replacement. Its root is absent from the exact reconstructed persistent pre-branch state.',
        'The one previous-query node used by the baseline is available under binary1 and occurs in another branch. The expensive branch has no seed/previous-query dependencies in any final proof; a smaller preceding archive alone does not explain the regression.',
        'Different routing/proof construction is the next hypothesis. Final proof reachability does not record every visited or unsuccessful search and is not a causal time attribution. A matched prestate policy ablation remains to be run.',
        'The retained keys include the preceding query and this query\'s probe, preparation and completed earlier branches only. No later answer is seeded.']))
    print(base.encode(dict(extra_count=len(keys),target_expansions=[10,35,33],prior_dependency_preserved=True)),flush=True)


if __name__=='__main__':diagnose(Path(sys.argv[1]))

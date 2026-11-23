#!/usr/bin/env python3
"""Profile remaining work and save exact pre-acquisition states after comparison."""
from collections import Counter
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
import cProfile,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_prefix as study,cnf_partition_preparation as prepared
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_preimage_fusion import fused_preimages
from experiments.cnf_joint_prefix import reused_joint_prefix
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
base=study.base


def query(s,c,p):
    return study.harness.query(s,c,'native',p['branch_limit']) if study.native_split(c['split']) else study.prepared_run(s,c['candidate'],'probe6',p['node_limit'])


def proof_census(observation):
    index,event=max(((i,e) for i,e in enumerate(observation['acquisitions']) if e['status']=='unsat'),key=lambda pair:pair[1]['expanded_nodes'])
    trial=study.bound(observation['trial']);prefix=study.read_zip(event['prefix']);delta=study.read_zip(trial['delta'])
    before={k for k,v in prefix[study.TABLES[0]]}|set(event['extra_ids'][study.TABLES[0]])
    rows=[];seen=set();todo=[event['root']]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';study.restore(prefix,path,delta);reader=SnapshotResidualSolver(path)
        try:
            while todo:
                key=todo.pop()
                if key in seen:continue
                seen.add(key);node=reader._read(key);assert node is not None and node['answer'] is False
                proof=node['proof'];children=[proof[f] for f in ('child','low','high') if f in proof]
                reasons={cid for _,cid in proof.get('trace',[])}
                if proof.get('conflict') is not None:reasons.add(proof['conflict'])
                rows.append(dict(key=key,kind=proof['kind'],available_before=key in before,children=children,
                    clauses=len(node['cnf']),literals=sum(map(len,node['cnf'])),trace_steps=len(proof.get('trace',[])),
                    reason_indices=sorted(reasons),reason_widths=dict(Counter(len(node['cnf'][i]) for i in reasons)),
                    reason_literals=sum(len(node['cnf'][i]) for i in reasons)))
                todo.extend(children)
        finally:reader.close()
    return dict(acquisition_index=index,root=event['root'],nodes=rows,kinds=dict(Counter(r['kind'] for r in rows)),
        limitations='Checked reachable native DAG, including earlier prerequisites when present. Local reason indices belong to each stored canonical node; no cross-node map or transferable mixed-width core is inferred.')


def run(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);scores=[]
    for index in (25,31,61):
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            times={m:sum(base.load(out/f'novel-{index}-{m}-{i}/queries.json')[j]['seconds'] for i in range(2))/2 for m in study.MODES}
            scores.append(dict(case=index,position=j,root=c['root'],variant=c['variant'],query_seconds=times))
    worst=max(scores,key=lambda r:r['query_seconds']['prefix']);profiles=[];observations=[]
    for split,index,position in (('controls',31,0),('novel',worst['case'],worst['position'])):
        cs=[c for c in cases if (c['split'],c['case'])==(split,index)];prefix_binding=p['prefixes'][str(index)]['archive'];prefix=study.read_zip(prefix_binding)
        for mode in study.MODES:
            trial_path=out/f'{split}-{index}-{mode}-0/report.json';trial=base.load(trial_path);expected=study.bound(trial['queries'])
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';study.restore(prefix,path);s=ConsequencePrioritySolver(path);prof=cProfile.Profile()
                try:
                    with fused_preimages(),reused_joint_prefix() if mode=='prefix' else nullcontext():
                        for j,c in enumerate(cs):
                            before=study.tables(s)
                            if j==position:prior=before;prof.enable()
                            r=query(s,c,p)
                            if j==position:prof.disable()
                            for f in ('expanded_nodes','status','partition'):assert r[f]==expected[j][f]
                    final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES};assert delta==study.read_zip(trial['delta'])
                finally:s.close()
            stats=pstats.Stats(prof)
            functions=[dict(file=f,line=line,name=name,primitive_calls=cc,calls=nc,self_seconds=own,cumulative_seconds=total)
                for (f,line,name),(cc,nc,own,total,callers) in sorted(stats.stats.items(),key=lambda x:x[1][3],reverse=True)[:60]]
            profiles.append(dict(split=split,case=index,position=position,mode=mode,trial=study.binding(trial_path),source=cs[position]['source'],root=cs[position]['root'],
                prefix=prefix_binding,extra_ids={t:[k for k,v in prior[t][len(prefix[t]):]] for t in study.TABLES},functions=functions,output_matches_trial=True))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';study.restore(prefix,path);s=ConsequencePrioritySolver(path);acquisitions=[];j=None;original=prepared.acquire
            def acquired(solver,source,budget,**kwargs):
                before=study.tables(solver) if j==position else None;r=original(solver,source,budget,**kwargs)
                if before is not None:
                    cnf,_=study.normalize(source);root=study.token(cnf,Counter())
                    acquisitions.append(dict(source=[list(c) for c in source],root=root,prefix=prefix_binding,budget=budget,
                        extra_ids={t:[k for k,v in before[t][len(prefix[t]):]] for t in study.TABLES},target_absent=all(root not in dict(before[t]) for t in study.TABLES),expanded_nodes=r['metrics'].get('expanded_nodes',0),status=r['status']))
                return r
            try:
                with fused_preimages(),reused_joint_prefix(),patch.object(prepared,'acquire',acquired):
                    for j,c in enumerate(cs):query(s,c,p)
                final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
                trial_path=out/f'{split}-{index}-prefix-0/report.json';trial=base.load(trial_path);assert delta==study.read_zip(trial['delta'])
                observations.append(dict(split=split,case=index,position=position,trial=study.binding(trial_path),acquisitions=acquisitions,output_matches_trial=True))
            finally:s.close()
    for o in observations:o['proof_census']=proof_census(o)
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,profiles=profiles,observations=observations,script_sha256=base.sha(__file__),limitations=[
        'Posthoc profiles are instrumented; cumulative times overlap and are not comparative speedups. Every output matches the frozen native trial.',
        'Prefix and earlier IDs reconstruct persistent availability, not warm pools. Replay the prior stream for those. Final union must not seed comparisons.',
        'Neither proof composition nor native checking is skipped. No new coverage cell, external benchmark or arbitrary-SAT bound.']))
    print(base.encode(dict(selection={k:v for k,v in worst.items() if k!='root'},observations=[dict(split=o['split'],branches=[a['expanded_nodes'] for a in o['acquisitions']]) for o in observations])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))

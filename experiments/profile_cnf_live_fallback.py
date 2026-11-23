#!/usr/bin/env python3
"""Posthoc attribution and live-frame census, separate from comparative timing."""
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import cProfile,inspect,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_live_fallback as study
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
base=study.base


def census(solver,eligible):
    # Copy local references only long enough to size this graph. No frame or
    # solver reference escapes. This is not marginal retained or process memory.
    frame=inspect.currentframe();locals_graph=[];frames=[]
    try:
        while frame is not None:
            if frame.f_code.co_name in ('_visit','_expand'):
                data={k:v for k,v in frame.f_locals.items() if k not in ('self','__class__') and not callable(v)}
                locals_graph.append(data);cnf=data.get('normalized',data.get('cnf',()))
                frames.append(dict(file=frame.f_code.co_filename,line=frame.f_lineno,function=frame.f_code.co_name,
                    frame_bytes=sys.getsizeof(frame),literals=sum(map(len,cnf)),clauses=len(cnf)))
            frame=frame.f_back
        return dict(eligible=eligible,frames=frames,frame_object_bytes=sum(r['frame_bytes'] for r in frames),
            reachable_locals_bytes=study.harness.prior.prior.deep_size(locals_graph),
            committed_native_records=solver.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0],
            pending_records=len(solver.db.pending),in_transaction=solver.db.in_transaction)
    finally:del frame;locals_graph.clear()


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);scores=[]
    for index in (25,31,61):
        stream=[c for c in cases if (c['split'],c['case'])==('novel',index)]
        for j,c in enumerate(stream):
            costs={m:sum(base.load(out/f'novel-{index}-{m}-{r}/queries.json')[j]['seconds'] for r in range(2))/2 for m in study.MODES}
            scores.append(dict(case=index,position=j,root=c['root'],variant=c['variant'],query_seconds=costs))
    worst=max(scores,key=lambda r:r['query_seconds']['resume']);targets=[('controls',61,1),('novel',worst['case'],worst['position'])];profiles=[];captures=[]
    with tempfile.TemporaryDirectory() as td:
        for n,(split,index,position) in enumerate(targets):
            cs=[c for c in cases if (c['split'],c['case'])==(split,index)];prefix=study.read_zip(p['prefixes'][str(index)]['archive'])
            for mode in study.MODES:
                trial_path=out/f'{split}-{index}-{mode}-0/report.json';trial=base.load(trial_path);expected=study.bound(trial['queries'])
                path=Path(td)/f'profile-{n}-{mode}';study.restore(prefix,path)
                cls=study.live.ContinuationSolver if mode=='resume' else InputSafeAffineProbeSolver
                s=cls(path,node_limit=p['node_limit']);prof=cProfile.Profile()
                try:
                    with patch.object(study.previous.targeted,'inspect_targeted_backbone',partial(study.previous.first,policy='binary1')):
                        for j,c in enumerate(cs):
                            if j==position:prof.enable()
                            r=(study.live.run if mode=='resume' else study.previous.prepared_run)(s,c['candidate'],'probe6',p['node_limit'])
                            if j==position:prof.disable()
                            assert r['expanded_nodes']==expected[j]['expanded_nodes'] and r['partition']==expected[j]['partition'] and r['status']==expected[j]['status']
                    final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES};assert delta==study.read_zip(trial['delta'])
                finally:s.close()
                stats=pstats.Stats(prof)
                functions=[dict(file=f,line=l,name=name,primitive_calls=cc,calls=nc,self_seconds=own,cumulative_seconds=total)
                    for (f,l,name),(cc,nc,own,total,callers) in sorted(stats.stats.items(),key=lambda x:x[1][3],reverse=True)[:40]]
                profiles.append(dict(split=split,case=index,position=position,mode=mode,trial=study.binding(trial_path),functions=functions,output_matches_trial=True))
            # Separate allocation/branch census; all produced bytes must still
            # match the same frozen resume stream, without creating extra proof authority.
            path=Path(td)/f'census-{n}';study.restore(prefix,path);s=study.live.ContinuationSolver(path,node_limit=p['node_limit']);events=[];branches=[]
            original=study.live.acquire;j=None
            def acquire(solver,source,budget,**kw):
                before=study.tables(solver) if j==position else None
                r=original(solver,source,budget,**kw)
                if before is not None:
                    cnf,names=study.previous.normalize(source);root=study.previous.token(cnf,Counter())
                    extra={t:[k for k,v in before[t][len(prefix[t]):]] for t in study.TABLES}
                    branches.append(dict(source=[list(c) for c in source],root=root,initial_budget=budget,effective_budget=p['node_limit'] if r['metrics'].get('continuation_resumptions') else budget,
                        prefix=p['prefixes'][str(index)]['archive'],extra_ids=extra,
                        target_absent=all(root not in dict(before[t]) for t in study.TABLES),
                        expanded_nodes=r['metrics'].get('expanded_nodes',0),status=r['status']))
                return r
            def observe(solver,eligible):
                if j==position:
                    event=census(solver,eligible)
                    event['query_root_absent']=solver.db.execute('SELECT 1 FROM cnf_residual_v1 WHERE id=?',(cs[j]['root'],)).fetchone() is None
                    assert event['query_root_absent'] and not event['pending_records'] and not event['in_transaction']
                    events.append(event)
            try:
                with patch.object(study.previous.targeted,'inspect_targeted_backbone',partial(study.previous.first,policy='binary1')),patch.object(study.live,'acquire',acquire):
                    for j,c in enumerate(cs):study.live.run(s,c['candidate'],'probe6',p['node_limit'],observe=observe)
                final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
                trial_path=out/f'{split}-{index}-resume-0/report.json';trial=base.load(trial_path);assert delta==study.read_zip(trial['delta'])
                captures.append(dict(split=split,case=index,position=position,trial=study.binding(trial_path),events=events,acquisitions=branches,output_matches_trial=True))
            finally:s.close()
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,profiles=profiles,captures=captures,script_sha256=base.sha(__file__),limitations=[
        'Posthoc exposed boundary and largest fresh resume query. Profiles replay exact prefixes and earlier queries; all native bytes, sidecars, verdicts and expansions match frozen trials. Instrumented time is not comparative performance.',
        'The separate census measures a deduplicated graph reachable from native visit/expand locals, excluding the solver reference, plus frame-object shallow bytes. It overlaps caches, excludes interpreter/C-stack overhead and routing plans, and is neither marginal retention nor peak process RAM.',
        'Saved acquisition prefixes contain only earlier proof rows from the bound trial delta. They reconstruct persistent availability, not live stack frames or warm hint pools. No unfinished continuation is serialized.',
        'The largest-query selection uses measured time after the comparison; it is not held-out policy tuning or proof of broad coverage.']))
    print(base.encode(dict(selection={k:v for k,v in worst.items() if k!='root'},censuses=[dict(split=c['split'],case=c['case'],events=c['events']) for c in captures])),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))

#!/usr/bin/env python3
"""Posthoc exact-output profiles, source census and transient allocation probe."""
from collections import Counter
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
import cProfile,pstats,sys,tempfile,tracemalloc
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_preimage_fusion as study,cnf_partition_preparation as prepared
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_preimage_fusion import fused_preimage,fused_preimages
base=study.base


def run_query(s,c,p):
    if study.native_split(c['split']):return study.harness.query(s,c,'native',p['branch_limit'])
    return study.prepared_run(s,c['candidate'],'probe6',p['node_limit'])


class Canonicalizer:
    def __init__(self):self.counts=Counter()
    def _canonical(self,cnf):
        result,names=study.normalize(cnf,self.counts);return result,names,study.token(result,self.counts)


def allocations(out,p):
    rows=study.bound(study.bound(p['exploration'])['requests']);results=[]
    for order in (study.MODES,tuple(reversed(study.MODES))):
        for mode in order:
            e=CausalSupportExtractor(Canonicalizer(),materialize=False);fn=fused_preimage if mode=='fused' else CausalSupportExtractor._preimage
            requests=[(tuple(map(tuple,r['source'])),r['ids'],dict(r['assignment']),r['child'],r['selected']) for r in rows]
            tracemalloc.start();tracemalloc.reset_peak()
            try:
                for args,r in zip(requests,rows):assert fn(e,*args)==set(r['result'])
                current,peak=tracemalloc.get_traced_memory()
            finally:tracemalloc.stop()
            results.append(dict(order=list(order),mode=mode,current_bytes=current,peak_bytes=peak,extractor_counts=dict(e.counts),canonical_counts=dict(e.solver.counts)))
    return dict(results=results,requests=len(rows),limitations=[
        'Posthoc traced Python allocations for the34 exposed preimage requests, with inputs already allocated and a pure canonicalizer. Includes counter growth and assertion temporaries; excludes the existing solver graph, input storage, SQLite and interpreter/C allocations.',
        'This is neither process peak RSS nor full-query marginal memory, and instrumented elapsed time is not reported as performance.'])


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);scores=[]
    for index in (25,31,61):
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            times={m:sum(base.load(out/f'novel-{index}-{m}-{i}/queries.json')[j]['seconds'] for i in range(2))/2 for m in study.MODES}
            scores.append(dict(case=index,position=j,root=c['root'],variant=c['variant'],query_seconds=times))
    worst=max(scores,key=lambda r:r['query_seconds']['fused']);profiles=[];observations=[]
    for split,index,position in (('controls',31,1),('novel',worst['case'],worst['position'])):
        cs=[c for c in cases if (c['split'],c['case'])==(split,index)]
        prefix_binding=p['prefixes'][str(index)]['archive'];prefix=study.read_zip(prefix_binding)
        for mode in study.MODES:
            trial_path=out/f'{split}-{index}-{mode}-0/report.json';trial=base.load(trial_path);expected=study.bound(trial['queries'])
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';study.restore(prefix,path);s=ConsequencePrioritySolver(path);prof=cProfile.Profile()
                try:
                    with fused_preimages() if mode=='fused' else nullcontext():
                        for j,c in enumerate(cs):
                            before=study.tables(s)
                            if j==position:prior=before;prof.enable()
                            r=run_query(s,c,p)
                            if j==position:prof.disable()
                            for f in ('expanded_nodes','status','partition'):assert r[f]==expected[j][f]
                    final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES};assert delta==study.read_zip(trial['delta'])
                finally:s.close()
            stats=pstats.Stats(prof)
            functions=[dict(file=f,line=line,name=name,primitive_calls=cc,calls=nc,self_seconds=own,cumulative_seconds=total)
                for (f,line,name),(cc,nc,own,total,callers) in sorted(stats.stats.items(),key=lambda x:x[1][3],reverse=True)[:45]]
            profiles.append(dict(split=split,case=index,position=position,mode=mode,trial=study.binding(trial_path),source=cs[position]['source'],root=cs[position]['root'],
                prefix=prefix_binding,extra_ids={t:[k for k,v in prior[t][len(prefix[t]):]] for t in study.TABLES},functions=functions,output_matches_trial=True))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';study.restore(prefix,path);s=ConsequencePrioritySolver(path);events=[];acquisitions=[];j=None;original_acquire=prepared.acquire
            def observed(self,cnf,ids,assignment,child,selected):
                ids=tuple(ids);selected=tuple(selected);result=fused_preimage(self,cnf,ids,assignment,child,selected)
                if j==position:events.append(dict(source=[list(c) for c in cnf],ids=list(ids),assignment=sorted(assignment.items()),child=child,selected=list(selected),result=sorted(result)))
                return result
            def acquired(solver,source,budget,**kwargs):
                before=study.tables(solver) if j==position else None
                result=original_acquire(solver,source,budget,**kwargs)
                if before is not None:
                    cnf,_=study.normalize(source);root=study.token(cnf,Counter())
                    acquisitions.append(dict(source=[list(c) for c in source],root=root,prefix=prefix_binding,budget=budget,
                        extra_ids={t:[k for k,value in before[t][len(prefix[t]):]] for t in study.TABLES},
                        target_absent=all(root not in dict(before[t]) for t in study.TABLES),expanded_nodes=result['metrics'].get('expanded_nodes',0),status=result['status']))
                return result
            try:
                with patch.object(CausalSupportExtractor,'_preimage',observed),patch.object(prepared,'acquire',acquired):
                    for j,c in enumerate(cs):run_query(s,c,p)
                final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
                trial_path=out/f'{split}-{index}-fused-0/report.json';trial=base.load(trial_path);assert delta==study.read_zip(trial['delta'])
                observations.append(dict(split=split,case=index,position=position,trial=study.binding(trial_path),events=events,acquisitions=acquisitions,output_matches_trial=True))
            finally:s.close()
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,profiles=profiles,observations=observations,allocations=allocations(out,p),script_sha256=base.sha(__file__),limitations=[
        'Posthoc preceding largest query and largest fresh fused query. Instrumented cumulative times overlap and are not comparative speedups. Every profile and observation reproduces frozen native bytes.',
        'Source/assignment/child/selection bindings remain exact. Recorded proposals do not authorize answers. The canonical-parent invariant is required; external inputs still use the general normalizer.',
        'Prefix plus listed earlier IDs reconstructs persistent availability; replay the prior stream for warm pools. The final union must not seed comparison queries.',
        'No broader decision coverage or alternative-support policy is introduced; every first-parent representative and support choice is unchanged.']))
    print(base.encode(dict(selection={k:v for k,v in worst.items() if k!='root'},observations=[dict(split=o['split'],preimages=len(o['events']),branches=[a['expanded_nodes'] for a in o['acquisitions']]) for o in observations])),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))

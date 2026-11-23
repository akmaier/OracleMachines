#!/usr/bin/env python3
"""Census exact forward/backward joint prefix reconstruction in the saved stream."""
from pathlib import Path
from unittest.mock import patch
import inspect,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_preimage_fusion as prior,cnf_joint_backbone as joint,cnf_consequence_priority as priority
from experiments.cnf_preimage_fusion import fused_preimages
base=prior.base;PARENT=Path('experiments/results/cnf-preimage-fusion')


def run(out):
    p=base.load(PARENT/'protocol.json');cases=prior.bound(p['cases']);prefix_binding=p['prefixes']['31']['archive'];prefix=prior.read_zip(prefix_binding)
    cs=[c for c in cases if (c['split'],c['case'])==('novel',31)];events=[];stack=[];original=joint.force_all;j=None
    def observe(s,cnf,evidence):
        event=dict(query_index=j,source=[list(c) for c in cnf],evidence=evidence,constructions=[]);events.append(event);stack.append(event)
        try:return original(s,cnf,evidence)
        finally:stack.pop()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';prior.restore(prefix,path);s=priority.ConsequencePrioritySolver(path);queries=[];canonical=s._canonical
        def capture(raw):
            result=canonical(raw);frame=inspect.currentframe().f_back
            try:
                if frame.f_code is original.__code__:
                    f=frame.f_locals;back='context' in f;assignment=f['context'] if back else f['fixed']
                    stack[-1]['constructions'].append(dict(phase='backward' if back else 'forward',index=f['index'],assignment=sorted(assignment.items()),raw=[list(c) for c in raw],canonical=[list(c) for c in result[0]],names=list(result[1]),key=result[2]))
            finally:del frame
            return result
        try:
            with fused_preimages(),patch.object(priority,'force_all',observe),patch.object(s,'_canonical',capture):
                for j,c in enumerate(cs):queries.append(prior.prepared_run(s,c['candidate'],'probe6',256))
            final=prior.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in prior.TABLES}
        finally:s.close()
    trial_path=PARENT/'novel-31-fused-0/report.json';trial=base.load(trial_path);assert delta==prior.read_zip(trial['delta'])
    for a,b in zip(queries,prior.bound(trial['queries'])):
        for f in ('status','expanded_nodes','partition'):assert a[f]==b[f]
    summary=[]
    for q in range(2):
        ev=[e for e in events if e['query_index']==q];repeated=[]
        for e in ev:
            forward=[x for x in e['constructions'] if x['phase']=='forward']
            for back in (x for x in e['constructions'] if x['phase']=='backward' and x['index']==1):
                assert len(forward)==1;first=forward[0]
                for field in ('assignment','raw','canonical','names','key'):assert first[field]==back[field]
                repeated.append(back)
        summary.append(dict(query_index=q,calls=len(ev),two_path_calls=sum(len(e['evidence'])==2 for e in ev),repeated_prefixes=len(repeated),repeated_literal_visits=sum(sum(map(len,r['raw'])) for r in repeated)))
    base.write(out/'prefix-census.json',events)
    base.write(out/'exploration.json',dict(parent=prior.binding(PARENT/'checkpoint.json'),trial=prior.binding(trial_path),prefix=prefix_binding,requests=prior.binding(out/'prefix-census.json'),summary=summary,output_matches_trial=True,script_sha256=base.sha(__file__),limitations=['Exposed case31 stream; instrumentation is untimed. Every native byte and partition matches the prior trial. No extra proof is created.','Construction equality is scoped to the exact original source and assignment, including the original-name map; canonical-key equality alone would not suffice.']))
    print(base.encode(summary),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))

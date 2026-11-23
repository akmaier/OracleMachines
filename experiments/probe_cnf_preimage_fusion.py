#!/usr/bin/env python3
"""Capture exact causal-preimage requests without changing their results."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_consequence_priority as prior
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_causal_support import CausalSupportExtractor
base=prior.base;PARENT=Path('experiments/results/cnf-consequence-priority')


def run(out):
    p=base.load(PARENT/'protocol.json');cases=prior.bound(p['cases']);prefix_binding=p['prefixes']['31']['archive'];prefix=prior.read_zip(prefix_binding)
    cs=[c for c in cases if (c['split'],c['case'])==('novel',31)];events=[];original=CausalSupportExtractor._preimage;j=None
    def observe(self,cnf,ids,assignment,child,selected):
        ids=tuple(ids);selected=tuple(selected);result=original(self,cnf,ids,assignment,child,selected)
        events.append(dict(query_index=j,source=[list(c) for c in cnf],ids=list(ids),assignment=sorted(assignment.items()),child=child,selected=list(selected),result=sorted(result)))
        return result
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';prior.restore(prefix,path);s=ConsequencePrioritySolver(path);queries=[]
        try:
            with patch.object(CausalSupportExtractor,'_preimage',observe):
                for j,c in enumerate(cs):queries.append(prior.previous.previous.previous.prepared_run(s,c['candidate'],'probe6',256))
            final=prior.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in prior.TABLES}
        finally:s.close()
    trial_path=PARENT/'novel-31-priority-0/report.json';trial=base.load(trial_path);assert delta==prior.read_zip(trial['delta'])
    expected=prior.bound(trial['queries'])
    for a,b in zip(queries,expected):
        for f in ('expanded_nodes','status','partition'):assert a[f]==b[f]
    summary=[]
    for q in range(2):
        ev=[e for e in events if e['query_index']==q];duplicates=0;clauses=0;literals=0;empty=0
        for e in ev:
            seen=set();assignment=dict(e['assignment'])
            for cid in e['ids']:
                c=e['source'][cid];clauses+=1;literals+=len(c)
                if any(abs(l) in assignment and assignment[abs(l)]==(l>0) for l in c):continue
                residual=tuple(l for l in c if abs(l) not in assignment);empty+=not residual
                duplicates+=residual in seen;seen.add(residual)
        summary.append(dict(query_index=q,preimages=len(ev),clauses=clauses,literals=literals,duplicate_residuals=duplicates,empty_residuals=empty,
            assignment_sizes=dict(Counter(len(e['assignment']) for e in ev))))
    base.write(out/'preimages.json',events)
    base.write(out/'exploration.json',dict(parent=prior.binding(PARENT/'checkpoint.json'),trial=prior.binding(trial_path),prefix=prefix_binding,
        requests=prior.binding(out/'preimages.json'),summary=summary,output_matches_trial=True,script_sha256=base.sha(__file__),limitations=[
        'Exposed case31 query stream. Observer allocations are excluded from performance comparisons. Every emitted byte matches the preceding frozen trial; no additional proof is created.',
        'Residual duplicates quantify shared reduced-clause descriptions, not alternative-support coverage or globally minimal cores.']))
    print(base.encode(summary),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))

#!/usr/bin/env python3
"""Attribute all three policies, including retained first-path regressions."""
from collections import Counter,defaultdict
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_residual_dag import ResidualSolver,two_cnf
from experiments.cnf_binary_backbone import inspect_backbones
from experiments import compare_cnf_binary_backbone as study
base=study.base



def frontier(out,cases):
    report=base.load(out/'frequency-0/report.json');queries=study.bound(report['queries']);counts=Counter();missed=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'archive';base.restore_archive(report['archive'],path);s=ResidualSolver(path)
        try:rows={base.key_sha(k):base.load_json(v) for k,v in study.native.rows(s).items()}
        finally:s.close()
    for query,case in zip(queries,cases):
        for key in query['new_ids']:
            cnf=tuple(tuple(c) for c in rows[key]['cnf']);binary=[c for c in cnf if len(c)==2]
            if any(len(c)<2 for c in cnf):counts['unit_or_empty']+=1;continue
            if not binary:counts['no_binary']+=1;continue
            if len(binary)==len(cnf):counts['only_binary']+=1;continue
            model,proof=two_cnf(binary,Counter())
            if proof is not None:counts['mixed_binary_unsat']+=1;continue
            counts['mixed_binary_sat']+=1;graph={}
            for a,b in binary:graph.setdefault(-a,[]).append(b);graph.setdefault(-b,[]).append(a)
            forced=set()
            for literal in graph:
                seen={literal};todo=[literal]
                while todo:
                    for target in graph.get(todo.pop(),[]):
                        if target not in seen:seen.add(target);todo.append(target)
                if -literal in seen:forced.add(-literal)
            counts['with_binary_backbone' if forced else 'without_binary_backbone']+=1
            if not forced:continue
            proof,cover,partials=inspect_backbones(cnf,Counter())
            if proof is not None or cover is not None:counts['already_refuted']+=1;continue
            freq=Counter(abs(l) for c in cnf for l in c);variable=min(freq,key=lambda v:(-freq[v],v))
            found={abs(p['literal']) for p in partials or []}
            if variable in {abs(l) for l in forced} and variable not in found:
                counts['missed_frequency_backbone']+=1
                missed.append(dict(case=case['case'],family=case['family'],root_sha256=key,variables=len(freq),clauses=len(cnf),
                    default_variable=variable,forced_literals=sorted(forced),native_kind=rows[key].get('proof',{}).get('kind','model'),native_split_matches=rows[key].get('proof',{}).get('variable')==variable,found_literals=sorted(found)))
    return dict(counts=dict(counts),missed=missed,limitations=['Posthoc uncapped reachability on stored nodes, including direct publications and compiled children; not timed expansion opportunities.',
        'A missing backbone here is a recognition opportunity, not a demonstrated improvement. Its targeted discovery and changed proof costs still need measurement.'])


def analyze(out):
    cases=base.load(out/'cases.json')['cases'];groups={};targets={};pairs=[];same=Counter()
    for repeat in range(2):
        rows={m:base.load(out/f'{m}-{repeat}/queries.json') for m in study.MODES}
        stats={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        for mode in ('first','frequency'):
            same[mode+'_admissions']=sum(a['admission']==b['admission'] for a,b in zip(rows['cover'],rows[mode]))+same[mode+'_admissions']
            same[mode+'_probe_counts']=sum(a['probe_counts']==b['probe_counts'] for a,b in zip(rows['cover'],rows[mode]))+same[mode+'_probe_counts']
            pairs.append(dict(repeat=repeat,mode=mode,**{k:stats[mode][k]-stats['cover'][k] for k in ('query_seconds','cold_seconds','complete_worker_seconds')}))
        if repeat:continue
        for mode,records in rows.items():
            g=defaultdict(Counter);t=[]
            for row,case in zip(records,cases):
                m=row['child']['metrics'];native={k:v for k,v in m.items() if k.startswith(('binary_subset_','binary_cover_','binary_backbone_'))}
                g[case['family']].update(native);g[case['family']].update(native_nodes=row['new_nodes'],native_expanded=m.get('expanded_nodes',0),
                    extension_nodes=m.get('affine_negative_inserted_nodes',0),child_propagation=m.get('propagation_literal_visits',0),discovery_propagation=row['probe_counts'].get('propagation_literal_visits',0))
                admission=row['admission'];bridge=admission.get('affine_bridge') if admission else None
                t.append(dict(case=case['case'],family=case['family'],answer=row['record']['answer'],native_nodes=row['new_nodes'],native_expanded=m.get('expanded_nodes',0),
                    child_propagation=m.get('propagation_literal_visits',0),discovery_propagation=row['probe_counts'].get('propagation_literal_visits',0),native_recognition=native,
                    reason=None if admission is None else admission['reason'],status=None if bridge is None else bridge['status'],free=None if bridge is None else bridge['free']))
            groups[mode]={f:dict(v) for f,v in g.items()};targets[mode]=t
    result=dict(frontier=frontier(out,cases),groups=groups,targets=targets,pairs=pairs,preceding_evidence_equal=dict(same),
        largest_acquisition=sorted(targets['frequency'],key=lambda r:r['child_propagation'],reverse=True)[:10],
        largest_discovery=sorted(targets['frequency'],key=lambda r:r['discovery_propagation'],reverse=True)[:10],
        limitations=['Posthoc attribution is outside worker timing; family labels never enter recognition.',
            'Compiled children, source copies, checks and ranking remain work even when ordinary expansion calls fall.',
            'Frequency matching is a sufficient admission gate, not proof of identical fallback control flow. First-path and gate misses/regressions remain retained.',
            'Finite source generators and two orders do not establish general runtime or memory dominance.'])
    base.write(out/'attribution.json',result);print(base.encode(dict(groups=groups,pairs=pairs,preceding_evidence_equal=dict(same))),flush=True)


if __name__=='__main__':analyze(Path(sys.argv[1]))

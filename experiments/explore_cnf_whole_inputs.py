#!/usr/bin/env python3
"""Freeze unlabelled whole inputs, then measure the current native policy."""
from collections import Counter
from pathlib import Path
import cProfile, json, pstats, sqlite3, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_refined_origins as prior
from experiments.cnf_fresh_mixtures import catalog, attempt, LIMIT
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_residual_dag import normalize, token
base, binding, bound = prior.base, prior.binding, prior.bound
PARENT=Path('experiments/results/cnf-refined-origins')
FILES=('experiments/cnf_fresh_mixtures.py','experiments/explore_cnf_whole_inputs.py')


def prepare(out):
    out.mkdir(exist_ok=True); assert not (out/'cases.json').exists()
    parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items(): assert base.sha(f)==h,f
    cases=catalog()
    # Freeze all sources before seeing any answers; no outcome filtering.
    for c in cases:
        cnf,names=normalize(c['source']); c.update(root=token(cnf,Counter()),variables=len(names),
            clauses=len(cnf),literals=sum(map(len,cnf)))
    base.write(out/'cases.json',cases)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'prior';base.restore_archive(parent['reference_union'],path)
        con=sqlite3.connect(path)
        try:known={k for t in prior.TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    base.write(out/'exploration-protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),
        parent_manifest=binding(PARENT/'manifest.json'),cases=binding(out/'cases.json'),node_limit=LIMIT,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        novelty=[dict(case=c['case'],known_in_parent=c['root'] in known) for c in cases],
        limitations=['Seventy-two whole CNFs: six designed families, sizes 36/60, two samples, base/edit/repeat. Fresh fixed RNG seed 202611231956; all inputs frozen before solving.',
            'Solver receives only the CNF; no supplied guard, map, family label or archived answer. Start empty and keep checked results and completed budget-stop prefixes for subsequent queries.',
            'A 256-dispatch cap is not a runtime, discovery, proof publication or memory bound. Unknown remains unknown.',
            'Exploration guides the subsequent candidate. Its diagnostic profile is separately rerun and excluded from elapsed means; this is not held-out evaluation.']))


def run(out):
    p=base.load(out/'exploration-protocol.json');cases=bound(p['cases']);rows=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'explore';s=ConsequencePrioritySolver(path,node_limit=p['node_limit'])
        try:
            for c in cases:
                r=attempt(s,c['source']);rows.append(dict(case=c['case'],family=c['family'],variant=c['variant'],**r))
            archive=base.archive(path,out/'exploration')
        finally:s.close()
    base.write(out/'exploration-queries.json',rows)
    groups={fam:dict(seconds=sum(r['solve_seconds'] for r in rows if r['family']==fam),
        statuses=dict(Counter(r['status'] for r in rows if r['family']==fam)),
        expanded=sum(r['metrics'].get('expanded_nodes',0) for r in rows if r['family']==fam)) for fam in dict.fromkeys(c['family'] for c in cases)}
    worst=max(rows,key=lambda r:r['solve_seconds']);c=cases[worst['case']]
    # Profile the costly input in isolation. Do not seed it with final answers.
    s=ConsequencePrioritySolver(node_limit=p['node_limit']);profile=cProfile.Profile()
    try:diagnostic=profile.runcall(attempt,s,c['source'])
    finally:s.close()
    destination=out/'exploration-profile.pstats';profile.dump_stats(destination)
    functions=[dict(file=f,line=l,function=n,calls=v[1],own_seconds=v[2],cumulative_seconds=v[3]) for (f,l,n),v in pstats.Stats(profile).stats.items()]
    report=dict(protocol=binding(out/'exploration-protocol.json'),queries=binding(out/'exploration-queries.json'),archive=archive,
        groups=groups,profile=dict(case=c['case'],source=c['source'],result=diagnostic,binding=binding(destination),functions=sorted(functions,key=lambda r:-r['cumulative_seconds'])))
    base.write(out/'exploration.json',report)
    print(base.encode(dict(groups=groups,worst_case=worst['case'],worst_status=worst['status'])),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    else:run(Path(sys.argv[1]))

#!/usr/bin/env python3
"""Locate the first later routing divergence and preserve its exact prestate."""
from collections import Counter,deque
from pathlib import Path
from unittest.mock import patch
import json,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_routing as study
from experiments.cnf_binary_routing import priority_expand
from experiments.cnf_targeted_backbone import TargetedBackboneMixin
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import normalize,token,propagate,restrict,FORMAT
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
base=study.base;NATIVE=study.TABLES[0]


class ReachedTarget(Exception):pass


def diagnose(out):
    p=base.load(out/'protocol.json');seed=study.read_zip(p['prefixes']['regression']['archive']);states={};reports={};queries={}
    for mode in ('baseline','priority'):
        path=out/f'regression-31-{mode}-0/report.json';r=base.load(path);reports[mode]=study.binding(path)
        queries[mode]=study.bound(r['queries'])[0]
        states[mode]={**dict(seed[NATIVE]),**dict(study.read_zip(r['delta'])[NATIVE])}
    assert queries['baseline']['root']==queries['priority']['root']
    queue=deque([queries['baseline']['root']]);seen=set();divergence=None
    while queue:
        key=queue.popleft()
        if key in seen:continue
        seen.add(key);nodes=[json.loads(states[m][key]) for m in ('baseline','priority')]
        proofs=[n['proof'] for n in nodes]
        if [(x['kind'],x.get('variable')) for x in proofs][0]!=[(x['kind'],x.get('variable')) for x in proofs][1]:
            divergence=(key,nodes,proofs);break
        for field in ('child','low','high'):
            if field in proofs[0] and proofs[0][field]==proofs[1].get(field):queue.append(proofs[0][field])
    assert divergence is not None
    key,nodes,proofs=divergence;source=nodes[0]['cnf'];assert nodes[1]['cnf']==source
    assert [x['kind'] for x in proofs]==['split','split'] and [x['variable'] for x in proofs]==[76,8]
    case=next(c for c in study.bound(p['cases']) if c['split']=='regression');captured={}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';study.restore(seed,path);s=InputSafeAffineProbeSolver(path);original=s._visit
        def visit(cnf):
            normalized,_=normalize(cnf);actual=token(normalized,Counter())
            if actual==key:
                captured.update(rows=study.tables(s),counts=dict(s.counts));raise ReachedTarget()
            return original(cnf)
        try:
            with patch.object(TargetedBackboneMixin,'_expand',priority_expand),patch.object(s,'_visit',visit):
                try:acquire(s,case['source'],256)
                except ReachedTarget:pass
                else:raise AssertionError('Divergent state was not reached')
            assert captured and not s.db.active and not s.db.pending
        finally:s.close()
        extra={t:[[k,v] for k,v in captured['rows'][t][len(seed[t]):]] for t in study.TABLES}
        assert all(not extra[t] for t in study.TABLES[1:])
        trial=study.bound(reports['priority']);delta=study.read_zip(trial['delta'])
        assert extra[NATIVE]==delta[NATIVE][:len(extra[NATIVE])]
        fresh=Path(td)/'snapshot';study.restore(seed,fresh,extra);digest=base.sha(fresh);s=CanonicalVerifySnapshot(fresh)
        try:
            cnf,_,actual=s._canonical(source);assert actual==key and s._read(key,cnf) is None
            for k,v in extra[NATIVE]:assert s._read(k) is not None
            tests=[]
            for value in (False,True):
                child,_,child_key=s._canonical(restrict(cnf,{76:value}));fixed,trace,conflict=propagate(child,Counter())
                cert=None
                if conflict is not None:
                    cert=dict(format=FORMAT,cnf=[list(c) for c in child],answer=False,proof=dict(kind='units',trace=trace,conflict=conflict))
                    s._verify(child_key,cert)
                tests.append(dict(value=value,root=child_key,unit_fixed=len(fixed),conflict=conflict,certificate=cert))
            assert tests[0]['conflict'] is None and tests[1]['conflict'] is not None
            counts=dict(s.counts)
        finally:s.close()
        assert digest==base.sha(fresh)
    base.write(out/'next-target.json',dict(source=source,root=key,prefix=p['prefixes']['regression']['archive'],trial_report=reports['priority'],
        extra_ids=[k for k,v in extra[NATIVE]],extra_count=len(extra[NATIVE]),reader_counts=counts,
        input_reports=reports,baseline_variable=76,priority_variable=8,polarity_checks=tests,prefix_discovery_counts=captured['counts'],
        limitations=[
        'Exposed posthoc diagnostic, excluded from timing. The first later common state branches on76 under the original policy and8 under priority. Its root is absent from the reconstructed state.',
        'An instrumented acquisition stops before visiting that target. Complete checked earlier rows, including pending transaction rows, are captured; the diagnostic aborts its live transaction and restores only those valid rows for read-only checking. No target search or target answer is imported.',
        'Both ordinary-variable cofactors are inspected by unit propagation. False has no conflict; true has an independently checked unit refutation. This exposes fixed-polarity incompleteness, not absence of other deductions or a claim of optimal routing.',
        'The original branch snapshot is already included in the prefix; extra_ids selects only this isolated query\'s earlier rows from the bound priority trial delta. Broad polarity/renaming transfer and cost-aware probing remain to be tested.']))
    print(base.encode(dict(extra_count=len(extra[NATIVE]),baseline_variable=76,priority_variable=8,false_conflict=False,true_conflict=True)),flush=True)


if __name__=='__main__':diagnose(Path(sys.argv[1]))

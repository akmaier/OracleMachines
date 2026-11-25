#!/usr/bin/env python3
"""Classify high-budget misses from checked snapshots and exact final cofactors.

Read-only diagnosis, never a new proof authority. Partial programs are replayed
using frozen source/edge checks. Snapshot absence is reported as unknown.
"""
from collections import Counter
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_budget_frontier as study
from experiments import cnf_guard_shortening_context as frozen
base=study.base;old=study.old;previous=study.previous;native=study.native


def diagnose(out):
    p=base.load(out/'protocol.json');rows=[];start=time.perf_counter()
    for target in p['targets']:
        source,ts,_,events=study.prior.reuse.inputs(p,target)
        report=base.load(out/f'census-{target}-prepared256-0/report.json')
        query=base.load(f'experiments/results/cnf-guard-covers/serial/target-{target}-census-0/report.json')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';previous.restore_archive(query['archive'],path);reader=previous.CanonicalVerifySnapshot(path)
            affine=previous.TerminalStore(reader);equiv=previous.MultiEquivalenceStore(reader)
            before=base.sha(path)
            try:
                for e in old.bound(report['events'])['rows']:
                    if e['program']['status']=='refuted':continue
                    tick=time.perf_counter();found=reader._read(e['root'])
                    if found is None:found=affine.read(e['root'])
                    if found is None:found=equiv.read(e['root'])
                    answer='unknown' if found is None else ('sat' if found['answer'] else 'unsat')
                    local,hints,_=previous.local_hints(source,ts,events[e['event']],Counter());templates=[h['template'] for h in hints]
                    c=Counter();fixed={};support=set();frozen._source(local,templates,c)
                    for step in e['program']['steps']:
                        state=frozen._state(local,templates,fixed,c)
                        frozen._bind_path(step['path'],step['forced'],state,local,templates,fixed,support,c,e['program']['path_limit'])
                        fixed[abs(step['forced'])]=step['forced']>0
                    state=frozen._state(local,templates,fixed,c);model,proof=native.two_cnf(state['graph'],c)
                    assert proof is None and () not in state['local']
                    # A deterministic completion of a necessary binary model is
                    # only a SAT witness if it passes the entire source check.
                    complete={v:model.get(v,False) for v in range(1,len(state['names'])+1)}
                    witness={**fixed,**{name:complete[i] for i,name in enumerate(state['names'],1)}}
                    witness.update({abs(l):False for cl in local for l in cl if abs(l) not in witness})
                    sat=native.holds(local,witness)
                    if sat:assert answer!='unsat'
                    clause_widths=Counter(map(len,state['local']));guard_widths=Counter(len(h['clause']) for h in state['hints'])
                    violated=[list(cl) for cl in state['local'] if not any(complete[abs(l)]==(l>0) for l in cl)]
                    rows.append(dict(target=target,event=e['event'],root=e['root'],reason=e['program']['reason'],snapshot_answer=answer,
                        snapshot_proof_kind=None if found is None else found.get('proof',{}).get('kind'),
                        forced_steps=len(e['program']['steps']),final_variables=len(state['names']),final_clause_widths=dict(clause_widths),final_guard_widths=dict(guard_widths),
                        binary_model_completion_is_sat=sat,violated_clauses=len(violated),violated_clause_widths=dict(Counter(map(len,violated))),
                        checked_step_supports=len(support),counts=dict(c),seconds=time.perf_counter()-tick))
            finally:reader.close()
            assert base.sha(path)==before
    base.write(out/'residual-diagnosis.json',dict(rows=rows,seconds=time.perf_counter()-start,
        program_source=old.binding(out/'censuses.json'),source_fingerprints={'experiments/probe_cnf_shortening_budget_residuals.py':base.sha(__file__)},
        summary=dict(snapshot_answers=dict(Counter(r['snapshot_answer'] for r in rows)),completion_witnesses=sum(r['binary_model_completion_is_sat'] for r in rows),
            unique_roots=len({r['root'] for r in rows}),with_wider_guards=sum(any(int(w)>2 for w in r['final_guard_widths']) for r in rows)),
        limitations='Read-only exposed-snapshot diagnosis, independently binding each partial-program edge. Snapshot absence stays unknown. A failed deterministic model completion does not prove UNSAT. No new positive or negative records are published.'))
    print(base.encode(base.load(out/'residual-diagnosis.json')['summary']),flush=True)


if __name__=='__main__':diagnose(Path(sys.argv[1]))

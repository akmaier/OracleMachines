#!/usr/bin/env python3
"""Compare deferred witness checking with the frozen eager gate and controls."""
from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_closure as previous
from experiments.cnf_guard_closure_solver import GuardClosureSolver
from experiments.cnf_guard_witness_solver import WitnessGuardClosureSolver
base=previous.base;old=previous.old
PARENT=Path('experiments/results/cnf-guard-closure')
MODES=('ordinary','certificate','eager','witness')
FILES=('experiments/cnf_guard_witness_solver.py','solver/test_cnf_guard_witness_solver.py',
       'experiments/compare_cnf_guard_witness.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    out.mkdir(parents=True,exist_ok=True)
    parent=base.load(PARENT/'checkpoint.json');prior=base.load(PARENT/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(
        parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        **{k:prior[k] for k in ('cases','origins','targets','inputs','node_limit','handoff_bytes',
                               'closure_checks','closure_literals','closure_edges','path_limit')},
        witness_retries=32,graph_checks=1024,orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=[
            'All eight exposed chronological edits, two alternating serial repetitions, and the same causal origin prefixes/banks. No later repeat, cumulative union or posthoc local hint archive seeds a query.',
            'Ordinary and guided certificate controls are unchanged. Eager is the frozen binary guard closure. Witness builds tentative unit/binary graphs and transports only supports used by a contradiction witness, with exact local checking and the existing native compiler.',
            'A satisfiable tentative superset graph rejects only this short-guard closure opportunity, not the original SAT problem. Every selected nonoriginal edge requires a local certificate; empty candidates require their own unit certificate. Unsupported candidates are removed, preserving alternatives.',
            'Witness adds at most 32 rejected candidates per site and 1024 tentative graph checks per query. Existing 100000 candidate checks, 1000000 reserved support literals, 4096 compiled edges and 256 edges per path remain. These do not bound all work, verification, retained storage or process memory.',
            'The worker and its accounting are reused from the frozen live-gate comparison. Setup/solve include loading, validation, tracking, matching, graph work, local checking, publication and fallback. Complete time additionally includes restoration, accounting, warm/cold replay, serialization and compression.',
            'Imports, source hashing, protocol/case loading, earlier origin acquisition/extraction and the final preservation audit remain additional. Native dispatch allowances exclude separately compiled proof nodes.',
            'The publication boundary is unchanged. Equality of final payloads and native counters is checked where observed; it does not by itself assert an identical ordered execution trace. Provisioned banks, exposed inputs, wider guards and unrestricted resource bounds remain limitations.']))


def trial(dest,out,target,mode):
    p=base.load(out/'protocol.json')
    assert mode in MODES
    original=previous.GuardClosureSolver
    def gate(*args,**kwargs):
        assert kwargs.pop('closure_mode')==mode and mode in ('eager','witness')
        if mode=='eager':return GuardClosureSolver(*args,closure_mode='binary',**kwargs)
        return WitnessGuardClosureSolver(*args,closure_mode='binary',witness_retries=p['witness_retries'],
                                        graph_checks=p['graph_checks'],**kwargs)
    previous.GuardClosureSolver=gate
    try:return previous.trial(dest,out,target,mode)
    finally:previous.GuardClosureSolver=original


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'target-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(dest),str(out),str(target),mode],check=True)
                r=base.load(dest/'report.json');v=old.bound(r['result'])
                samples.append(dict(target=target,mode=mode,repeat=repeat,**old.binding(dest/'report.json')))
                print('finished',target,repeat,mode,v['result']['status'],round(r['solve_seconds'],4),
                      None if v['closure'] is None else {k:n for k,n in v['closure']['counts'].items()
                      if k.startswith('closed_') or k in ('witness_support_checks','verified_core_hints')},flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])

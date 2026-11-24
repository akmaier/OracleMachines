#!/usr/bin/env python3
"""Compare full-context witness composition with support-subset composition."""
from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_witness as previous
from experiments.cnf_guard_witness_solver import WitnessGuardClosureSolver
from experiments.cnf_guard_support_solver import SupportGuardClosureSolver
base=previous.base;old=previous.old;worker=previous.previous
PARENT=Path('experiments/results/cnf-guard-witness')
MODES=('ordinary','witness','support')
FILES=('experiments/cnf_guard_support_solver.py','solver/test_cnf_guard_support_solver.py',
       'experiments/compare_cnf_guard_support.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    out.mkdir(parents=True,exist_ok=True)
    parent=base.load(PARENT/'checkpoint.json');prior=base.load(PARENT/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),
        parent_manifest=old.binding(PARENT/'manifest.json'),
        **{k:prior[k] for k in ('cases','origins','targets','inputs','node_limit','handoff_bytes',
            'closure_checks','closure_literals','closure_edges','path_limit','witness_retries','graph_checks')},
        orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=[
            'All eight exposed chronological edits, two alternating serial repetitions. Every worker restores only its causal origin prefix and provisioned bank. No cumulative union, later repeat or posthoc hints seed queries.',
            'Ordinary and witness controls are frozen. Support changes only native contradiction compilation: collect original path clauses and selected local template supports, compile a native refutation of their subset, and lift with the existing negative component certificate. Equal full support retains the previous compiler.',
            'No component independence is required for a negative subset lift; no positive join or new native proof kind is introduced. Sparse coordinates and premises absent from the support require explicit native binding.',
            'Native search remains capped at 256 dispatches; separately compiled proof nodes are additional. All preceding candidate, support-literal, edge, path, graph and retry limits remain. These do not bound total work, verification or process memory.',
            'The unchanged worker charges restoration, setup, solve, accounting, warm/cold native replay, serialization and compression. Imports, source hashing, protocol/case loading, earlier acquisition/extraction and final preservation audits remain additional.',
            'Proof structure and cache keys change; search trajectories may change. Measure coverage, support size, native state and total costs rather than assuming equal counters or improved work.',
            'Provisioned banks, exposed edits, fresh unlabelled performance, automatic origin discovery, wider guards and arbitrary-SAT bounds remain limitations. The inherited bank-bytes counter excludes local temporary support maps and candidate structures.']))


def trial(dest,out,target,mode):
    p=base.load(out/'protocol.json');assert mode in MODES
    original=worker.GuardClosureSolver
    def gate(*args,**kwargs):
        assert kwargs.pop('closure_mode')==mode and mode in ('witness','support')
        cls=WitnessGuardClosureSolver if mode=='witness' else SupportGuardClosureSolver
        return cls(*args,closure_mode='binary',witness_retries=p['witness_retries'],
                   graph_checks=p['graph_checks'],**kwargs)
    worker.GuardClosureSolver=gate
    try:return worker.trial(dest,out,target,mode)
    finally:worker.GuardClosureSolver=original


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
                    if k.startswith('closed_') or k in ('support_source_literals','support_selected_literals','support_root_hits')},flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])

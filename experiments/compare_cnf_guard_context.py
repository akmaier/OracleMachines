#!/usr/bin/env python3
"""Compare repeated source validation with one immutable witness context."""
from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_support as previous
from experiments.cnf_guard_context_solver import ContextGuardClosureSolver
from experiments.cnf_guard_support_solver import SupportGuardClosureSolver
base=previous.base;old=previous.old;worker=previous.worker
PARENT=Path('experiments/results/cnf-history-layers')
CONTROL=Path('experiments/results/cnf-guard-support')
MODES=('ordinary','support','context')
FILES=('experiments/cnf_guard_context_solver.py','solver/test_cnf_guard_context_solver.py',
       'experiments/compare_cnf_guard_context.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    out.mkdir(parents=True,exist_ok=True)
    parent=base.load(PARENT/'checkpoint.json');prior=base.load(CONTROL/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),
        parent_manifest=old.binding(PARENT/'manifest.json'),control_checkpoint=old.binding(CONTROL/'checkpoint.json'),
        **{k:prior[k] for k in ('cases','origins','targets','inputs','node_limit','handoff_bytes',
            'closure_checks','closure_literals','closure_edges','path_limit','witness_retries','graph_checks')},
        orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=[
            'All eight exposed chronological edits, two alternating serial repetitions. Each worker restores only its causal origin prefix and provisioned bank, never the cumulative union or a later query.',
            'Ordinary and support controls are frozen. Context changes only short-guard support transport: lazily prepare one immutable canonical local CNF and position map per witness call, then check every selected clause, reason and conflict against that bound source.',
            'The context is a local implementation value, never a persistent proof or trust token. Native compilation, publication and cold readers remain unchanged. No context survives a guard-call boundary; inconclusive graphs prepare none.',
            'Native search remains capped at 256 dispatches; separately compiled proof nodes and previous gate limits are unchanged. This is not a bound on total work, process memory or verification.',
            'The unchanged worker charges restoration, setup, solve, accounting, warm/cold native replay, serialization and compression. Imports, source hashing, protocol/case loading, earlier acquisition/extraction and final preservation audits remain additional.',
            'All source/proof counters are compared except the specifically reduced position/normalization visits and new context-allocation counters. Identical counters and archive bytes do not establish identical ordered execution traces.',
            'Provisioned banks, exposed edits, automatic origin discovery, wider guards and arbitrary-SAT bounds remain limitations. Fresh small unlabelled tests establish correctness, not fresh large-instance performance. Peak context slots are additional to bank-byte counters; RSS includes the whole worker.']))


def trial(dest,out,target,mode):
    p=base.load(out/'protocol.json');assert mode in MODES
    original=worker.GuardClosureSolver
    def gate(*args,**kwargs):
        assert kwargs.pop('closure_mode')==mode and mode in ('support','context')
        cls=SupportGuardClosureSolver if mode=='support' else ContextGuardClosureSolver
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
                    if k.startswith('closed_') or k in ('context_preparations','context_hint_checks','position_clauses')},flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])

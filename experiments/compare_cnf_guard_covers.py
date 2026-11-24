#!/usr/bin/env python3
"""Matched read-only discovery census; live solver policy remains unchanged."""
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_context as previous
from experiments.cnf_guard_context_solver import ContextGuardClosureSolver
from experiments.cnf_guard_cover_observer import CoverObserver
base=previous.base; old=previous.old; worker=previous.worker
PARENT=Path('experiments/results/cnf-guard-context')
FILES=('experiments/cnf_guard_clause_cover.py','experiments/cnf_guard_cover_cases.py',
       'experiments/cnf_guard_cover_observer.py','experiments/compare_cnf_guard_covers.py',
       'solver/test_cnf_guard_clause_cover.py')
MODES=('context','census')


def prepare(out):
    assert not (out/'protocol.json').exists()
    out.mkdir(parents=True,exist_ok=True)
    parent=base.load(PARENT/'checkpoint.json'); prior=base.load(PARENT/'protocol.json')
    for f,h in parent['source_fingerprints'].items(): assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),
        parent_manifest=old.binding(PARENT/'manifest.json'),
        **{k:prior[k] for k in ('cases','origins','targets','inputs','node_limit','handoff_bytes',
            'closure_checks','closure_literals','closure_edges','path_limit','witness_retries','graph_checks')},
        discovery=dict(width_limit=8,root_limit=8,edge_limit=4096,path_limit=256),
        orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=[
            'Read-only census of eight exposed queries, two serial alternating repetitions; frozen context control, causal origin prefixes only. No cover proof influences live decisions.',
            'Discovery inspects each satisfiable tentative graph with width 8, eight BFS roots, 4096 visited edges and path length 256. Source/model/graph scanning and event serialization remain additional work, explicitly charged; bounds are not total query bounds.',
            'A tentative graph can contain unsupported local guards. A cover is not authority until each used edge is source-supported and its strengthened-context native proof checks. Absence at these bounded sites does not establish absence of other covers or origins.',
            'Census retains full local graphs, models and bindings for independent rediscovery. This diagnostic memory and JSON output are not a proposed live policy.',
            'Complete worker includes restore, setup, solve, warm/cold native replay, accounting, archive compression and census serialization. Imports, source hashing, earlier acquisition and final preservation audits remain additional.',
            'Native history remains unchanged by observation. Separate controlled-family proof archives preserve new compiler results without replacing the cumulative bank. These deliberately provisioned templates do not measure automatic origin discovery or unrestricted SAT efficiency.']))


def trial(dest,out,target,mode):
    p=base.load(out/'protocol.json'); original=worker.GuardClosureSolver; instances=[]
    def gate(*args,**kwargs):
        assert kwargs.pop('closure_mode')==mode
        cls=CoverObserver if mode=='census' else ContextGuardClosureSolver
        s=cls(*args,closure_mode='binary',witness_retries=p['witness_retries'],graph_checks=p['graph_checks'],**kwargs)
        instances.append(s);return s
    worker.GuardClosureSolver=gate
    try: worker.trial(dest,out,target,mode)
    finally: worker.GuardClosureSolver=original
    if mode=='census':
        started=time.perf_counter(); s=instances[0]
        base.write(dest/'events.json',dict(events=s.cover_events,observation_seconds=s.cover_seconds))
        r=base.load(dest/'report.json'); r['events']=old.binding(dest/'events.json')
        r['event_bytes']=(dest/'events.json').stat().st_size
        r['event_serialization_seconds']=time.perf_counter()-started
        r['complete_seconds']+=r['event_serialization_seconds']
        base.write(dest/'report.json',r)


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'target-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(dest),str(out),str(target),mode],check=True)
                r=base.load(dest/'report.json')
                samples.append(dict(target=target,mode=mode,repeat=repeat,**old.binding(dest/'report.json')))
                print('finished',target,repeat,mode,round(r['solve_seconds'],4),flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])

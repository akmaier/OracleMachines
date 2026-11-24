#!/usr/bin/env python3
"""Compare selective live guard closures with ordinary and guided search."""
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_certificates as previous
from experiments.cnf_guard_certificate_solver import GuardCertificateSolver
from experiments.cnf_guard_closure_solver import GuardClosureSolver
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_partial_residual_pool import charge
from experiments.cnf_fresh_mixtures import attempt

base=previous.base;old=previous.old
PARENT=Path('experiments/results/cnf-guard-interactions')
ORIGINS=previous.ORIGINS
MODES=('ordinary','certificate','units','binary')
FILES=('experiments/cnf_guard_closure_solver.py','solver/test_cnf_guard_closure_solver.py',
       'experiments/compare_cnf_guard_closure.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    parent=base.load(PARENT/'checkpoint.json')
    prior=base.load('experiments/results/cnf-guard-certificate-reuse/protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(
        parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        cases=prior['cases'],origins=prior['origins'],targets=prior['targets'],
        inputs=[old.binding(ORIGINS/f'origin-{i}/report.json') for i in prior['origins']],
        node_limit=256,handoff_bytes=2*1024*1024,closure_checks=100000,
        closure_literals=1000000,closure_edges=4096,path_limit=256,
        orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=[
            'All eight exposed edits, with two alternating serial repetitions. Restore only each chronological origin prefix and its prior conditional support bank; no later repeat, cumulative union or posthoc hint archive seeds search.',
            'Ordinary uses the frozen lazy binary closure solver. Certificate uses the frozen guided selector with direct trace reuse. Units and binary use ordinary fallback selection, exact source-coordinate tracking and a short-guard closure at ordinary probe sites. No distinct new tracking-only arm is measured.',
            'Units checks zero/one-unfixed guards, opposite units first, then original binary clauses plus units. Binary also admits two-unfixed guards. The SCC result supplies only contradictions; both implication paths compile to native source unit/split certificates.',
            'Budgets cap candidate checks, reserved support literals and compiled witness edges. They do not cap initial validation, guard-pair scans, native checking, total work, retained database size or process memory. The native 256-dispatch allowance excludes separately compiled proof nodes.',
            'Worker time includes prefix restoration, setup, solve, new-node warm replay, full native cold replay, accounting, serialization and compression. Imports, frozen-source hashing and case loading are outside it. Earlier origin acquisition/extraction and final preservation audits remain additional.',
            'Templates are explicitly provisioned and the population exposed. Whole-query completion, total cost and preservation must be measured; the preceding offline local savings do not establish a live gain or arbitrary-SAT bound.']))


def trial(dest,out,target,mode):
    p=base.load(out/'protocol.json');cases=old.bound(p['cases'])
    origin=old.bound(p['inputs'][p['targets'].index(target)])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    dest.mkdir();began=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';tick=time.perf_counter()
        restore_archive(origin['prefix_archive'],path);restore_seconds=time.perf_counter()-tick
        tick=time.perf_counter()
        kwargs=dict(node_limit=p['node_limit'],handoff_bytes=p['handoff_bytes'])
        if mode=='ordinary':solver=LazyBinaryClosureSolver(path,**kwargs)
        else:
            templates=old.bound(origin['extraction'])['templates']
            if mode=='certificate':solver=GuardCertificateSolver(path,templates=templates,**kwargs)
            else:solver=GuardClosureSolver(path,templates=templates,closure_mode=mode,
                **{k:p[k] for k in ('closure_checks','closure_literals','closure_edges','path_limit')},**kwargs)
        setup_seconds=time.perf_counter()-tick;initial=old.tables(solver.db)
        try:
            tick=time.perf_counter();result=attempt(solver,cases[target]['source']);solve_seconds=time.perf_counter()-tick
            guide=getattr(solver,'guard_summary',None);certificate=getattr(solver,'certificate_summary',None)
            closure=getattr(solver,'closure_summary',None);final=old.tables(solver.db)
            checked_bytes=charge(solver.checked)
            new=final[old.previous.ALL_TABLES[0]].keys()-initial[old.previous.ALL_TABLES[0]].keys()
            tick=time.perf_counter()
            for key in sorted(new):assert solver._read(key) is not None
            warm_seconds=time.perf_counter()-tick;assert old.tables(solver.db)==final
        finally:solver.close()
        tick=time.perf_counter();reader=CanonicalVerifySnapshot(path)
        try:
            for key in final[old.previous.ALL_TABLES[0]]:assert reader._read(key) is not None
        finally:reader.close()
        cold_seconds=time.perf_counter()-tick
        base.write(dest/'result.json',dict(result=result,guard=guide,certificate=certificate,closure=closure))
        archive=base.archive(path,dest)
    base.write(dest/'report.json',dict(protocol=old.binding(out/'protocol.json'),origin=target-1,target=target,mode=mode,
        restore_seconds=restore_seconds,setup_seconds=setup_seconds,solve_seconds=solve_seconds,warm_seconds=warm_seconds,
        cold_seconds=cold_seconds,complete_seconds=time.perf_counter()-began,native_checked_bytes=checked_bytes,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        added={t:len(final[t].keys()-initial[t].keys()) for t in old.previous.ALL_TABLES},
        payload_bytes={t:sum(len(v.encode()) for v in rows.values()) for t,rows in final.items()},
        digest={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in final.items()},
        archive=archive,result=old.binding(dest/'result.json')))


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
                      None if v['closure'] is None else {k:n for k,n in v['closure']['counts'].items() if k.startswith('closed_')},flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])

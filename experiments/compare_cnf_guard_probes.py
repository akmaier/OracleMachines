#!/usr/bin/env python3
"""Cold, paired comparisons of ordinary and guard-guided probe selection."""
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_guard_probes as previous
from experiments.cnf_guard_probe_solver import GuardProbeSolver
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_partial_residual_pool import charge
from experiments.cnf_fresh_mixtures import attempt
base=previous.base;old=previous.old
PARENT=Path('experiments/results/cnf-guard-probe-census');ORIGINS=previous.ORIGINS
MODES=('native','tracking','variable','guided')
FILES=('experiments/cnf_guard_probe_solver.py','solver/test_cnf_guard_probe_solver.py','experiments/compare_cnf_guard_probes.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    parent=base.load(PARENT/'checkpoint.json');prior=base.load(PARENT/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        cases=prior['cases'],origins=prior['origins'],targets=[i+1 for i in prior['origins']],node_limit=256,handoff_bytes=2*1024*1024,
        guard_checks=100000,tracking_slots=1000000,tracking_pending=4096,
        orders=[list(MODES),list(reversed(MODES))]*2,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
            'All eight exposed origin/edit pairs are fixed before comparison, without outcome filtering. Source templates are provisioned; no fresh or population claim.',
            'Four alternating serial repetitions per arm restore the exact causal prefix immediately after each origin. Later repeats, cumulative unions and posthoc census certificates never seed search.',
            'Native is the preceding lazy solver. Tracking preserves its probe order with the new coordinate tracker and bank checks. Variable selects the first sorted eligible guard variable but probes False then True. Guided uses that same selector with the offered polarity first.',
            'Variable is a polarity-order control, not a guarantee of identical complete search paths. Earlier probe publication and subsequent persisted reuse can affect later paths.',
            'Actual local cofactors must pass the unchanged native lazy unit/binary probe before an exclusion is used. Hints never certify a parent; the opposite branch is visited and existing split/model lifting remains responsible for recomposition.',
            'Template loading/copying is charged in setup; root normalization, certificate/support checks, matching, coordinate maintenance, native acquisition and publication are charged in solve. Source acquisition/extraction and final historical audits remain additional.',
            'Complete-worker timing includes restoration, setup, retained-state accounting, warm replay of new native nodes, full native cold replay, result serialization and compression. Imports, frozen-source hashing and case loading are outside it.',
            'Reuse native canonicalization and clean expansion-owned pending bindings on unwind. Guard-check and tracking-slot limits bound only those resources, not all verification, probe work, depth, copied banks or process memory.',
            'Native checked-cache and template-bank bytes are retained-graph diagnostics. Process peak RSS includes preparation and cold replay; active tracking slots are not bytes. No uniform storage or polynomial SAT bound is claimed.']))


def trial(dest,out,target,mode):
    p=base.load(out/'protocol.json');cases=old.bound(p['cases']);origin=base.load(ORIGINS/f'origin-{target-1}/report.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    dest.mkdir();began=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';tick=time.perf_counter();restore_archive(origin['prefix_archive'],path);restore_seconds=time.perf_counter()-tick
        tick=time.perf_counter()
        if mode=='native':s=LazyBinaryClosureSolver(path,node_limit=p['node_limit'],handoff_bytes=p['handoff_bytes'])
        else:
            ts=old.bound(origin['extraction'])['templates']
            s=GuardProbeSolver(path,node_limit=p['node_limit'],handoff_bytes=p['handoff_bytes'],templates=ts,guard_mode=mode,
                guard_checks=p['guard_checks'],tracking_slots=p['tracking_slots'],tracking_pending=p['tracking_pending'])
        setup_seconds=time.perf_counter()-tick;initial=old.tables(s.db)
        try:
            tick=time.perf_counter();result=attempt(s,cases[target]['source']);solve_seconds=time.perf_counter()-tick
            guide=None if mode=='native' else s.guard_summary;final=old.tables(s.db)
            checked_bytes=charge(s.checked);new=final[old.previous.ALL_TABLES[0]].keys()-initial[old.previous.ALL_TABLES[0]].keys()
            tick=time.perf_counter()
            for key in sorted(new):assert s._read(key) is not None
            warm_seconds=time.perf_counter()-tick;assert old.tables(s.db)==final
        finally:s.close()
        tick=time.perf_counter();reader=CanonicalVerifySnapshot(path)
        try:
            for key in final[old.previous.ALL_TABLES[0]]:assert reader._read(key) is not None
        finally:reader.close()
        cold_seconds=time.perf_counter()-tick
        base.write(dest/'result.json',dict(result=result,guard=guide))
        archive=base.archive(path,dest)
    base.write(dest/'report.json',dict(protocol=old.binding(out/'protocol.json'),origin=target-1,target=target,mode=mode,
        restore_seconds=restore_seconds,setup_seconds=setup_seconds,solve_seconds=solve_seconds,warm_seconds=warm_seconds,
        cold_seconds=cold_seconds,complete_seconds=time.perf_counter()-began,native_checked_bytes=checked_bytes,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        added={t:len(final[t].keys()-initial[t].keys()) for t in old.previous.ALL_TABLES},
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
                print('finished',target,repeat,mode,v['result']['status'],round(r['solve_seconds'],4),flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])

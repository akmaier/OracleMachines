#!/usr/bin/env python3
"""Compare direct local certificate transport under a fixed guided probe path."""
from pathlib import Path
import hashlib,json,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_guard_probes as previous
from experiments.cnf_guard_probe_solver import GuardProbeSolver
from experiments.cnf_guard_certificate_solver import GuardCertificateSolver
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_partial_residual_pool import charge
from experiments.cnf_fresh_mixtures import attempt
base=previous.base;old=previous.old
PARENT=Path('experiments/results/cnf-guard-probe-selection');ORIGINS=previous.ORIGINS
MODES=('guided','certificate')
FILES=('experiments/cnf_guard_certificate_solver.py','solver/test_cnf_guard_certificate_solver.py','experiments/compare_cnf_guard_certificates.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    parent=base.load(PARENT/'checkpoint.json');prior=base.load(PARENT/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        cases=prior['cases'],origins=prior['origins'],targets=[i+1 for i in prior['origins']],node_limit=256,handoff_bytes=2*1024*1024,
        guard_checks=100000,tracking_slots=1000000,tracking_pending=4096,
        certificate_checks=100000,certificate_literals=1000000,
        orders=[list(MODES),list(reversed(MODES))]*2,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
            'All eight exposed edits and causal source banks are fixed. Four alternating serial repetitions restore the prefix immediately after each origin. No later repeats, union history or posthoc census bank seeds search.',
            'Both arms use the frozen guided selector. Certificate transport is attempted only after a checked cache miss, before full-cofactor unit propagation. It uses existing native unit publication and original recomposition; no new proof authority.',
            'Exact local containment is required for every surviving support clause. Already fixed trace steps are skipped; an opposite fixed step yields an earlier conflict. Failure or budget exhaustion falls back to the unchanged lazy probe.',
            'Setup charges bank loading/copying. Solve charges validation, coordinate tracking, matching, local support maps, trace transport, publication and fallback. Initial source acquisition/extraction remains additional.',
            'Complete-worker timing includes restoration, setup, retained-graph accounting, new-node warm replay, full native cold replay, result serialization and compression. Imports, frozen-source hashing and case loading are outside it.',
            'Separate traced reruns record an ordered digest of native visits, expansions, probe inputs and guard choices, outside timed comparisons; they must reproduce untraced counters and payloads.',
            'Counters bound candidate checks and reserved support literals only, not bank validation, whole-cofactor position construction, guard pairs, trace steps or total memory. Checked-cache/bank bytes and peak process RSS are reported separately.',
            'All prior payloads and alternate valid certificates are preserved. Local refutation reuse does not establish broader root coverage or polynomial unrestricted expansion.']))



def trial(dest,out,target,mode,*,traced=False):
    p=base.load(out/'protocol.json');cases=old.bound(p['cases']);origin=base.load(ORIGINS/f'origin-{target-1}/report.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    dest.mkdir();began=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';tick=time.perf_counter();restore_archive(origin['prefix_archive'],path);restore_seconds=time.perf_counter()-tick
        tick=time.perf_counter()
        ts=old.bound(origin['extraction'])['templates']
        cls=GuardProbeSolver if mode=='guided' else GuardCertificateSolver
        events=hashlib.sha256();event_counts={}
        if traced:
            class Traced(cls):
                def event(self,kind,value):
                    events.update(json.dumps([kind,value],separators=(',',':')).encode()+b'\n')
                    event_counts[kind]=event_counts.get(kind,0)+1
                def _visit(self,cnf):
                    self.event('visit',cnf);return super()._visit(cnf)
                def _expand(self,cnf):
                    self.event('expand',cnf);return super()._expand(cnf)
                def _probe(self,cnf,variable,value):
                    self.event('probe',(cnf,variable,value));return super()._probe(cnf,variable,value)
                def _guard_choice(self,cnf,ordinary):
                    result=super()._guard_choice(cnf,ordinary);self.event('choice',(cnf,ordinary,result));return result
            cls=Traced
        extra={} if mode=='guided' else dict(certificate_checks=p['certificate_checks'],certificate_literals=p['certificate_literals'])
        s=cls(path,node_limit=p['node_limit'],handoff_bytes=p['handoff_bytes'],templates=ts,guard_mode='guided',
            guard_checks=p['guard_checks'],tracking_slots=p['tracking_slots'],tracking_pending=p['tracking_pending'],**extra)
        setup_seconds=time.perf_counter()-tick;initial=old.tables(s.db)
        try:
            tick=time.perf_counter();result=attempt(s,cases[target]['source']);solve_seconds=time.perf_counter()-tick
            guide=s.guard_summary;certificate=getattr(s,'certificate_summary',None);final=old.tables(s.db)
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
        base.write(dest/'result.json',dict(result=result,guard=guide,certificate=certificate))
        archive=base.archive(path,dest)
    base.write(dest/'report.json',dict(protocol=old.binding(out/'protocol.json'),origin=target-1,target=target,mode=mode,
        traced=traced,path_trace=None if not traced else dict(sha256=events.hexdigest(),counts=event_counts),
        restore_seconds=restore_seconds,setup_seconds=setup_seconds,solve_seconds=solve_seconds,warm_seconds=warm_seconds,
        cold_seconds=cold_seconds,complete_seconds=time.perf_counter()-began,native_checked_bytes=checked_bytes,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        added={t:len(final[t].keys()-initial[t].keys()) for t in old.previous.ALL_TABLES},
        key_digest={t:base.key_sha(base.encode(sorted(rows))) for t,rows in final.items()},
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
                print('finished',target,repeat,mode,v['result']['status'],round(r['solve_seconds'],4),flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


def trace(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for mode in MODES:
            dest=out/f'trace-{target}-{mode}'
            subprocess.run([sys.executable,__file__,'traced',str(dest),str(out),str(target),mode],check=True)
            samples.append(dict(target=target,mode=mode,**old.binding(dest/'report.json')))
            print('traced',target,mode,flush=True)
    base.write(out/'traces.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trace':trace(out)
    elif action in ('trial','traced'):trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5],traced=action=='traced')

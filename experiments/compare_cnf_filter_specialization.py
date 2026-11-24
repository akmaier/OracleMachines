#!/usr/bin/env python3
"""Matched clause-specific filter preparation, with frozen generic controls."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_filters as prior
from experiments import cnf_shortening_clause_filters as candidate
base=prior.base;old=prior.old
MODES=('numeric_endpoint','numeric_weak','priority_endpoint','priority_weak')
FILES=('experiments/cnf_shortening_clause_filters.py','solver/test_cnf_shortening_clause_filters.py','experiments/compare_cnf_filter_specialization.py')


def prepare(out):
    p=base.load(out/'protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    assert not (out/'specialization-protocol.json').exists()
    base.write(out/'specialization-protocol.json',dict(parent_protocol=old.binding(out/'protocol.json'),generic_censuses=old.binding(out/'censuses.json'),
        source_fingerprints={**p['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        orders=[['generic','specialized'],['specialized','generic']],modes=list(MODES),
        rule='The adjacency builder inserts contrapositive edge pairs; incoming(-r) is empty exactly when outgoing(r) is empty. Remove the incoming index only inside that clausal builder.',
        limitations='Specialization chosen after observing generic counts and deriving the edge-pair invariant. Two new alternating isolated repetitions per target/mode compare generic and specialized preparation; general directed graphs are outside the private specialization precondition.'))


def trial(dest,out,target,mode,engine):
    p=base.load(out/'protocol.json');source,templates,refs,events=prior.prior.prior.inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    rr=base.load(out/f'census-{target}-{mode}-0/report.json');control={r['event']:r for r in old.bound(rr['events'])['rows']}
    order,kind=mode.split('_')
    for ref in refs:
        c=Counter();tick=time.perf_counter();local,hints,_=prior.previous.local_hints(source,templates,events[ref['event']],c);binding=time.perf_counter()-tick
        c=Counter();tick=time.perf_counter()
        module=prior.candidate if engine=='generic' else candidate
        program=module.discover(local,[h['template'] for h in hints],c,order=order,filters=kind,**p['limits']);elapsed=time.perf_counter()-tick
        oldrow=control[ref['event']];assert program==oldrow['program']
        for key,value in oldrow['counts'].items():
            if engine=='specialized' and key in ('filter_incoming_edges','filter_adjacency_vertices'):continue
            assert c[key]==value,(target,ref['event'],mode,key)
        if engine=='specialized':assert c['filter_incoming_edges']==0
        rows.append(dict(event=ref['event'],root=ref['source_root'],program_sha256=base.key_sha(base.encode(program)),counts=dict(c),binding_seconds=binding,discovery_seconds=elapsed))
    base.write(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,engine=engine,events=old.binding(dest/'events.json'),
        binding_seconds=sum(r['binding_seconds'] for r in rows),discovery_seconds=sum(r['discovery_seconds'] for r in rows),
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


def run(out):
    p=base.load(out/'protocol.json');sp=base.load(out/'specialization-protocol.json');samples=[]
    for target in p['targets']:
        for mode in MODES:
            for repeat,order in enumerate(sp['orders']):
                for engine in order:
                    dest=out/f'special-{target}-{mode}-{engine}-{repeat}'
                    subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),str(target),mode,engine],check=True)
                    samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,engine=engine,repeat=repeat))
        print(base.encode(dict(target=target)),flush=True)
    base.write(out/'specializations.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action in ('prepare','run'):globals()[action](out)
    else:trial(Path(sys.argv[3]),out,int(sys.argv[4]),sys.argv[5],sys.argv[6])

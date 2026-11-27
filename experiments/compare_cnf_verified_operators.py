#!/usr/bin/env python3
"""Matched total-cost comparison of ephemeral verified bucket-operator reuse."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_selective_width_buckets as prior
from experiments import cnf_verified_operators as verified
base=prior.base;old=prior.old;native=prior.native;k=prior.k
FALLBACK=prior.FALLBACK;ATTEMPT=prior.ATTEMPT
PARENT=Path('experiments/results/cnf-selective-width-buckets')
MODES=('fresh','legacy','off','query','pass')
FILES=('experiments/cnf_verified_operators.py','experiments/compare_cnf_verified_operators.py','solver/test_cnf_verified_operators.py')


class Engine:
    FORMAT=k.FORMAT
    def __init__(self,mode,limits):
        if mode not in MODES:raise ValueError('Invalid verifier mode')
        self.mode=mode;self.limits=limits;self.bank=None;self.sessions=[];self.label='discovery'
        if mode=='pass':self.bank=verified.VerifiedOperators(**limits)

    def save(self):
        if self.bank is not None:self.sessions.append(dict(phase=self.label,**self.bank.stats()))
        self.bank=None

    def phase(self,label):
        self.save();self.label=label
        if self.mode=='pass':self.bank=verified.VerifiedOperators(**self.limits)

    def query(self):
        if self.mode=='query':self.save();self.bank=verified.VerifiedOperators(**self.limits)

    def finish(self):self.save();return self.sessions

    def invoke(self,method,*args,**kwargs):
        if self.mode in ('fresh','legacy'):return method(*args,**kwargs)
        with verified.installed(self.bank):return method(*args,**kwargs)

    def discover(self,*args,**kwargs):return self.invoke(k.discover,*args,**kwargs)
    def check_certificate(self,*args,**kwargs):return self.invoke(k.check_certificate,*args,**kwargs)


def prepare(out):
    out.mkdir();parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    # Frozen existing panel; this experiment changes only checking, not coverage.
    for name in ('panel','descriptions','truth'):base.write(out/(name+'.json'),base.load(PARENT/(name+'.json')))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),panel=old.binding(out/'panel.json'),descriptions=old.binding(out/'descriptions.json'),truth=old.binding(out/'truth.json'),
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limits=k.DEFAULTS,cache_limits=dict(max_entries=4096,max_bytes=4*1024*1024),node_limit=256,orders=[list(MODES[i:]+MODES[:i]) for i in range(len(MODES))],limitations=[
        'Same frozen 182-query synthetic panel as the previous checkpoint; no new coverage or generalization claim. All variants use the unchanged two-round selective-width acquisition and certificates. Labels remain audit-only.',
        'Legacy is the unchanged checker. Off uses the new checker with no bank. Query shares a bank across discovery/internal/explicit checks for one query, then discards it. Pass shares across one complete phase. Warm starts empty and each of two cold passes starts empty. No persistent authority or restored cache exists.',
        'Every source, incident bucket, encoding, output scope, verdict and root witness is checked on each occurrence. Only the independent exhaustive operator row loop may be skipped after an exactly matching immutable input/pivot/output/choice signature has passed that loop in the current bank.',
        'FIFO bounds are 4096 entries and 4 MiB conservative retained key/value object accounting, excluding dictionary infrastructure. These are not total RAM bounds; peak RSS is measured. Key construction, size accounting, insertion, lookup and eviction are charged.',
        'The adapter temporarily replaces the legacy bucket checker only inside an isolated single-threaded experimental call and restores it on exit. It rejects nested hooks and concurrent/background execution. Production defaults and historical scientific files are unchanged.',
        'Five cyclic process orders start empty with the same fallback. Complete cost charges input, discovery/internal checking, explicit checks, persistence, compression and warm/cold replay. Startup, final report metadata, labels, historical acquisition and independent audits are additional. Two native archive readers and two JSON passes are retained.']))


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);input_seconds=time.perf_counter()-started
    phases=Counter();total=Counter();sc=Counter();cases=[];results=[];stored={};fallback_rows=[];fallback_results=[]
    engine=Engine(mode,p['cache_limits']);options=dict(mode='two',**p['limits'])
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'db';solver=FALLBACK.LazyBinaryClosureSolver(db,node_limit=p['node_limit'])
        try:
            for row in rows:
                cc=Counter();case=dict(id=row['id']);proof=None;diag=None
                if mode!='fresh':
                    start=time.perf_counter();engine.query();cnf,_=native.normalize(row['source'],cc);root=native.token(cnf,cc)
                    if root in stored:
                        proof=base.load(dest/stored[root]);diag=dict(reason='exact-program-reuse');cc['bucket_source_hits']+=1
                    else:proof,diag=engine.discover(row['source'],cc,**options)
                    case['discovery_seconds']=time.perf_counter()-start;start=time.perf_counter()
                    if root not in stored:
                        file=base.key_sha(root)+'-proof.json';base.write(dest/file,proof);stored[root]=file
                    base.write(dest/(row['id']+'-diagnostic.json'),diag);case['evidence_persistence_seconds']=time.perf_counter()-start
                start=time.perf_counter();solver.counts=Counter();got=None if proof is None else engine.check_certificate(row['source'],proof,cc)
                if got is not None and got['answer'] is not None:
                    result=dict(answer=got['answer'],model=got['model'],root=root,authority=engine.FORMAT);case['route']='bucket'
                else:
                    wrapped=ATTEMPT.attempt(solver,row['source']);case['route']='fresh'
                    if wrapped['result'] is None:result=dict(answer=None,root=None,model=None,authority='unresolved')
                    else:
                        result={key:wrapped['result'][key] for key in ('answer','model','root','authority')};fallback_rows.append(row);fallback_results.append(result)
                case['solve_check_seconds']=time.perf_counter()-start;case.update(diagnostic=diag,counts=dict(cc),solver_counts=dict(solver.counts))
                total.update(cc);sc.update(solver.counts);phases.update({key:value for key,value in case.items() if key.endswith('_seconds')});cases.append(case);results.append(result)
            tables=old.tables(solver.db);start=time.perf_counter();wc=Counter();engine.phase('warm')
            for row,result,case in zip(rows,results,cases):
                if mode!='fresh':
                    engine.query();cnf,_=native.normalize(row['source'],wc);root=native.token(cnf,wc);got=engine.check_certificate(row['source'],base.load(dest/stored[root]),wc)
                    if case['route']=='bucket':assert got['answer']==result['answer']
                if case['route']=='fresh':
                    wrapped=ATTEMPT.attempt(solver,row['source']);assert (None if wrapped['result'] is None else wrapped['result']['answer'])==result['answer']
            warm=time.perf_counter()-start;assert tables==old.tables(solver.db)
        finally:solver.close()
        start=time.perf_counter();readers=FALLBACK.audit(db,fallback_rows,fallback_results);coldcounts=Counter()
        for replay in range(2):
            engine.phase('cold-'+str(replay))
            if mode!='fresh':
                for row,result,case in zip(rows,results,cases):
                    engine.query();cnf,_=native.normalize(row['source'],coldcounts);root=native.token(cnf,coldcounts)
                    got=engine.check_certificate(row['source'],base.load(dest/stored[root]),coldcounts)
                    if case['route']=='bucket':assert got['answer']==result['answer']
        cold=time.perf_counter()-start;start=time.perf_counter();archive=base.archive(db,dest)
        payload=base.encode({f:base.load(dest/f) for f in sorted(stored.values())}).encode();(dest/'certificates.json.gz').write_bytes(gzip.compress(payload,mtime=0))
        persistence=time.perf_counter()-start
    base.write(dest/'report.json',dict(mode=mode,panel=p['panel'],cases=cases,results=results,counts=dict(total),solver_counts=dict(sc),warm_counts=dict(wc),cold_counts=dict(coldcounts),input_seconds=input_seconds,phases=dict(phases),
        warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,stored=stored,certificate_bytes=sum((dest/f).stat().st_size for f in stored.values()),certificate_compressed_bytes=(dest/'certificates.json.gz').stat().st_size,
        diagnostic_bytes=sum(f.stat().st_size for f in dest.glob('*-diagnostic.json')),
        records=sum(map(len,tables.values())),record_bytes=sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items()),digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},archive=archive,readers=readers,cache_sessions=engine.finish(),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))

def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for i,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{i}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True);samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=i))
        print(base.encode(dict(completed=i)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)

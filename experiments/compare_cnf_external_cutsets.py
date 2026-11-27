#!/usr/bin/env python3
"""Frozen external-input evaluation of existing SAT structural certificates."""
from collections import Counter
from pathlib import Path
import gzip,random,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_factor_conditioning as prior
from experiments import cnf_external_cutsets as e
base=prior.base;old=prior.old;verified=prior.verified
PARENT=Path('experiments/results/cnf-factor-conditioning')
MODES=('baseline','expanded')
FILES=('experiments/cnf_external_cutsets.py','experiments/compare_cnf_external_cutsets.py','solver/test_cnf_external_cutsets.py')


def emit_dimacs(source):
    return 'p cnf '+str(max((abs(v) for c in source for v in c),default=0))+' '+str(len(source))+'\n'+'\n'.join(' '.join(map(str,c+[0])) for c in source)+'\n'


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    for name,h in parent['source_fingerprints'].items():assert base.sha(name)==h,name
    acquisition=base.load(out/'acquisition.json');assert acquisition['selection_sha256']==base.sha(out/'selection.json')
    rows=[];descriptions={};first={}
    for r in acquisition['records']:
        assert base.sha(r['path'])==r['sha256'];source,header=e.parse_dimacs(Path(r['path']).read_text());key=f'e{len(rows):03}'
        rows.append(dict(id=key,source=source,raw=old.binding(r['path'])));descriptions[key]=dict(**r,kind='original',header=header);first.setdefault(r['group'],(key,source,r))
    for i,(group,(original,source,r)) in enumerate(first.items()):
        names=sorted({abs(v) for c in source for v in c});rng=random.Random(2711271954+i);permutation=rng.sample(range(11,11+len(names)),len(names));signs=[rng.choice((-1,1)) for _ in names];mapping={v:(permutation[j],signs[j]) for j,v in enumerate(names)}
        renamed=[[mapping[abs(v)][0]*mapping[abs(v)][1]*(1 if v>0 else -1) for v in c] for c in reversed(source)]
        edited=[c[:] for c in source[1:]]
        last=next(c for c in reversed(edited) if c);last[0]=-last[0]
        for kind,variant,label in [('signed-permutation',renamed,r['publisher_answer']),('edit',edited,None)]:
            key=f'e{len(rows):03}';raw=out/'raw'/(key+'-'+kind+'.cnf');raw.write_text(emit_dimacs(variant));assert e.parse_dimacs(raw.read_text())[0]==variant
            rows.append(dict(id=key,source=variant,raw=old.binding(raw)));descriptions[key]=dict(kind=kind,group=group,original=original,publisher_answer=label,scope='Label transported under signed permutation only; edited truth unknown. Derived control, not independent external sample.')
    assert len(rows)==37
    oldpanel=base.load('experiments/results/cnf-verified-operators/panel.json');oldkeys={e.native.normalize(r['source'])[0] for r in oldpanel};seen={};overlaps=[]
    for row in rows:
        key=e.native.normalize(row['source'])[0];overlaps.append(dict(id=row['id'],same_panel_exact=seen.get(key),prior_182_exact=key in oldkeys));seen.setdefault(key,row['id'])
    base.write(out/'panel.json',rows);base.write(out/'descriptions.json',descriptions);base.write(out/'overlaps.json',dict(records=overlaps,scope='Exact normalized-source equality only, against the preceding 182-query panel. Signed permutations are known related controls whether or not exact normalization identifies them. No semantic-isomorphism or all-historical-input novelty claim.'))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),selection=old.binding(out/'selection.json'),acquisition=old.binding(out/'acquisition.json'),panel=old.binding(out/'panel.json'),descriptions=old.binding(out/'descriptions.json'),overlaps=old.binding(out/'overlaps.json'),source_fingerprints={**parent['source_fingerprints'],**{name:base.sha(name) for name in FILES}},orders=[['baseline','expanded'],['expanded','baseline'],['baseline','expanded'],['expanded','baseline']],limits=e.previous.DEFAULTS,limitations=[
        'First size/family-limited external audit: 25 fixed public SATLIB inputs and 12 derived controls. Lexicographic selection and archive groups were frozen before any external evaluation. Not random, representative or a SAT Competition performance claim.',
        'Unchanged two-round selective-width baseline versus that same baseline plus the previously tested cut-four frontier continuation. Same existing limits, degree ranking, covers and checkers. No solver-result-guided parameter adjustment.',
        'Algorithms receive only parsed CNFs. Opaque IDs organize persistence; family, provenance and publisher labels are separate audit data. Labels are never proof authority. Edited-input truth remains unknown unless independently certified.',
        'Expanded admits only materialized open depth-zero frontiers. It attempts eligible leaves in stored order and stops after a checked original-source SAT witness. No promotion of individual frontier UNSAT to whole-root UNSAT; unsuccessful covers and branches remain explicit.',
        'All new-input preparation and initial structural discovery are charged, along with expansion/internal checks, explicit validation, JSON writes, compression, warm and two cold passes. Every replay reparses the raw DIMACS source. Each phase starts with an empty bounded verified-operator bank; operating-system caches are not flushed.',
        'There is no fallback solver in this comparison. Unresolved inputs stay unresolved. This evaluates cost and certified coverage of bounded structural discovery, not total cost of answering every query or a speedup over fresh solving. Startup, download/selection, final metadata and independent audits are additional.',
        'All old evidence and the previous 182/182 structural union remain unchanged. This external panel is separately denominated; derived controls are not independent samples. Exact overlap audit does not detect general semantic equivalence or arbitrary variable/sign isomorphism.']))


def source(row):
    assert base.sha(row['raw']['path'])==row['raw']['sha256']
    cnf,_=e.parse_dimacs(Path(row['raw']['path']).read_text());assert cnf==row['source']
    return cnf


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);sources=[source(r) for r in rows];input_seconds=time.perf_counter()-started;cases=[];proofs=[];total=Counter();phases=Counter();sessions=[]
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row,cnf in zip(rows,sources):
            counts=Counter();start=time.perf_counter();proof,diag=e.discover(cnf,counts,expand=mode=='expanded');acquisition=time.perf_counter()-start
            start=time.perf_counter();got=e.check(cnf,proof,counts);checking=time.perf_counter()-start
            start=time.perf_counter();base.write(dest/(row['id']+'.json'),proof);writing=time.perf_counter()-start
            cases.append(dict(id=row['id'],status=proof['status'],result=got,diagnostic=diag,counts=dict(counts),acquisition_seconds=acquisition,checking_seconds=checking));proofs.append(proof);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing));print(mode,row['id'],proof['status'],round(acquisition,3),flush=True)
    sessions.append(bank.stats());start=time.perf_counter();warm=Counter()
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row in rows:e.check(source(row),base.load(dest/(row['id']+'.json')),warm)
    warm_seconds=time.perf_counter()-start;sessions.append(bank.stats());start=time.perf_counter();cold=Counter()
    for _ in range(2):
        with verified.installed(bank:=verified.VerifiedOperators()):
            for row in rows:e.check(source(row),base.load(dest/(row['id']+'.json')),cold)
        sessions.append(bank.stats())
    cold_seconds=time.perf_counter()-start;start=time.perf_counter();(dest/'certificates.json.gz').write_bytes(gzip.compress(base.encode(proofs).encode(),mtime=0));persistence=time.perf_counter()-start
    base.write(dest/'report.json',dict(mode=mode,panel=p['panel'],cases=cases,counts=dict(total),warm_counts=dict(warm),cold_counts=dict(cold),input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm_seconds,cold_seconds=cold_seconds,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,proof_bytes=sum((dest/(r['id']+'.json')).stat().st_size for r in rows),compressed_bytes=(dest/'certificates.json.gz').stat().st_size,cache_sessions=sessions,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run(out):
    samples=[]
    for i,order in enumerate(base.load(out/'protocol.json')['orders']):
        for mode in order:
            dest=out/f'{mode}-{i}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True);samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=i))
        print(base.encode(dict(completed=i)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)

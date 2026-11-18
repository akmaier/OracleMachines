#!/usr/bin/env python3
"""Fresh matched streams with persistent, explicitly versioned affine negatives."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,json,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_completion as prior
from experiments.cnf_affine_session import TerminalStore,NegativeChainBank,store_for,evaluate as session_evaluate
from experiments.cnf_affine_negative import CHAIN,TABLE,check_composed
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
base=prior.base;bound=prior.bound;binding=prior.binding;native=prior.native;prep=prior.prep
workerlib=prior.positive.old
PARENT=Path('experiments/results/cnf-affine-negative')
NATIVE_PARENT=Path('experiments/results/cnf-affine-completion')
FILES=('experiments/cnf_affine_session.py','experiments/compare_cnf_affine_session.py','solver/test_cnf_affine_session.py')
MODES=('affine','session')
original_banks=workerlib.partition.banks
original_audit=native.audit_records


def inherited(parent):
    return prior.inherited(parent)+bound(parent['affine_completion_decisions'])+bound(parent['affine_negative_decisions'])


def exclusions(parent):
    all_records=sum((bound(parent[f]) for f in prior.FIELDS),[])+inherited(parent)
    return [dict(query_root=k) for k in sorted({r['query_root'] for r in all_records})]


def banks(s,records):
    normal=[r for r in records if r['format']!=CHAIN];negative=[r for r in records if r['format']==CHAIN]
    return original_banks(s,normal)+([NegativeChainBank(store_for(s),negative)] if negative else [])


def audit_records(path,records,projections,prepared,catalogs,indices):
    started=time.perf_counter();normal=[r for r in records if r['format']!=CHAIN];negative=[r for r in records if r['format']==CHAIN]
    legacy=original_audit(path,normal,projections,prepared,catalogs,indices)
    s=SnapshotResidualSolver(path)
    try:
        store=TerminalStore(s);before=time.perf_counter()
        results=[check_composed(store,r) for r in negative]
        bank=NegativeChainBank(store,negative)
        assert [bank.lookup(r['source']) for r in negative]==results
        extension=dict(seconds=time.perf_counter()-before,records=len(negative),metrics=dict(s.counts),
            stored_nodes=s.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0])
    finally:s.close()
    return dict(native=legacy,extension=extension,seconds=time.perf_counter()-started)


def evaluate(s,source,target,guards,mode,eligible,limit):
    tick=time.perf_counter();before=Counter(s.counts);cnf,names,root=s._canonical(target)
    familiarity=dict(root=root,known_after_preparation=not eligible,guards=len(guards),
        variables=len(names),clauses=len(cnf),literals=sum(map(len,cnf)))
    metrics=dict(s.counts-before);seconds=time.perf_counter()-tick
    if mode=='session':r=session_evaluate(s,source,target,guards,eligible,limit)
    else:
        r=prior.evaluate(s,source,target,guards,'affine',eligible,limit)
        r.update(extension=False,extension_lookup_hit=False,extension_lookup_seconds=0.,extension_lookup_metrics={})
    r.update(familiarity=familiarity,familiarity_metrics=metrics,familiarity_seconds=seconds)
    return r


def summarize(records):
    result=prior.summarize(records)
    result.update(new_extension_nodes=sum(r['child']['metrics'].get('affine_negative_inserted_nodes',0) for r in records),
        new_extension_bytes=sum(r['child']['metrics'].get('affine_negative_inserted_bytes',0) for r in records),
        extension_publications=sum(r['extension'] and not r['extension_lookup_hit'] for r in records),
        extension_hits=sum(r['extension_lookup_hit'] for r in records),
        extension_lookup_seconds=sum(r['extension_lookup_seconds'] for r in records),
        extension_lookup_bytes=sum(r['extension_lookup_metrics'].get('affine_negative_read_bytes',0) for r in records),
        extension_lookup_attempts=sum(r['extension_lookup_metrics'].get('affine_negative_database_lookups',0)+r['extension_lookup_metrics'].get('affine_negative_memory_hits',0) for r in records))
    return result


def worker(out,p,catalog,mode):
    with patch.object(workerlib,'inherited',inherited),patch.object(workerlib,'evaluate',evaluate),patch.object(workerlib,'summarize',summarize),patch.object(workerlib.partition,'banks',banks),patch.object(native,'audit_records',audit_records):
        workerlib.worker(out,p,catalog,mode)


def prepare(out):
    out.mkdir(exist_ok=False);parent=base.load(PARENT/'checkpoint.json');seed=copy.deepcopy(bound(parent['native_parent']))
    seed.update(reference_union=parent['extended_archive'],affine_negative_decisions=parent['negative_decisions'])
    base.write(out/'seed-checkpoint.json',seed)
    sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    base.write(out/'previous-decisions.json',exclusions(seed))
    p=dict(base.load(NATIVE_PARENT/'protocol.json'))
    p.update(parent=binding(out/'seed-checkpoint.json'),extension_parent=binding(PARENT/'checkpoint.json'),
        source_fingerprints=sources,previous_decisions=binding(out/'previous-decisions.json'),orders=[list(MODES),list(MODES[::-1])],
        limitations=['Fresh sixty-query stream excluded from every inherited query and native root; metadata labels never enter selection.',
            'Both modes preserve seven inherited extension certificates and replay all historical native/composed/projection records. Only the session mode admits new affine negatives and attempts exact target extension lookup.',
            'Versioned chain replay uses its already checked extension terminal; native search cannot read extension proofs. Support/preparation still uses native availability only.',
            'All lookup misses, preceding discovery, checking, persistence, source sidecars, full cold replay, compression and RSS remain charged. No arbitrary-SAT bound.'])
    base.write(out/'protocol.json',p)
    tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'initial';base.restore_archive(seed['reference_union'],path);s=native.ResidualSolver(path)
        try:catalog=prior.inputs(s,p)
        finally:s.close()
    assert len(catalog['cases'])==60
    base.write(out/'cases.json',catalog);base.write(out/'generation.json',dict(seconds=time.perf_counter()-tick,selection=catalog['selection']))
    return p,catalog


def run(out):
    p=base.load(out/'protocol.json');catalog=base.load(out/'cases.json');samples=[]
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True)
            samples.append(dict(repeat=repeat,mode=mode,**binding(dest/'report.json')));print('fresh',repeat,mode,flush=True)
    summary={}
    for mode in MODES:
        data=[bound(e)['summary'] for e in samples if e['mode']==mode];first=data[0]
        timed=[k for k in first if k.endswith('_seconds') or k=='peak_rss_bytes']
        fixed=[k for k in first if k not in timed and k not in ('mode','sidecar_bytes')]
        for other in data[1:]:
            for k in fixed:assert first[k]==other[k],k
        summary[mode]={**{k:first[k] for k in fixed},**{'mean_'+k:sum(r[k] for r in data)/len(data) for k in timed},'sidecar_bytes':[r['sidecar_bytes'] for r in data]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    elif sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    else:run(Path(sys.argv[1]))

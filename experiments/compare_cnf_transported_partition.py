#!/usr/bin/env python3
"""Historical prefix-controlled residual pilot and fixed neighbouring edits.

Candidate selection is supplied and posthoc. The trials do not claim discovery
coverage, or an original-query speedup. Every arm starts from the same prefix.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import gzip,json,random,resource,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_residual_transport as prior
from experiments.cnf_transported_partition import run as partition,native_query,target_source
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_clause_partition import PartitionBank,check_record
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_negative import NegativeStore
from experiments.cnf_residual_dag import normalize,token
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
base=prior.base;binding=prior.binding;bound=prior.bound;TABLES=prior.TABLES
PARENT=Path('experiments/results/cnf-residual-transport')
CASES=(25,31,61);MODES=('affine','native','forward','reverse','screen');SPLITS=('historical','edits')
FILES=('experiments/cnf_transported_partition.py','experiments/compare_cnf_transported_partition.py','solver/test_cnf_transported_partition.py')


def write_zip(path,value):
    start=time.perf_counter();raw=base.encode(value).encode();path.write_bytes(gzip.compress(raw,mtime=0))
    return dict(**binding(path),raw_bytes=len(raw),compressed_bytes=path.stat().st_size,seconds=time.perf_counter()-start)


def read_zip(entry):
    assert base.sha(entry['path'])==entry['sha256'];return json.loads(gzip.decompress(Path(entry['path']).read_bytes()))


def tables(s):return {t:list(s.db.execute(f'SELECT id,payload FROM {t} ORDER BY rowid')) for t in TABLES}


def restore(prefix,path,delta=None):
    """Fresh schema: never copy a final archive with future records/free pages."""
    s=InputSafeAffineProbeSolver(path)
    try:
        with s.db:
            for state in (prefix,delta or {}):
                for t in TABLES:s.db.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)',state.get(t,[]))
    finally:s.close()


def prepare(out):
    out.mkdir(exist_ok=True);assert not (out/'protocol.json').exists();began=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    source=base.load(PARENT/'mismatch-analysis.json');history=base.load(PARENT/'holdout-mapped-0/queries.json')
    archive=base.load(PARENT/'holdout-mapped-0/report.json')['archive'];cases=[];prefixes={}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'final';base.restore_archive(archive,path);s=CanonicalVerifySnapshot(path)
        try:final=tables(s)
        finally:s.close()
        # Exclude all previously retained proof roots, including final histories,
        # only for novelty reporting; never feed them to a trial.
        path=Path(td)/'old-union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={key for t in TABLES for key, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
        for index in CASES:
            candidate={k:deepcopy(next(x for x in source['records'] if x['case']==index)[k]) for k in ('origin','origin_names','target','target_names')}
            available={t:{key for r in history[:index] for key in r['new_ids'][t]} for t in TABLES}
            prefix={t:[[k,v] for k,v in final[t] if k in available[t]] for t in TABLES}
            assert all(len(prefix[t])==len(available[t]) for t in TABLES)
            assert candidate['origin'] in available[TABLES[0]]
            root=token(tuple(map(tuple,candidate['target'])),Counter());assert all(root not in available[t] for t in TABLES)
            entry=write_zip(out/f'prefix-{index}.json.gz',prefix)
            original=target_source(candidate);rng=random.Random(202611190644+index)
            added=sorted(v*(1 if rng.randrange(2) else -1) for v in rng.sample(candidate['target_names'],3))
            assert added not in original
            deleted=rng.randrange(len(original))
            variants=[('historical','original',original),('edits','add',original+[added]),('edits','delete',original[:deleted]+original[deleted+1:])]
            for split,name,src in variants:
                cnf,names=normalize(src);c=deepcopy(candidate);c.update(target=[list(c) for c in cnf],target_names=list(names))
                key=token(cnf,Counter());assert all(key not in available[t] for t in TABLES)
                if split=='edits':assert key not in known
                cases.append(dict(case=index,split=split,variant=name,candidate=c,source=target_source(c),root=key,
                    known_in_prior_union=key in known,edit_clause=added if name=='add' else original[deleted] if name=='delete' else None))
            prefixes[str(index)]=dict(archive=entry,counts={t:len(v) for t,v in prefix.items()},before_case=index,origin=candidate['origin'])
    base.write(out/'cases.json',cases)
    p=dict(parent=binding(PARENT/'checkpoint.json'),historical_archive=archive,historical_queries=binding(PARENT/'holdout-mapped-0/queries.json'),
        supplied_candidates=binding(PARENT/'mismatch-analysis.json'),cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,
        orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        preparation_seconds=time.perf_counter()-began,limitations=[
        'Three posthoc residual candidates supplied from the preceding mismatch census. No automatic candidate discovery, representative coverage, or original source-query verdict is claimed.',
        'Every trial starts from proof rows committed before the selected original query; no work within that query is seeded. Final-archive preflight is descriptive only. Native/affine query roots are absent from all prefixes.',
        'One deterministic addition and deletion per case, generated before timing, use the same supplied donor. All six edit roots are absent from the prior union. This is a local-neighbour test, not an independent broad SAT holdout.',
        'Separate serial processes for each split/case/mode/repeat. Each edit stream shares its own prefix and newly acquired state. Two opposite arm orders. Affine baseline and native-only ablation distinguish dispatch effects.',
        'At most 256 native expansions total across all branches per query. Support extraction limits32 nodes,8192 literals,128KiB retained charge. Prerequisite checking, strengthened-premise publication, unit-trace publication, branch copies, archive and checked graph are separately charged and uncapped.',
        'Forward/reverse first-false orders run unconditionally if eligible. Screen checks both orders, admits all-terminal or one unresolved branch with at least two unit conflicts and fewer residual literals than baseline. No outcome-based selector tuning.',
        'Each target with all missing clauses is refuted by a checked transported core. Every first-false region is separately checked; all negative children are required for UNSAT. SAT lifts an independently checked native witness. Conditional residual evidence is not source-level evidence.',
        'Delta archives preserve dependency-ordered rows plus independent checked partition sidecars. Warm-bank setup, lookup, full cold proof replay, metadata encoding, persistence and compression are timed. Complete worker time includes measurement/audit overhead; query time excludes those costs.',
        'No theorem about polynomial arbitrary-SAT expansion follows. Retain negative results and both order regressions.'])
    base.write(out/'protocol.json',p)


def validate_rows(path,cases,records):
    tick=time.perf_counter();before=base.sha(path);s=CanonicalVerifySnapshot(path);store=MultiEquivalenceStore(s);negative=NegativeStore(s)
    try:
        for t,rows in tables(s).items():
            for key,payload in rows:
                if t==TABLES[0]:assert s._read(key) is not None
                elif t==prior.AFFINE_TABLE:assert negative.read(key) is not None
                else:assert store.read(key) is not None
        for c,r in zip(cases,records,strict=True):
            if r['partition'] is not None:
                got=check_record(s,r['partition']);assert got['root']==c['root'];assert got['answer']==r['result']['answer']
            elif r['result'] is not None:prior.check_answer(s,store,c['source'],r['result'],negative)
            else:assert r['status']=='unresolved' and r['reason']==BUDGET_MESSAGE
        counts=dict(s.counts)
    finally:s.close()
    assert before==base.sha(path)
    return dict(seconds=time.perf_counter()-tick,counts=counts)


def query(s,c,mode,budget):
    if mode in ('forward','reverse','screen'):return partition(s,c['candidate'],mode,budget)
    tick=time.perf_counter()
    try:result=s.solve(c['source']) if mode=='affine' else native_query(s,c['source'],budget)
    except RuntimeError as e:
        if str(e)!=BUDGET_MESSAGE:raise
        result=None;reason=str(e)
    else:reason=None
    return dict(mode=mode,route=mode,status='unresolved' if result is None else 'sat' if result['answer'] else 'unsat',result=result,
        reason=reason,partition=None,expanded_nodes=s.counts.get('expanded_nodes',0),metrics=dict(s.counts),seconds=time.perf_counter()-tick)


def worker(out,p,split,index,mode):
    began=time.perf_counter();out.mkdir();cases=[c for c in bound(p['cases']) if c['case']==index and c['split']==split]
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    prefix=read_zip(p['prefixes'][str(index)]['archive']);records=[];sidecars=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';tick=time.perf_counter();restore(prefix,path);restore_seconds=time.perf_counter()-tick
        tick=time.perf_counter();s=InputSafeAffineProbeSolver(path,node_limit=p['node_limit']);setup=time.perf_counter()-tick
        try:
            marks={t:len(v) for t,v in prefix.items()}
            for c in cases:
                tick=time.perf_counter();r=query(s,c,mode,p['node_limit']);r.update(case=index,variant=c['variant'],root=c['root'])
                current=tables(s);r['new_ids']={t:[k for k,_ in current[t][marks[t]:]] for t in TABLES};marks={t:len(v) for t,v in current.items()}
                r['measured_seconds']=time.perf_counter()-tick;records.append(r)
                if r['partition'] is not None:sidecars.append(r['partition'])
                assert r['expanded_nodes']<=p['node_limit']
            final=tables(s);delta={t:final[t][len(prefix[t]):] for t in TABLES}
            memory=prior.prior.deep_size((s.checked,s.equivalences.checked,s.equivalences.old.checked,s.equivalences.old.legacy.checked,
                s.binary_cores.checked,s.witness_pool,s.negative_pool,s.affine.checked,sidecars))
            tick=time.perf_counter();bank=PartitionBank(s,sidecars);warm_setup=time.perf_counter()-tick
            tick=time.perf_counter();warm=[]
            with patch.object(s,'_expand',side_effect=AssertionError('Warm expansion')):
                for c,r in zip(cases,records):
                    if r['result'] is None:continue
                    got=bank.lookup(c['source']) if r['partition'] is not None else s.solve(c['source'])
                    assert got['answer']==r['result']['answer'];warm.append(dict(variant=c['variant'],result=got))
            warm_seconds=time.perf_counter()-tick
            assert tables(s)==final
        finally:s.close()
        cold=validate_rows(path,cases,records);database_bytes=path.stat().st_size
        # Persistence of the actual reusable proofs, distinct from diagnostic logs.
        tick=time.perf_counter();delta_archive=write_zip(out/'delta.json.gz',delta);base.write(out/'partitions.json',sidecars)
        persistence=time.perf_counter()-tick
        tick=time.perf_counter();rebuilt=Path(td)/'rebuilt';restore(prefix,rebuilt,read_zip(delta_archive));rebuild=time.perf_counter()-tick
        reconstructed=validate_rows(rebuilt,cases,records)
        base.write(out/'queries.json',records);base.write(out/'warm.json',warm)
    summary=dict(case=index,split=split,mode=mode,statuses=dict(Counter(r['status'] for r in records)),routes=dict(Counter(r['route'] for r in records)),
        expanded_nodes=sum(r['expanded_nodes'] for r in records),new_records={t:len(v) for t,v in delta.items()},
        new_payload_bytes=sum(len(k.encode())+len(v.encode()) for rows in delta.values() for k,v in rows),database_bytes=database_bytes,
        checked_python_bytes=memory,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        query_seconds=sum(r['seconds'] for r in records),measured_seconds=sum(r['measured_seconds'] for r in records),restore_seconds=restore_seconds,
        setup_seconds=setup,warm_setup_seconds=warm_setup,warm_seconds=warm_seconds,cold_seconds=cold['seconds'],persistence_seconds=persistence,
        reconstruction_seconds=rebuild+reconstructed['seconds'],complete_worker_seconds=time.perf_counter()-began,
        proof_delta_compressed_bytes=delta_archive['compressed_bytes'],partition_bytes=(out/'partitions.json').stat().st_size,
        delta_digest={t:base.key_sha(base.encode(v)) for t,v in delta.items()})
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),partitions=binding(out/'partitions.json'),
        delta=delta_archive,cold=cold,reconstructed=reconstructed))


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for split in SPLITS:
        for index in CASES:
            for repeat,order in enumerate(p['orders']):
                for mode in order:
                    dest=out/f'{split}-{index}-{mode}-{repeat}'
                    subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),split,str(index),mode],check=True)
                    samples.append(dict(split=split,case=index,mode=mode,repeat=repeat,**binding(dest/'report.json')))
                print('finished',split,index,repeat,flush=True)
    summary={}
    for split in SPLITS:
        summary[split]={}
        for mode in MODES:
            arms=[bound(s)['summary'] for s in samples if s['split']==split and s['mode']==mode];summary[split][mode]={}
            for key in ('query_seconds','complete_worker_seconds','cold_seconds','warm_setup_seconds','warm_seconds','persistence_seconds','reconstruction_seconds',
                        'checked_python_bytes','peak_rss_bytes','database_bytes','new_payload_bytes','proof_delta_compressed_bytes','partition_bytes','expanded_nodes'):
                summary[split][mode][key]=sum(a[key] for a in arms)/2
            statuses=Counter()
            for a in arms[:]:statuses.update(a['statuses'])
            summary[split][mode]['statuses']={k:v//2 for k,v in statuses.items()}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4],int(sys.argv[5]),sys.argv[6])
    else:run(Path(sys.argv[1]))

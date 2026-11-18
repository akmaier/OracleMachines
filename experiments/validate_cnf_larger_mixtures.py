#!/usr/bin/env python3
"""Validate larger decisions, explicit unknowns, discovery certificates and append-only union."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_larger_mixtures as study
from experiments.cnf_larger_mixtures import catalog,BUDGET_MESSAGE
from experiments.cnf_pattern_inventory import PatternInventory
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_residual_dag import normalize,token
from experiments.validate_cnf_ordered_normalization import TABLES,PILOTS
base=study.base;previous=study.prior.previous


def ordinary(c):return {k:v for k,v in c.items() if not k.startswith(('ordered_','proof_memo_')) and k not in ('normalization_literal_visits','key_serialized_bytes')}


def discovery(out,cases):
    config=dict(max_depth=1,candidate_limit=4,parity_width=8,decompose=True);dest=out/'inventory';dest.mkdir();records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';tick=time.perf_counter();s=PatternInventory(path,**config)
        try:
            for c in cases:
                r=s.inspect(c['source']);node=s._load(r['root']['key']);records.append(dict(case=c['case'],result=r,root_kind=node['kind']))
            storage=s.storage();retained=study.prior.deep_size(s.checked)
        finally:s.close()
        acquisition=time.perf_counter()-tick;before=base.sha(path);tick=time.perf_counter();s=PatternInventory(path,**config)
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_discover',side_effect=AssertionError('Cold discovery')):
                for key, in s.db.execute('SELECT id FROM cnf_patterns_v1'):assert s._load(key) is not None
                for c,r in zip(cases,records):
                    _,names,key=s._canonical(c['source'],1);assert r['result']['root']==dict(key=key,names=names)
                    node=s._load(key);assert node['summary']==r['result']['summary'] and node['profile']==r['result']['profile']
                    payload=json.loads(s.db.execute('SELECT payload FROM cnf_pattern_sources_v1 WHERE id=?',(r['result']['source_id'],)).fetchone()[0])
                    assert payload==dict(source=c['source'],root=r['result']['root'],config=config)
            verified=s.counts['verified_pattern_nodes']
        finally:s.close()
        assert base.sha(path)==before;cold_seconds=time.perf_counter()-tick;archive=base.archive(path,dest)
    base.write(out/'discovery-records.json',records)
    result=dict(config=config,records=study.binding(out/'discovery-records.json'),archive=archive,storage=storage,retained_python_bytes=retained,
        acquisition_seconds=acquisition,cold_seconds=cold_seconds,verified_nodes=verified,
        closed_queries=sum(r['result']['summary']['closed'] for r in records),cells=dict(Counter(r['result']['profile']['cell'] for r in records)),
        root_kinds=dict(Counter(r['root_kind'] for r in records)),
        limitations=['Posthoc bounded inventory, not part of timed solver search. Closure is a recognized-family decomposition, not a SAT/UNSAT verdict.',
        'Seven overlapping syntax recognizers, depth one and four ranked conditioning candidates. Width-capped single-parity recognition can remain unresolved. Not a complete semantic taxonomy.'])
    base.write(out/'discovery.json',result);return result


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases']);report=base.load(out/'report.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    for generated,c in zip(catalog(),cases):
        for k,v in generated.items():assert c[k]==v
        cnf,names=normalize(c['source']);assert token(cnf,Counter())==c['root'] and len(names)==c['variables']
    old=base.load(study.PARENT/'validation.json');manifests=dict(old['parent_manifests']);path=study.PARENT/'manifest.json'
    manifests[str(path)]=dict(sha256=base.sha(path),artifacts_checked=len(base.load(path)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
        artifacts+=len(items)
    assert len(manifests)==118 and artifacts==8032
    states=[];by_mode={};audits=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'union';base.restore_archive(parent['reference_union'],path);s=SnapshotResidualSolver(path)
        try:initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:s.close()
        known=set().union(*(set(initial[t]) for t in TABLES if 'equivalence' in t or t=='cnf_residual_v1'))
        assert all(c['known_in_parent']==(c['root'] in known) for c in cases)
        for sample in report['samples']:
            data=study.bound(sample);rows=study.bound(data['queries']);db=tmp/(sample['mode']+str(sample['repeat']));base.restore_archive(data['archive'],db)
            s=SnapshotResidualSolver(db)
            try:tables={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in study.TABLES}
            finally:s.close()
            available={t:set() for t in study.TABLES};sizes=Counter()
            for c,r in zip(cases,rows):
                assert r['case']==c['case'];added=0;payload=0
                for t in study.TABLES:
                    ids=r['new_ids'][t];assert len(ids)==len(set(ids)) and not set(ids)&available[t]
                    available[t].update(ids);size=sum(len(k)+len(tables[t][k]) for k in ids);added+=len(ids);payload+=size
                    sizes[t+'_nodes']+=len(ids);sizes[t+'_payload']+=size
                assert dict(sizes)==r['retained']
                assert r['metrics'].get('batch_committed_records',0)==added
                assert r['metrics'].get('batch_committed_payload',0)==payload
                for key in r['new_ids'][study.TABLES[0]]:
                    proof=json.loads(tables[study.TABLES[0]][key]).get('proof',{})
                    assert {proof[f] for f in ('child','low','high') if f in proof}<=available[study.TABLES[0]]
                if r['status']=='unresolved':
                    assert r['result'] is None and r['reason']==BUDGET_MESSAGE and r['metrics']['expanded_nodes']==p['node_limit']
                else:
                    assert r['result']['root']==c['root'] and r['status']==('sat' if r['result']['answer'] else 'unsat')
                    assert c['root'] in set().union(*available.values())
                    assert r['metrics']['expanded_nodes']<=p['node_limit'] if 'expanded_nodes' in r['metrics'] else True
            assert all(available[t]==set(tables[t]) for t in study.TABLES)
            states.append(tables);by_mode[(sample['mode'],sample['repeat'])]=rows;audits.append(study.cold(db,cases,rows))
        assert all(state==states[0] for state in states)
        control=by_mode[('batch32',0)]
        for (mode,repeat),rows in by_mode.items():
            for a,b in zip(control,rows):
                for f in ('case','status','reason','new_ids','retained'):assert a[f]==b[f]
                if a['result'] is not None:
                    for f in ('answer','model','root','authority','quotient_choice'):assert a['result'][f]==b['result'][f]
                assert ordinary(a['metrics'])==ordinary(b['metrics'])
                if mode=='ordered':assert a['metrics']=={k:v for k,v in b['metrics'].items() if not k.startswith('ordered_')}
                assert a['metrics'].get('normalization_literal_visits',0)==b['metrics'].get('normalization_literal_visits',0)+b['metrics'].get('proof_memo_reused_literals',0)
        # Append all newly checked records atomically to the preserved union.
        con=sqlite3.connect(path);added={}
        try:
            with con:
                for t,rows in states[0].items():
                    added[t]=0
                    for key,payload in rows.items():
                        if key in initial[t]:assert initial[t][key]==payload
                        else:con.execute(f'INSERT INTO {t}(id,payload) VALUES (?,?)',(key,payload));added[t]+=1
        finally:con.close()
        merged={};reader_counts={}
        for reader in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=reader(path);store=MultiEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
            try:
                merged={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
                for t in TABLES:assert initial[t].items()<=merged[t].items()
                for key in merged['cnf_residual_v1']:assert s._read(key) is not None
                for t in TABLES[2:5]:
                    for key in merged[t]:assert store.read(key) is not None
                for key in merged[TABLES[1]]:assert terminal.read(key) is not None
                for key,payload in merged[TABLES[-1]].items():cache.verify(key,payload)
                for r in sum((study.bound(parent[f]) for f in PILOTS),[]):study.prior.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
                for c,r in zip(cases,control):
                    if r['result'] is not None:study.prior.check_answer(s,store,c['source'],r['result'])
                reader_counts[reader.__name__]=dict(s.counts)
            finally:s.close()
        s=previous.native.ResidualSolver(path)
        try:_,_,indices,prepared,_=previous.prep.setup(s,base.load('experiments/results/cnf-targeted-backbone/protocol.json'))
        finally:s.close()
        historical=previous.audit_records(path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS],indices)
        dest=out/'union';dest.mkdir();archive=base.archive(path,dest)
    # Posthoc opportunity only: the catalog supplies the related base query.
    # Full edited-source witness validation is mandatory; this is not a lookup algorithm.
    tick=time.perf_counter();opportunities=[]
    for c,r in zip(cases,control):
        if c['variant']!='edit':continue
        base_result=control[c['base_case']]['result'];model=None
        if base_result is not None and base_result['answer']:
            model={int(k):v for k,v in base_result['model'].items()}
        valid=model is not None and all(any(model.get(abs(l),False)==(l>0) for l in clause) for clause in c['source'])
        if valid:assert r['status']=='sat'
        opportunities.append(dict(case=c['case'],base_case=c['base_case'],base_sat=model is not None,model_survives=valid,
            witness_check_literal_payload=sum(map(len,c['source'])) if model is not None else 0,
            observed_expansions=r['metrics'].get('expanded_nodes',0),observed_new_nodes=len(r['new_ids'][study.TABLES[0]])))
    base.write(out/'reuse-opportunities.json',dict(cases=opportunities,seconds=time.perf_counter()-tick,
        eligible=sum(o['model_survives'] for o in opportunities),base_sat=sum(o['base_sat'] for o in opportunities),
        limitations=['Related base candidates are supplied by generator metadata only for this posthoc check; timed search never receives labels.',
        'A complete edited-source model check certifies SAT only. Finding candidates, name transport, publication and altered future cache contents remain unmeasured.',
        'Observed work on eligible edits is an opportunity indicator, not an additive counterfactual stream saving. No proof reuse or UNSAT verdict follows from a failed model check.']))
    inventory=discovery(out,cases)
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_larger_mixtures.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],source_fingerprints=sources,reference_union=archive,
        larger_mixtures=dict(cases=p['cases'],queries=study.binding(out/'batch32-0/queries.json'),archive=base.load(out/'batch32-0/report.json')['archive'],
            discovery=study.binding(out/'discovery.json'),report=study.binding(out/'report.json'),node_limit=p['node_limit']))
    base.write(out/'checkpoint.json',checkpoint)
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        prior_tables={t:len(rows) for t,rows in initial.items()},preserved_tables={t:len(rows) for t,rows in merged.items()},new_records=added,
        query_audits=648,exact_comparisons=540,statuses=report['summary']['batch32']['statuses'],known_parent_queries=sum(c['known_in_parent'] for c in cases),
        distinct_roots=len({c['root'] for c in cases}),old_composed_records=len(previous.inherited(parent)),old_pilot_records=sum(len(study.bound(parent[f])) for f in PILOTS),
        reader_counts=reader_counts,audits=audits,historical_cold=historical,discovery=study.binding(out/'discovery.json'),checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result);print(base.encode({k:result[k] for k in ('passed','new_records','statuses','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))

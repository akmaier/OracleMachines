#!/usr/bin/env python3
"""Validate variable transport, untrusted cold hints and all preserved histories."""
from collections import Counter
from itertools import product
from pathlib import Path
from unittest.mock import patch
import copy,json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_residual_transport as study
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_pattern_inventory import PatternInventory
from experiments.cnf_residual_transport import ResidualTransportSolver,TABLE as HINT_TABLE
from experiments.cnf_residual_dag import holds
from experiments.cnf_cross_family import truth_table
from experiments.cnf_affine_patterns import extract_affine,check_affine
from experiments.cnf_residual_dag import normalize,token
from experiments.validate_cnf_ordered_normalization import TABLES,PILOTS
base=study.base;previous=study.prior.previous


def frontier(out,cases,rows):
    """Describe all held-out affine subsystems after timing, without new verdicts."""
    records=[]
    for c,r in zip(cases,rows,strict=True):
        began=time.perf_counter();counts=Counter();cnf,names=normalize(c['source'],counts)
        assert token(cnf,counts)==c['root'];certificate=extract_affine(cnf,counts)
        summary=check_affine(cnf,certificate,counts)
        records.append(dict(case=c['case'],root=c['root'],status=r['status'],family=c['family'],
            free_variables=len(names)-summary['rank'],summary=summary,certificate=certificate,
            metrics=dict(counts),seconds=time.perf_counter()-began,query_seconds=r['seconds']))
    unresolved=[r for r in records if r['status']=='unresolved']
    result=dict(cases=study.binding(out/'holdout-cases.json'),queries=study.binding(out/'holdout-mapped-0/queries.json'),records=records,
        unresolved_cases=[r['case'] for r in unresolved],unknown_query_seconds=sum(r['query_seconds'] for r in unresolved),
        free_dimension_histogram=dict(Counter(r['free_variables'] for r in unresolved)),
        low_dimension_unknowns=[r['case'] for r in unresolved if not r['summary']['inconsistent'] and r['free_variables']<=8],
        seconds=sum(r['seconds'] for r in records),limitations=[
        'Posthoc all-input description, excluded from policy timing. No new decisions or authority records are published here.',
        'A consistent extracted subsystem may leave an arbitrary coupling CNF. Free dimension describes an enumeration opportunity, not proof of cheap arbitrary-SAT closure.'])
    base.write(out/'residual-frontier.json',result)


def tiny(out):
    clauses=[[v*sign for v,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=2)]
    cases=[];records=[];dest=out/'tiny';dest.mkdir()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=ResidualTransportSolver(path,pool_capacity=4,candidate_limit=2)
        try:
            for bits in product((False,True),repeat=len(clauses)):
                source=[c for b,c in zip(bits,clauses) if b];r=study.attempt(s,source)
                assert r['result']['answer']==truth_table(source)['answer']
                if r['result']['answer']:assert holds(source,r['result']['model'])
                cases.append(dict(case=len(cases),source=source));records.append(r)
        finally:s.close()
        audit=study.cold(path,cases,records);archive=base.archive(path,dest)
    base.write(dest/'queries.json',records)
    return dict(formulas=len(cases),statuses=dict(Counter(r['status'] for r in records)),audit=audit,archive=archive,queries=study.binding(dest/'queries.json'))


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);report=base.load(out/'report.json')
    cases={split:study.bound(b) for split,b in p['cases'].items()}
    for split,cs in cases.items():assert cs==study.catalog(split)
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    old=base.load(study.PARENT/'validation.json');manifests=dict(old['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
        artifacts+=len(items)
    assert (len(manifests),artifacts)==(125,8462)
    audits=[];by_mode={};state_digests={};alternatives=Counter();new=Counter();query_audits=0
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'union';base.restore_archive(parent['reference_union'],path);s=SnapshotResidualSolver(path)
        try:initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:s.close()
        merged=copy.deepcopy(initial)
        known=set().union(*(set(initial[t]) for t in TABLES if 'equivalence' in t or t in ('cnf_residual_v1',study.AFFINE_TABLE)))
        novelty={split:dict(queries=len(cs),known_queries=sum(c['root'] in known for c in cs),distinct_roots=len({c['root'] for c in cs})) for split,cs in cases.items()}
        for sample in report['samples']:
            data=study.bound(sample);rows=study.bound(data['queries']);cs=cases[sample['split']]
            assert len(rows)==len(cs) and len(cs)==(12 if sample['split']=='mapping' else 108)
            db=tmp/('-'.join(str(sample[k]) for k in ('split','mode','repeat')));base.restore_archive(data['archive'],db)
            s=SnapshotResidualSolver(db)
            try:tables={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in study.TABLES}
            finally:s.close()
            state_digests[(sample['split'],sample['mode'],sample['repeat'])]={t:base.key_sha(base.encode(sorted(values.items()))) for t,values in tables.items()}
            available={t:set() for t in study.TABLES};sizes=Counter()
            for c,r in zip(cs,rows):
                query_audits+=1;assert r['case']==c['case'];added=payload=0
                for t in study.TABLES:
                    ids=r['new_ids'][t];assert len(ids)==len(set(ids)) and not set(ids)&available[t]
                    available[t].update(ids);size=sum(len(k)+len(tables[t][k]) for k in ids);added+=len(ids);payload+=size
                    sizes[t+'_nodes']+=len(ids);sizes[t+'_payload']+=size
                assert dict(sizes)==r['retained']
                assert r['metrics'].get('batch_committed_records',0)+r['metrics'].get('affine_negative_inserted_nodes',0)==added
                assert r['metrics'].get('batch_committed_payload',0)+r['metrics'].get('affine_negative_inserted_bytes',0)==payload
                for counter,limit in (('transport_probes','transport_probes'),('transport_staged','transport_stage_limit'),
                        ('transport_retained_entries','transport_capacity'),('transport_retained_bytes','transport_bytes'),
                        ('transport_stage_peak_bytes','transport_bytes'),('transport_map_peak_bytes','transport_map_bytes')):
                    assert r['metrics'].get(counter,0)<=p['transport_limits'][limit]
                assert r['metrics'].get('transport_candidates',0)<=p['transport_limits']['transport_candidates']*r['metrics'].get('transport_probes',0)
                assert r['metrics'].get('transport_index_entries',0)<=p['transport_limits']['transport_capacity']*r['metrics'].get('transport_probes',0)
                assert r['metrics'].get('affine_probe_attempts',0)<=1
                assert r['metrics'].get('affine_elimination_xors',0)<=p['affine_limits']['affine_xors']
                assert r['metrics'].get('witness_peak_entries',0)<=64
                assert r['metrics'].get('witness_candidates',0)<=4*r['metrics'].get('witness_probes',0)
                assert r['metrics'].get('witness_index_entries',0)<=64*r['metrics'].get('witness_probes',0)
                assert r['metrics'].get('plan_peak_bytes',0)<=p['plan_byte_limit']
                assert r['metrics'].get('negative_materialize_plan_emitted_recipes',0)<=p['negative_limits']['negative_node_limit']
                assert r['metrics'].get('negative_retained_entries',0)<=p['negative_limits']['negative_capacity']
                assert r['metrics'].get('negative_retained_literals',0)<=p['negative_limits']['negative_capacity']*p['negative_limits']['negative_literal_limit']
                for prefix in ('negative_discover_','negative_materialize_'):
                    assert r['metrics'].get(prefix+'attempts',0)<=1
                    assert r['metrics'].get(prefix+'support_nodes',0)<=p['negative_limits']['negative_node_limit']
                    assert r['metrics'].get(prefix+'support_source_literals',0)<=p['negative_limits']['negative_support_literals']
                for key in r['new_ids'][study.TABLES[0]]:
                    proof=json.loads(tables[study.TABLES[0]][key]).get('proof',{})
                    assert {proof[f] for f in ('child','low','high') if f in proof}<=available[study.TABLES[0]]
                if r['status']=='unresolved':assert r['result'] is None and r['reason']==BUDGET_MESSAGE and r['metrics']['expanded_nodes']==p['node_limit']
                else:
                    assert r['result']['root']==c['root'] and r['status']==('sat' if r['result']['answer'] else 'unsat')
                    assert c['root'] in set().union(*available.values())
                    assert r['metrics'].get('expanded_nodes',0)<=p['node_limit']
            assert all(available[t]==set(tables[t]) for t in study.TABLES)
            audit=study.cold(db,cs,rows)
            before=base.sha(db);s=ResidualTransportSolver(db,transport=sample['mode']=='mapped',**p['transport_limits'])
            try:
                hints=dict(s.db.execute(f'SELECT id,payload FROM {HINT_TABLE}'))
                assert len(hints)==data['summary']['hint_rows'] and len(hints)<=p['transport_limits']['transport_capacity']
                assert base.key_sha(base.encode(sorted(hints.items())))==data['summary']['hint_digest']
                assert set(hints)==set(s.transport_pool)
                for key,payload in hints.items():
                    entry=s._decode_hint(key,payload);node=s._read(entry['origin'])
                    assert node is not None and node['answer'] is False
                    cnf,names,origin=s._canonical(entry['clauses'])
                    assert origin==entry['origin'] and cnf==tuple(tuple(c) for c in node['cnf'])
                audit['checked_hint_records']=len(hints)
            finally:s.close()
            assert before==base.sha(db)
            audits.append(audit)
            by_mode[(sample['split'],sample['mode'],sample['repeat'])]=rows
            for t,values in tables.items():
                for key,payload in values.items():
                    if key in merged[t]:
                        if payload!=merged[t][key]:
                            # Each entire trial was checked above. Keep the earlier
                            # authoritative bytes, even when another witness differs.
                            assert json.loads(payload)['answer']==json.loads(merged[t][key])['answer']
                            alternatives[t]+=1
                    else:merged[t][key]=payload;new[t]+=1
        comparisons=0
        for split in cases:
            control=by_mode[(split,'base',0)]
            for mode in study.MODES:
                a=by_mode[(split,mode,0)];b=by_mode[(split,mode,1)]
                for x,y in zip(a,b):
                    for field in ('case','status','reason','metrics','new_ids','retained'):assert x[field]==y[field]
                    if x['result'] is not None:
                        for field in ('answer','model','root','authority','quotient_choice'):assert x['result'][field]==y['result'][field]
                for x,y in zip(control,a):
                    if x['result'] is not None and y['result'] is not None:assert x['status']==y['status'];comparisons+=1
        con=sqlite3.connect(path)
        try:
            with con:
                for t,values in merged.items():
                    for key,payload in values.items():
                        if key not in initial[t]:con.execute(f'INSERT INTO {t}(id,payload) VALUES (?,?)',(key,payload))
        finally:con.close()
        old_cases=study.bound(parent['larger_mixtures']['cases']);old_rows=study.bound(parent['larger_mixtures']['queries']);recovery=study.bound(parent['larger_mixtures']['recovery'])
        prior_protocol=study.bound(parent['witness_pool_study']['protocol'])
        prior_report=study.bound(parent['witness_pool_study']['report'])
        prior_streams=[(study.bound(prior_protocol['cases'][entry['split']]),study.bound(study.bound(entry)['queries'])) for entry in prior_report['samples']]
        negative_protocol=study.bound(parent['negative_edit_pool_study']['protocol'])
        negative_report=study.bound(parent['negative_edit_pool_study']['report'])
        negative_streams=[(study.bound(negative_protocol['cases'][entry['split']]),study.bound(study.bound(entry)['queries'])) for entry in negative_report['samples']]
        plan_protocol=study.bound(parent['support_plan_study']['protocol'])
        plan_report=study.bound(parent['support_plan_study']['report'])
        plan_streams=[(study.bound(plan_protocol['cases'][entry['split']]),study.bound(study.bound(entry)['queries'])) for entry in plan_report['samples']]
        affine_protocol=study.bound(parent['affine_probe_study']['protocol'])
        affine_report=study.bound(parent['affine_probe_study']['report'])
        affine_streams=[(study.bound(affine_protocol['cases'][entry['split']]),study.bound(study.bound(entry)['queries'])) for entry in affine_report['samples']]
        partial_protocol=study.bound(parent['partial_residual_study']['protocol'])
        partial_report=study.bound(parent['partial_residual_study']['report'])
        partial_streams=[(study.bound(partial_protocol['cases'][entry['split']]),study.bound(study.bound(entry)['queries'])) for entry in partial_report['samples']]
        reader_counts={}
        for reader in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=reader(path);store=MultiEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
            try:
                for t in TABLES:assert initial[t].items()<=dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
                for key in merged['cnf_residual_v1']:assert s._read(key) is not None
                for t in TABLES[2:5]:
                    for key in merged[t]:assert store.read(key) is not None
                for key in merged[TABLES[1]]:assert terminal.read(key) is not None
                for key,payload in merged[TABLES[-1]].items():cache.verify(key,payload)
                for r in sum((study.bound(parent[f]) for f in PILOTS),[]):study.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
                for cs,rs in [(old_cases,old_rows)]+prior_streams+negative_streams+plan_streams+affine_streams+partial_streams+[(cases[split],rs) for (split,mode,rep),rs in by_mode.items() if rep==0]:
                    for c,r in zip(cs,rs):
                        if r['result'] is not None:study.check_answer(s,store,c['source'],r['result'])
                study.check_answer(s,store,old_cases[recovery['target_case']]['source'],recovery['result'])
                reader_counts[reader.__name__]=dict(s.counts)
            finally:s.close()
        s=previous.native.ResidualSolver(path)
        try:_,_,indices,prepared,_=previous.prep.setup(s,base.load('experiments/results/cnf-targeted-backbone/protocol.json'))
        finally:s.close()
        historical=previous.audit_records(path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS],indices)
        dest=out/'union';dest.mkdir();archive=base.archive(path,dest)
        # Explicitly check the preceding classification archive, not just its hash.
        inventory=study.bound(parent['larger_mixtures']['discovery']);ip=tmp/'inventory';base.restore_archive(inventory['archive'],ip)
        before=base.sha(ip);s=PatternInventory(ip,**inventory['config'])
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_discover',side_effect=AssertionError('Old discovery')):
                for key, in s.db.execute('SELECT id FROM cnf_patterns_v1'):assert s._load(key) is not None
                for c,r in zip(old_cases,study.bound(inventory['records'])):
                    _,names,key=s._canonical(c['source'],1);assert r['result']['root']==dict(key=key,names=names)
                    node=s._load(key);assert node['summary']==r['result']['summary'] and node['profile']==r['result']['profile']
                    source=json.loads(s.db.execute('SELECT payload FROM cnf_pattern_sources_v1 WHERE id=?',(r['result']['source_id'],)).fetchone()[0])
                    assert source==dict(source=c['source'],root=r['result']['root'],config=inventory['config'])
            old_inventory_nodes=s.counts['verified_pattern_nodes']
        finally:s.close()
        assert before==base.sha(ip)
    tiny_result=tiny(out)
    analysis={}
    for split in cases:
        rows={mode:by_mode[(split,mode,0)] for mode in study.MODES};arms=report['summary'][split]
        groups={}
        for field in ('family','variant'):
            groups[field]={}
            for value in sorted({c[field] for c in cases[split]}):
                groups[field][value]={}
                for mode in study.MODES:
                    selected=[r for c,r in zip(cases[split],rows[mode]) if c[field]==value]
                    groups[field][value][mode]=dict(seconds=sum(r['seconds'] for r in selected),expansions=sum(r['metrics'].get('expanded_nodes',0) for r in selected),new_nodes=sum(len(r['new_ids']['cnf_residual_v1']) for r in selected),transport_hits=sum(r['metrics'].get('transport_hits',0) for r in selected),transport_probes=sum(r['metrics'].get('transport_probes',0) for r in selected),transport_candidates=sum(r['metrics'].get('transport_candidates',0) for r in selected),negative_hits=sum(r['metrics'].get('negative_hits',0) for r in selected),affine_conflicts=sum(r['metrics'].get('affine_probe_conflicts',0) for r in selected),affine_replays=sum(r['metrics'].get('affine_probe_exact_hits',0) for r in selected),statuses=dict(Counter(r['status'] for r in selected)))
        keys=('mean_query_seconds','mean_complete_worker_seconds','mean_cold_seconds','native_nodes','native_payload','database_bytes','compressed_bytes','checked_python_bytes')
        reductions={m:{k:1-arms['mapped'][k]/arms[m][k] for k in keys} for m in ('base','compact')}
        paired=[]
        for repeat in (0,1):
            values={m:study.bound(next(s for s in report['samples'] if s['split']==split and s['repeat']==repeat and s['mode']==m))['summary'] for m in study.MODES}
            paired.append({m:{k:values['mapped'][k]-values[m][k] for k in ('query_seconds','complete_worker_seconds','warm_seconds','cold_seconds','reconstruction_seconds')} for m in ('base','compact')})
        changes={m:dict(newly_completed=[c['case'] for c,a,b in zip(cases[split],rows[m],rows['mapped']) if a['status']=='unresolved' and b['status']!='unresolved'],
            newly_stopped=[c['case'] for c,a,b in zip(cases[split],rows[m],rows['mapped']) if a['status']!='unresolved' and b['status']=='unresolved']) for m in ('base','compact')}
        analysis[split]=dict(groups=groups,mapped_reductions=reductions,paired_mapped_minus_baseline=paired,status_changes=changes,
            unknown_cases={m:[r['case'] for r in rows[m] if r['status']=='unresolved'] for m in study.MODES},
            authorities={m:dict(Counter(r['result']['authority'] for r in rows[m] if r['result'] is not None)) for m in study.MODES})
    base.write(out/'analysis.json',analysis)
    frontier(out,cases['holdout'],by_mode[('holdout','mapped',0)])
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_residual_transport.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],source_fingerprints=sources,reference_union=archive,
        residual_transport_study=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),analysis=study.binding(out/'analysis.json'),frontier=study.binding(out/'residual-frontier.json'),solver=study.binding('experiments/cnf_residual_transport.py')))
    base.write(out/'checkpoint.json',checkpoint)
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        prior_tables={t:len(v) for t,v in initial.items()},preserved_tables={t:len(v) for t,v in merged.items()},new_records=dict(new),alternative_payload_observations=dict(alternatives),
        query_audits=query_audits,completed_status_comparisons=comparisons,novelty=novelty,old_composed_records=len(previous.inherited(parent)),old_pilot_records=sum(len(study.bound(parent[f])) for f in PILOTS),
        old_larger_queries=len(old_rows),old_witness_observations=sum(len(rs) for _,rs in prior_streams),old_negative_observations=sum(len(rs) for _,rs in negative_streams),old_support_plan_observations=sum(len(rs) for _,rs in plan_streams),old_affine_probe_observations=sum(len(rs) for _,rs in affine_streams),old_partial_observations=sum(len(rs) for _,rs in partial_streams),old_inventory_nodes=old_inventory_nodes,reader_counts=reader_counts,audits=audits,historical_cold=historical,tiny=tiny_result,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result);print(base.encode({k:result[k] for k in ('passed','new_records','alternative_payload_observations','novelty','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))

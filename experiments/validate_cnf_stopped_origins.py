#!/usr/bin/env python3
"""Check causal supports, matched controls and append-only proof preservation."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import json, shutil, sqlite3, sys, tempfile, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_stopped_origins as study
from experiments.compare_cnf_stopped_plans import erase
from experiments.cnf_stopped_support import extract,make_open_plan
from experiments.cnf_partial_proof_plan import survival
from experiments.cnf_conditional_unit_support import materialize
from experiments.cnf_archive_parts import restore_archive,split_archive
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
base=study.base
TABLES=study.previous.ALL_TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');q=base.load(out/'comparison-protocol.json')
    parent=study.bound(p['parent']);census=study.bound(q['census']);cases=study.bound(p['cases'])
    sources=q['source_fingerprints']
    for f,h in sources.items():assert base.sha(f)==h,f
    manifests=deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests'])
    mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(160,14522)
    observed=study.bound(census['queries']);expected=study.bound(p['expected'])
    assert len(observed)==len(expected)==len(cases)==72
    for a,b in zip(observed,expected):
        for k in ('case','status','metrics'):assert a[k]==b[k],(a['case'],k)
    report=base.load(out/'comparisons.json')
    assert report['protocol']==study.binding(out/'comparison-protocol.json') and len(report['samples'])==24
    groups={};trials=[]
    for sample in report['samples']:
        r=study.bound(sample);v=study.bound(r['result']);key=(sample['target'],sample['mode'])
        if key not in groups:
            groups[key]=[];trials.append((key,r,v))
        else:
            first,values=groups[key][0]
            for k in ('digest','added'):assert r[k]==first[k],key
            for k in ('status','metrics','extra_counts'):
                assert v['result'].get(k)==values['result'].get(k),key
            assert v['outcome']==values['outcome'],key
        groups[key].append((r,v))
    assert all(len(g)==4 for g in groups.values())
    origin_audits=[];audits=[];added={t:[] for t in TABLES};alternatives=Counter()
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);original=temp/'parent';union=temp/'union'
        restore_archive(parent['reference_union'],original);shutil.copyfile(original,union)
        con=sqlite3.connect(union)
        def merge(path):
            inp=sqlite3.connect(path)
            try:
                present={n for n, in inp.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                with con:
                    for t in TABLES:
                        if t not in present:continue
                        for key,payload in inp.execute(f'SELECT id,payload FROM {t}'):
                            old=con.execute(f'SELECT payload FROM {t} WHERE id=?',(key,)).fetchone()
                            if old is None:
                                con.execute(f'INSERT INTO {t}(id,payload) VALUES (?,?)',(key,payload));added[t].append(key)
                            else:
                                assert json.loads(old[0]).get('answer')==json.loads(payload).get('answer')
                                alternatives[t]+=old[0]!=payload
            finally:inp.close()
        search=temp/'search';restore_archive(census['search_archive'],search)
        ref=temp/'reference';restore_archive(base.load(study.PARENT/'holdout-lazy-0/report.json')['archive'],ref)
        a=sqlite3.connect(search);b=sqlite3.connect(ref)
        try:assert study.tables(a)==study.tables(b)
        finally:a.close();b.close()
        # Each source prefix is audited before its edit. No later repeat may
        # supply a missing endpoint; extraction is reproduced from that prefix.
        conditional=temp/'conditional';restore_archive(census['conditional_archive'],conditional)
        bank=SnapshotResidualSolver(conditional)
        for entry in census['origins']:
            r=study.bound(entry);capture=study.bound(r['capture']);extraction=study.bound(r['extraction'])
            source,names=study.native.normalize(cases[r['origin']]['source'])
            target,target_names=study.native.normalize(cases[r['target']]['source'])
            assert names==target_names and source==tuple(map(tuple,capture['source']))
            path=temp/'prefix';restore_archive(r['prefix_archive'],path)
            reader=SnapshotResidualSolver(path)
            try:
                counts=Counter();actual=extract(source,capture['candidates'],reader,counts)
                assert actual==extraction
                plan=make_open_plan(actual['templates'],node_limit=129,counts=counts)
                assert plan==study.bound(r['plan'])
                assert sum(survival(target,plan,Counter()))==r['surviving_plan_templates']
            finally:reader.close()
            materialized=study.bound(r['materialized'])
            wanted=[i for i,t in enumerate(actual['templates']) if set(map(tuple,t['clauses']))<=set(target)]
            assert [x['template'] for x in materialized]==wanted
            for m in materialized:
                t=actual['templates'][m['template']]
                child=study.native.restrict_scan(target,dict(t['assumptions']),Counter())
                canonical,_=study.native.normalize(child)
                assert m['root']==study.native.token(canonical,Counter())
                assert m['assignment']==t['assumptions'] and m['conditional'] and m['answer'] is False
                assert bank._read(m['root'])['answer'] is False
            # Prefix payloads must be part of the unchanged chronological run.
            a=sqlite3.connect(path);b=sqlite3.connect(search)
            try:
                aa,bb=study.tables(a),study.tables(b)
                for t in TABLES:assert aa[t].items()<=bb[t].items()
            finally:a.close();b.close()
            def closed(node,depth=0):
                if 'leaf' in node:
                    return Fraction(0) if plan['templates'][node['leaf']].get('open') else Fraction(1,2**depth)
                return closed(node['low'],depth+1)+closed(node['high'],depth+1)
            mass=closed(plan['tree'])
            origin_audits.append(dict(origin=r['origin'],templates=len(actual['templates']),counts=dict(counts),
                uniform_assignment_closed_fraction=str(mass),uniform_assignment_closed_mass=float(mass)))
            path.unlink()
        bank.close()
        _,checked=audit(conditional);merge(conditional);audits.append(dict(name='conditional',readers=checked))
        for key,r,v in trials:
            path=temp/'trial';restore_archive(r['archive'],path)
            stored,checked=audit(path)
            assert r['digest']=={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in stored.items()}
            result=v['result'];assert result['metrics'].get('expanded_nodes',0)<=256
            if result['status']=='unresolved':
                assert result['result'] is None and result['metrics']['expanded_nodes']==256
                if v['outcome'] is not None:assert v['outcome']['stopped']
            else:
                root=cases[key[0]]['root'];assert root in stored[TABLES[0]]
                node=json.loads(stored[TABLES[0]][root]);assert result['status']==('sat' if node['answer'] else 'unsat')
                if node['answer']:
                    _,names=study.native.normalize(cases[key[0]]['source'])
                    assert study.native.holds(cases[key[0]]['source'],dict(zip(names,node['model'])))
            if key[1]!='native':
                origin=base.load(out/f'origin-{key[0]-1}/report.json');plan=study.bound(origin['plan'])
                if key[1]=='open':plan=erase(plan)
                target,_=study.native.normalize(cases[key[0]]['source'])
                assert v['outcome']['intact']==survival(target,plan,Counter())
            merge(path);audits.append(dict(name=list(key),readers=checked));path.unlink()
            print('audited',key,flush=True)
        # Incremental preservation: all old six-table bytes remain exactly
        # present. Recheck new authority and its dependency closure in the union.
        con.execute('ATTACH DATABASE ? AS prior',(str(original),))
        for t in TABLES:
            assert con.execute(f'SELECT count(*) FROM prior.{t} p LEFT JOIN main.{t} u ON p.id=u.id WHERE u.id IS NULL OR p.payload!=u.payload').fetchone()[0]==0
        counts={t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES};con.close()
        readers={}
        for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=cls(union);affine=TerminalStore(s);equiv=MultiEquivalenceStore(s);cache=BinaryCoreCache(s)
            try:
                for key in added[TABLES[0]]:assert s._read(key) is not None
                for key in added[TABLES[1]]:assert affine.read(key) is not None
                for t in TABLES[2:5]:
                    for key in added[t]:assert equiv.read(key) is not None
                for key in added[TABLES[-1]]:
                    payload=s.db.execute(f'SELECT payload FROM {TABLES[-1]} WHERE id=?',(key,)).fetchone()[0];cache.verify(key,payload)
                readers[cls.__name__]=dict(s.counts)
            finally:s.close()
        assert base.sha(original)==parent['reference_union']['database_sha256']
        (out/'union').mkdir();single=base.archive(union,out/'union')
        archive=split_archive(single,out/'union-parts') if single['compressed_bytes']>96*1024*1024 else single
        restored=temp/'restored';restore_archive(archive,restored);assert base.sha(restored)==base.sha(union)
        if archive!=single:Path(single['path']).unlink()
    summary={}
    for (target,mode),values in groups.items():
        r,v=values[0];origin=base.load(out/f'origin-{target-1}/report.json')
        summary.setdefault(str(target),{})[mode]=dict(status=v['result']['status'],expanded=v['result']['metrics']['expanded_nodes'],
            support_leaves=v['result'].get('extra_counts',{}).get('partial_support_leaves',0),added=r['added'],
            **{'mean_'+k:sum(a[k] for a,b in values)/4 for k in ('solve_seconds','complete_seconds','cold_seconds')},
            database_bytes=r['archive']['database_bytes'],compressed_bytes=r['archive']['compressed_bytes'],
            source_attempt_seconds=origin['origin_attempt_seconds'],extraction_seconds=origin['extraction_seconds'],
            plan_seconds=origin['plan_seconds'],serialization_seconds=origin['serialization_seconds'])
    base.write(out/'analysis.json',dict(summary=summary,limitations=q['limitations']))
    sources={**sources,'experiments/validate_cnf_stopped_origins.py':base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        stopped_origins=dict(protocol=study.binding(out/'protocol.json'),census=study.binding(out/'census.json'),
            comparisons=study.binding(out/'comparisons.json'),analysis=study.binding(out/'analysis.json')))
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,query_audits=72,comparison_trials=24,distinct_trial_archives=6,
        origin_audits=origin_audits,audits=audits,new_records={t:len(v) for t,v in added.items()},preserved_tables=counts,
        alternative_payload_observations=dict(alternatives),readers=readers,checkpoint=study.binding(out/'checkpoint.json'),
        archive_roundtrip_byte_identical=True,seconds=time.perf_counter()-began,limitations=[
            'Incremental cumulative audit: every earlier payload is byte-identical and every new node and its dependency closure is replayed by both readers. The preceding full-history and 342 partition audits are preserved through verified manifests, not rerun.',
            'Every distinct trial archive and the conditional bank is fully replayed by both native readers. Four repetitions per arm have identical authority digests; alternative valid payloads stay in raw archives.',
            'All checked contexts are conditional. An open plan, an unfinished parent or a budget stop never supplies a whole-input verdict.',
            'No new solver default, efficient arbitrary-CNF partition, optimal support selection or polynomial bound follows from this census.']))
    print(base.encode(dict(passed=True,tables=counts,new_records={t:len(v) for t,v in added.items()},summary=summary)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))

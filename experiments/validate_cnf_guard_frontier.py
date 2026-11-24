#!/usr/bin/env python3
"""Recheck guard-region plans and preserve all compared native acquisitions."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import json,shutil,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_frontier as study
from experiments.cnf_guard_frontier import make_frontier_plan,closed_mass,guard_census
from experiments.cnf_partial_proof_plan import survival
from experiments.compare_cnf_stopped_plans import erase
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_archive_parts import restore_archive,split_archive
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
base=study.base;old=study.study;TABLES=old.previous.ALL_TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    manifests=deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests'])
    mp=study.PARENT/'manifest.json';manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(161,14672)
    cases=old.bound(p['cases']);census=base.load(out/'census.json');plans={};origin_audits=[]
    assert census['protocol']==old.binding(out/'protocol.json') and len(census['origins'])==8
    for entry in census['origins']:
        r=old.bound(entry);origin=r['origin'];prior=base.load(study.PARENT/f'origin-{origin}/report.json')
        ts=old.bound(prior['extraction'])['templates'];source,_=old.native.normalize(cases[origin]['source'])
        target,names=old.native.normalize(cases[origin+1]['source']);assert names==old.native.normalize(cases[origin]['source'])[1]
        for t in ts:assert check_template(t)<=set(source)
        counts=Counter();plan=make_frontier_plan(target,ts,counts=counts)
        assert plan==old.bound(r['plan']) and dict(counts)==r['counts']
        assert r['closed_mass']==str(closed_mass(plan)) and r['guards']==guard_census(ts)
        assert r['old_closed_mass']==str(closed_mass(old.bound(prior['plan'])))
        assert sum(t.get('open') is True for t in plan['templates'])==1
        assert all(survival(target,plan,Counter())[i] for i,t in enumerate(plan['templates']) if not t.get('open'))
        plans[origin+1]=plan;origin_audits.append(r)
    report=base.load(out/'comparisons.json');assert len(report['samples'])==32 and report['protocol']==old.binding(out/'protocol.json')
    groups={};trials=[]
    for sample in report['samples']:
        r=old.bound(sample);v=old.bound(r['result']);key=(sample['target'],sample['mode'])
        if key not in groups:groups[key]=[];trials.append((key,r,v))
        else:
            a,b=groups[key][0]
            for k in ('digest','added'):assert r[k]==a[k],key
            for k in ('status','metrics','extra_counts'):assert v['result'].get(k)==b['result'].get(k),key
            assert v['outcome']==b['outcome'],key
        groups[key].append((r,v))
    assert all(len(g)==4 for g in groups.values())
    for target in p['targets']:
        for mode,previous in (('native','native'),('old','plan')):
            r,v=groups[(target,mode)][0]
            reference=base.load(study.PARENT/f'comparison-{target}-{previous}-0/report.json')
            earlier=old.bound(reference['result'])
            assert r['digest']==reference['digest'] and v['outcome']==earlier['outcome']
            for k in ('status','metrics','extra_counts'):assert v['result'].get(k)==earlier['result'].get(k)
    added={t:[] for t in TABLES};alternatives=Counter();audits=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);original=temp/'parent';union=temp/'union'
        restore_archive(parent['reference_union'],original);shutil.copyfile(original,union);con=sqlite3.connect(union)
        for key,r,v in trials:
            path=temp/'trial';restore_archive(r['archive'],path);stored,checked=audit(path)
            assert r['digest']=={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in stored.items()}
            result=v['result'];assert result['metrics'].get('expanded_nodes',0)<=256
            if result['status']=='unresolved':
                assert result['result'] is None and result['metrics']['expanded_nodes']==256
                if v['outcome'] is not None:assert v['outcome']['stopped']
            else:
                root=cases[key[0]]['root'];assert root in stored[TABLES[0]]
                node=json.loads(stored[TABLES[0]][root]);assert result['status']==('sat' if node['answer'] else 'unsat')
                if node['answer']:
                    _,names=old.native.normalize(cases[key[0]]['source'])
                    assert old.native.holds(cases[key[0]]['source'],dict(zip(names,node['model'])))
            if key[1]!='native':
                plan=plans[key[0]]
                if key[1]=='open':plan=erase(plan)
                elif key[1]=='old':plan=base.load(study.PARENT/f'origin-{key[0]-1}/plan.json')
                target,_=old.native.normalize(cases[key[0]]['source'])
                assert v['outcome']['intact']==survival(target,plan,Counter())
            with con:
                for table,rows in stored.items():
                    for root,payload in rows.items():
                        prior=con.execute(f'SELECT payload FROM {table} WHERE id=?',(root,)).fetchone()
                        if prior is None:
                            con.execute(f'INSERT INTO {table}(id,payload) VALUES (?,?)',(root,payload));added[table].append(root)
                        else:
                            assert json.loads(prior[0]).get('answer')==json.loads(payload).get('answer')
                            alternatives[table]+=prior[0]!=payload
            audits.append(dict(target=key[0],mode=key[1],readers=checked));path.unlink();print('audited',key,flush=True)
        con.execute('ATTACH DATABASE ? AS prior',(str(original),))
        for t in TABLES:
            assert con.execute(f'SELECT count(*) FROM prior.{t} p LEFT JOIN main.{t} u ON p.id=u.id WHERE u.id IS NULL OR p.payload!=u.payload').fetchone()[0]==0
        tables={t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES};con.close()
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
        (out/'union').mkdir();single=base.archive(union,out/'union');archive=split_archive(single,out/'union-parts')
        restored=temp/'restored';restore_archive(archive,restored);assert base.sha(restored)==base.sha(union)
        Path(single['path']).unlink()
    summary={};leaf_costs=[]
    for (target,mode),values in groups.items():
        r,v=values[0];events=[] if v['outcome'] is None else v['outcome']['leaves']
        native_events=[e for e in events if e['route']=='native']
        summary.setdefault(str(target),{})[mode]=dict(status=v['result']['status'],expanded=v['result']['metrics']['expanded_nodes'],
            support_leaves=v['result'].get('extra_counts',{}).get('partial_support_leaves',0),added=r['added'],
            **{'mean_'+k:sum(a[k] for a,b in values)/4 for k in ('solve_seconds','complete_seconds','cold_seconds')},
            database_bytes=r['archive']['database_bytes'],compressed_bytes=r['archive']['compressed_bytes'])
        leaf_costs.append(dict(target=target,mode=mode,native_leaves=native_events,
            largest_leaf_dispatches=max((e['expanded_nodes'] for e in native_events),default=0),
            native_leaf_dispatches=sum(e['expanded_nodes'] for e in native_events)))
    base.write(out/'analysis.json',dict(summary=summary,origins=origin_audits,leaf_costs=leaf_costs,limitations=p['limitations']))
    sources={**p['source_fingerprints'],'experiments/validate_cnf_guard_frontier.py':base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        guard_frontier=dict(protocol=old.binding(out/'protocol.json'),census=old.binding(out/'census.json'),
            comparisons=old.binding(out/'comparisons.json'),analysis=old.binding(out/'analysis.json')))
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,origins_checked=8,comparison_trials=32,distinct_trial_archives=8,
        audits=audits,new_records={t:len(v) for t,v in added.items()},preserved_tables=tables,
        alternative_payload_observations=dict(alternatives),readers=readers,checkpoint=old.binding(out/'checkpoint.json'),
        archive_roundtrip_byte_identical=True,seconds=time.perf_counter()-began,limitations=[
            'Incremental history audit: old six-table payloads remain byte-identical; every new node and its dependency closure is replayed by both readers. Earlier full-history and partition audits remain hash-bound, not rerun.',
            'Both readers fully check every distinct trial archive. Four repetitions per arm retain identical authority digests; raw archives preserve alternative valid proofs.',
            'All source captures and original templates remain in the verified parent. New selection filters support against the current target without discarding old alternatives.',
            'Greater closed assignment mass is not broader SAT-instance coverage, an optimal search order or a uniformly polynomial algorithm.']))
    print(base.encode(dict(passed=True,new_records={t:len(v) for t,v in added.items()},tables=tables,summary=summary)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))

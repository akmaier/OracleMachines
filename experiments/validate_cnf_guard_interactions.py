#!/usr/bin/env python3
"""Verify guard consequences, their native compositions and preserved history."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,shutil,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_guard_interactions as study
from experiments.cnf_guard_interactions import local_hints,inspect,binary_paths
from experiments.cnf_hint_transport import CoreHintStore
from experiments.cnf_guard_probe_census import decode_key
from experiments.cnf_archive_parts import restore_archive,split_archive
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments import cnf_residual_dag as native
base=study.base;old=study.old;TABLES=old.previous.ALL_TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);report=base.load(out/'report.json')
    assert report['protocol']==old.binding(out/'protocol.json')
    manifests=deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests'])
    mp=study.PARENT/'manifest.json';assert old.binding(mp)==p['parent_manifest']
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(165,15566)
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    closures=base.load(out/'closures.json');cp=old.bound(closures['protocol'])
    assert cp['study']==old.binding(out/'report.json') and cp['source']['sha256']==base.sha('experiments/close_cnf_guard_interactions.py')
    total=Counter();counts=Counter();timings=Counter();sat=Counter();selections=[];by_context={};targets=[];expected_hints={}
    cases=old.bound(base.load(study.PARENT/'protocol.json')['cases'])
    for target,binding in zip(p['targets'],report['targets']):
        r=old.bound(binding);assert r['target']==target
        previous=old.bound(r['input']);observed=old.bound(previous['observation']);origin=old.bound(previous['source_report'])
        templates=old.bound(origin['extraction'])['templates'];records=old.bound(r['records']);c=Counter();assert len(records)==len(observed['events'])
        selected=0
        for i,(row,event) in enumerate(zip(records,observed['events'])):
            local,hs,whole=local_hints(observed['source'],templates,event,c);analysis=inspect(local,hs,c)
            assert row['root']==event['root'] and row['event']==i and row['whole']==whole
            assert json.loads(base.encode(hs))==row['hints'] and json.loads(base.encode(analysis))==row['analysis']
            for h in hs:
                key=base.encode([local,h['clause']]);expected_hints[key]=dict(core=local,clause=h['clause'],proof=h['proof'])
            combined=analysis['profiles']['combined'];original=set(analysis['profiles']['original']['clauses'])
            new_binary={tuple(h['clause']) for h in hs if len(h['clause'])==2}-original
            candidates=[lit for lit in analysis['new_candidates'] if any(combined['clauses'][cid] in new_binary for _,cid in combined['paths'][lit])]
            candidates.sort(key=lambda lit:(lit not in analysis['mixed'],lit));assert candidates==row['multi_candidates']
            expected=candidates[:min(p['compile_per_context'],p['compile_per_target']-selected)]
            expected=[lit for lit in expected if len(combined['paths'][lit])<=p['path_limit']]
            assert [v['forced'] for v in row['selected']]==expected;selected+=len(expected)
            for q in row['selected']:
                expected_root=native.token(native.normalize(native.restrict_scan(local,{abs(q['forced']):q['forced']<0},Counter()))[0],Counter())
                assert q['comparison']['compile']['root']==expected_root and q['comparison']['compile']['status']=='unsat'
                assert q['path']==combined['paths'][q['forced']]
                selections.append(dict(target=target,event=i,**q))
            for mode,profile in analysis['profiles'].items():
                # Independently check SCC satisfiability and every reported path.
                graph,names=native.normalize(profile['clauses'])
                if () in graph:assert profile['empty'];continue
                model,proof=native.two_cnf(graph,Counter())
                assert (proof is not None)==bool(profile['contradictory'])
                if model is not None:assert native.holds(graph,model)
                for forced,path in profile['paths'].items():
                    current=-forced
                    for nxt,cid in path:
                        assert profile['clauses'][cid]==tuple(sorted({-current,nxt}));current=nxt
                    assert current==forced
            # Do not call path-set differences new logical backbones on UNSAT
            # graphs: an inconsistent fragment already entails every literal.
            if not combined['contradictory'] and not combined['empty']:
                sat['contexts']+=1;sat['multi_candidates']+=len(candidates);sat['contexts_with_multi_candidates']+=bool(candidates)
                for k in ('guard_composed','mixed','new_candidates'):sat[k]+=len(analysis[k])
            by_context[(target,i)]=row
        assert selected==r['selected'];total.update(r['summary']);counts.update(r['counts']);timings.update(r['timings'])
        targets.append(dict(target=target,family=cases[target]['family'],size=cases[target]['size'],summary=r['summary'],selected=selected))
    assert total['contexts']==648
    chosen=[dict(target=t,event=i) for (t,i),row in by_context.items() if row['analysis']['profiles']['combined']['contradictory']]
    assert cp['chosen']==chosen and [(r['target'],r['event']) for r in closures['records']]==[(r['target'],r['event']) for r in chosen]
    closed={};closure_summary=Counter()
    for r in closures['records']:
        row=by_context[(r['target'],r['event'])];local=decode_key(row['root']);a=row['analysis']
        units=binary_paths(a['profiles']['original']['clauses']+[h['clause'] for h in row['hints'] if len(h['clause'])<=1],Counter())
        assert r['needs_binary_guard']==(not (units['contradictory'] or units['empty']))
        assert r['variable']==min(a['profiles']['combined']['contradictory'])
        assert r['comparison']['compile']['root']==r['root']==row['root']
        closed[r['root']]=r;closure_summary['contexts']+=1;closure_summary['needs_binary_guard']+=r['needs_binary_guard']
        closure_summary['missing_after_native_query']+=not r['present_after_native_query']
    def paired(rows):
        return {mode:dict(cases=len(rows),unresolved=sum(q['comparison'][mode]['status']=='unresolved' for q in rows),
            seconds=sum(q['comparison'][mode]['seconds'] for q in rows),nodes=sum(q['comparison'][mode]['nodes'] for q in rows),
            payload_bytes=sum(q['comparison'][mode]['payload_bytes'] for q in rows)) for mode in ('compile','fresh')}
    added={t:[] for t in TABLES};alternatives=Counter();audits=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);original=temp/'parent';union=temp/'union'
        restore_archive(parent['reference_union'],original);shutil.copyfile(original,union);con=sqlite3.connect(union)
        hints=temp/'hints';restore_archive(report['archives']['hints'],hints);store=CoreHintStore(hints)
        try:
            assert store.audit()==report['hint_audit']==len(expected_hints)
            assert store.storage()==report['hint_storage']
            for h in expected_hints.values():assert store.get(h['core'],h['clause']) is not None
        finally:store.close()
        assert base.sha(hints)==report['archives']['hints']['database_sha256']
        for name,archive in (('selected',report['archives']['native']),('closures',closures['archive'])):
            path=temp/name;restore_archive(archive,path);stored,checked=audit(path)
            required=[q['comparison']['compile']['root'] for q in selections] if name=='selected' else list(closed)
            for key in required:assert key in stored[TABLES[0]] and json.loads(stored[TABLES[0]][key])['answer'] is False
            with con:
                for table,rows in stored.items():
                    for root,payload in rows.items():
                        prior=con.execute(f'SELECT payload FROM {table} WHERE id=?',(root,)).fetchone()
                        if prior is None:con.execute(f'INSERT INTO {table}(id,payload) VALUES (?,?)',(root,payload));added[table].append(root)
                        else:
                            assert json.loads(prior[0]).get('answer')==json.loads(payload).get('answer');alternatives[table]+=prior[0]!=payload
            audits.append(dict(bank=name,readers=checked,nodes=len(stored[TABLES[0]])))
        for target,binding in zip(p['targets'],p['inputs']):
            relevant=[r for r in closures['records'] if r['target']==target]
            if not relevant:continue
            prior=old.bound(binding);path=temp/'prefix';restore_archive(prior['archives']['native'],path);reader=SnapshotResidualSolver(path)
            try:
                for r in relevant:assert (reader._read(r['root']) is not None)==r['present_after_native_query']
            finally:reader.close();path.unlink()
        con.execute('ATTACH DATABASE ? AS prior',(str(original),))
        for t in TABLES:assert con.execute(f'SELECT count(*) FROM prior.{t} p LEFT JOIN main.{t} u ON p.id=u.id WHERE u.id IS NULL OR p.payload!=u.payload').fetchone()[0]==0
        tables={t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES};con.close();readers={}
        for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=cls(union)
            try:
                for key in added[TABLES[0]]:assert s._read(key) is not None
                readers[cls.__name__]=dict(s.counts)
            finally:s.close()
        assert base.sha(original)==parent['reference_union']['database_sha256']
        (out/'union').mkdir();single=base.archive(union,out/'union');archive=split_archive(single,out/'union-parts')
        restored=temp/'restored';restore_archive(archive,restored);assert base.sha(restored)==base.sha(union);Path(single['path']).unlink()
    analysis=dict(summary=dict(total),satisfiable_combined_graphs=dict(sat),counts=dict(counts),timings=dict(timings),targets=targets,
        selected_pairs=paired(selections),closure_pairs=paired(closures['records']),closure_summary=dict(closure_summary),distinct_closed_roots=len(closed),
        study=report,closure_study=closures,limitations=p['limitations']+cp['limitations']+[
            'Mixed/new candidate counts in raw records are path-witness differences. On inconsistent graphs they are not new logical consequences; use the separate satisfiable_combined_graphs census for non-vacuous backbone comparisons.',
            'The preserved six-table cumulative native bank and separate exact-core RUP hint bank have different roles. The latter is not a source verdict; source exclusions and local closures require their compiled native certificates.'])
    base.write(out/'analysis.json',analysis)
    sources={**p['source_fingerprints'],'experiments/close_cnf_guard_interactions.py':base.sha('experiments/close_cnf_guard_interactions.py'),
        'experiments/validate_cnf_guard_interactions.py':base.sha(__file__)}
    checkpoint=deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        guard_interactions=dict(protocol=old.binding(out/'protocol.json'),report=old.binding(out/'report.json'),closures=old.binding(out/'closures.json'),analysis=old.binding(out/'analysis.json')))
    base.write(out/'checkpoint.json',checkpoint)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        contexts_checked=648,hints_checked=len(expected_hints),selected_checked=len(selections),closures_checked=len(closed),
        audits=audits,new_records={t:len(v) for t,v in added.items()},preserved_tables=tables,alternative_payload_observations=dict(alternatives),
        readers=readers,checkpoint=old.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,limitations=analysis['limitations']))
    print(base.encode(dict(passed=True,tables=tables,new_records={t:len(v) for t,v in added.items()},satisfiable_graphs=sat,closures=closure_summary)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))

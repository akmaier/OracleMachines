#!/usr/bin/env python3
"""Audit both authorities, chronological dependencies, exhaustive truth and history."""
from collections import Counter,defaultdict
from pathlib import Path
import copy,json,shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_equivalence as study
from experiments.cnf_binary_equivalence import EquivalenceStore,TABLE,FORMAT
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_affine_negative import TABLE as AFFINE_TABLE
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_cross_family import truth_table
from experiments.cnf_residual_dag import normalize,token
base=study.base;previous=study.previous





def extension_byte_parts(rows):
    totals=Counter()
    for key,payload in rows.items():
        node=json.loads(payload);totals['id_bytes']+=len(key);totals['payload_bytes']+=len(payload)
        for name in ('cnf','evidence','child'):
            totals[name+'_json_bytes']+=len(json.dumps(node[name],sort_keys=True,separators=(',',':')))
    return dict(totals)


def binary_repetition(cases):
    seen={};repeated=[];eligible=0
    for case in cases:
        cnf,_=normalize(case['source']);binary=tuple(c for c in cnf if len(c)==2)
        if not binary or len(binary)==len(cnf) or any(len(c)<2 for c in cnf):continue
        eligible+=1
        if binary in seen:
            repeated.append(dict(case=case['case'],group=case['group'],earlier_case=seen[binary],binary_clauses=len(binary)))
        else:seen[binary]=case['case']
    return dict(eligible=eligible,distinct_binary_keys=len(seen),repeated=repeated,
        limitations='Exact binary clauses in full-source canonical coordinates only; reusable tree indices must be transported back to current full-source clause positions. This census is not an implemented cache or timing gain.')


def quotient_structure(cases,truths,rows):
    """Untimed census of additional disjoint SCC blocks omitted by one-block policy."""
    result=[];available=set()
    for case,truth,row in zip(cases,truths,rows):
        cnf,_=normalize(case['source']);graph={}
        for c in cnf:
            if len(c)==2:
                a,b=c;graph.setdefault(-a,set()).add(b);graph.setdefault(-b,set()).add(a)
        reach={}
        for root in graph:
            seen={root};todo=[root]
            while todo:
                for v in graph.get(todo.pop(),()):
                    if v not in seen:seen.add(v);todo.append(v)
            reach[root]=seen
        groups=set();inconsistent=False
        for root,seen in reach.items():
            if -root in seen and root in reach.get(-root,set()):inconsistent=True;break
            block=tuple(sorted((v for v in seen if root in reach.get(v,{v})),key=abs))
            if len(block)>1 and block[0]>0:groups.add(block)
        if len(groups)>1 and not inconsistent and not any(len(c)<2 for c in cnf):
            mapping={abs(v):block[0]*(1 if v>0 else -1) for block in groups for v in block}
            target,_=normalize([[mapping.get(abs(v),abs(v))*(1 if v>0 else -1) for v in c] for c in cnf])
            assert truth_table(target)['answer']==truth['answer']
            key=token(target,Counter())
            result.append(dict(case=case['case'],group=case['group'],family=case['family'],blocks=[list(b) for b in sorted(groups)],
                variables_before=len({abs(l) for c in cnf for l in c}),variables_after=len({abs(l) for c in target for l in c}),
                literals_before=sum(map(len,cnf)),literals_after=sum(map(len,target)),all_quotient_known_before_query=key in available,
                current_selected=row['result']['metrics'].get('equiv_variables_merged',0)))
        available.update(row['new_native_ids'])
    return result


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases']);report=base.load(out/'report.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    old_validation=base.load(study.PARENT/'validation.json');manifests=dict(old_validation['parent_manifests'])
    path=study.PARENT/'manifest.json';manifests[str(path)]=dict(sha256=base.sha(path),artifacts_checked=len(base.load(path)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];m=base.load(path)['artifacts'];assert len(m)==entry['artifacts_checked']
        for f,h in m.items():assert base.sha(f)==h,f
        artifacts+=len(m)
    assert len(manifests)==108 and artifacts==7608
    truths=[truth_table(c['source']) for c in cases];base.write(out/'truth.json',truths)
    answers=None;by_mode={};records=[];alternatives=[];attribution={};diagnostics=[];audits=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);initial_path=tmp/'initial';base.restore_archive(parent['reference_union'],initial_path);s=SnapshotResidualSolver(initial_path)
        try:initial=study.native_rows(s);affine=dict(s.db.execute(f'SELECT id,payload FROM {AFFINE_TABLE}'));assert not study.extension_rows(s)
        finally:s.close()
        assert len(initial)==28145 and len(affine)==26
        union=dict(initial);extensions={}
        for sample in report['samples']:
            data=study.bound(sample);rows=study.bound(data['queries']);path=tmp/(sample['mode']+str(sample['repeat']));base.restore_archive(data['archive'],path)
            assert len(rows)==68
            s=SnapshotResidualSolver(path);store=EquivalenceStore(s)
            try:
                final=study.native_rows(s);ext=study.extension_rows(s);available=set();ext_available=set();groups=defaultdict(Counter);targets=[]
                for c,r,truth in zip(cases,rows,truths):
                    assert r['case']==c['case'];n=set(r['new_native_ids']);e=set(r['new_extension_ids'])
                    assert len(n)==len(r['new_native_ids']) and len(e)==len(r['new_extension_ids'])
                    assert not n&available and not e&ext_available
                    assert len(n)==r['native_nodes'] and len(e)==r['extension_nodes']
                    assert r['native_payload']==sum(len(k)+len(final[k]) for k in n)
                    assert r['extension_payload']==sum(len(k)+len(ext[k]) for k in e)
                    # All native dependencies must exist by this query, never in
                    # the new extension namespace or in a later query.
                    for k in n:
                        node=json.loads(final[k]);proof=node.get('proof',{})
                        dependencies=[proof[f] for f in ('child','low','high') if f in proof]
                        assert set(dependencies)<=available|n
                    reuse=0;cert_edges=0;merged=0
                    for k in e:
                        node=json.loads(ext[k]);assert node['child'] in available|n
                        reuse+=node['child'] in available
                        cert_edges+=len(node['evidence']['forward'])+len(node['evidence']['backward'])
                        merged+=len(node['evidence']['forward'])
                    available|=n;ext_available|=e
                    rr=r['result'];assert rr['root'] in (ext_available if rr.get('authority')==FORMAT else available)
                    study.check_answer(s,store,c['source'],rr);assert rr['answer']==truth['answer']
                    metrics=rr['metrics'];amount=dict(native_nodes=len(n),extension_nodes=len(e),total_nodes=len(n)+len(e),
                        payload=r['native_payload']+r['extension_payload'],expanded=metrics.get('expanded_nodes',0),
                        propagation=metrics.get('propagation_literal_visits',0),selected=metrics.get('equiv_blocks_found',0),
                        merged=metrics.get('equiv_variables_merged',0),scc_edges=metrics.get('equiv_scc_edge_visits',0),
                        negative_child_reuses=reuse,negative_certificate_edges=cert_edges,negative_merged=merged)
                    groups[c['group']].update(amount);targets.append(dict(case=c['case'],group=c['group'],family=c['family'],**amount))
                assert available==set(final) and ext_available==set(ext)
                got=[r['result']['answer'] for r in rows]
                if answers is None:answers=got
                else:assert answers==got
                state=(final,ext)
                if sample['mode'] in by_mode:assert state==by_mode[sample['mode']]
                else:by_mode[sample['mode']]=state
                if sample['repeat']==0:
                    attribution[sample['mode']]=dict(groups={k:dict(v) for k,v in groups.items()},targets=targets,extension_byte_parts=extension_byte_parts(ext))
                    records.extend(dict(source=c['source'],result={k:r['result'][k] for k in ('answer','model','root')},authority=r['result'].get('authority','native')) for c,r in zip(cases,rows))
            finally:s.close()
            audits.append(study.cold(path,cases,rows))
            for k,v in final.items():
                if k in union and union[k]!=v:
                    assert json.loads(union[k])['answer']==json.loads(v)['answer'];alternatives.append(dict(root=k,archive=data['archive']))
                union.setdefault(k,v)
            for k,v in ext.items():
                if k in extensions:assert extensions[k]==v
                extensions.setdefault(k,v)
        path=tmp/'union';shutil.copyfile(initial_path,path);s=previous.native.ResidualSolver(path)
        try:
            with s.db:
                s.db.execute(f'CREATE TABLE {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
                s.db.executemany(f'INSERT INTO {TABLE} VALUES (?,?)',extensions.items())
            assert study.native_rows(s)==union and dict(s.db.execute(f'SELECT id,payload FROM {AFFINE_TABLE}'))==affine
            _,_,indices,prepared,_=previous.prep.setup(s,base.load(study.PARENT/'protocol.json'))
        finally:s.close()
        assert base.sha(initial_path)==parent['reference_union']['database_sha256']
        # All earlier native/composed/projection/affine history still uses its
        # unchanged authorities; no new native node depends on an extension.
        used=[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS]
        historical=previous.audit_records(path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,used,indices)
        s=SnapshotResidualSolver(path);store=EquivalenceStore(s);terminal=TerminalStore(s)
        try:
            for root in union:assert s._read(root) is not None
            for root in extensions:assert store.read(root) is not None
            for root in affine:assert terminal.read(root) is not None
            for r in records:study.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
            union_check=dict(native=len(s.checked),equivalences=len(store.checked),affine=len(affine),records=len(records))
        finally:s.close()
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
    base.write(out/'decisions.json',records)
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_binary_equivalence.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        binary_equivalence_study=study.binding(out/'report.json'),binary_equivalence_decisions=study.binding(out/'decisions.json'),
        binary_equivalence_solver='experiments.cnf_binary_equivalence.BinaryEquivalenceSolver',binary_equivalence_reader='experiments.cnf_binary_equivalence.EquivalenceStore',
        binary_equivalence_limitations='Top-level empty-archive pilot only; native recursive and prepared production admission integration remain open.')
    base.write(out/'checkpoint.json',checkpoint)
    pairs=[]
    for repeat in range(2):
        a=base.load(out/f'targeted-{repeat}/report.json')['summary'];b=base.load(out/f'quotient-{repeat}/report.json')['summary']
        pairs.append(dict(repeat=repeat,**{k:b[k]-a[k] for k in ('query_seconds','cold_seconds','complete_worker_seconds')}))
    structure=quotient_structure(cases,truths,base.load(out/'quotient-0/queries.json'))
    base.write(out/'attribution.json',dict(modes=attribution,pairs=pairs,multiple_blocks=structure,binary_repetition=binary_repetition(cases),limitations=['Chronological row deltas include differing within-stream reuse; they are not independent marginal costs.',
        'All authorities and source decisions are checked; finite saved/edited inputs are not arbitrary SAT coverage or historical production-prefix evaluation.']))
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        native_preserved=len(initial),native_union=len(union),affine_preserved=len(affine),equivalence_union=len(extensions),
        query_audits=4*len(cases),truth_tables=len(truths),old_records=len(previous.inherited(parent)),new_records=len(records),
        alternate_native_occurrences=alternatives,audits=audits,historical_cold=historical,union_check=union_check,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result)
    print(base.encode({k:result[k] for k in ('passed','native_union','equivalence_union','query_audits','truth_tables','seconds')}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='structure':
        out=Path(sys.argv[2]);a=base.load(out/'attribution.json')
        with tempfile.TemporaryDirectory() as td:
            for mode in study.MODES:
                report=base.load(out/f'{mode}-0/report.json');path=Path(td)/mode;base.restore_archive(report['archive'],path)
                solver=SnapshotResidualSolver(path)
                try:a['modes'][mode]['extension_byte_parts']=extension_byte_parts(study.extension_rows(solver))
                finally:solver.close()
        a['binary_repetition']=binary_repetition(base.load(out/'cases.json'))
        a['multiple_blocks']=quotient_structure(base.load(out/'cases.json'),base.load(out/'truth.json'),base.load(out/'quotient-0/queries.json'))
        base.write(out/'attribution.json',a);print(base.encode(a['multiple_blocks']),flush=True)
    else:validate(Path(sys.argv[1]))

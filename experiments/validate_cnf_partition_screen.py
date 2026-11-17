#!/usr/bin/env python3
"""Independent bounded-plan reconstruction, fresh exclusions and proof replay."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_screen as study
from experiments.cnf_clause_deletion_guard import clause_set,check_guard,ExtensionBank
from experiments.cnf_residual_dag import propagate,restrict
from experiments.validate_cnf_premise_guard import expected_choice
from experiments.validate_cnf_terminal_guard import check_selection
from experiments.validate_cnf_guard_chain import independent_chain
from experiments.validate_cnf_clause_partition import independent as independent_partition
from experiments.cnf_snapshot_replay import audit,SnapshotResidualSolver
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
from experiments.validate_cnf_unsat_support import bound
base=study.base


def expected_screen(s,target,cores,available,p):
    # Direct set scan and branch construction: no selector/postings/branch helper.
    trace=dict(attempts=[],selected=None,core_checks=[])
    if not p['plan_limit'] or not p['core_read_limit']:return None,trace
    def probe(source):
        cnf,_,key=s._canonical(source);fixed,units,conflict=propagate(cnf,Counter());residual=() if conflict is not None else restrict(cnf,fixed)
        return dict(root=key,trace=units,conflict=conflict,residual_literals=sum(map(len,residual)))
    members=clause_set(target,Counter());variables={abs(l) for c in members for l in c};candidates=[]
    for i,core in enumerate(cores):
        wanted=clause_set(core['source'],Counter());missing=wanted-members
        if wanted&members and 2<=len(missing)<=3:candidates.append((len(missing),i,missing))
    baseline=probe(target);trace['baseline']=baseline;reads=0;plans=0;best=None;score=None
    for _,i,missing in sorted(candidates):
        missing=[list(c) for c in sorted(missing)]
        if any(not c for c in missing) or not {abs(l) for c in missing for l in c}<=variables:continue
        if reads>=p['core_read_limit'] or plans>=p['plan_limit']:break
        cnf,_,root=s._canonical(cores[i]['source']);assert root==cores[i]['root'];reads+=1;ready=base.key_sha(root) in available;trace['core_checks'].append(dict(core=i,ready=ready))
        if not ready:continue
        assert s._read(root,cnf)['answer'] is False
        for order in ('forward','reverse'):
            if plans>=p['plan_limit']:break
            ordered=missing if order=='forward' else list(reversed(missing));prefix=[list(c) for c in target];screens=[]
            for clause in ordered:
                screens.append(probe(restrict(prefix,{abs(l):l<0 for l in clause})));prefix.append(clause)
            plans+=1;terminal=sum(x['conflict'] is not None for x in screens);remaining=len(screens)-terminal;literals=sum(x['residual_literals'] for x in screens)
            admitted=remaining==0 or (terminal>=2 and remaining==1 and literals<baseline['residual_literals'])
            entry=dict(core=i,order=order,missing=ordered,branches=screens,terminal=terminal,remaining=remaining,residual_literals=literals,admitted=admitted);trace['attempts'].append(entry)
            candidate=(remaining,literals,len(screens),i,order)
            if admitted and (score is None or candidate<score):score=candidate;best=entry;trace['selected']=len(trace['attempts'])-1
    return best,trace


def check_composed(s,r):
    got=(study.check_partition if r['format']==study.PARTITION_FORMAT else study.check_chain)(s,r)
    assert got==(independent_partition if r['format']==study.PARTITION_FORMAT else independent_chain)(s,r)
    return got


def validate(out):
    start=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);catalog=bound(report['cases']);parent=bound(p['parent'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    ordinary=sum((bound(parent[f]) for f in study.FIELDS),[]);old=study.inherited(parent);assert bound(p['previous_decisions'])==study.exclusions(parent)
    bindings=dict(legacy=p['support_index'],causal=p['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=study.previous.ordinary.compose(indices,bindings);cores=prepared['cores'];used=[(n,bound(parent[n])) for n in study.OLD_FIELDS]
    assert [(e['repeat'],e['mode']) for e in report['samples']]==[(i,m) for i,order in enumerate(p['orders']) for m in order]
    answers=None;by_mode={};audits=[];decisions=None;alternates=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);base.restore_archive(parent['reference_union'],tmp/'initial');s=study.ResidualSolver(tmp/'initial')
        try:
            initial=study.rows(s);assert study.previous.ordinary.eager.previous.inputs(s,p)==catalog
            keys={s._canonical(c['source'])[2] for c in catalog['cases']};assert len(keys)==192 and not keys&set(initial) and not keys&{r['query_root'] for r in ordinary+old}
        finally:s.close()
        union=dict(initial)
        for num,entry in enumerate(report['samples']):
            data=bound(entry);mode=entry['mode'];records=bound(data['queries']);warm=bound(data['warm']);path=tmp/f'trial-{num}';base.restore_archive(data['archive'],path);s=SnapshotResidualSolver(path)
            try:
                final=study.rows(s);assert initial.items()<=final.items();available=set(map(base.key_sha,initial));by_hash={base.key_sha(k):k for k in final};assert len(by_hash)==len(final)
                assert data['summary']['row_digest']==base.key_sha(base.encode(sorted(final.items()))) and len(records)==len(warm)==192
                extensions=ExtensionBank(bound(p['bank_catalog'])['bank'])
                with patch.object(s,'_expand',side_effect=AssertionError('Validation search')),patch.object(s,'_store',side_effect=AssertionError('Validation publication')):
                    for row,case,w in zip(records,catalog['cases'],warm):
                        r=row['record'];assert row['case']==case['case']==w['case'] and row['template_case']==case['template_case'] and r['source']==case['source']
                        ids=row['new_ids'];assert len(ids)==row['new_nodes']==len(set(ids)) and not available.intersection(ids) and set(row['early_ids'])<=set(ids)
                        normal=dict(row['ordinary'],new_ids=ids);assert normal['source']==case['source'];check_selection(s,extensions,normal,prepared,available,'ready',p['alternative_budget'])
                        guards=[] if normal['guard'] is None else [normal['guard']];target=case['source'] if not guards else check_guard(s,case['source'],guards[0])[1]
                        current=available|set(row['early_ids']);key=s._canonical(target)[2];members=clause_set(target,Counter())
                        eligible=bool(guards) and base.key_sha(key) not in current and not any(clause_set(c['source'],Counter())<=members for c in cores);assert eligible==row['eligible']
                        choice=expected_choice(s,target,cores,current,'premise-first') if eligible else None;assert choice==row['choice']
                        if choice:
                            extra=r['guards'][-1];assert extra['stronger']==[list(c) for c in target]+[choice['missing_clause']] and extra['removed_clause']==choice['missing_clause'];guards.append(extra)
                            assert choice['inserted']==(base.key_sha(extra['stronger_root']) not in current)
                        assert guards==r['guards'];plan=None;trace=None
                        if eligible and choice is None and mode=='screened':plan,trace=expected_screen(s,target,cores,current,p)
                        assert plan==row['plan'] and trace==row['screen']
                        if plan:
                            assert r['format']==study.PARTITION_FORMAT and r['missing_clauses']==plan['missing'] and row['premise_inserted']==(base.key_sha(r['stronger_root']) not in current)
                            expected_children=r['children']
                        else:assert r['format']!=study.PARTITION_FORMAT and not row['premise_inserted'];expected_children=[r['child']]
                        assert len(row['children'])==len(expected_children)
                        for actual,expected in zip(row['children'],expected_children):assert all(actual[k]==expected[k] for k in ('root','answer','model'))
                        got=check_composed(s,r);assert base.load_json(base.encode(got))==w['result'];available.update(ids)
                assert available==set(by_hash);summary=data['summary'];assert summary['new_nodes']==len(final)-len(initial)==sum(r['new_nodes'] for r in records)
                assert summary['new_payload_units']==sum(len(k)+len(v) for k,v in final.items() if k not in initial)
                for field,metric in [('expanded_nodes','expanded_nodes'),('trace_publications','screen_trace_publications'),('traces_reused','screen_traces_reused')]:assert summary[field]==sum(c['metrics'].get(metric,0) for r in records for c in r['children'])
                assert summary['partitions']==sum(r['plan'] is not None for r in records)
                truth=[r['record']['answer'] for r in records]
                if answers is None:answers=truth
                else:assert answers==truth
                if mode in by_mode:assert final==by_mode[mode]
                else:by_mode[mode]=final
                if mode=='screened' and decisions is None:decisions=[r['record'] for r in records]
            finally:s.close()
            cold=study.audit_records(path,[r['record'] for r in records]+old,prepared,used,indices);assert cold['native']['lineage']==data['cold']['native']['lineage'];audits.append(dict(mode=mode,repeat=entry['repeat'],cold=cold))
            for k,v in final.items():
                if k in union and union[k]!=v:assert base.load_json(union[k])['answer']==base.load_json(v)['answer'];alternates.append(dict(root_sha256=base.key_sha(k),archive=data['archive']))
                union.setdefault(k,v)
        base.restore_archive(parent['reference_union'],tmp/'union');s=study.ResidualSolver(tmp/'union');direct=[];rebuilt=[]
        try:
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
            assert study.rows(s)==union;s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Union search')),patch.object(s,'_store',side_effect=AssertionError('Union publication')):
                for r in decisions:
                    target=r['source']
                    for g in r['guards']:_,target=check_guard(s,target,g)
                    if r['format']==study.PARTITION_FORMAT:
                        prefix=[list(c) for c in target];children=[]
                        for clause in r['missing_clauses']:
                            child=s.solve(restrict(prefix,{abs(l):l<0 for l in clause}));children.append(child);prefix.append(clause)
                            if child['answer']:break
                        rebuilt.append(study.partition_record(s,r['source'],r['guards'],r['missing_clauses'],r['stronger_root'],children))
                    else:rebuilt.append(study.chain_record(s,r['source'],r['guards'],s.solve(target)))
                for r in old+rebuilt:check_composed(s,r)
                original=base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions']):
                    source=d['source'] if 'source' in d else original[d['case']]['source'];child=s.solve(source);assert child['root']==d['root'] and child['answer']==d['answer'] and child['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                    direct.append(dict(source=source,guard=None,witness=None,child=child,answer=child['answer'],model=child['model']))
        finally:s.close()
        inherited_audit=audit(tmp/'union',direct+ordinary);composed_audit=study.audit_records(tmp/'union',old+rebuilt,prepared,used,indices);dest=out/'reference-union';dest.mkdir();archive=base.archive(tmp/'union',dest);base.write(out/'union-decisions.json',rebuilt)
        checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=p['source_fingerprints'],partition_screen_study=study.binding(out/'report.json'),partition_screen_decisions=study.binding(out/'union-decisions.json'));base.write(out/'checkpoint.json',checkpoint)
        _,old_structural=restore_checkpoint(p['parent']['path'],tmp/'old-patterns');_,structural=restore_checkpoint(out/'checkpoint.json',tmp/'patterns');assert structural==old_structural;supplemental=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,protocol=report['protocol'],report=study.binding(out/'report.json'),checkpoint=study.binding(out/'checkpoint.json'),audits=audits,preserved_keys=len(initial),union_keys=len(union),new_keys=len(union)-len(initial),alternate_certificate_occurrences=alternates,
        inherited_decisions=len(direct)+len(ordinary),inherited_composed=len(old),new_composed=len(rebuilt),inherited_audit=inherited_audit,composed_audit=composed_audit,structural=structural,supplemental=supplemental,seconds=time.perf_counter()-start)
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','preserved_keys','union_keys','new_keys','inherited_decisions','inherited_composed','new_composed','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))

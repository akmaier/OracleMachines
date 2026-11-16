#!/usr/bin/env python3
"""Replay matched-history join transfer and preserve every result in a union."""
from collections import Counter
import copy
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_join_transfer as study
from experiments.compare_cnf_scoped_refinement import audit as frozen_audit
from experiments.cnf_query_checkpoint import check_query
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_join_workloads import check_image, parent_case
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments import compare_cnf_nested_refinement as nested
base=study.base


def bound(entry):
    assert base.sha(entry['path'])==entry['sha256'],entry['path']
    return base.load(entry['path'])


def semantic_audit(result):
    return {k:v for k,v in result.items() if k not in ('seconds','canonical','normalization_counts')}


def validate(out):
    started=time.perf_counter();protocol=base.load(out/'protocol.json');report=base.load(out/'report.json')
    assert report['protocol_sha256']==base.sha(out/'protocol.json');seed=bound(report['seed']);cases=bound(seed['cases'])
    for p,d in protocol['source_fingerprints'].items():assert base.sha(p)==d,p
    for field in ('checkpoint','control','join_anchors','join_proof','queries'):bound(protocol[field])
    joins=bound(protocol['join_anchors']);join_proof=bound(protocol['join_proof']);audits=[];comparisons={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);current,current_check=restore_checkpoint(protocol['checkpoint']['path'],tmp/'current')
        control,control_check=restore_checkpoint(protocol['control']['path'],tmp/'control')
        h=base.CompleteAdmissionInventory(tmp/'current',**protocol['options']);h.set_admission_budget(0)
        try:
            authority=base.rows(h);authority_pairs=study.pairs(h);union=dict(authority);union_pairs=dict(authority_pairs)
            observed=set()
            with base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('validator acquisition')):
                ordered=sorted(joins,key=lambda a:a['shape']['variables'])
                for case in cases:
                    anchor=next(a for a in ordered if a['source']==case['anchor'])
                    generated=parent_case(base.load_json(anchor['source'])[-1],case['split_clause'],case['variant'],edited=case['edited'])
                    assert generated['source']==case['source'] and generated['witness_variable']==case['witness_variable']
                    assert h._canonical(case['source'],0)[2]==case['root'] and case['root'] not in authority and case['root'] not in observed
                    observed.add(case['root']);check_image(h,case['source'],case['witness_variable'],case['image'])
                    assert (case['image']==case['anchor']) is (not case['edited'])
                    if case['edited']:
                        try:check_image(h,case['source'],case['witness_variable'],case['anchor'])
                        except ValueError:pass
                        else:raise AssertionError('Invalid image was accepted')
        finally:h.close()
        seed_rows={};seed_pairs={}
        for mode in study.MODES:
            path=tmp/f'seed-{mode}';base.restore_archive(seed['seeds'][mode]['archive'],path)
            cold=frozen_audit(path,protocol);assert semantic_audit(cold)==semantic_audit(seed['seeds'][mode]['cold'])
            h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
            try:seed_rows[mode]=base.rows(h);seed_pairs[mode]=study.pairs(h)
            finally:h.close()
        assert seed_rows['base'].items()<=seed_rows['joins'].items() and seed_pairs['base'].items()<=seed_pairs['joins'].items()
        assert set(seed_rows['joins'])-set(seed_rows['base'])=={s['source'] for s in join_proof['steps']}-set(seed_rows['base'])
        assert set(seed_pairs['joins'])-set(seed_pairs['base'])=={s['rule']['id'] for s in join_proof['steps'] if s['rule']['kind']==base.split.KIND}-set(seed_pairs['base'])
        for sample in report['samples']:
            data=bound(sample);mode=sample['mode'];repeat=sample['repeat'];path=tmp/f'{mode}-{repeat}'
            base.restore_archive(data['archive'],path);cold=frozen_audit(path,protocol)
            assert semantic_audit(cold)==semantic_audit(data['cold'])
            h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
            try:
                saved=base.rows(h);records=study.pairs(h)
                assert seed_rows[mode].items()<=saved.items() and seed_pairs[mode].items()<=records.items()
                assert base.key_sha(base.encode(sorted(saved.items())))==data['summary']['pattern_digest']
                assert base.key_sha(base.encode(sorted(records.items())))==data['summary']['pair_digest']
                stored=[];query_checks=0
                for index,row in enumerate(data['records']):
                    case=cases[index%len(cases)];assert row['case']==case['case'] and row['visit']==index//len(cases)
                    assert row['root']==case['root'] and (row['visit']!=0 or not row['present_before'])
                    assert row['prefix']['entered']==len(set(row['prefix']['admitted_ids']))<=protocol['prefix_limit']
                    assert len(row['batches'])<=protocol['max_batches']
                    for b in row['batches']:
                        assert b['entered']==len(set(b['admitted_ids']))<=protocol['state_limit']
                        assert len(b['operations'])<=protocol['pair_limit']
                        assert b['selection_counts'].get('bootstrap_fresh_assumptions',0)<=2*protocol['pair_limit']
                    assert row['entered']==row['prefix']['entered']+sum(b['entered'] for b in row['batches'])
                    assert row['probes']==row['prefix']['probes']+sum(b['probes'] for b in row['batches'])
                    admitted=set(row['prefix']['admitted_ids'])|{k for b in row['batches'] for k in b['admitted_ids']}
                    assert row['stored']==len(set(row['stored_ids'])) and set(row['stored_ids'])<=admitted
                    stored.extend(row['stored_ids'])
                    if row['query_check'] is not None:
                        checked=check_query(path,protocol['options'],case['source'],row['root'],row['proof'],row['closed'])
                        assert {k:v for k,v in checked.items() if k!='seconds'}=={k:v for k,v in row['query_check'].items() if k!='seconds'}
                        query_checks+=1
                    else:assert not row['closed'] and not row['proof']['steps']
                assert len(stored)==len(set(stored)) and set(stored)==set(map(base.key_sha,set(saved)-set(seed_rows[mode])))
                for k,v in saved.items():assert k not in union or union[k]==v;union[k]=v
                for k,v in records.items():assert k not in union_pairs or union_pairs[k]==v;union_pairs[k]=v
            finally:h.close();assert base.sha(path)==data['archive']['database_sha256']
            deterministic=[]
            for row in data['records']:
                row=copy.deepcopy(row);row.pop('solve_and_bookkeeping_seconds');row['prefix'].pop('seconds')
                if row['query_check']:row['query_check'].pop('seconds')
                for b in row['batches']:b.pop('seconds')
                deterministic.append(row)
            comparisons[(mode,repeat)]=(deterministic,data['archive']['database_sha256'])
            audits.append(dict(mode=mode,repeat=repeat,patterns=len(saved),pairs=len(records),new_queries_checked=query_checks,
                original_bindings=cold['original_bindings'],original_covered=cold['coverage']['covered'],no_acquisition=True))
        for mode in study.MODES:assert comparisons[(mode,0)]==comparisons[(mode,1)]
        path=tmp/'union';base.restore_archive(current['archive'],path);h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        try:
            with h.db:
                h.db.executemany('INSERT INTO cnf_patterns_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in authority])
                h.db.executemany(f'INSERT INTO {base.split.TABLE} VALUES (?,?)',[(k,v) for k,v in union_pairs.items() if k not in authority_pairs])
            evidence=[base.load_json(p) for p in union_pairs.values()];routes=base.routes_for(h,evidence)
            old_queries=base.load(current['queries']['path']);coverage=nested.all_coverage(h,routes,old_queries)
            base.split.verify_positive(h,coverage['proof'],coverage['roots'],evidence,Counter())
            queries=copy.deepcopy(old_queries)
            for q,depth in zip(queries,coverage['selected_depths'],strict=True):
                q['selected_depth']=depth;q['closed_by_depth']=[h._load(k) is not None and base.compose(h,[k],routes,Counter())[0][0] for k in q['roots']]
            pending=[dict(source=r['source'],variable=r['variable'],value=v,target=b['edge']['key']) for r in evidence for v,b in zip((False,True),r['branches']) if h._load(b['edge']['key']) is None]
            extra=[];extra_roots=[]
            for case in cases:
                present=h._load(case['root']) is not None
                closed=present and base.compose(h,[case['root']],routes,Counter())[0][0]
                extra.append(dict(case=case['case'],source=case['source'],root=case['root'],closed=closed))
                if closed:extra_roots.append(case['root'])
            flags,plan=base.compose(h,extra_roots,routes,Counter());assert all(flags)
            extra_proof=base.expand(h,plan,extra_roots,routes,Counter());base.split.verify_positive(h,extra_proof,extra_roots,evidence,Counter())
        finally:h.close()
        for name,value in [('queries',queries),('proof',coverage['proof']),('pending',pending),('transfer-queries',extra),('transfer-proof',extra_proof)]:base.write(out/f'{name}.json',value)
        old_protocol=base.load(current['protocol']['path'])
        base.write(out/'checkpoint-protocol.json',dict(options=protocol['options'],cases=old_protocol['cases'],parent_protocol=current['protocol'],continuation_protocol=study.binding(out/'protocol.json')))
        dest=out/'union';dest.mkdir();archive=base.archive(path,dest)
        cp=dict(format='bootstrap-coverage-union-v1',source_fingerprints=protocol['source_fingerprints'],archive=archive,
            roots=coverage['roots'],coverage=coverage['covered'],uncovered_originals=[q['case'] for q in queries if q['selected_depth'] is None],
            initial_patterns=len(authority),new_patterns=len(union)-len(authority),patterns=len(union),pairs=len(union_pairs),
            report=study.binding(out/'report.json'),protocol=study.binding(out/'checkpoint-protocol.json'),queries=study.binding(out/'queries.json'),
            proof=study.binding(out/'proof.json'),pending=study.binding(out/'pending.json'),
            supplemental_queries=study.binding(out/'transfer-queries.json'),supplemental_proof=study.binding(out/'transfer-proof.json'))
        base.write(out/'checkpoint.json',cp);_,union_check=restore_checkpoint(out/'checkpoint.json',tmp/'cold-union')
        pointer=base.load(study.PARENT/'next-discovery.json')
        assert pointer['case'] in cp['uncovered_originals'],'Update the discovery pointer if the old target closed'
        pointer['checkpoint']=study.binding(out/'checkpoint.json')
        h=base.CompleteAdmissionInventory(tmp/'cold-union',**protocol['options']);h.set_admission_budget(0)
        try:
            routes=base.routes_for(h,evidence)
            for record in pointer['prior_pairs']:
                for branch in record['branches']:
                    child=h._load(branch['child']);branch['present']=child is not None
                    branch['closed']=child is not None and base.compose(h,[branch['child']],routes,Counter())[0][0]
            pointer['root_presence']=[h._load(k) is not None for k in queries[pointer['case']]['roots']]
        finally:h.close();assert base.sha(tmp/'cold-union')==archive['database_sha256']
        base.write(out/'next-discovery.json',pointer)
    result=dict(passed=True,checkpoint_sha256=base.sha(out/'checkpoint.json'),report_sha256=base.sha(out/'report.json'),
        parent_check=current_check,control_check=control_check,archives=audits,union_check=union_check,
        supplemental_covered=len(extra_roots),supplemental_queries=len(cases),supplemental_positive_steps=len(extra_proof['steps']),
        identical_within_mode_repetitions=True,exact_seed_delta=True,absent_original_roots=True,negative_images_rejected=True,
        no_acquisition=True,seconds=time.perf_counter()-started,validator_sha256=base.sha(__file__))
    base.write(out/'reconstruction.json',result);print(base.encode(result))


if __name__=='__main__':validate(Path(sys.argv[1]))

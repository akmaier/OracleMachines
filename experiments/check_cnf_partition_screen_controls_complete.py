#!/usr/bin/env python3
"""Historical-prefix controls for the frozen bounded-screen policy (post hoc)."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_screen as study
from experiments.validate_cnf_partition_screen import expected_screen,check_composed
from experiments.cnf_partition_screen import PartitionScreen,publish_screened_branch
from experiments.validate_cnf_unsat_support import bound
base=study.base


def run(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');hp=base.load('experiments/results/cnf-premise-guard/protocol.json');authority=bound(hp['parent']);trial=base.load('experiments/results/cnf-premise-guard/premise-first-0/report.json');records=bound(trial['queries']);results=[]
    dest=out/'historical-controls-complete';dest.mkdir();base.write(dest/'protocol.json',dict(historical_protocol=study.binding('experiments/results/cnf-premise-guard/protocol.json'),historical_trial=study.binding('experiments/results/cnf-premise-guard/premise-first-0/report.json'),policy=study.binding(out/'protocol.json'),sources={__file__:base.sha(__file__)},cases=[6,68,135],limitation='Post-hoc historical controls, exact prefixes, single sample per arm. Not fresh generalization or stable timing evidence.'))
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');union=read(base.load(out/'checkpoint.json')['reference_union'],'union');prefixes=study.partition_study.prefixes(initial,final,records)
        for cid in (6,68,135):
            before=prefixes[cid];old=next(r for r in records if r['case']==cid)
            for mode in study.MODES:
                tick=time.perf_counter();path=tmp/f'{cid}-{mode}';shutil.copyfile(tmp/'initial',path);s=study.previous.ordinary.AccountedResidualSolver(path)
                with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in before.items() if k not in initial])
                try:
                    phase=time.perf_counter();target,guard,indices,prepared,normal_counts,near_counts=study.partition_study.prepare(s,hp,old);preparation_seconds=time.perf_counter()-phase;assert study.rows(s)==before
                    plan=None;trace=None;screen_counts={};screen_solver_counts={};setup_seconds=0.;screen_seconds=0.
                    if mode=='screened':
                        phase=time.perf_counter();screen=PartitionScreen(prepared['cores'],p['plan_limit'],p['core_read_limit']);setup_seconds=time.perf_counter()-phase;counts=Counter(s.counts);phase=time.perf_counter()
                        with patch.object(s,'_expand',side_effect=AssertionError('Screen search')),patch.object(s,'_store',side_effect=AssertionError('Screen publication')):plan,trace=screen.select(s,target)
                        screen_seconds=time.perf_counter()-phase;screen_counts=dict(screen.counts);screen_solver_counts=dict(s.counts-counts)
                        assert (plan,trace)==expected_screen(s,target,prepared['cores'],set(map(base.key_sha,before)),p)
                    premise_counts=Counter();premise_solver_counts={};premise_inserted=False;premise_seconds=0.;construction_counts=Counter();construction_seconds=0.;children=[]
                    if plan is None:children=[s.solve(target)]
                    else:
                        phase=time.perf_counter();counts=Counter(s.counts)
                        with patch.object(s,'_expand',side_effect=AssertionError('Premise search')):premise_inserted,root=study.publish_premise(s,target,prepared['cores'][plan['core']],plan['missing'],premise_counts)
                        premise_seconds=time.perf_counter()-phase;premise_solver_counts=dict(s.counts-counts);phase=time.perf_counter();branches=study.branch_sources(target,plan['missing'],construction_counts)[1];construction_seconds=time.perf_counter()-phase
                        for (_,_,source),saved in zip(branches,plan['branches']):
                            child=publish_screened_branch(s,source,saved);children.append(child)
                            if child['answer']:break
                    phase=time.perf_counter();r=study.chain_record(s,old['chain']['source'],[guard],children[0]) if plan is None else study.partition_record(s,old['chain']['source'],[guard],plan['missing'],root,children);composition_seconds=time.perf_counter()-phase
                    with patch.object(s,'_expand',side_effect=AssertionError('Control verification search')),patch.object(s,'_store',side_effect=AssertionError('Control verification publication')):
                        check_composed(s,r);phase=time.perf_counter();bank=study.banks(s,[r]);warm_setup_seconds=time.perf_counter()-phase;phase=time.perf_counter();warm=study.lookup(bank,r['source']);warm_seconds=time.perf_counter()-phase;assert warm['answer']==r['answer']==old['chain']['answer']
                    after=study.rows(s);assert before.items()<=after.items();delta=[(k,v) for k,v in after.items() if k not in before]
                    if mode=='single':assert set(map(base.key_sha,dict(delta)))==set(old['new_ids']) and all(final[k]==v for k,v in delta)
                    new_keys=[base.key_sha(k) for k,v in delta if k not in union]
                    alternatives=[base.key_sha(k) for k,v in delta if k in union and union[k]!=v]
                finally:s.close()
                arm=dest/f'{cid}-{mode}';arm.mkdir();phase=time.perf_counter();base.write(arm/'delta.json',delta);base.write(arm/'records.json',[r]);serialization_seconds=time.perf_counter()-phase
                catalogs=[(n,bound(authority[n])) for n in study.OLD_FIELDS];cold=study.audit_records(path,[r],prepared,catalogs,indices);metrics=Counter()
                for child in children:metrics.update(child['metrics'])
                result=dict(case=cid,mode=mode,plan=plan,screen=trace,prefix_nodes=len(before),prefix_digest=base.key_sha(base.encode(sorted(before.items()))),delta=study.binding(arm/'delta.json'),records=study.binding(arm/'records.json'),
                    new_nodes=len(delta),new_payload_units=sum(len(k)+len(v) for k,v in delta),retained_bytes=(arm/'delta.json').stat().st_size+(arm/'records.json').stat().st_size,expanded_nodes=metrics['expanded_nodes'],trace_publications=metrics['screen_trace_publications'],premise_inserted=premise_inserted,children=children,screen_counts=screen_counts,screen_solver_counts=screen_solver_counts,normal_counts=normal_counts,near_counts=near_counts,premise_counts=dict(premise_counts),premise_solver_counts=premise_solver_counts,construction_counts=dict(construction_counts),
                    preparation_seconds=preparation_seconds,screen_setup_seconds=setup_seconds,screen_seconds=screen_seconds,premise_seconds=premise_seconds,construction_seconds=construction_seconds,composition_seconds=composition_seconds,warm_setup_seconds=warm_setup_seconds,warm_seconds=warm_seconds,serialization_seconds=serialization_seconds,cold=cold,alternate_payloads=alternatives,keys_missing_from_fresh_union=new_keys,seconds=time.perf_counter()-tick)
                base.write(arm/'report.json',result);results.append(study.binding(arm/'report.json'));print(base.encode({k:result[k] for k in ('case','mode','expanded_nodes','trace_publications','new_nodes','new_payload_units')}),flush=True)
    base.write(out/'historical-controls.json',dict(passed=True,protocol=study.binding(dest/'protocol.json'),samples=results,seconds=time.perf_counter()-start))


if __name__=='__main__':run(Path(sys.argv[1]))

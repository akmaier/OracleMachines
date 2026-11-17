#!/usr/bin/env python3
"""Matched exact-prefix regression and nonterminal controls for terminal-first reuse."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_screen as previous
from experiments.cnf_partition_screen import PartitionScreen,publish_screened_branch
from experiments.cnf_terminal_first_screen import TerminalFirstScreen
from experiments.validate_cnf_unsat_support import bound
base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver;FIELDS=previous.FIELDS;OLD_FIELDS=previous.OLD_FIELDS
PARENT=Path('experiments/results/cnf-partition-screen')
FILES=('experiments/cnf_terminal_first_screen.py','solver/test_cnf_terminal_first_screen.py','experiments/compare_cnf_terminal_first.py','experiments/validate_cnf_terminal_first.py')
MODES=('screened','terminal-first')


def inherited(parent):
    return previous.inherited(parent)+bound(parent['partition_screen_decisions'])+bound(parent['partition_screen_control_decisions'])


def prepare(s,p,row):
    bank,extensions,indices,prepared,cofactors=previous.previous.setup(s,p);selector=previous.previous.ordinary.AlternativeGuardSelector(p['alternative_budget']);record=row.get('record',row.get('chain'));source=record['source']
    target,normal,normal_counts=previous.previous.prepare(s,source,p,bank,extensions,cofactors,selector);assert normal==row['ordinary']
    assert normal['guard'] is not None and not normal['target_known'] and normal['cofactor'] is None
    near=previous.PremiseGuardSelector(prepared['cores']);choice,guard,child=near.select(s,target);assert choice is None and guard is None and child==target
    return target,normal['guard'],indices,prepared,dict(normal_counts),dict(near.counts)


def run(out):
    out.mkdir(exist_ok=False);start=time.perf_counter();sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    p=dict(parent=binding(PARENT/'expanded-checkpoint.json'),source_fingerprints=sources,plan_limit=4,core_read_limit=8,
        cohorts=[dict(name='older',protocol=binding('experiments/results/cnf-premise-guard/protocol.json'),trial=binding('experiments/results/cnf-premise-guard/premise-first-0/report.json'),cases=[6,68,135]),
                 dict(name='regression',protocol=binding(PARENT/'protocol.json'),trial=binding(PARENT/'single-0/report.json'),cases=[176])],modes=MODES,
        limitations=['Eight historical exact-prefix arms, one sample each: regression case 176 and nonterminal controls 6/68/135. This is a targeted correction, not a new excluded-input evaluation or stable time/RSS comparison.',
            'Both arms repeat ordinary preparation and the failed extra-guard selector, including prepared core index setup. Terminal-first checks the unsplit target before posting visits/core proof reads/branch construction; a conflict publishes the retained trace once through the frozen native verifier. Nonterminal plans retain the prior policy and do not repeat baseline propagation.',
            'Every selected proof, screening operation, publication, warm-bank setup/lookup, serialization and full cold audit is charged. Prefix reconstruction/export overhead stays in complete study time. Original acquisition is inherited. No tests/builds/profiles overlap production.',
            'Budgets bound examined core proofs and plans, not posting discovery, dependency checking or residual search. Native schemas are unchanged. This correction does not establish minimum-cost expansion, unrestricted-SAT bounds or new structural coverage.'])
    base.write(out/'protocol.json',p);samples=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for cohort in p['cohorts']:
            hp=bound(cohort['protocol']);authority=bound(hp['parent']);trial=bound(cohort['trial']);records=bound(trial['queries'])
            def read(entry,name):
                path=tmp/name;base.restore_archive(entry,path);s=ResidualSolver(path)
                try:return rows(s)
                finally:s.close()
            initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');prefixes=previous.partition_study.prefixes(initial,final,records)
            for cid in cohort['cases']:
                before=prefixes[cid];old=next(r for r in records if r['case']==cid);source=old.get('record',old.get('chain'))['source']
                for mode in MODES:
                    tick=time.perf_counter();dest=out/f"{cohort['name']}-{cid}-{mode}";dest.mkdir();path=tmp/'arm';shutil.copyfile(tmp/'initial',path);s=previous.previous.ordinary.AccountedResidualSolver(path)
                    with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in before.items() if k not in initial])
                    open_seconds=time.perf_counter()-tick
                    try:
                        phase=time.perf_counter();target,guard,indices,prepared,normal_counts,near_counts=prepare(s,hp,old);preparation_seconds=time.perf_counter()-phase;assert rows(s)==before
                        phase=time.perf_counter();selector=(PartitionScreen if mode=='screened' else TerminalFirstScreen)(prepared['cores'],p['plan_limit'],p['core_read_limit']);screen_setup_seconds=time.perf_counter()-phase;setup_counts=dict(selector.counts);counts=Counter(s.counts);phase=time.perf_counter()
                        with patch.object(s,'_expand',side_effect=AssertionError('Screen search')),patch.object(s,'_store',side_effect=AssertionError('Screen publication')):plan,trace=selector.select(s,target)
                        screen_seconds=time.perf_counter()-phase;screen_solver_counts=dict(s.counts-counts);screen_counts=dict(selector.counts);terminal=mode=='terminal-first' and trace.get('terminal',False)
                        premise_counts=Counter();premise_solver_counts={};inserted=False;premise_seconds=0.;construction_counts=Counter();construction_seconds=0.;children=[]
                        if terminal:children=[publish_screened_branch(s,target,trace['baseline'])]
                        elif plan is None:children=[s.solve(target)]
                        else:
                            phase=time.perf_counter();counts=Counter(s.counts)
                            with patch.object(s,'_expand',side_effect=AssertionError('Premise search')):inserted,root=previous.publish_premise(s,target,prepared['cores'][plan['core']],plan['missing'],premise_counts)
                            premise_seconds=time.perf_counter()-phase;premise_solver_counts=dict(s.counts-counts);phase=time.perf_counter();branches=previous.branch_sources(target,plan['missing'],construction_counts)[1];construction_seconds=time.perf_counter()-phase
                            for (_,_,child_source),saved in zip(branches,plan['branches']):
                                child=publish_screened_branch(s,child_source,saved);children.append(child)
                                if child['answer']:break
                        phase=time.perf_counter();r=previous.chain_record(s,source,[guard],children[0]) if plan is None else previous.partition_record(s,source,[guard],plan['missing'],root,children);composition_seconds=time.perf_counter()-phase
                        with patch.object(s,'_expand',side_effect=AssertionError('Warm search')),patch.object(s,'_store',side_effect=AssertionError('Warm publication')):
                            phase=time.perf_counter();bank=previous.banks(s,[r]);warm_setup_seconds=time.perf_counter()-phase;phase=time.perf_counter();warm=previous.lookup(bank,source);warm_seconds=time.perf_counter()-phase;assert warm['answer']==r['answer']==old.get('record',old.get('chain'))['answer']
                        after=rows(s);assert before.items()<=after.items();delta=[(k,v) for k,v in after.items() if k not in before]
                    finally:s.close()
                    phase=time.perf_counter();base.write(dest/'delta.json',delta);base.write(dest/'records.json',[r]);serialization_seconds=time.perf_counter()-phase
                    catalogs=[(n,bound(authority[n])) for n in OLD_FIELDS];cold=previous.audit_records(path,[r],prepared,catalogs,indices);metrics=Counter()
                    for child in children:metrics.update(child['metrics'])
                    result=dict(cohort=cohort['name'],case=cid,mode=mode,plan=plan,screen=trace,terminal=terminal,prefix_nodes=len(before),prefix_digest=base.key_sha(base.encode(sorted(before.items()))),delta=binding(dest/'delta.json'),records=binding(dest/'records.json'),
                        new_nodes=len(delta),new_payload_units=sum(len(k)+len(v) for k,v in delta),retained_bytes=(dest/'delta.json').stat().st_size+(dest/'records.json').stat().st_size,expanded_nodes=metrics['expanded_nodes'],trace_publications=metrics['screen_trace_publications'],premise_inserted=inserted,children=children,
                        setup_counts=setup_counts,screen_counts=screen_counts,screen_solver_counts=screen_solver_counts,normal_counts=normal_counts,near_counts=near_counts,premise_counts=dict(premise_counts),premise_solver_counts=premise_solver_counts,construction_counts=dict(construction_counts),
                        open_seconds=open_seconds,preparation_seconds=preparation_seconds,screen_setup_seconds=screen_setup_seconds,screen_seconds=screen_seconds,premise_seconds=premise_seconds,construction_seconds=construction_seconds,composition_seconds=composition_seconds,warm_setup_seconds=warm_setup_seconds,warm_seconds=warm_seconds,serialization_seconds=serialization_seconds,cold=cold,seconds=time.perf_counter()-tick)
                    base.write(dest/'report.json',result);samples.append(binding(dest/'report.json'));print(base.encode({k:result[k] for k in ('cohort','case','mode','terminal','expanded_nodes','trace_publications','new_nodes','new_payload_units')}),flush=True)
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,seconds=time.perf_counter()-start))


if __name__=='__main__':run(Path(sys.argv[1]))

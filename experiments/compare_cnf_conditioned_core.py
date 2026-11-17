#!/usr/bin/env python3
"""Price conditioned cores against baseline solving and identical direct partitions."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_screen as history
from experiments import compare_cnf_terminal_first as terminal
from experiments.cnf_conditioned_core import project_core,acquire_core,check_record as check_projection
from experiments.cnf_clause_deletion_guard import check_guard,clause_set
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.validate_cnf_unsat_support import bound
base=history.base;binding=history.binding;rows=history.rows;ResidualSolver=history.ResidualSolver;FIELDS=history.FIELDS;OLD_FIELDS=history.OLD_FIELDS
PARENT=Path('experiments/results/cnf-terminal-first-complete')
FILES=('experiments/cnf_conditioned_core.py','solver/test_cnf_conditioned_core.py','experiments/compare_cnf_conditioned_core.py','experiments/validate_cnf_conditioned_core.py')


def inherited(parent):return terminal.inherited(parent)+bound(parent['terminal_first_decisions'])


def prepare(s,hp,row):
    bank,extensions,indices,prepared,cofactors=history.previous.setup(s,hp);selector=history.previous.ordinary.AlternativeGuardSelector(hp['alternative_budget'])
    target,normal,counts=history.previous.prepare(s,row['record']['source'],hp,bank,extensions,cofactors,selector);assert normal==row['ordinary']
    near=history.PremiseGuardSelector(prepared['cores']);choice,guard,target=near.select(s,target);assert choice==row['choice'] and guard==row['record']['guards'][-1] and choice['inserted'] is False
    fixed={};walk=row['record']['source']
    for g in row['record']['guards']:
        assignment,walk=check_guard(s,walk,g)
        for var,bit in assignment.items():assert var not in fixed or fixed[var]==bit;fixed[var]=bit
    assert walk==target
    return target,fixed,indices,prepared,dict(counts),dict(near.counts)


def audit_records(path,records,projections,prepared,catalogs,indices):
    start=time.perf_counter();result=history.audit_records(path,records,prepared,catalogs,indices);s=SnapshotResidualSolver(path)
    try:
        with patch.object(s,'_expand',side_effect=AssertionError('Cold projection search')),patch.object(s,'_store',side_effect=AssertionError('Cold projection publication')):
            checked=[check_projection(s,r) for r in projections]
    finally:s.close()
    return dict(composed=result,projections=checked,seconds=time.perf_counter()-start)


def run(out):
    out.mkdir(exist_ok=False);start=time.perf_counter();probe=base.load(PARENT/'guarded-residual-probe.json');targets=[]
    for cid,core in ((43,214),(172,209),(70,209)):
        row=next(r for r in probe['cases'] if r['case']==cid);candidate=next(r for r in row['conditioning']['guard_only']['examples'] if r['core']==core)
        targets.append(dict(case=cid,core=core,missing=candidate['missing_clauses']))
    sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    p=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,probe=binding(PARENT/'guarded-residual-probe.json'),historical_protocol=probe['historical_protocol'],historical_trial=probe['historical_trial'],targets=targets,
        modes=['baseline','conditioned-forward','direct-forward','conditioned-reverse','direct-reverse'],
        limitations=['Fifteen historical exact-prefix arms on three already selected cases. One projected core per case, forward/reverse missing-clause order, no new excluded queries or inexpensive selection policy. The full-bank discovery probe is separately retained and charged, not an oracle supplied for free.',
            'Every arm repeats ordinary preparation and the accepted extra guard. Conditioned arms bind a checked negative parent and the exact guard assignment, reuse an existing native cofactor or acquire a missing two-CNF certificate, then publish the strengthened premise from that cofactor. No new native proof format or unchecked restriction inference.',
            'Direct arms solve the same strengthened premise natively, then use exactly the same branch construction. This isolates certificate reuse from the effect of a chosen split; an explicit contained-clause test identifies ordinary literal-clause splits.',
            'All selected cofactor acquisition, premise publication, branch solving, checking, warm lookup, serialization and full cold replay are counted. Prefix restoration/export stays in complete time. All alternatives/regressions remain retained. One sample per arm establishes no stable runtime or peak-memory gain.',
            'Fresh cofactor acquisition is allowed only for two-CNF; a missing wider cofactor is rejected. Remaining general residual search is unrestricted and may be expensive. Exact composition is not a uniform polynomial SAT algorithm.'])
    base.write(out/'protocol.json',p);hp=bound(p['historical_protocol']);authority=bound(hp['parent']);trial=bound(p['historical_trial']);old_rows=bound(trial['queries']);samples=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=ResidualSolver(path)
            try:return rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');prefixes=history.partition_study.prefixes(initial,final,old_rows)
        for selection in targets:
            cid=selection['case'];old=next(r for r in old_rows if r['case']==cid);before=prefixes[cid]
            for mode in p['modes']:
                tick=time.perf_counter();dest=out/f'{cid}-{mode}';dest.mkdir();path=tmp/'arm';shutil.copyfile(tmp/'initial',path);s=history.previous.ordinary.AccountedResidualSolver(path)
                with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in before.items() if k not in initial])
                open_seconds=time.perf_counter()-tick
                try:
                    phase=time.perf_counter();target,fixed,indices,prepared,normal_counts,near_counts=prepare(s,hp,old);preparation_seconds=time.perf_counter()-phase;assert rows(s)==before;preparation_solver_counts=dict(s.counts)
                    missing=selection['missing'] if not mode.endswith('reverse') else list(reversed(selection['missing']));projection=None;projection_counts=Counter();projection_solver_counts={};projection_check_counts=Counter();projection_check_metrics={};cofactor=None;cofactor_was_known=None;projection_seconds=0.;cofactor_seconds=0.;projection_check_seconds=0.
                    if mode.startswith('conditioned'):
                        s.counts=Counter();phase=time.perf_counter();projection=project_core(s,prepared['cores'][selection['core']],fixed,projection_counts);projection_seconds=time.perf_counter()-phase
                        assert clause_set(projection['source'],projection_counts)-clause_set(target,projection_counts)==clause_set(missing,projection_counts)
                        cnf,_,key=s._canonical(projection['source']);cofactor_was_known=s._read(key,cnf) is not None;projection_solver_counts=dict(s.counts)
                        phase=time.perf_counter();cofactor=acquire_core(s,projection);cofactor_seconds=time.perf_counter()-phase;counts=Counter(s.counts);phase=time.perf_counter();hint=check_projection(s,projection,projection_check_counts);projection_check_seconds=time.perf_counter()-phase;projection_check_metrics=dict(s.counts-counts)
                    premise_counts=Counter();premise_metrics={};premise_child=None;premise_inserted=False;premise_seconds=0.;construction_counts=Counter();construction_seconds=0.;children=[]
                    contained_clause=None
                    if all(len(c)==1 for c in missing):
                        clause=[-c[0] for c in missing]
                        if clause_set([clause],Counter())<=clause_set(target,Counter()):contained_clause=clause
                    if mode=='baseline':children=[s.solve(target)]
                    else:
                        stronger=[list(c) for c in target]+missing;counts=Counter(s.counts);phase=time.perf_counter()
                        if mode.startswith('conditioned'):
                            with patch.object(s,'_expand',side_effect=AssertionError('Subset premise search')):premise_inserted,root=history.publish_premise(s,target,hint,missing,premise_counts)
                            premise_metrics=dict(s.counts-counts)
                        else:
                            premise_child=s.solve(stronger);assert premise_child['answer'] is False;root=premise_child['root'];premise_inserted=premise_child['metrics'].get('inserted_nodes',0)>0;premise_metrics=premise_child['metrics']
                        premise_seconds=time.perf_counter()-phase;phase=time.perf_counter();branches=history.branch_sources(target,missing,construction_counts)[1];construction_seconds=time.perf_counter()-phase
                        for _,_,child_source in branches:
                            child=s.solve(child_source);children.append(child)
                            if child['answer']:break
                    phase=time.perf_counter();source=old['record']['source'];guards=old['record']['guards'];record=history.chain_record(s,source,guards,children[0]) if mode=='baseline' else history.partition_record(s,source,guards,missing,root,children);composition_seconds=time.perf_counter()-phase
                    with patch.object(s,'_expand',side_effect=AssertionError('Warm search')),patch.object(s,'_store',side_effect=AssertionError('Warm publication')):
                        phase=time.perf_counter();bank=history.banks(s,[record]);warm_setup_seconds=time.perf_counter()-phase;phase=time.perf_counter();answer=history.lookup(bank,source);warm_seconds=time.perf_counter()-phase;assert answer['answer']==record['answer']==old['record']['answer']
                    after=rows(s);assert before.items()<=after.items();delta=[(k,v) for k,v in after.items() if k not in before]
                    if mode=='baseline':assert set(map(base.key_sha,dict(delta)))==set(old['new_ids']) and all(final[k]==v for k,v in delta)
                finally:s.close()
                phase=time.perf_counter();base.write(dest/'delta.json',delta);base.write(dest/'records.json',[record]);base.write(dest/'projections.json',[] if projection is None else [projection]);serialization_seconds=time.perf_counter()-phase
                catalogs=[(n,bound(authority[n])) for n in OLD_FIELDS];cold=audit_records(path,[record],[] if projection is None else [projection],prepared,catalogs,indices)
                acquired=[c for c in (cofactor,premise_child) if c is not None];expansions=sum(c['metrics'].get('expanded_nodes',0) for c in children+acquired)
                result=dict(case=cid,mode=mode,core=selection['core'],missing=missing,prefix_nodes=len(before),prefix_digest=base.key_sha(base.encode(sorted(before.items()))),delta=binding(dest/'delta.json'),records=binding(dest/'records.json'),projections=binding(dest/'projections.json'),
                    new_nodes=len(delta),new_payload_units=sum(len(k)+len(v) for k,v in delta),retained_bytes=sum((dest/f).stat().st_size for f in ('delta.json','records.json','projections.json')),expanded_nodes=expansions,children=children,cofactor=cofactor,cofactor_was_known=cofactor_was_known,premise_child=premise_child,premise_inserted=premise_inserted,contained_clause=contained_clause,
                    preparation_solver_counts=preparation_solver_counts,normal_counts=normal_counts,near_counts=near_counts,projection_counts=dict(projection_counts),projection_solver_counts=projection_solver_counts,projection_check_counts=dict(projection_check_counts),projection_check_metrics=projection_check_metrics,premise_counts=dict(premise_counts),premise_metrics=premise_metrics,construction_counts=dict(construction_counts),
                    open_seconds=open_seconds,preparation_seconds=preparation_seconds,projection_seconds=projection_seconds,cofactor_seconds=cofactor_seconds,projection_check_seconds=projection_check_seconds,premise_seconds=premise_seconds,construction_seconds=construction_seconds,composition_seconds=composition_seconds,warm_setup_seconds=warm_setup_seconds,warm_seconds=warm_seconds,serialization_seconds=serialization_seconds,cold=cold,seconds=time.perf_counter()-tick)
                base.write(dest/'report.json',result);samples.append(binding(dest/'report.json'));print(base.encode({k:result[k] for k in ('case','mode','expanded_nodes','new_nodes','new_payload_units','cofactor_was_known','contained_clause')}),flush=True)
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,seconds=time.perf_counter()-start))


if __name__=='__main__':run(Path(sys.argv[1]))

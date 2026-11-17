#!/usr/bin/env python3
"""Read-only discovery after the extra guard on the largest preserved residuals."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_terminal_first as study
from experiments.cnf_terminal_first_screen import TerminalFirstScreen
from experiments.cnf_partition_screen import screen_branch
from experiments.validate_cnf_partition_screen import expected_screen
from experiments.validate_cnf_terminal_first import expected_terminal
from experiments.validate_cnf_premise_guard import expected_choice
from experiments.cnf_residual_dag import restrict,propagate
from experiments.cnf_clause_deletion_guard import clause_set,check_guard
from experiments.validate_cnf_unsat_support import bound
base=study.base



def conditioned_candidates(s,target,cores,fixed,counts):
    members=clause_set(target,counts);variables={abs(l) for c in members for l in c};best=None;examples=[];ready=0;foreign=0;overlapping=0
    for i,core in enumerate(cores):
        cnf,_,root=s._canonical(core['source']);assert root==core['root'];node=s._read(root,cnf,purpose='conditioning_parent')
        if node is None:continue
        assert node['answer'] is False;ready+=1
        residual=restrict(core['source'],fixed,counts);wanted=clause_set(residual,counts);missing=wanted-members
        if not wanted&members:continue
        overlapping+=1
        if any(not c for c in missing) or not {abs(l) for c in missing for l in c}<=variables:foreign+=1;continue
        distance=len(missing)
        if best is None or distance<best:best=distance;examples=[]
        if distance==best and len(examples)<4:
            cf,_,key=s._canonical(residual);cached=s._read(key,cf,purpose='conditioned_core');assert cached is None or cached['answer'] is False
            examples.append(dict(core=i,parent_root=root,restricted_root=key,restricted_clauses=len(wanted),restricted_literals=sum(map(len,wanted)),missing_clauses=[list(c) for c in sorted(missing)],native_ready=cached is not None))
    return dict(ready_parents=ready,overlapping=overlapping,ineligible_empty_or_foreign=foreign,minimum_missing=best,examples=examples)


def run(out):
    start=time.perf_counter();parent=study.PARENT;hp=base.load(parent/'protocol.json');authority=bound(hp['parent']);trial=base.load(parent/'single-0/report.json');records=bound(trial['queries']);settings=base.load(out/'protocol.json');result=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');prefixes=study.previous.partition_study.prefixes(initial,final,records)
        for cid in (43,172,70):
            before=prefixes[cid];old=next(r for r in records if r['case']==cid);path=tmp/'probe';shutil.copyfile(tmp/'initial',path);s=study.ResidualSolver(path)
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in before.items() if k not in initial])
            s.db.execute('PRAGMA query_only=ON');phase=time.perf_counter()
            try:
                with patch.object(s,'_expand',side_effect=AssertionError('Probe search')),patch.object(s,'_store',side_effect=AssertionError('Probe publication')):
                    bank,extensions,indices,prepared,cofactors=study.previous.previous.setup(s,hp);selector=study.previous.previous.ordinary.AlternativeGuardSelector(hp['alternative_budget']);target,normal,counts=study.previous.previous.prepare(s,old['record']['source'],hp,bank,extensions,cofactors,selector);assert normal==old['ordinary']
                    near=study.previous.PremiseGuardSelector(prepared['cores']);choice,guard,target=near.select(s,target);assert choice==old['choice'] and guard==old['record']['guards'][-1] and choice['inserted'] is False
                    current=set(map(base.key_sha,before));screen=TerminalFirstScreen(prepared['cores'],settings['plan_limit'],settings['core_read_limit']);plan,trace=screen.select(s,target);assert (plan,trace)==expected_terminal(s,target,prepared['cores'],current,settings)
                    next_guard=expected_choice(s,target,prepared['cores'],current,'premise-first');next_result=None;next_counts=Counter()
                    if next_guard:
                        clause=next_guard['missing_clause'];residual=restrict(target,{abs(l):l<0 for l in clause},next_counts);probe=screen_branch(s,residual,next_counts);cnf,_,root=s._canonical(residual);known=s._read(root,cnf)
                        next_result=dict(choice=next_guard,clauses=len(residual),literals=sum(map(len,residual)),screen=probe,known_answer=None if known is None else known['answer'],root=root)
                    fixed={};walk=old['record']['source']
                    for g in old['record']['guards']:
                        assignment,walk=check_guard(s,walk,g)
                        for var,val in assignment.items():assert var not in fixed or fixed[var]==val;fixed[var]=val
                    assert walk==target;conditioning_counts=Counter();conditioned=conditioned_candidates(s,target,prepared['cores'],fixed,conditioning_counts)
                    cnf,names,root=s._canonical(target);unit_fixed,unit_trace,conflict=propagate(cnf,conditioning_counts);assert conflict is None
                    units={names[i-1]:value for i,value in unit_fixed.items()};reduced=restrict(target,units,conditioning_counts);after_units=conditioned_candidates(s,reduced,prepared['cores'],{**fixed,**units},conditioning_counts)
                    row=dict(case=cid,template_case=old['template_case'],source_root=old['record']['query_root'],prefix_nodes=len(before),prefix_digest=base.key_sha(base.encode(sorted(before.items()))),target_root=root,target=[list(c) for c in target],guards=old['record']['guards'],baseline_expansions=sum(c['metrics'].get('expanded_nodes',0) for c in old['children']),baseline_splits=sum(c['metrics'].get('split_nodes',0) for c in old['children']),
                        clauses=len(target),literals=sum(map(len,target)),conditioning=dict(guard_assignments=fixed,unit_assignments=units,guard_only=conditioned,after_units=after_units,counts=dict(conditioning_counts)),plan=plan,screen=trace,screen_counts=dict(screen.counts),additional_guard=next_result,additional_counts=dict(next_counts),seconds=time.perf_counter()-phase)
                assert study.rows(s)==before;result.append(row)
            finally:s.close()
    data=dict(passed=True,historical_protocol=study.binding(parent/'protocol.json'),historical_trial=study.binding(parent/'single-0/report.json'),policy=study.binding(out/'protocol.json'),cases=result,seconds=time.perf_counter()-start,
        limitations=['Read-only historical discovery after two already checked guards. No remaining child solve, premise publication or composed new source decision is performed. Candidate signals do not measure net savings. The following step must price any selected plan at these exact prefixes.', 'Conditioned-core candidates restrict checked-negative parents under the exact guard/unit assignment, then compare the resulting clauses. No new restricted-core certificate or reusable index is published; counts and existing native readiness are recorded. One further single-clause candidate is reconstructed independently. A checked core can justify publishing a missing strengthened premise, but publication and remaining solve are still unpaid here.'])
    base.write(out/'guarded-residual-probe.json',data);print(base.encode([dict(case=r['case'],baseline_expansions=r['baseline_expansions'],terminal=r['screen'].get('terminal'),plan=None if r['plan'] is None else {k:r['plan'][k] for k in ('core','order','terminal','remaining','residual_literals')},additional_guard=r['additional_guard'],conditioned_minimum=r['conditioning']['guard_only']['minimum_missing'],conditioned_after_units_minimum=r['conditioning']['after_units']['minimum_missing']) for r in result]),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))

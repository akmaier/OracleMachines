#!/usr/bin/env python3
"""Retain the unsuccessful unfused compiler and retrospective opportunities."""
from pathlib import Path
from collections import Counter
from unittest.mock import patch
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_clause_cover as study
from experiments import cnf_binary_clause_cover as cover_module
from experiments.cnf_binary_subset import BinarySubsetSolver
from experiments.cnf_residual_dag import ResidualSolver,FORMAT,two_cnf,holds,normalize,propagate,restrict
base=study.base


def compile_unfused(solver, cnf, cover):
    """Return a root proof; publish checked children without recursive solving."""
    cid=cover['clause_index']
    if type(cid) is not int or not 0<=cid<len(cnf):raise ValueError('Invalid cover source index')
    clause=cnf[cid]
    if len(clause)<3 or len(cover['paths'])!=len(clause):raise ValueError('Incomplete cover')
    for literal,path in zip(clause,cover['paths']):
        current=literal
        for nxt,reason in path:
            if (type(nxt) is not int or not nxt or type(reason) is not int or not 0<=reason<len(cnf)
                    or len(cnf[reason])!=2 or cnf[reason]!=tuple(sorted((-current,nxt)))):
                raise ValueError('Invalid binary cover path')
            solver.counts['binary_cover_checked_edges'] += 1;current=nxt
        if current!=-literal:raise ValueError('Incomplete binary implication')
    def node(external,index,terminal=False,root=False):
        source=cnf if root else restrict(cnf,external,solver.counts)
        local,names,key=solver._canonical(source)
        if not root:
            old=solver._read(key,local,purpose='binary_cover_compile')
            if old is not None:
                if old['answer']:raise ValueError('Cover contradicts a known model')
                return key
        proof=None
        if () in local:proof=dict(kind='empty')
        elif not root:
            _,trace,conflict=propagate(local,solver.counts)
            if conflict is not None:proof=dict(kind='units',trace=trace,conflict=conflict)
        if proof is None:
            if terminal or index==len(clause)-1:raise ValueError('Covered condition did not unit-refute')
            literal=clause[index];variable=names.index(abs(literal))+1
            yes={**external,abs(literal):literal>0};no={**external,abs(literal):literal<0}
            yes_key=node(yes,index,terminal=True);no_key=node(no,index+1)
            proof=dict(kind='split',variable=variable,low=no_key if literal>0 else yes_key,high=yes_key if literal>0 else no_key)
        if root:return proof
        solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in local],answer=False,proof=proof))
        solver.counts['binary_cover_compiled_children'] += 1
        return key
    return node({},0,root=True)


def diagnose(out):
    parent=study.PARENT;trial=base.load(parent/'binary-0/report.json');queries=study.bound(trial['queries']);cases=base.load(parent/'cases.json')['cases']
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'old';base.restore_archive(trial['archive'],path);s=ResidualSolver(path)
        try:rows={base.key_sha(k):base.load_json(v) for k,v in study.native.rows(s).items()}
        finally:s.close()
    census=[];core_keys=Counter()
    for row,case in zip(queries,cases):
        data=dict(case=case['case'],family=case['family'],satisfiable_cores=0,positive_completions=[],backbones=[],covered=[])
        for key in row['new_ids']:
            f=rows[key]['cnf'];binary=[c for c in f if len(c)==2]
            if not binary or len(binary)==len(f) or any(len(c)<2 for c in f):continue
            model,proof=two_cnf(binary,Counter())
            if model is None:continue
            data['satisfiable_cores']+=1;canonical,_=normalize(binary);core_keys[base.encode(canonical)]+=1
            vs={abs(l) for c in f for l in c}
            for fill in (False,True):
                if holds(f,{v:model.get(v,fill) for v in vs}):
                    data['positive_completions'].append(dict(root_sha256=key,fill=fill));break
            graph={}
            for a,b in binary:graph.setdefault(-a,[]).append(b);graph.setdefault(-b,[]).append(a)
            forced=set()
            for root in graph:
                seen={root};pending=[root]
                while pending:
                    for target in graph.get(pending.pop(),[]):
                        if target not in seen:seen.add(target);pending.append(target)
                if -root in seen:forced.add(-root)
            closed=[c for c in f if all(-l in forced for l in c)]
            if forced:data['backbones'].append(dict(root_sha256=key,forced=sorted(forced)))
            if closed:data['covered'].append(dict(root_sha256=key,clauses=closed))
        census.append(data)
    isolated=[]
    for case in cases:
        if case['case'] not in (35,40,44,48,52,55,56):continue
        arms={}
        for mode in ('binary','unfused','cover'):
            cls=BinarySubsetSolver if mode=='binary' else cover_module.BinaryClauseCoverSolver
            s=cls()
            try:
                if mode=='unfused':
                    with patch.object(cover_module,'compile_cover',compile_unfused):r=s.solve(case['source'])
                else:r=s.solve(case['source'])
                arms[mode]=dict(answer=r['answer'],metrics=r['metrics'],nodes=r['archive_nodes'],payload=r['archive_payload_bytes'])
            finally:s.close()
        assert len({a['answer'] for a in arms.values()})==1
        isolated.append(dict(case=case['case'],family=case['family'],arms=arms))
    base.write(out/'diagnosis.json',dict(source_catalog=study.binding(parent/'cases.json'),source_trial=study.binding(parent/'binary-0/report.json'),census=census,
        totals=dict(satisfiable_cores=sum(r['satisfiable_cores'] for r in census),positive_completions=sum(len(r['positive_completions']) for r in census),
            backbone_residuals=sum(len(r['backbones']) for r in census),covered_residuals=sum(len(r['covered']) for r in census),distinct_binary_keys=len(core_keys),repeated_binary_keys=sum(n>1 for n in core_keys.values())),
        isolated_checks=isolated,limitations=[
            'Retrospective census of stored nodes includes direct publications, so it is not the number of native expansion opportunities. Reachability is uncapped for diagnosis only.',
            'Positive whole-source completions were inspected but are not enabled by the new policy.',
            'Seven mechanism checks use separate empty in-memory archives and are untimed. The unfused compiler is retained as a rejected larger-proof alternative.',
            'Binary keys use existing ordered variable renaming, not arbitrary signed graph isomorphism. Repeated keys alone do not establish cost-effective reuse.']))


if __name__=='__main__':diagnose(Path(sys.argv[1]))

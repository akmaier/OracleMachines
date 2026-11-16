"""Backward causal slicing of checked unit traces, without fresh SAT search.

Keep only assignments required by the final conflict or selected negative child
clauses, recursively retaining their unit reasons. All derived nodes use the
unchanged residual certificate format and checker. Index-only mode stores no
proof; pending roots remain proposals until materialization and checking.
"""
from collections import Counter
from experiments.cnf_residual_dag import FORMAT,restrict
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_unsat_support import checked_subset
from experiments.cnf_active_support import ActiveCoreBank
from experiments import cnf_cofactor_support as cofactor
from unittest.mock import patch


def slice_trace(cnf,trace,needed,counts):
    """Input trace is already checked. Return its dependency-closed subsequence."""
    needed=set(needed);kept=[]
    for lit,cid in reversed(trace):
        counts['unit_trace_steps_examined']+=1;variable=abs(lit)
        if variable not in needed:continue
        needed.remove(variable);kept.append([lit,cid])
        needed.update(abs(other) for other in cnf[cid] if abs(other)!=variable)
        counts['unit_reason_literals_examined']+=len(cnf[cid])
    if needed:raise ValueError('Unit dependencies do not precede their use')
    kept.reverse();counts['unit_trace_steps_retained']+=len(kept)
    counts['unit_trace_steps_removed']+=len(trace)-len(kept)
    return kept


def discover_causal(solver,catalogs):
    with patch.object(cofactor,'SupportExtractor',lambda s:CausalSupportExtractor(s,materialize=False)):
        result=cofactor.prepare(solver,catalogs)
    result['deferred']=True;result['causal_unit_slicing']=True
    result['limitation']='Dependency-closed unit supports, not minimum cores. Pending roots require causal materialization and ordinary checking; complete lineage audit remains required.'
    return result


class CausalCoreBank(ActiveCoreBank):
    def __init__(self,solver,cores):
        super().__init__(solver,cores);self.extractor=CausalSupportExtractor(solver)


class CausalSupportExtractor:
    def __init__(self,solver,*,materialize=True):
        self.solver=solver;self.materialize=materialize;self.memo={};self.counts=Counter()

    def _preimage(self,cnf,ids,assignment,child,selected):
        """Lift selected normalized residual clauses to one actual parent clause each."""
        residual=[];origin={}
        for cid in ids:
            reduced=restrict([cnf[cid]],assignment,self.counts)
            if reduced:
                c=tuple(sorted(reduced[0]));residual.append(c);origin.setdefault(c,cid)
        normalized,names,key=self.solver._canonical(residual)
        if key!=child:raise ValueError('Wrong parent-to-child edge')
        return {origin[tuple(sorted((1 if l>0 else -1)*names[abs(l)-1] for l in normalized[i]))] for i in selected}

    def extract(self,key):
        if key in self.memo:self.counts['support_memo_hits']+=1;return self.memo[key]
        node=self.solver._read(key,purpose='support_source')
        if node is None or node['answer'] is not False:raise ValueError('A checked UNSAT source is required')
        cnf=tuple(tuple(c) for c in node['cnf']);proof=node['proof'];kind=proof['kind'];allids=range(len(cnf))
        self.counts['support_nodes']+=1;self.counts['support_source_literals']+=sum(map(len,cnf))
        self.counts['support_kind_'+kind]+=1
        if kind=='empty':selected={cnf.index(())};newproof=dict(kind='empty')
        elif kind=='implications':
            selected={cid for _,cid in proof['forward']+proof['backward']};newproof=None
        elif kind=='hall-v1':
            selected=set(proof['groups'])|{i for i,c in enumerate(cnf) if any(l<0 for l in c)};newproof=None
        elif kind in ('component','positive-subsumption-v1'):
            ids=proof['clauses'] if kind=='component' else [i for i in allids if i not in {p[0] for p in proof['removed']}]
            child=self.extract(proof['child']);selected=self._preimage(cnf,ids,{},proof['child'],child['indices']);newproof=None
        elif kind=='units':
            full_assignment={abs(l):l>0 for l,_ in proof['trace']}
            if proof.get('conflict') is not None:target_ids={proof['conflict']}
            else:
                child=self.extract(proof['child'])
                target_ids=self._preimage(cnf,allids,full_assignment,proof['child'],child['indices'])
            needed={abs(l) for cid in target_ids for l in cnf[cid] if abs(l) in full_assignment}
            unit_trace=slice_trace(cnf,proof['trace'],needed,self.counts)
            assignment={abs(l):l>0 for l,_ in unit_trace}
            selected=set(target_ids)|{cid for _,cid in unit_trace};newproof=None
            if restrict([cnf[i] for i in target_ids],assignment)!=restrict([cnf[i] for i in target_ids],full_assignment):
                raise ValueError('Slicing changed the required residual')
        elif kind=='split':
            v=proof['variable'];children={};supports={}
            for value,field in ((False,'low'),(True,'high')):
                children[value]=self.extract(proof[field]);supports[value]=self._preimage(cnf,allids,{v:value},proof[field],children[value]['indices'])
            independent=[ids for ids in supports.values() if all(all(abs(l)!=v for l in cnf[i]) for i in ids)]
            selected=min(independent,key=lambda ids:(len(ids),sorted(ids))) if independent else supports[False]|supports[True]
            newproof=None
        else:raise ValueError('Unsupported negative proof kind')
        indices=sorted(selected);source=[cnf[i] for i in indices];core,names,root=self.solver._canonical(source)
        if not self.materialize:
            result=dict(indices=indices,root=root);self.memo[key]=result
            self.counts['support_dropped_clauses']+=len(cnf)-len(indices);return result
        old=self.solver._read(root,core,purpose='support_existing')
        if old is None:
            rename={v:i+1 for i,v in enumerate(names)}
            def literal(l):return (1 if l>0 else -1)*rename[abs(l)]
            positions={c:i for i,c in enumerate(core)}
            cids={i:positions[tuple(sorted(literal(l) for l in cnf[i]))] for i in indices}
            if kind=='implications':newproof=dict(kind=kind,variable=rename[proof['variable']],
                forward=[[literal(l),cids[c]] for l,c in proof['forward']],backward=[[literal(l),cids[c]] for l,c in proof['backward']])
            elif kind=='hall-v1':newproof=dict(kind=kind,groups=[cids[i] for i in proof['groups']])
            elif kind in ('component','positive-subsumption-v1'):
                if root!=child['root']:raise ValueError('Subset core transport changed identity')
                raise ValueError('Extracted child core was not retained')
            elif kind=='units':
                newproof=dict(kind=kind,trace=[[literal(l),cids[c]] for l,c in unit_trace])
                if proof.get('conflict') is not None:newproof['conflict']=cids[proof['conflict']]
                else:
                    residual=restrict(source,assignment,self.counts)
                    # Use the exact extracted child subset, transported through its original residual.
                    child_source=restrict([cnf[i] for i in target_ids],assignment,self.counts)
                    _,newproof['child']=checked_subset(self.solver,residual,child_source,self.counts)
            elif kind=='split':
                if independent:raise ValueError('Independent child core was not retained')
                newproof=dict(kind=kind,variable=rename[v])
                for value,field in ((False,'low'),(True,'high')):
                    residual=restrict(source,{v:value},self.counts)
                    small=restrict([cnf[i] for i in supports[value]],{v:value},self.counts)
                    _,newproof[field]=checked_subset(self.solver,residual,small,self.counts)
            self.solver._store(root,dict(format=FORMAT,cnf=[list(c) for c in core],answer=False,proof=newproof))
            self.counts['extracted_core_publications']+=1
        elif old['answer'] is not False:raise ValueError('Conflicting core answer')
        result=dict(indices=indices,root=root);self.memo[key]=result
        self.counts['support_dropped_clauses']+=len(cnf)-len(indices)
        return result

    def source_core(self,source):
        cnf,names,key=self.solver._canonical(source);entry=self.extract(key)
        core=[[(1 if l>0 else -1)*names[abs(l)-1] for l in cnf[i]] for i in entry['indices']]
        if not clause_set(core,self.counts)<=clause_set(source,self.counts):raise ValueError('Source core is not contained')
        return dict(source=core,root=entry['root'],origin=key)


"""Discover support proposals, but materialize their proofs only on a match.

Proposals are not UNSAT certificates. A match must have a checked negative core
before the frozen subset rule may publish a target result. Original proof nodes
are read and checked during discovery; no derived proof is stored at that stage.
"""
from collections import Counter
from copy import deepcopy
from unittest.mock import patch
from experiments import cnf_cofactor_support as eager
from experiments.cnf_unsat_support import SupportExtractor,checked_subset
from experiments.cnf_clause_deletion_guard import clause_set


class SupportIndexExtractor(SupportExtractor):
    def extract(self,key):
        if key in self.memo:self.counts['support_memo_hits']+=1;return self.memo[key]
        node=self.solver._read(key,purpose='support_source')
        if node is None or node['answer'] is not False:raise ValueError('A checked UNSAT source is required')
        cnf=tuple(tuple(c) for c in node['cnf']);proof=node['proof'];kind=proof['kind'];allids=range(len(cnf))
        self.counts['support_nodes']+=1;self.counts['support_source_literals']+=sum(map(len,cnf));self.counts['support_kind_'+kind]+=1
        if kind=='empty':selected={cnf.index(())}
        elif kind=='implications':selected={cid for _,cid in proof['forward']+proof['backward']}
        elif kind=='hall-v1':selected=set(proof['groups'])|{i for i,c in enumerate(cnf) if any(l<0 for l in c)}
        elif kind in ('component','positive-subsumption-v1'):
            ids=proof['clauses'] if kind=='component' else [i for i in allids if i not in {p[0] for p in proof['removed']}]
            child=self.extract(proof['child']);selected=self._preimage(cnf,ids,{},proof['child'],child['indices'])
        elif kind=='units':
            selected={cid for _,cid in proof['trace']};assignment={abs(l):l>0 for l,_ in proof['trace']}
            if proof.get('conflict') is not None:selected.add(proof['conflict'])
            else:
                child=self.extract(proof['child']);selected|=self._preimage(cnf,allids,assignment,proof['child'],child['indices'])
        elif kind=='split':
            v=proof['variable'];supports={}
            for value,field in ((False,'low'),(True,'high')):
                child=self.extract(proof[field]);supports[value]=self._preimage(cnf,allids,{v:value},proof[field],child['indices'])
            independent=[ids for ids in supports.values() if all(all(abs(l)!=v for l in cnf[i]) for i in ids)]
            selected=min(independent,key=lambda ids:(len(ids),sorted(ids))) if independent else supports[False]|supports[True]
        else:raise ValueError('Unsupported negative proof kind')
        indices=sorted(selected);_,_,root=self.solver._canonical([cnf[i] for i in indices])
        result=dict(indices=indices,root=root);self.memo[key]=result;self.counts['support_dropped_clauses']+=len(cnf)-len(indices)
        return result


def discover(solver,catalogs):
    # Scoped substitution reuses the frozen provenance, coordinate transport and
    # antichain selection. The experiment owns this process during discovery.
    with patch.object(eager,'SupportExtractor',SupportIndexExtractor):result=eager.prepare(solver,catalogs)
    result['deferred']=True
    result['limitation']='Source-bound proposals only. A checked negative proof is required before any target publication; no fresh solving during discovery or materialization.'
    return result


class DeferredCoreBank:
    def __init__(self,solver,cores):
        self.solver=solver;self.counts=Counter();self.extractor=SupportExtractor(solver);self.cores=[]
        for item in deepcopy(cores):
            clauses=clause_set(item['source'],self.counts);cnf,_,key=solver._canonical(item['source'])
            if key!=item['root']:raise ValueError('Unbound support proposal')
            origin=solver._read(item['origin'],purpose='deferred_origin')
            if origin is None or origin['answer'] is not False:raise ValueError('Missing negative proposal origin')
            self.cores.append((item,clauses))

    def reuse(self,source):
        clauses=clause_set(source,self.counts)
        for index,(core,wanted) in enumerate(self.cores):
            self.counts['core_candidates']+=1;self.counts['core_containment_clauses']+=len(wanted)
            if not wanted<=clauses:continue
            cnf,_,key=self.solver._canonical(core['source']);node=self.solver._read(key,cnf,purpose='deferred_core')
            if node is None:
                self.counts['materialization_attempts']+=1;before=self.solver.counts['inserted_nodes']
                derived=self.extractor.extract(core['origin'])
                self.counts['materialization_nodes']+=self.solver.counts['inserted_nodes']-before
                if derived['root']!=key:raise ValueError('Proposal differs from checked extracted support')
                node=self.solver._read(key,cnf,purpose='materialized_core')
            else:self.counts['existing_core_proofs']+=1
            if node is None or node['answer'] is not False:raise ValueError('Checked negative support required')
            inserted,root=checked_subset(self.solver,source,core['source'],self.counts)
            return dict(core=index,inserted=inserted,root=root)
        return None

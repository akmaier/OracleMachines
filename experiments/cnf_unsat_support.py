"""Extract checked UNSAT clause supports without fresh search.

Derived cores and weakenings use only the frozen residual certificate format.
The existing checker validates every published node. Supports need not be minimal.
"""
from collections import Counter
from experiments.cnf_residual_dag import FORMAT,restrict
from experiments.cnf_clause_deletion_guard import clause_set


def checked_subset(solver,source,core,counts=None):
    """Publish UNSAT(source) from an already checked UNSAT subset in raw coordinates."""
    counts=Counter() if counts is None else counts
    outer=clause_set(source,counts);inner=clause_set(core,counts)
    if not inner<=outer:raise ValueError('Core is not a clause subset in common coordinates')
    cnf,names,key=solver._canonical(source);small,_,child=solver._canonical(core)
    node=solver._read(child,small,purpose='support_premise')
    if node is None or node['answer'] is not False:raise ValueError('A checked UNSAT core is required')
    old=solver._read(key,cnf,purpose='support_query')
    if old is not None:
        if old['answer'] is not False:raise ValueError('Conflicting checked answers')
        return False,key
    if cnf==((),):
        solver._store(key,dict(format=FORMAT,cnf=[[]],answer=False,proof=dict(kind='empty')))
        counts['support_publications']+=1
        return True,key
    rename={v:i+1 for i,v in enumerate(names)}
    wanted={tuple(sorted((1 if l>0 else -1)*rename[abs(l)] for l in c)) for c in inner}
    ids=[i for i,c in enumerate(cnf) if c in wanted]
    if solver._canonical([cnf[i] for i in ids])[2]!=child:raise ValueError('Core transport changed identity')
    solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=False,
                           proof=dict(kind='component',clauses=ids,child=child)))
    counts['support_publications']+=1;counts['support_publication_literals']+=sum(map(len,cnf))
    return True,key


class SupportExtractor:
    def __init__(self,solver):self.solver=solver;self.memo={};self.counts=Counter()

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
            selected={cid for _,cid in proof['trace']};assignment={abs(l):l>0 for l,_ in proof['trace']}
            if proof.get('conflict') is not None:selected.add(proof['conflict'])
            else:
                child=self.extract(proof['child']);selected|=self._preimage(cnf,allids,assignment,proof['child'],child['indices'])
            newproof=None
        elif kind=='split':
            v=proof['variable'];children={};supports={}
            for value,field in ((False,'low'),(True,'high')):
                children[value]=self.extract(proof[field]);supports[value]=self._preimage(cnf,allids,{v:value},proof[field],children[value]['indices'])
            independent=[ids for ids in supports.values() if all(all(abs(l)!=v for l in cnf[i]) for i in ids)]
            selected=min(independent,key=lambda ids:(len(ids),sorted(ids))) if independent else supports[False]|supports[True]
            newproof=None
        else:raise ValueError('Unsupported negative proof kind')
        indices=sorted(selected);source=[cnf[i] for i in indices];core,names,root=self.solver._canonical(source)
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
                newproof=dict(kind=kind,trace=[[literal(l),cids[c]] for l,c in proof['trace']])
                if proof.get('conflict') is not None:newproof['conflict']=cids[proof['conflict']]
                else:
                    residual=restrict(source,assignment,self.counts)
                    # Use the exact extracted child subset, transported through its original residual.
                    target_ids=self._preimage(cnf,allids,assignment,proof['child'],child['indices'])
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


class CoreBank:
    def __init__(self,solver,cores):
        self.solver=solver;self.counts=Counter();self.cores=[]
        for item in cores:
            clauses=clause_set(item['source'],self.counts);cnf,_,key=solver._canonical(item['source'])
            if key!=item['root']:raise ValueError('Unbound core')
            node=solver._read(key,cnf,purpose='core_bank')
            if node is None or node['answer'] is not False:raise ValueError('Missing negative core')
            self.cores.append((item,clauses))
    def reuse(self,source):
        clauses=clause_set(source,self.counts)
        for index,(core,wanted) in enumerate(self.cores):
            self.counts['core_candidates']+=1;self.counts['core_containment_clauses']+=len(wanted)
            if wanted<=clauses:
                inserted,root=checked_subset(self.solver,source,core['source'],self.counts)
                return dict(core=index,inserted=inserted,root=root)
        return None

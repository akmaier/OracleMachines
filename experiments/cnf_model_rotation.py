"""Bounded, checked model rotation for single-clause deletions.

Each template keeps one complete witness per discovered transition clause.
Failed flips, unprocessed witnesses and consumed budgets remain exportable.
Only a fully checked SAT model is published; failures never certify UNSAT.
"""
from collections import Counter
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_residual_dag import FORMAT, holds


def publish(solver, source, model, counts):
    support={abs(l) for c in source for l in c}
    if any(type(model.get(v)) is not bool for v in support) or not holds(source,model):
        raise ValueError('Invalid rotation witness')
    counts['rotation_publication_literal_checks']+=sum(map(len,source))
    cnf,names,key=solver._canonical(source);old=solver._read(key,cnf,purpose='rotation')
    if old is not None:
        if old['answer'] is not True:raise ValueError('Conflicting checked answers')
        counts['rotation_already_stored']+=1;return False,key
    solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=True,model=[model[v] for v in names]))
    counts['rotation_publications']+=1
    return True,key


class ModelRotation:
    def __init__(self, solver, templates, seeds, *, flip_limit=64):
        if type(flip_limit) is not int or flip_limit<0:raise ValueError('Invalid flip budget')
        self.solver=solver;self.limit=flip_limit;self.counts=Counter();self.templates=[]
        for item in templates:
            clauses=[list(c) for c in sorted(clause_set(item['source'],self.counts))]
            normalized,_,root=solver._canonical(clauses)
            if root!=item['root']:raise ValueError('Unbound rotation template')
            old=solver._read(root,normalized,purpose='rotation_template')
            if old is None or old['answer'] is not False:raise ValueError('A checked UNSAT template is required')
            self.templates.append(dict(source=clauses,root=root,models=[],by_clause={},cursor=0,next_literal=0,attempts=[]))
        for seed in seeds:
            source=seed['source'];cnf,names,key=solver._canonical(source)
            if key!=seed['root']:raise ValueError('Unbound seed query')
            node=solver._read(key,cnf,purpose='rotation_seed')
            if node is None or node['answer'] is not True:raise ValueError('A checked SAT seed is required')
            model={v:node['model'][i] for i,v in enumerate(names)}
            self.observe(source,model,dict(kind='seed',root=key))

    def observe(self, source, model, origin):
        query=clause_set(source,self.counts)
        for t in self.templates:
            clauses={tuple(c) for c in t['source']}
            self.counts['rotation_template_comparisons']+=1
            if len(clauses)!=len(query)+1 or not query<clauses:continue
            support={abs(l) for c in t['source'] for l in c}
            complete={v:model.get(v,False) for v in support}
            if any(type(v) is not bool for v in complete.values()) or not holds(source,complete):
                raise ValueError('Observed query model is invalid')
            bad=[i for i,c in enumerate(t['source']) if not holds([c],complete)]
            self.counts['rotation_observation_literals']+=sum(map(len,t['source']))+sum(map(len,source))
            if len(bad)!=1 or tuple(t['source'][bad[0]]) in query:raise ValueError('Model is not bound to the deleted clause')
            cid=bad[0]
            if cid in t['by_clause']:
                self.counts['rotation_duplicate_clause_witnesses']+=1;continue
            t['by_clause'][cid]=len(t['models']);t['models'].append(dict(clause=cid,model=complete,origin=origin))
            self.counts['rotation_new_clause_witnesses']+=1

    def drain(self):
        for ti,t in enumerate(self.templates):
            while t['cursor']<len(t['models']) and len(t['attempts'])<self.limit:
                mi=t['cursor'];entry=t['models'][mi];clause=t['source'][entry['clause']]
                if t['next_literal']==len(clause):t['cursor']+=1;t['next_literal']=0;continue
                variable=abs(clause[t['next_literal']]);t['next_literal']+=1
                original=entry['model'];model={**original,variable:not original[variable]}
                bad=[i for i,c in enumerate(t['source']) if not holds([c],model)]
                self.counts['rotation_flip_attempts']+=1;self.counts['rotation_scan_literals']+=sum(map(len,t['source']))
                attempt=dict(model=mi,variable=variable,falsified=bad,published=False)
                if len(bad)==1:
                    target=[c for i,c in enumerate(t['source']) if i!=bad[0]]
                    inserted,key=publish(self.solver,target,model,self.counts)
                    attempt.update(published=inserted,root=key)
                    self.observe(target,model,dict(kind='rotation',template=ti,attempt=len(t['attempts'])))
                t['attempts'].append(attempt)

    def state(self):
        return dict(format='bounded-model-rotation-v1',flip_limit=self.limit,counts=dict(self.counts),
                    templates=[{k:v for k,v in t.items() if k!='by_clause'} for t in self.templates])

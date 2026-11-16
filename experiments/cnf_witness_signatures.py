"""Bounded model exploration with exact falsified-clause signatures.

A signature B for template F recognizes a query Q subset F precisely when
B is disjoint from Q. Only a fully checked query model may be published.
One representative per signature preserves current lookup coverage, but all
distinct accepted assignments are kept for exploration: the quotient need not
preserve flip transitions. Exhaustion or a miss never means UNSAT.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_residual_dag import holds
from experiments.cnf_model_rotation import publish


class WitnessSignatures:
    def __init__(self,templates,*,attempt_limit=256,max_bad=2):
        if type(attempt_limit) is not int or attempt_limit<0 or type(max_bad) is not int or max_bad<0:raise ValueError('Invalid exploration budget')
        self.limit=attempt_limit;self.max_bad=max_bad;self.counts=Counter();self.templates=[];self.compiled=[];self.sealed=False
        for template in templates:
            source=[list(c) for c in sorted(clause_set(template['source'],self.counts))];names=sorted({abs(l) for c in source for l in c});positions={v:i for i,v in enumerate(names)}
            masks=[(sum(1<<positions[l] for l in c if l>0),sum(1<<positions[-l] for l in c if l<0)) for c in source]
            incidence=[[i for i,c in enumerate(source) if v in c or -v in c] for v in names]
            self.compiled.append(dict(masks=masks,incidence=incidence,members={tuple(c):i for i,c in enumerate(source)},seen={},representatives={}))
            self.templates.append(dict(source=source,names=names,states=[],attempts=[],cursor=0,next_variable=0))

    def _bad(self,ti,bits):
        self.counts['signature_clause_evaluations']+=len(self.compiled[ti]['masks'])
        return sum(1<<i for i,(pos,neg) in enumerate(self.compiled[ti]['masks']) if not (bits&pos or ~bits&neg))

    def _add(self,ti,bits,bad,origin):
        t=self.templates[ti];c=self.compiled[ti]
        if bits in c['seen']:self.counts['duplicate_assignments']+=1;return c['seen'][bits],False
        index=len(t['states']);c['seen'][bits]=index;t['states'].append(dict(bits=bits,bad=bad,origin=deepcopy(origin)))
        if bad not in c['representatives']:c['representatives'][bad]=index;self.counts['new_signatures']+=1
        self.counts['new_assignments']+=1;return index,True

    def observe(self,source,model,origin):
        if self.sealed:raise ValueError('Seed batch is sealed after exploration begins')
        if type(origin) is not dict or origin.get('kind')=='flip':raise ValueError('Invalid seed origin')
        query=clause_set(source,self.counts);support={abs(l) for c in query for l in c}
        if any(type(model.get(v)) is not bool for v in support) or not holds(source,model):raise ValueError('Invalid observed SAT model')
        self.counts['observed_model_literal_checks']+=sum(map(len,source))
        for ti,(t,c) in enumerate(zip(self.templates,self.compiled)):
            self.counts['template_containment_checks']+=1
            if not query<=c['members'].keys():continue
            if any(v in model and type(model[v]) is not bool for v in t['names']):raise ValueError('Invalid template coordinate')
            bits=sum(1<<i for i,v in enumerate(t['names']) if model.get(v,False));bad=self._bad(ti,bits)
            if bad.bit_count()<=self.max_bad:self._add(ti,bits,bad,origin)

    def drain(self):
        self.sealed=True
        for ti,(t,c) in enumerate(zip(self.templates,self.compiled)):
            while t['cursor']<len(t['states']) and len(t['attempts'])<self.limit:
                parent=t['cursor'];state=t['states'][parent]
                variables=sorted({j for i in range(len(t['source'])) if state['bad']>>i&1 for j in range(len(t['names'])) if c['masks'][i][0]>>j&1 or c['masks'][i][1]>>j&1})
                if t['next_variable']==len(variables):t['cursor']+=1;t['next_variable']=0;continue
                variable=variables[t['next_variable']];t['next_variable']+=1;bits=state['bits']^(1<<variable);bad=state['bad']
                for i in c['incidence'][variable]:
                    pos,neg=c['masks'][i];bad=(bad&~(1<<i))|((0 if bits&pos or ~bits&neg else 1)<<i)
                    self.counts['flip_clause_evaluations']+=1
                accepted=bad.bit_count()<=self.max_bad;child=None;fresh=False
                if accepted:child,fresh=self._add(ti,bits,bad,dict(kind='flip',parent=parent,variable=variable))
                t['attempts'].append(dict(parent=parent,variable=variable,bad=bad,accepted=accepted,child=child,fresh=fresh));self.counts['flip_attempts']+=1

    def reuse(self,solver,source):
        query=clause_set(source,self.counts)
        for ti,(t,c) in enumerate(zip(self.templates,self.compiled)):
            self.counts['template_containment_checks']+=1
            if not query<=c['members'].keys():continue
            present=sum(1<<c['members'][clause] for clause in query)
            for bad,si in c['representatives'].items():
                self.counts['signature_tests']+=1
                if bad&present:continue
                state=t['states'][si];model={v:bool(state['bits']>>i&1) for i,v in enumerate(t['names'])}
                inserted,key=publish(solver,source,model,self.counts)
                return dict(template=ti,state=si,bad=bad,root=key,inserted=inserted)
        return None

    def state(self):
        return dict(format='bounded-witness-signatures-v1',attempt_limit=self.limit,max_bad=self.max_bad,sealed=self.sealed,counts=dict(self.counts),templates=deepcopy(self.templates))

    @classmethod
    def restore(cls,saved):
        if saved['format']!='bounded-witness-signatures-v1':raise ValueError('Unknown witness index')
        bank=cls(saved['templates'],attempt_limit=saved['attempt_limit'],max_bad=saved['max_bad'])
        if type(saved['sealed']) is not bool:raise ValueError('Invalid exploration phase')
        for ti,t in enumerate(saved['templates']):
            if t['source']!=bank.templates[ti]['source'] or t['names']!=bank.templates[ti]['names']:raise ValueError('Unbound template coordinates')
            for si,state in enumerate(t['states']):
                bits=state['bits'];bad=state['bad'];origin=state['origin']
                if type(bits) is not int or bits<0 or bits>=1<<len(t['names']) or type(bad) is not int or bad<0 or bank._bad(ti,bits)!=bad or bad.bit_count()>bank.max_bad:raise ValueError('Invalid signature state')
                if origin.get('kind')=='flip':
                    parent=origin['parent'];variable=origin['variable']
                    if type(parent) is not int or type(variable) is not int or not 0<=parent<si or not 0<=variable<len(t['names']) or t['states'][parent]['bits']^(1<<variable)!=bits:raise ValueError('Invalid flip origin')
                _,fresh=bank._add(ti,bits,bad,origin)
                if not fresh:raise ValueError('Duplicate stored assignment')
            # Replay the bounded queue exactly, including rejected/duplicate flips.
            replay=cls([t],attempt_limit=bank.limit,max_bad=bank.max_bad)
            seeds=[state for state in t['states'] if state['origin'].get('kind')!='flip']
            for state in seeds:replay._add(0,state['bits'],state['bad'],state['origin'])
            if saved['sealed']:replay.drain()
            if replay.templates[0]!=t:raise ValueError('Unbound exploration transcript')
            if len(t['attempts'])>bank.limit:raise ValueError('Exceeded saved budget')
            bank.templates[ti]=deepcopy(t)
        bank.counts=Counter(saved['counts']);bank.sealed=saved['sealed'];return bank

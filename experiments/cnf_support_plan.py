"""Query-local causal derivation plans, emitted through unchanged native checking.

Discovery retains exact support choices and compact-name mappings. Emission uses
those choices without repeating the support walk. Plans confer no proof authority.
The conservative charge bounds retained plan objects, not encoding/decoding
transients, emission workspaces, or the solver's existing checked graph.
"""
from collections import Counter
import json,sys
from experiments.cnf_causal_support import CausalSupportExtractor,slice_trace
from experiments.cnf_negative_edit_pool import NegativeEditPoolSolver,SupportBudget
from experiments.cnf_residual_dag import FORMAT,restrict
from experiments.cnf_unsat_support import checked_subset


class PlanBudget(RuntimeError):pass


class CausalPlan(CausalSupportExtractor):
    def __init__(self,solver,*,node_limit=256,literal_limit=131072,byte_limit=4*1024*1024):
        if any(type(v) is not int or v<1 for v in (node_limit,literal_limit,byte_limit)):
            raise ValueError('Invalid causal plan limits')
        super().__init__(solver,materialize=False)
        self.node_limit=node_limit;self.literal_limit=literal_limit;self.byte_limit=byte_limit
        self.plans={};self.charge=0;self.emitted=set()

    def prepare(self,key):
        if key in self.memo:self.counts['support_memo_hits']+=1;return self.memo[key]
        if self.counts['support_nodes']>=self.node_limit:raise SupportBudget('Support node budget')
        node=self.solver._read(key,purpose='plan_origin')
        if node is None or node['answer'] is not False:raise ValueError('Checked negative origin required')
        cnf=tuple(tuple(c) for c in node['cnf']);literals=sum(map(len,cnf))
        if self.counts['support_source_literals']+literals>self.literal_limit:raise SupportBudget('Support literal budget')
        proof=node['proof'];kind=proof['kind'];allids=range(len(cnf));deps=[];extra={}
        self.counts['support_nodes']+=1;self.counts['support_source_literals']+=literals
        self.counts['support_kind_'+kind]+=1
        if kind=='empty':selected={cnf.index(())}
        elif kind=='implications':
            selected={cid for _,cid in proof['forward']+proof['backward']}
            extra=dict(variable=proof['variable'],forward=proof['forward'],backward=proof['backward'])
        elif kind=='hall-v1':
            selected=set(proof['groups'])|{i for i,c in enumerate(cnf) if any(l<0 for l in c)}
            extra=dict(groups=proof['groups'])
        elif kind in ('component','positive-subsumption-v1'):
            deps=[proof['child']];child=self.prepare(deps[0])
            ids=proof['clauses'] if kind=='component' else [i for i in allids if i not in {p[0] for p in proof['removed']}]
            selected=self._preimage(cnf,ids,{},deps[0],child['indices'])
        elif kind=='units':
            full={abs(l):l>0 for l,_ in proof['trace']}
            if proof.get('conflict') is not None:target_ids={proof['conflict']}
            else:
                deps=[proof['child']];child=self.prepare(deps[0])
                target_ids=self._preimage(cnf,allids,full,deps[0],child['indices'])
            needed={abs(l) for i in target_ids for l in cnf[i] if abs(l) in full}
            trace=slice_trace(cnf,proof['trace'],needed,self.counts);assignment={abs(l):l>0 for l,_ in trace}
            targets=[cnf[i] for i in target_ids]
            if restrict(targets,assignment)!=restrict(targets,full):raise ValueError('Slicing changed required residual')
            selected=set(target_ids)|{cid for _,cid in trace}
            extra=dict(trace=trace,conflict=proof.get('conflict'),targets=targets)
        elif kind=='split':
            v=proof['variable'];supports={}
            for value,field in ((False,'low'),(True,'high')):
                deps.append(proof[field]);child=self.prepare(proof[field])
                supports[value]=self._preimage(cnf,allids,{v:value},proof[field],child['indices'])
            independent=[ids for ids in supports.values() if all(all(abs(l)!=v for l in cnf[i]) for i in ids)]
            selected=min(independent,key=lambda ids:(len(ids),sorted(ids))) if independent else supports[False]|supports[True]
            extra=dict(variable=v,independent=bool(independent),targets=[[cnf[i] for i in supports[value]] for value in (False,True)])
        else:raise ValueError('Unsupported negative proof kind')
        indices=sorted(selected);source=[cnf[i] for i in indices];core,names,root=self.solver._canonical(source)
        result=dict(indices=indices,root=root)
        recipe=dict(kind=kind,dependencies=deps,source=source,core=core,names=names,extra=extra)
        encoded=json.dumps(recipe,separators=(',',':'),sort_keys=True)
        self.counts['plan_encoded_bytes']+=len(encoded.encode());self.counts['plan_recipes']+=1
        # Charge duplicate references conservatively, including mapping keys and
        # every result integer. Both dict tables are measured after insertion.
        charge=(sys.getsizeof(key)+sys.getsizeof(encoded)+sys.getsizeof(result)
                +sum(sys.getsizeof(k) for k in result)+sys.getsizeof(indices)
                +sum(sys.getsizeof(i) for i in indices)+sys.getsizeof(root))
        self.plans[key]=encoded;self.memo[key]=result;self.charge+=charge
        total=self.charge+sys.getsizeof(self.plans)+sys.getsizeof(self.memo)
        if total>self.byte_limit:
            self.plans.clear();self.memo.clear();self.charge=0
            self.counts['plan_capacity_stops']+=1;raise PlanBudget('Retained causal plan budget')
        self.counts['plan_peak_bytes']=max(self.counts['plan_peak_bytes'],total)
        self.counts['support_dropped_clauses']+=len(cnf)-len(indices)
        return result

    def emit(self,key):
        if key in self.emitted:self.counts['plan_emit_memo_hits']+=1;return self.memo[key]
        recipe=json.loads(self.plans[key]);self.counts['plan_decoded_bytes']+=len(self.plans[key].encode())
        result=self.memo[key];root=result['root'];core=tuple(tuple(c) for c in recipe['core'])
        source=recipe['source'];names=recipe['names'];kind=recipe['kind'];extra=recipe['extra']
        children=[self.emit(dep) for dep in recipe['dependencies']]
        old=self.solver._read(root,core,purpose='plan_existing')
        if old is None:
            rename={v:i+1 for i,v in enumerate(names)}
            def literal(l):return (1 if l>0 else -1)*rename[abs(l)]
            positions={c:i for i,c in enumerate(core)}
            cids={i:positions[tuple(sorted(literal(l) for l in clause))] for i,clause in zip(result['indices'],source,strict=True)}
            if kind=='empty':newproof=dict(kind='empty')
            elif kind=='implications':newproof=dict(kind=kind,variable=rename[extra['variable']],
                forward=[[literal(l),cids[c]] for l,c in extra['forward']],backward=[[literal(l),cids[c]] for l,c in extra['backward']])
            elif kind=='hall-v1':newproof=dict(kind=kind,groups=[cids[i] for i in extra['groups']])
            elif kind in ('component','positive-subsumption-v1'):
                if root!=children[0]['root']:raise ValueError('Subset plan changed identity')
                raise ValueError('Extracted child core was not retained')
            elif kind=='units':
                newproof=dict(kind=kind,trace=[[literal(l),cids[c]] for l,c in extra['trace']])
                if extra['conflict'] is not None:newproof['conflict']=cids[extra['conflict']]
                else:
                    assignment={abs(l):l>0 for l,_ in extra['trace']}
                    residual=restrict(source,assignment,self.counts)
                    child_source=restrict(extra['targets'],assignment,self.counts)
                    _,newproof['child']=checked_subset(self.solver,residual,child_source,self.counts)
            elif kind=='split':
                if extra['independent']:raise ValueError('Independent child core was not retained')
                v=extra['variable'];newproof=dict(kind=kind,variable=rename[v])
                for index,(value,field) in enumerate(((False,'low'),(True,'high'))):
                    residual=restrict(source,{v:value},self.counts)
                    small=restrict(extra['targets'][index],{v:value},self.counts)
                    _,newproof[field]=checked_subset(self.solver,residual,small,self.counts)
            else:raise ValueError('Unsupported plan kind')
            self.solver._store(root,dict(format=FORMAT,cnf=[list(c) for c in core],answer=False,proof=newproof))
            self.counts['extracted_core_publications']+=1
        elif old['answer'] is not False:raise ValueError('Conflicting core answer')
        self.emitted.add(key);self.counts['plan_emitted_recipes']+=1
        return result


class PlannedNegativeSolver(NegativeEditPoolSolver):
    def __init__(self,*args,plan_byte_limit=4*1024*1024,**kwargs):
        if type(plan_byte_limit) is not int or plan_byte_limit<1:raise ValueError('Invalid plan byte limit')
        self.plan_byte_limit=plan_byte_limit;self._support_plan=None;self._support_plan_origin=None
        super().__init__(*args,**kwargs)

    def _extract(self,key,materialize):
        if materialize:
            if self._support_plan is None or self._support_plan_origin!=key:
                self.counts['plan_materialize_fallbacks']+=1;return super()._extract(key,True)
            plan=self._support_plan;before=Counter(plan.counts)
            self.counts['negative_materialize_attempts']+=1;self.counts['plan_hits']+=1
            try:return plan.emit(key)
            finally:
                for k,v in plan.counts.items():self.counts['negative_materialize_'+k]+=v-before[k]
        plan=CausalPlan(self,node_limit=self.negative_node_limit,literal_limit=self.negative_support_literals,byte_limit=self.plan_byte_limit)
        self.counts['plan_discovery_attempts']+=1;fallback=False
        try:
            result=plan.prepare(key);self._support_plan=plan;self._support_plan_origin=key
            self.counts['negative_discover_attempts']+=1
            return result
        except PlanBudget:
            fallback=True;self.counts['plan_discovery_fallbacks']+=1
        except SupportBudget:
            self.counts['negative_discover_attempts']+=1;self.counts['negative_discover_budget_stops']+=1;return None
        finally:
            prefix='discarded_plan_' if fallback else 'negative_discover_'
            for k,v in plan.counts.items():self.counts[prefix+k]+=v
            self.counts['plan_peak_bytes']=max(self.counts['plan_peak_bytes'],plan.counts['plan_peak_bytes'])
        # No hint/proof from a discarded partial plan is promoted. Charge the
        # abandoned preparation, then preserve the preceding discovery policy.
        del plan
        return super()._extract(key,False)

    def _negative_reuse(self,cnf):
        try:return super()._negative_reuse(cnf)
        finally:self._support_plan=None;self._support_plan_origin=None

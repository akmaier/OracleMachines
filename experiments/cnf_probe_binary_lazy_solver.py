"""Run raw binary discovery before canonical certificate preparation.

Only a verified negative cofactor changes the branch selection. Satisfiable
binary subsets retain the same pending preparation and ordinary SAT fallback.
"""
from collections import Counter
from experiments import cnf_residual_dag as native
from experiments import cnf_cofactor_handoff as prepared
from experiments.cnf_probe_handoff import prepare
from experiments.cnf_probe_lifetime import ProbeLifetimeSolver
from experiments.cnf_probe_binary_lazy import lazy_closure


class LazyBinaryClosureSolver(ProbeLifetimeSolver):
    def _probe(self,cnf,variable,value):
        c=self.counts;c['bipolar_true_probes' if value else 'bipolar_false_probes']+=1
        raw,canonical=prepare(cnf,variable,value,c);child,names,key=canonical
        old=self._read(key,child,purpose='bipolar_cofactor') if self.reuse else None
        if old is not None:
            c['bipolar_cached_negative' if not old['answer'] else 'bipolar_cached_positive']+=1
            return (key,None) if not old['answer'] else (None,self._offer(raw,canonical,None))
        local=Counter();fixed,trace,conflict=prepared.original_propagate(child,local)
        c.update({'bipolar_'+k:v for k,v in local.items()});c['bipolar_probe_trace_entries']+=len(trace)
        if conflict is not None:
            self._store(key,dict(format=native.FORMAT,cnf=[list(cl) for cl in child],answer=False,
                proof=dict(kind='units',trace=trace,conflict=conflict)))
            c['bipolar_compiled_children']+=1;return key,None
        c['bipolar_no_conflict']+=1
        up=(fixed,trace,conflict,local.get('propagation_literal_visits',0))
        result=lazy_closure(canonical,up,c)
        if result['nodes']:
            for item in result['nodes']:
                node=item['node'];known=self._read(item['key'],tuple(map(tuple,node['cnf'])),purpose='closure_publication') if self.reuse else None
                if known is None:
                    self._store(item['key'],node);c['closure_published_nodes']+=1
                else:
                    if known['answer'] is not False:raise AssertionError('Contradictory binary certificate')
                    c['closure_existing_nodes']+=1
            c['closure_compiled_children']+=1
            return key,None
        c['closure_inconclusive']+=1
        return None,self._offer(raw,canonical,up)

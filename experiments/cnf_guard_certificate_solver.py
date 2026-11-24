"""Transport checked conditional unit traces into actual local probe cofactors.

Selection and recomposition remain inherited. All surviving support clauses must
occur in the actual cofactor; a full-source exclusion alone is insufficient.
No new proof rule: publication rechecks the resulting native unit certificate.
"""
from collections import Counter
from experiments import cnf_residual_dag as native
from experiments import cnf_cofactor_handoff as prepared
from experiments.cnf_guard_probe_solver import GuardProbeSolver
from experiments.cnf_probe_handoff import prepare
from experiments.cnf_probe_binary_lazy import lazy_closure
from experiments.cnf_partial_residual_pool import charge


def transport_checked(template,fixed,rename,child,counts):
    """Transform an already validated template; return None on missing support.

    fixed uses canonical source names; rename injects remaining source variables
    into the actual canonical child. The caller checks the guard and template.
    This private preparation result still requires the native proof checker.
    """
    if (any(type(v) is not int or v<1 or type(b) is not bool for v,b in fixed.items())
            or any(type(v) is not int or v<1 or type(w) is not int or w<1 for v,w in rename.items())
            or len(set(rename.values()))!=len(rename) or fixed.keys()&rename.keys()):
        return None
    if any(fixed.get(v)!=b for v,b in template['assumptions']):return None
    counts['position_clauses']+=len(child);counts['position_literals']+=sum(map(len,child))
    positions={cl:i for i,cl in enumerate(child)};ids=[]
    for clause in template['clauses']:
        reduced=[];satisfied=False
        for lit in clause:
            counts['transport_literal_visits']+=1;v=abs(lit)
            if v in fixed:
                if fixed[v]==(lit>0):satisfied=True;break
            elif v not in rename:return None
            else:reduced.append(rename[v]*(1 if lit>0 else -1))
        if satisfied:ids.append(None);continue
        cid=positions.get(tuple(sorted(reduced)))
        if cid is None:return None
        ids.append(cid)
    trace=[]
    for lit,cid in template['trace']:
        counts['transport_trace_steps']+=1
        if abs(lit) in fixed:
            if fixed[abs(lit)]==(lit>0):
                counts['transport_skipped_steps']+=1;continue
            if ids[cid] is None:return None
            counts['transport_early_conflicts']+=1
            return dict(kind='units',trace=trace,conflict=ids[cid])
        if ids[cid] is None or abs(lit) not in rename:return None
        trace.append([rename[abs(lit)]*(1 if lit>0 else -1),ids[cid]])
    cid=ids[template['conflict']]
    return None if cid is None else dict(kind='units',trace=trace,conflict=cid)


class GuardCertificateSolver(GuardProbeSolver):
    def __init__(self,*args,certificate_checks=100000,certificate_literals=1000000,**kwargs):
        if any(type(n) is not int or n<1 for n in (certificate_checks,certificate_literals)):
            raise ValueError('Positive certificate limits required')
        self.certificate_checks=certificate_checks;self.certificate_literals=certificate_literals
        self.certificate_summary=None
        super().__init__(*args,**kwargs)

    def solve(self,source):
        self.certificate_counts=Counter();self.certificate_records=None
        try:return super().solve(source)
        finally:
            self.certificate_summary=dict(counts=dict(self.certificate_counts),
                bank_bytes=charge((self.guard_templates,getattr(self,'guard_compiled',()),self.certificate_records)),
                limits=dict(checks=self.certificate_checks,literals=self.certificate_literals))
            self.certificate_records=None

    def _certificate(self,cnf,variable,value,canonical):
        c=self.certificate_counts
        parent=self.guard_parents[-1] if self.guard_parents else None
        if parent is None or parent['cnf'] is not cnf or variable not in parent['mapping']:
            c['unbound_probes']+=1;return None
        if self.certificate_records is None:
            # GuardProbeSolver has already validated every template this query.
            members=set(self.guard_source);self.certificate_records=[]
            for t in self.guard_templates:
                c['compile_support_clauses']+=len(t['clauses'])
                if all(tuple(cl) in members for cl in t['clauses']):
                    self.certificate_records.append((t,sum(map(len,t['clauses']))))
        fixed={**parent['fixed'],parent['mapping'][variable]:value}
        c['fixed_copy_entries']+=len(fixed)
        child,names,_=canonical;rename=None
        for t,size in self.certificate_records:
            if c['candidate_checks']>=self.certificate_checks:
                c['check_limit_misses']+=1;return None
            c['candidate_checks']+=1;matched=True
            for v,b in t['assumptions']:
                c['guard_pair_checks']+=1
                if fixed.get(v)!=b:matched=False;break
            if not matched:continue
            if c['reserved_support_literals']+size>self.certificate_literals:
                c['literal_limit_misses']+=1;continue
            c['reserved_support_literals']+=size;c['matched_templates']+=1
            if rename is None:
                if any(v not in parent['mapping'] for v in names):return None
                rename={parent['mapping'][v]:i+1 for i,v in enumerate(names)}
                c['mapped_names']+=len(names)
            proof=transport_checked(t,fixed,rename,child,c)
            if proof is not None:
                c['transported_proofs']+=1;c['transported_proof_steps']+=len(proof['trace'])
                return proof
            c['local_support_misses']+=1
        return None

    def _probe(self,cnf,variable,value):
        # Same preparation/cache/fallback as the frozen lazy probe. Insert only
        # the local certificate attempt before fresh full-cofactor propagation.
        c=self.counts;c['bipolar_true_probes' if value else 'bipolar_false_probes']+=1
        raw,canonical=prepare(cnf,variable,value,c);child,names,key=canonical
        old=self._read(key,child,purpose='bipolar_cofactor') if self.reuse else None
        if old is not None:
            c['bipolar_cached_negative' if not old['answer'] else 'bipolar_cached_positive']+=1
            return (key,None) if not old['answer'] else (None,self._offer(raw,canonical,None))
        proof=self._certificate(cnf,variable,value,canonical)
        if proof is not None:
            self._store(key,dict(format=native.FORMAT,cnf=[list(cl) for cl in child],answer=False,proof=proof))
            c['bipolar_compiled_children']+=1;return key,None
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

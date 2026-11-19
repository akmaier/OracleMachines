"""Bounded top-level affine refutations with the existing separate authority.

No native certificate acquires an extension dependency. Misses and budget stops
fall through to planned negative reuse; only independently checked contradictions
can return early. The owned connection is idle during immediate affine commits.
"""
from collections import Counter,defaultdict
import time
from experiments.cnf_support_plan import PlannedNegativeSolver
from experiments.cnf_affine_patterns import complete_half
from experiments.cnf_affine_negative import NegativeStore,FORMAT


def bounded_extract(cnf,counts,xor_limit):
    """The existing direct-XOR extraction, stopping before excess row XORs.

    The caller bounds normalized source size/variable width. No absent sign
    patterns are enumerated. None is a discovery stop, never a SAT verdict.
    """
    groups=defaultdict(list)
    for cid,clause in enumerate(cnf):
        support=tuple(sorted(abs(lit) for lit in clause));forbidden=sum(lit<0 for lit in clause)%2
        groups[support,forbidden].append(cid);counts['affine_grouping_literals']+=len(clause)
    equations=[];leftovers=[]
    for (support,forbidden),ids in sorted(groups.items()):
        if not support or complete_half(len(ids),len(support)):
            equations.append(dict(variables=list(support),rhs=1-forbidden,clauses=ids))
        else:leftovers.extend(ids)
    counts['affine_extracted_equations']+=len(equations);counts['affine_leftover_clauses']+=len(leftovers)
    basis={};reductions=[];xors=0
    for equation in equations:
        mask=sum(1<<(v-1) for v in equation['variables']);rhs=equation['rhs'];using=[]
        while mask:
            pivot=mask&-mask
            if pivot not in basis:basis[pivot]=len(reductions);break
            if xors==xor_limit:counts['affine_probe_xor_stops']+=1;return None
            previous=basis[pivot];using.append(previous)
            mask^=reductions[previous]['mask'];rhs^=reductions[previous]['rhs']
            xors+=1;counts['affine_elimination_xors']+=1
        reductions.append(dict(using=using,mask=mask,rhs=rhs))
    return dict(equations=equations,leftovers=sorted(leftovers),reductions=reductions)


class AffineProbeSolver(PlannedNegativeSolver):
    def __init__(self,*args,affine_variables=256,affine_clauses=4096,
                 affine_literals=16384,affine_xors=65536,**kwargs):
        if any(type(v) is not int or v<1 for v in (affine_variables,affine_clauses,affine_literals,affine_xors)):
            raise ValueError('Invalid affine probe limits')
        self.affine_variables=affine_variables;self.affine_clauses=affine_clauses
        self.affine_literals=affine_literals;self.affine_xors=affine_xors
        super().__init__(*args,**kwargs)
        try:self.affine=NegativeStore(self,create=True)
        except BaseException:self.close();raise

    def solve(self,source):
        if self.db.active or self.db.poisoned or self.db.in_transaction:
            raise RuntimeError('Affine probe requires an owned healthy idle connection')
        began=time.perf_counter();self.counts=Counter();cnf,names,root=self._canonical(source)
        node=self.affine.read(root,cnf) if self.reuse else None
        if node is not None:self.counts['affine_probe_exact_hits']+=1
        else:
            known=self.reuse and (self._read(root,cnf) is not None or self.equivalences.read(root) is not None)
            if known:self.counts['affine_probe_known_skips']+=1
            else:
                literals=sum(map(len,cnf));self.counts['affine_probe_size_literals']+=literals
                if len(names)>self.affine_variables or len(cnf)>self.affine_clauses or literals>self.affine_literals:
                    self.counts['affine_probe_size_skips']+=1
                else:
                    self.counts['affine_probe_attempts']+=1
                    evidence=bounded_extract(cnf,self.counts,self.affine_xors)
                    if evidence is not None and any(r['mask']==0 and r['rhs']==1 for r in evidence['reductions']):
                        # publish resets the counter and canonicalizes/checks again.
                        # Preserve every prepublication charge on success or failure.
                        before=Counter(self.counts)
                        try:self.affine.publish(cnf,dict(root=root,status='linear-conflict',affine=evidence))
                        finally:self.counts.update(before)
                        node=self.affine.read(root,cnf);self.counts['affine_probe_conflicts']+=1
                    else:self.counts['affine_probe_misses']+=1
        if node is None:
            before=Counter(self.counts)
            try:result=super().solve(source)
            finally:self.counts.update(before)
        else:
            nodes,payload=self.archive_storage()
            result=dict(answer=False,model=None,root=root,authority=FORMAT,quotient_choice=None,
                        archive_nodes=nodes,archive_payload_bytes=payload)
        result['affine_archive_nodes'],result['affine_archive_payload_bytes']=self.affine.storage()
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        return result

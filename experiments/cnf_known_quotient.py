"""Choose a checked known quotient before acquiring a fresh all-block quotient.

At most two alternatives: all discovered blocks, then the original first block.
Only ordinary native certificates qualify. Known models are transported back to
quotient coordinates; source recomposition uses the actually selected evidence.
"""
from collections import Counter
import time
from experiments.cnf_multiblock_equivalence import MultiEquivalenceSolver,check_blocks
from experiments.cnf_residual_dag import FORMAT as NATIVE_FORMAT,holds


class KnownQuotientSolver(MultiEquivalenceSolver):
    def choose_quotient(self,cnf,evidence):
        target,mapping=check_blocks(cnf,evidence,self.counts)
        if len(evidence)<2 or not self.reuse:return evidence,target,mapping,None,None
        c=self.counts;c['quotient_choice_calls']+=1;trace=dict(candidates=[],selected='all')
        def lookup(formula,label):
            normalized,names,key=self._canonical(formula);c['quotient_choice_lookups']+=1
            node=self._read(key,normalized,purpose='quotient_choice')
            trace['candidates'].append(dict(kind=label,key=key,known=node is not None))
            if node is None:return None
            c['quotient_choice_hits']+=1
            # _visit normally performs this canonical-name transport. No fresh
            # acquisition or second canonicalization is needed for a checked hit.
            model={old:node['model'][i] for i,old in enumerate(names)} if node['answer'] else None
            c['quotient_choice_model_variables']+=len(names) if model is not None else 0
            return model,key
        known=lookup(target,'all')
        if known is not None:
            c['quotient_choice_all_hits']+=1;return evidence,target,mapping,known,trace
        first=evidence[:1];alternate,alternate_mapping=check_blocks(cnf,first,c)
        c['quotient_choice_alternates_built']+=1
        known=lookup(alternate,'first')
        if known is not None:
            c['quotient_choice_first_hits']+=1;trace['selected']='first'
            return first,alternate,alternate_mapping,known,trace
        c['quotient_choice_both_miss']+=1
        return evidence,target,mapping,None,trace

    def solve(self,source):
        began=time.perf_counter();self.counts=Counter();cnf,names,root=self._canonical(source)
        native=self._read(root,cnf) if self.reuse else None;authority='native';model=None;choice=None
        if native is not None:
            if native['answer']:model=dict(enumerate(native['model'],1))
        elif self.reuse and self.equivalences.read(root) is not None:authority=self.equivalences.checked[root]['format']
        else:
            evidence=self.binary_cores.find(cnf) if self.leaves else None
            if evidence is None:model,_=self._visit(cnf)
            else:
                evidence,target,mapping,known,choice=self.choose_quotient(cnf,evidence)
                self.counts['multi_applied_blocks']+=len(evidence);self.counts['multi_applied_merges']+=len(mapping)-len(evidence)
                child_model,child=self._visit(target) if known is None else known
                if child_model is None:
                    node=self.equivalences.publish(root,cnf,evidence,child);authority=node['format']
                else:
                    model={v:False for v in range(1,len(names)+1)};model.update(child_model)
                    for variable,signed in mapping.items():model[variable]=model[abs(signed)] if signed>0 else not model[abs(signed)]
                    if not holds(cnf,model):raise ValueError('Invalid selected-quotient model lift')
                    self.counts['multi_positive_lifts']+=1;self.counts['multi_lift_variables']+=len(mapping)
                    self._store(root,dict(format=NATIVE_FORMAT,cnf=[list(c) for c in cnf],answer=True,model=[model[v] for v in range(1,len(names)+1)]))
        external=None if model is None else {old:model.get(i,False) for i,old in enumerate(names,1)}
        if external is not None and not holds(source,external):raise ValueError('Invalid source witness')
        self.counts['source_witness_literal_payload']+=sum(map(len,source)) if external is not None else 0
        nodes,payload=self.archive_storage()
        return dict(answer=external is not None,model=external,root=root,authority=authority,metrics=dict(self.counts),quotient_choice=choice,
            seconds=time.perf_counter()-began,archive_nodes=nodes,archive_payload_bytes=payload)

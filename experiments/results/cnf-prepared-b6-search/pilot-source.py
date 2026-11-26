"""Own one checked B6 input and reuse its index and live continuation state.

The input snapshot is private and never exposed through returned results.
Changing source/proofs/closure/trace allowance requires a new session. This is
an in-process owned object, not a security boundary against private reflection.
Cold recovery always rechecks the original inputs and the portable cursor.
"""
from copy import deepcopy
from experiments import cnf_b6_probe_cursor as candidate


class PreparedB6Search:
    def __init__(self,*inputs,counts,policy='reuse',cursor=None,trace_limit=256):
        if policy not in ('reuse','restart'):raise ValueError('Invalid prepared policy')
        # Own mutable caller payloads before checking them. No borrowed aliases
        # may change a validated clause, closure, guard or imported history.
        owned=deepcopy(inputs);counts['prepared_input_copies']+=1
        prepared,bank,ids,order,binding=candidate.prepare(*owned,counts,trace_limit=trace_limit)
        same=candidate.equivalent(prepared,owned[11],owned[13],owned[12],trace_limit,counts)
        if cursor is None and policy=='reuse' and same:
            cursor=deepcopy(owned[12]['cursor']);cursor.update(format=candidate.FORMAT,binding=binding)
            counts['b6_imported_completed']+=len(cursor['completed']);counts['b6_imported_failures']+=len(cursor['probes']);counts['b6_imported_cursors']+=1
        elif cursor is None:counts['b6_fresh_cursors']+=1
        else:cursor=deepcopy(cursor);counts['b6_continued_cursors']+=1
        (self._queue,self._promoted,self._tested,self._completed,self._probes,self._found,self._terminal)=candidate.load(prepared,order,binding,cursor,counts,trace_limit)
        self._binding=binding;self._prefix=tuple(map(tuple,owned[13]['units']));self._ids=tuple(ids);self._trace_limit=trace_limit
        self._bank=tuple(map(tuple,bank));self._index=None;self._pending=None
        counts['prepared_sessions']+=1
        # The earlier proof layers are discarded here after validation. The
        # exact binding and owned result proofs suffice for this fixed search;
        # a cold reader/native compiler still needs the original provenance.

    def advance(self,counts,*,probe_limit=64,work_limit=262144):
        if any(type(v) is not int or v<1 for v in (probe_limit,work_limit)):raise ValueError('Invalid prepared probe bounds')
        counts['prepared_advances']+=1
        def result(reason):
            state=dict(format=candidate.FORMAT,binding=self._binding,completed=self._completed,probes=self._probes)
            payload=dict(action='searched',program=candidate._program(self._probes,self._terminal,self._trace_limit,reason),cursor=state)
            counts['prepared_result_copies']+=1
            return deepcopy(payload)
        if self._terminal is not None:return result('opposite_probes')
        if len(self._prefix)>self._trace_limit:return result('trace_limit')
        if self._index is None:self._index=candidate.frozen.UnitIndex(self._bank,counts)
        start=counts['probe_occurrence_visits'];attempts=0
        while True:
            if self._pending is None:
                self._pending=candidate._next(self._queue,self._promoted,self._tested);self._promoted=None
            root,priority=self._pending
            if root is None:return result('complete')
            if attempts>=probe_limit:return result('probe_limit')
            attempts+=1;counts['probe_roots']+=1
            counts['cursor_promoted_probes' if priority else 'cursor_base_probes']+=1
            try:
                proof=self._index.probe(root,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),self._trace_limit-len(self._prefix))
            except candidate.frozen.ProbeLimit as error:
                # Keep the exact interrupted candidate, including promotion.
                counts['cursor_interrupted_probes']+=1
                return result(str(error))
            self._pending=None;self._completed.append(root);self._tested.add(root);counts['cursor_completed_probes']+=1
            if proof is None:continue
            proof=dict(units=[list(p) for p in self._prefix]+[[l,self._ids[cid]] for l,cid in proof['units']],conflict=self._ids[proof['conflict']])
            counts['cursor_lifted_steps']+=len(self._prefix)
            self._probes.append(dict(assumption=root,proof=proof));self._found[root]=len(self._probes)-1;counts['probe_exclusions']+=1
            if -root in self._found:
                self._terminal=dict(low=self._found[-abs(root)],high=self._found[abs(root)])
                return result('opposite_probes')
            if -root not in self._tested:self._promoted=-root

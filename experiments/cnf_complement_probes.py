"""Prioritize the untested opposite of a certified failed unit probe.

The clause bank and inference/checking/compilation are frozen. Scheduling uses
retained failures, never an assumption that the opposite branch also fails.
A per-call tested set prevents a promoted root from being probed twice.
"""
from collections import deque
from experiments import cnf_wide_guard_probes as frozen
validate=frozen.validate
compile_program=frozen.compile_program
compile_extension=frozen.compile_extension
bind_prefix=frozen.bind_prefix


def discover(source,templates,counts,*,mode='all',probe_limit=64,work_limit=262144,trace_limit=256):
    if any(type(v) is not int or v<1 for v in (probe_limit,work_limit,trace_limit)):raise ValueError('Positive probe bounds required')
    source,state,clauses,basis=frozen.prepare(source,templates,mode,counts);index=frozen.UnitIndex(clauses,counts)
    start=counts['probe_occurrence_visits'];records=[];found={}
    def remaining():return work_limit-(counts['probe_occurrence_visits']-start)
    def result(status,reason,terminal=None):return dict(status=status,reason=reason,mode=mode,probes=records,terminal=terminal,trace_limit=trace_limit)
    try:
        initial=index.probe(None,counts,remaining,trace_limit)
        if initial is not None:return result('refuted','units',dict(proof=initial))
        queue=deque(frozen.roots(source));tested=set();promoted=None
        counts['complement_queue_slots']=max(counts['complement_queue_slots'],len(queue))
        while queue or promoted is not None:
            priority=promoted is not None
            root=promoted if priority else queue.popleft();promoted=None
            if root in tested:counts['complement_duplicate_skips']+=1;continue
            if len(tested)>=probe_limit:return result('unresolved','probe_limit')
            tested.add(root);counts['complement_tested_peak']=max(counts['complement_tested_peak'],len(tested))
            counts['complement_promoted_probes' if priority else 'complement_base_probes']+=1
            counts['probe_roots']+=1;proof=index.probe(root,counts,remaining,trace_limit)
            if proof is None:
                if priority:counts['complement_open_opposites']+=1
                continue
            records.append(dict(assumption=root,proof=proof));found[root]=len(records)-1;counts['probe_exclusions']+=1
            if -root in found:return result('refuted','opposite_probes',dict(low=found[-abs(root)],high=found[abs(root)]))
            if -root not in tested:
                promoted=-root;counts['complement_promotions']+=1
    except frozen.ProbeLimit as error:return result('unresolved',str(error))
    return result('unresolved','complete')

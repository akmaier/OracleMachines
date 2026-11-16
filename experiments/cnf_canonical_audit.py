"""Reuse independently checked canonical form inside a complete cold audit.

The existing normalizer fast path scans the actual CNF, with the old normalizer
as fallback. No parent attestation, persisted validity bit or warm verifier is
trusted. Acquisition and the public inference default remain unchanged.
"""
from collections import Counter
import time
from types import MethodType
from unittest.mock import patch
from experiments import compare_cnf_scoped_refinement as previous
from experiments.cnf_canonical_source import canonical_key
from experiments.cnf_expanded_coverage import verifier_views
base=previous.base


class CanonicalAuditInventory(base.CompleteAdmissionInventory):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for _,view in verifier_views(self):
            view._canonical=MethodType(canonical_key,view)


def audit(path,protocol,*,canonical=False):
    if type(canonical) is not bool:raise ValueError('Boolean audit mode required')
    before=base.sha(path);start=time.perf_counter()
    cls=CanonicalAuditInventory if canonical else base.CompleteAdmissionInventory
    h=cls(path,**protocol['options']);h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with (base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')),
              patch.object(base.split,'discover_simplification',side_effect=AssertionError('assumption'))):
            rows=base.rows(h)
            for key in rows:assert base.owner(h,key)._load(key) is not None
            records=[]
            for identity,payload in h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'):
                record=base.load_json(payload);assert base.split.record_key(record)==identity
                base.split.verify(h,record,Counter());records.append(record)
            queries=base.load(protocol['queries']['path'])
            for q in queries:assert q['roots']==[h._canonical(q['source'],d)[2] for d in (0,1)]
            routes=base.routes_for(h,records);coverage=previous.nested.all_coverage(h,routes,queries)
            base.split.verify_positive(h,coverage['proof'],coverage['roots'],records,Counter())
            counters=Counter()
            for _,view in verifier_views(h):counters.update(view.counts)
            return dict(coverage=coverage,patterns=len(rows),pairs=len(records),original_bindings=len(queries),
                no_acquisition=True,seconds=time.perf_counter()-start,canonical=canonical,
                normalization_counts={k:v for k,v in counters.items() if k.startswith(('canonical_','normalize_','normalization_'))})
    finally:
        h.close()
        if base.sha(path)!=before:raise ValueError('Cold audit changed the database')

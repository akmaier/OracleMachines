"""Cold positive-query checks between complete archive checkpoints.

This checks a bound positive proof on the exact current snapshot. It does not
certify unrelated history or interpret absence of a proof as a negative verdict.
The caller must still completely audit the final archive before publishing it.
"""
from collections import Counter
import time
from unittest.mock import patch
from experiments import compare_cnf_bootstrap as base


def check_query(path, options, original, root, proof, claimed_closed):
    if type(claimed_closed) is not bool:
        raise ValueError('Boolean positive-claim flag required')
    before = base.sha(path); start = time.perf_counter()
    h = base.CompleteAdmissionInventory(path, **options); h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with (base.no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('acquisition')),
              patch.object(base.split, 'discover_simplification', side_effect=AssertionError('assumption'))):
            if h._canonical(original, 0)[2] != root or h._load(root) is None:
                raise ValueError('Unbound original query')
            expected = [root] if claimed_closed else []
            if proof.get('roots') != expected or (not claimed_closed and proof.get('steps') != []):
                raise ValueError('Proof does not match positive claim')
            identities = {s['rule']['id'] for s in proof['steps'] if s['rule']['kind'] == base.split.KIND}
            records = []
            for identity in sorted(identities):
                row = h.db.execute(f'SELECT payload FROM {base.split.TABLE} WHERE id=?', (identity,)).fetchone()
                if row is None:
                    raise ValueError('Missing query split record')
                record = base.load_json(row[0])
                if base.split.record_key(record) != identity:
                    raise ValueError('Foreign query split record')
                records.append(record)
            replay = base.split.verify_positive(h, proof, expected, records, Counter())
            return dict(positive_claim_checked=claimed_closed, no_negative_claim=True, no_acquisition=True,
                        split_records=len(records), positive_steps=len(replay.justified),
                        main_inventory_checked_nodes=len(h.checked), seconds=time.perf_counter()-start)
    finally:
        h.close()
        if base.sha(path) != before:
            raise ValueError('Query checking changed the snapshot')

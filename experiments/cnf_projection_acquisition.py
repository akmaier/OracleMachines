"""Acquire a minimal projection under the caller's shared admission budget.

A checked proposal is retained even when acquisition stops. It becomes a proof
route only when the exact target has an acquired, checked inventory record.
"""
import json
from collections import Counter

from experiments.cnf_anchored_subsets import anchored_certificate
from experiments.cnf_projection_bridge import FORMAT, projection, check, verify
from experiments.cnf_learning_batch import acquire
from experiments.cnf_variable_elimination import _limit


def propose(h, source_key, variable, counts):
    node = h._load(source_key)
    if node is None: raise ValueError('Missing projection source')
    if h._canonical(node['cnf'], node['depth'])[2] != source_key:
        raise ValueError('Foreign projection source policy')
    projected, names = projection(node['cnf'], variable, counts, 64)
    certificate = anchored_certificate(projected, counts)
    kept = certificate['kept']; positions = {old:new for new,old in enumerate(kept)}
    raw = [projected[i] for i in kept]
    target, _, key = h._canonical(raw, node['depth'])
    proof = dict(format=FORMAT, variable=variable, names=list(names),
                 subsumers=sorted([[i,positions[j]] for i,j in certificate['removed']]))
    # The existing bridge contract also rejects support lost by deletion.
    check(node['cnf'], [list(c) for c in target], proof, counts)
    return dict(source=source_key, target=key, proof=proof)


def acquire_projection(h, record, counts=None, *, state_limit=32, target_limit=32):
    counts = Counter() if counts is None else counts
    _limit(state_limit); _limit(target_limit)
    if not hasattr(h,'admitted') or h.admission_limit != state_limit:
        raise ValueError('Caller must establish one shared admission allowance')
    if type(record) is not dict or set(record) != {'source','target','proof'}:
        raise ValueError('Invalid projection proposal')
    node = h._load(record['source'])
    if node is None or h._canonical(node['cnf'],node['depth'])[2] != record['source']:
        raise ValueError('Missing or foreign projection source')
    try: target = json.loads(record['target'])[-1]
    except (ValueError,TypeError,IndexError) as exc: raise ValueError('Malformed projection target') from exc
    if h._canonical(target,node['depth'])[2] != record['target']:
        raise ValueError('Foreign projection target policy or depth')
    check(node['cnf'],target,record['proof'],counts)
    before = set(h.admitted)
    edge, pending, added = acquire(h,target,node['depth'],total_limit=state_limit,target_limit=target_limit)
    if not before <= h.admitted or len(h.admitted)>state_limit:
        raise ValueError('Projection acquisition lost shared accounting')
    if not pending:
        if edge['key'] != record['target']: raise ValueError('Incorrect acquired projection target')
        verify(h,record,counts)
    return dict(proposal=record, pending=pending, added=sorted(added),
                bridge=None if pending else record)

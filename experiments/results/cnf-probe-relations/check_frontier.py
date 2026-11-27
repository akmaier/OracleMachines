"""Separate cold replay and label audit for the post-hoc larger-input census."""
from pathlib import Path
from collections import Counter
from unittest.mock import patch
import json
from experiments import compare_cnf_probe_relations as s
base=s.base;old=s.old;k=s.k
out=Path('experiments/results/cnf-probe-relations');f=base.load(out/'frontier.json')
old.bound(f['inputs']);checked=0;failures=0
for row in f['cases']:
    p=old.bound(row['proof'])
    with patch.object(k.prior,'prepare_edge',side_effect=AssertionError('discovery')),patch.object(k.relations,'prepare_edge',side_effect=AssertionError('recognition')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')):
        got=k.check_certificate(row['source'],p)
    assert got['answer'] is None or got['answer']==row['truth']['answer']
    if row['truth']['answer']:assert k.native.holds(row['source'],{int(v):b for v,b in row['truth']['model'].items()})
    # Compare JSON values; integer-key ordering before serialization differs
    # from the lexicographic ordering of decoded string keys.
    assert row['truth']==json.loads(base.encode(s.oracle(row['source'])))
    for leaf in row['leaf_profiles']:
        cnf=tuple(map(tuple,p['nodes'][leaf['node']]['cnf']))
        for proof in leaf['failed_assumptions']:k.prior.check_probe(cnf,proof,Counter());failures+=1
    checked+=1
base.write(out/'frontier-validation.json',dict(passed=True,roots=checked,failed_assumptions_checked=failures,discovery_disabled_for_cold_replay=True,oracle_recomputed=True,frontier=old.binding(out/'frontier.json')))
print('Frontier:',checked,'roots cold replayed;',failures,'failed-assumption traces checked')

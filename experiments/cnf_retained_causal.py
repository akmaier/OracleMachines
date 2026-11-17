"""Load fingerprinted causal support hints without repeating their discovery.

Loading does not certify a core or its historical provenance. CausalCoreBank
checks the actual matched proof (materializing it when absent); the caller must
retain the complete cold query/proof and index-lineage audit.
"""
import hashlib
import json
from pathlib import Path
from experiments.cnf_causal_support import CausalCoreBank


def load_causal(path,expected_sha256):
    payload=Path(path).read_bytes()
    if hashlib.sha256(payload).hexdigest()!=expected_sha256:
        raise ValueError('Causal frontier fingerprint changed')
    frontier=json.loads(payload)
    if type(frontier) is not dict or frontier.get('causal_unit_slicing') is not True or frontier.get('deferred') is not True:
        raise ValueError('Expected a deferred causal frontier, not an old-rule bank')
    return frontier


def retained_bank(solver,frontier):
    if frontier.get('causal_unit_slicing') is not True or frontier.get('deferred') is not True:
        raise ValueError('Causal materializer binding required')
    return CausalCoreBank(solver,frontier['cores'])

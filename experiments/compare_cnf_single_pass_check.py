#!/usr/bin/env python3
"""Matched one-pass checking; reuse the archive-preserving comparison protocol."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_indexed_restriction as protocol
from experiments.cnf_indexed_restriction_inventory import IndexedRestrictionInventory
from experiments.cnf_single_pass_inventory import SinglePassCheckInventory

MODES = dict(baseline=(IndexedRestrictionInventory, protocol.OPTIONS),
             single=(SinglePassCheckInventory, protocol.OPTIONS))


def main():
    protocol.MODES = MODES
    protocol.main()
    # The shared protocol still checks prior answers, profiles, roots and every
    # persistent byte, then audits the archive with empty caches. Bind this
    # experiment's implementation and replace the previous study's description.
    output = Path(sys.argv[sys.argv.index('--output')+1])
    path = output/'report.json'; report = json.loads(path.read_text())
    for name in (str(Path(__file__)), 'experiments/cnf_single_pass_check.py',
                 'experiments/cnf_single_pass_inventory.py', 'solver/test_cnf_single_pass_check.py',
                 'experiments/cnf_shared_clause_check.py'):
        report['fingerprints'][name] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    report['limitations'] = [
        'Both modes use the same indexed restriction, ordered propagation and 1 MiB probe-check cache',
        'Candidate reconstructs directly in one pass, lazily copies affected clauses and shares untouched immutable tuples',
        'No additional retained cache; no dependence on discovery indexes or previously accepted verdicts',
        'Unit reasons, conflicts, fixed points, pure rounds and source bindings remain independently checked',
        'No recognition policy, budget, persistent proof or structural coverage change',
        'All reconstruction, validation, checking, serialization, persistence, solving and root lifts are timed',
        'All answers, profiles, identities and archive bytes match the previous 1497-source study',
        'Cold audits check all evidence with empty ephemeral caches; no duplicate full archive',
        'Generation, summaries, hashing, compression, initialization and audits excluded or measured separately',
        'One sequential synthetic-corpus timing; repeated subset controls are separate, not significance evidence',
        'Six-case Python allocation excludes native SQLite, RSS and full-corpus peak',
        'Operation categories differ; fewer literal visits are not an interchangeable CPU speed ratio']
    path.write_text(json.dumps(report, separators=(',', ':'))+'\n')


if __name__ == '__main__':main()

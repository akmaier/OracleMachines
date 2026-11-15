"""Resume with the complete historical source ledger, including indirect helpers.

The matched benchmark checks the acquisition report's immediate fingerprints.
Historical restoration also traverses older reports. Their complete preserved
source ledger is checked here before taking either the optional cache path or
its fallback. Charge this additional guard separately from the frozen benchmark.
"""
import json
from pathlib import Path
import time

from experiments.cnf_materialized_checkpoint import sha
from experiments.compare_cnf_materialized_checkpoint import (
    restore_checkpoint as restore_bound_snapshot, PARENT_SHA, DEFAULT_CACHE)

LEDGER = Path('experiments/results/cnf-retained-discovery/validation.json')
LEDGER_SHA = '5454d8b769ea90643ee4c16100f7da12af29ec54675d784dae0d67b727316075'


def check_source_ledger(path, expected_sha, parent_sha):
    if sha(path) != expected_sha: raise ValueError('Changed historical source ledger')
    ledger = json.loads(Path(path).read_text())
    if ledger['report_sha256'] != parent_sha:
        raise ValueError('Historical source ledger belongs to another checkpoint')
    for name, expected in ledger['source_fingerprints'].items():
        if sha(name) != expected: raise ValueError('Changed historical implementation')
    return len(ledger['source_fingerprints'])


def restore_checkpoint(report_path, path, tmp, cache_dir=DEFAULT_CACHE, metrics=None):
    """Authenticate the full source ledger before delegating to the bound loader."""
    started = time.perf_counter(); m = metrics if metrics is not None else {}
    count = check_source_ledger(LEDGER, LEDGER_SHA, PARENT_SHA)
    guard_seconds = time.perf_counter()-started
    result = restore_bound_snapshot(report_path, path, tmp, cache_dir, m)
    m.update(historical_source_files=count, source_ledger_seconds=guard_seconds,
             guarded_restore_seconds=time.perf_counter()-started)
    return result

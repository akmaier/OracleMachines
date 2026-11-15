#!/usr/bin/env python3
"""Compare full historical replay with a bound materialized checkpoint."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.cnf_materialized_checkpoint import materialize, restore_cached, sha
from experiments.continue_cnf_retained_discovery import (
    restore_checkpoint as authoritative_restore, prepare_handoff, BudgetedInventory,
    read_archive, digests, FILES as INHERITED_FILES)
from experiments.cnf_pattern_inventory import encode

PARENT = Path('experiments/results/cnf-retained-discovery/report.json')
PARENT_SHA = '0d59f8bb3018c78b5da947a31d1a0d492103c15968df7d706b7ad1910b038f84'
DEFAULT_CACHE = Path('solver/.cache/materialized-checkpoints')/PARENT_SHA
FORMAT = 'materialized-checkpoint-comparison-v1'
FILES = ['experiments/cnf_materialized_checkpoint.py',
         'experiments/compare_cnf_materialized_checkpoint.py',
         'experiments/validate_cnf_materialized_checkpoint.py',
         'solver/test_cnf_materialized_checkpoint.py', *INHERITED_FILES]


def evidence_digest(evidence):
    return hashlib.sha256(encode(evidence).encode()).hexdigest()


def restore_checkpoint(report_path, path, tmp, cache_dir=DEFAULT_CACHE, metrics=None):
    """Drop-in optional accelerator; return the acquisition report and evidence.

    The caller must authenticate this experiment report as with any checkpoint.
    Missing local objects use the unchanged authoritative restorer. This report
    does not create a new acquisition state or change the pending selection.
    """
    r = json.loads(Path(report_path).read_text())
    if r['format'] != FORMAT or r['parent'] != dict(path=str(PARENT), sha256=PARENT_SHA):
        raise ValueError('Incorrect materialization experiment parent')
    for name, digest in r['fingerprints'].items():
        if sha(name) != digest: raise ValueError('Changed materialization implementation')
    d = r['descriptor']
    return restore_cached(d['path'], d['sha256'], PARENT, PARENT_SHA, cache_dir,
                          path, tmp, authoritative_restore, metrics)


def run(out, cache_dir=DEFAULT_CACHE):
    out.mkdir(exist_ok=False); started = time.perf_counter()
    if sha(PARENT) != PARENT_SHA: raise ValueError('Changed acquisition checkpoint')
    result = dict(format=FORMAT, parent=dict(path=str(PARENT), sha256=PARENT_SHA),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        fingerprints={name:sha(name) for name in FILES}, runs=[],
        cache_directory=str(cache_dir), limitations=[
        'The descriptor is authenticated by this reviewed report. Digests establish equality to an independently checked history, not mathematical truth from an untrusted hash.',
        'Cache publication requires an exclusively owned closed database restored by the frozen authoritative chain. The original reports, archives and proofs remain authoritative and unchanged.',
        'Two reversed-order repetitions share OS caches; cold means fresh process-level verifier state, not a flushed filesystem cache. This is a single development-history measurement, not a universal speedup.',
        'Each arm runs a fresh canonical inventory and complete catalog/global query. No persisted Python verifier, negative-frontier certificate or altered recognition policy is used.',
        'Positive proofs, all ordered-table digests, full database byte identity including schema, complete sidecars and all parent implementation fingerprints remain checked. Archive bytes are authenticated before SQLite opens.',
        'One optional compressed database and evidence object consume additional disk space. Decoding creates a full working database. Peak RAM and multi-checkpoint cache eviction remain unmeasured/unimplemented.',
        'No new patterns, reference proofs or original coverage are acquired. The pending case 1062 split and interrupted admissions remain in their original acquisition artifacts. No unrestricted-SAT complexity bound follows.'])
    with tempfile.TemporaryDirectory() as td, patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('fresh discovery')):
        tmp = Path(td); prep = tmp/'preparation'; prep.mkdir(); seed = prep/'history'
        tick = time.perf_counter(); parent, *evidence = authoritative_restore(PARENT, seed, prep)
        result['preparation_restore_seconds'] = time.perf_counter()-tick
        bridges = read_archive(parent['bridges']); identity = sha(seed)
        descriptor, result['materialization'] = materialize(seed, evidence, bridges, PARENT, PARENT_SHA, cache_dir)
        descriptor_path = out/'snapshot-descriptor.json'; descriptor_path.write_text(encode(descriptor)+'\n')
        result['descriptor'] = dict(path=str(descriptor_path), sha256=sha(descriptor_path))
        result['evidence_sha256'] = evidence_digest(evidence)
        result['evidence_counts'] = list(map(len,evidence)); result['bridges'] = len(bridges)
        print(json.dumps(dict(prepared=True, restore=result['preparation_restore_seconds'],
                             materialization=result['materialization']['seconds'],
                             cache_bytes=result['materialization']['cached_bytes'])), flush=True)
        # Seed is not used by either arm: both independently reconstruct the same state.
        for repeat in range(2):
            for mode in (('legacy','materialized') if repeat == 0 else ('materialized','legacy')):
                name = f'{repeat}-{mode}'; work = tmp/name; work.mkdir(); output = out/name; output.mkdir()
                history = work/'history'; tick = time.perf_counter(); restore_metrics = {}
                if mode == 'legacy':
                    actual, *actual_evidence = authoritative_restore(PARENT, history, work)
                else:
                    actual, *actual_evidence = restore_cached(descriptor_path, result['descriptor']['sha256'],
                        PARENT, PARENT_SHA, cache_dir, history, work, authoritative_restore, restore_metrics)
                    assert restore_metrics['mode'] == 'materialized'
                restore_seconds = time.perf_counter()-tick
                assert actual == parent and evidence_digest(actual_evidence) == result['evidence_sha256']
                selection = read_archive(parent['next_selection'])
                startup, session = prepare_handoff(output/'startup', history, parent,
                    actual_evidence, bridges, selection, 'canonical')
                try:
                    retained = dict(current=len(session.h.checked), prepared=len(session.h.prepared.checked))
                    assert not session.h.admitted
                finally: session.h.close()
                sequence_seconds = time.perf_counter()-tick
                assert read_archive(startup['certificate']) == read_archive(parent['certificate'])
                # Independent post-timing identity audit includes full file bytes and all tables.
                audit_start = time.perf_counter(); db_sha = sha(history); tables = digests(history)
                assert db_sha == identity == descriptor['database']['raw_sha256']
                assert tables == parent['logical_table_digests']
                arm = dict(mode=mode, repeat=repeat, restore_seconds=restore_seconds,
                    startup_seconds=startup['seconds'], sequence_seconds=sequence_seconds,
                    restore_metrics=restore_metrics, startup_report=dict(path=str(output/'startup/report.json'),
                    sha256=sha(output/'startup/report.json')), table_digests=tables,
                    database_sha256=db_sha, database_bytes=history.stat().st_size,
                    evidence_sha256=evidence_digest(actual_evidence), retained_checked_nodes=retained,
                    covered=sum(startup['closed'][0]), no_discovery=True,
                    identity_audit_seconds=time.perf_counter()-audit_start)
                (output/'report.json').write_text(encode(arm)+'\n')
                result['runs'].append(dict(repeat=repeat, mode=mode, path=str(output/'report.json'), sha256=sha(output/'report.json')))
                print(json.dumps(dict(repeat=repeat, mode=mode, restore=restore_seconds,
                                     startup=startup['seconds'], sequence=sequence_seconds)), flush=True)
        assert sha(seed) == identity
    result.update(seconds=time.perf_counter()-started, seed_unchanged=True)
    (out/'report.json').write_text(encode(result)+'\n')
    print(json.dumps(dict(passed=True, seconds=result['seconds'], new_patterns=0)), flush=True)


if __name__ == '__main__': run(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv)>2 else DEFAULT_CACHE)

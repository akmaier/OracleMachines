#!/usr/bin/env python3
"""Matched fresh versus retained verifiers for five checkpoint stages and startup."""
from collections import Counter
import copy
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.cnf_checked_replay import CheckedReplay
from experiments.compare_cnf_canonical_source import (
    BudgetedInventory, read_archive, sha, digests, unpack, add_splits,
    verify_bridge, verify_positive, archive_json, FILES as INHERITED_FILES,
    restore_checkpoint as legacy_restore)
from experiments.cnf_expanded_coverage import verifier_views
from experiments.cnf_expansion_session import ExpansionSession
from experiments.cnf_session_query import query

STAGES = (
    ('compare_cnf_guarded_digests', 'cnf-guarded-digests'),
    ('compare_cnf_original_handoff', 'cnf-original-handoff'),
    ('compare_cnf_session_catalog', 'cnf-session-catalog'),
    ('compare_cnf_copyless_sequence', 'cnf-copyless-sequence'),
    ('compare_cnf_canonical_source', 'cnf-canonical-source'))
BASE = Path('experiments/results/cnf-reduction-reuse/report.json')
LATEST = Path('experiments/results/cnf-canonical-source/report.json')
FILES = ['experiments/cnf_checked_replay.py', 'experiments/compare_cnf_checked_replay.py',
         'solver/test_cnf_checked_replay.py', *INHERITED_FILES]


def counters(h):
    c = Counter()
    for _, view in verifier_views(h):
        c.update(view.counts)
    return c


def cache_size(h):
    return sum(len(view.checked) for _, view in verifier_views(h))


def suffix(seed, history, tmp, out, parent, evidence, mode):
    started = time.perf_counter(); shutil.copyfile(seed, history)
    result = dict(mode=mode, stages=[]); totals = Counter(); peak = 0
    state = None; parent_path = BASE
    try:
        for module_name, directory in STAGES:
            tick = time.perf_counter()
            module = importlib.import_module('experiments.'+module_name)
            report_path = Path('experiments/results')/directory/'report.json'
            r = json.loads(report_path.read_text())
            if (r['format'] != module.FORMAT or module.BASE != parent_path or
                    Path(r['parent']['path']) != parent_path or sha(parent_path) != r['parent']['sha256'] or
                    r['options'] != parent['options'] or r['baseline_closed'] != parent['final_closed']):
                raise ValueError('Checkpoint stage identity/policy mismatch')
            for name, digest in r['fingerprints'].items():
                if sha(name) != digest: raise ValueError('Changed checkpoint source')
            if digests(history) != r['seed_table_digests']:
                raise ValueError('Incorrect suffix seed')
            d = r['delta']; delta = tmp/directory
            if sha(d['path']) != d['sha256']: raise ValueError('Changed suffix archive')
            unpack(d['path'], delta, d['database_sha256'])
            row = dict(report=dict(path=str(report_path), sha256=sha(report_path)),
                       preparation_seconds=time.perf_counter()-tick)
            tick = time.perf_counter()
            if state is None: state = CheckedReplay(history, r['options'])
            before = counters(state.h)
            row['delta_check'] = state.merge(delta)
            row['delta_counts'] = dict(counters(state.h)-before)
            peak = max(peak, cache_size(state.h))
            if mode == 'fresh':
                totals.update(counters(state.h)); state.close(); state = None
            row['merge_check_seconds'] = time.perf_counter()-tick
            tick = time.perf_counter()
            if digests(history) != r['logical_table_digests']:
                raise ValueError('Incorrect suffix reconstruction')
            row['final_digest_seconds'] = time.perf_counter()-tick
            tick = time.perf_counter()
            evidence = add_splits(evidence, read_archive(r['splits']))
            bridges = read_archive(r['bridges'])
            if state is None: state = CheckedReplay(history, r['options'])
            before = counters(state.h)
            def check_positive(h):
                counts = Counter()
                for bridge in bridges: verify_bridge(h, bridge, counts)
                roots = [h._canonical(c['source'], h.config['max_depth'])[2]
                         for c, b in zip(r['cases'], r['final_closed'], strict=True) if b]
                verify_positive(h, read_archive(r['expanded_certificate']), roots, evidence, bridges, counts)
                return dict(counts)
            row['positive_check'] = state.check(check_positive)
            row['positive_counts'] = dict(counters(state.h)-before)
            peak = max(peak, cache_size(state.h))
            if mode == 'fresh':
                totals.update(counters(state.h)); state.close(); state = None
            row['positive_seconds'] = time.perf_counter()-tick
            result['stages'].append(row); parent = r; parent_path = report_path
        result['suffix_seconds'] = time.perf_counter()-started
        tick = time.perf_counter()
        if state is None: state = CheckedReplay(history, parent['options'])
        result['handoff_checked_nodes'] = cache_size(state.h)
        h = state.handoff()
        try:
            session = ExpansionSession(h, evidence, bridges)
            result['session_construction_seconds'] = time.perf_counter()-tick
            roots = [h._canonical(c['source'], h.config['max_depth'])[2] for c in parent['cases']]
            qr, selected, proofs = query(session, evidence, bridges, roots)
            assert qr['closed'] == [parent['final_closed'], parent['without_growth_closed']]
            assert selected == read_archive(parent['next_selection'])
            assert proofs[0] == read_archive(parent['certificate'])
            result['global_query'] = qr
            result['certificate'] = archive_json(out/'coverage.json.gz', proofs[0])
            result['selection'] = archive_json(out/'selection.json.gz', selected)
            result['startup_seconds'] = time.perf_counter()-tick
            result['sequence_seconds'] = time.perf_counter()-started
            result['final_checked_nodes'] = cache_size(h)
            result['peak_checked_nodes'] = max(peak, cache_size(h))
            totals.update(counters(h)); result['inventory_counts'] = dict(totals)
            assert not h.admitted
        finally: h.close()
        result['table_digests'] = digests(history)
        assert result['table_digests'] == parent['logical_table_digests']
        result['history_bytes'] = history.stat().st_size
        (out/'report.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
        return result
    finally:
        if state is not None: state.close()


def run(out):
    out.mkdir(exist_ok=False); start = time.perf_counter()
    result = dict(format='checked-checkpoint-suffix-v1',
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        parent=dict(path=str(LATEST),sha256=sha(LATEST)),
        base=dict(path=str(BASE),sha256=sha(BASE)),
        fingerprints={p:sha(p) for p in FILES}, runs=[])
    with tempfile.TemporaryDirectory() as td, patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('fresh discovery')):
        tmp = Path(td); seed = tmp/'seed'; tick = time.perf_counter()
        common = importlib.import_module('experiments.compare_cnf_guarded_digests')
        parent, *evidence = common.restore_base(BASE, seed, tmp)
        result['common_restore_seconds'] = time.perf_counter()-tick
        seed_sha = sha(seed)
        print(json.dumps(dict(common_restored=True,seconds=result['common_restore_seconds'])),flush=True)
        for repeat in range(2):
            for mode in (('fresh','retained') if repeat==0 else ('retained','fresh')):
                name=f'{repeat}-{mode}'; work=tmp/name; work.mkdir(); output=out/name; output.mkdir()
                r=suffix(seed,work/'history',work,output,parent,copy.deepcopy(evidence),mode)
                result['runs'].append(dict(repeat=repeat,mode=mode,path=str(output/'report.json'),sha256=sha(output/'report.json')))
                print(json.dumps(dict(repeat=repeat,mode=mode,suffix=r['suffix_seconds'],startup=r['startup_seconds'],sequence=r['sequence_seconds'],verified=r['inventory_counts']['verified_pattern_nodes'])),flush=True)
        assert sha(seed)==seed_sha
        # Independent replay uses the old restorers and fresh caches throughout.
        cold=tmp/'legacy';cold.mkdir();tick=time.perf_counter()
        latest,*final_evidence=legacy_restore(LATEST,cold/'history',cold)
        audit=dict(restore_seconds=time.perf_counter()-tick)
        before=sha(cold/'history');h=BudgetedInventory(cold/'history',**latest['options']);h.set_admission_budget(0)
        try:
            tick=time.perf_counter();bridges=read_archive(latest['bridges'])
            session=ExpansionSession(h,final_evidence,bridges)
            roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in latest['cases']]
            qr,chosen,plans=query(session,final_evidence,bridges,roots)
            assert qr['closed']==[latest['final_closed'],latest['without_growth_closed']]
            assert chosen==read_archive(latest['next_selection'])
            assert plans[0]==read_archive(latest['certificate'])
            audit.update(startup_seconds=time.perf_counter()-tick,covered=sum(qr['closed'][0]),
                         selection_matches=True,certificate_matches=True,no_discovery=not h.admitted)
        finally:h.close()
        assert sha(cold/'history')==before and digests(cold/'history')==latest['logical_table_digests']
        result['legacy_audit']=audit
    result.update(seconds=time.perf_counter()-start,seed_unchanged=True,
        scope='Five existing append checkpoints, no new SAT acquisition. Each arm includes a seed copy, metadata/source checks, ten full table-digest scans, archive hashing/decompression, conflict checks, all delta and positive checks, then complete session construction/global query and output serialization. Fresh closes verifier caches between phases; retained carries them across checked appends and into startup. Common older restoration and independent legacy audit are separate. Two reversed-order observations share OS caches; retained object counts are not peak RAM. Cached objects and rows remain exclusively owned and immutable except for checked append merges. Positive evidence does not establish negative frontier completeness; the complete global query still runs. No unrestricted-SAT or universal speedup claim.')
    (out/'report.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True,seconds=result['seconds'],covered=result['legacy_audit']['covered'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))

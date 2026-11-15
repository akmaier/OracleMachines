#!/usr/bin/env python3
"""Independent archive checks and exact selected-frontier diagnosis."""
from collections import Counter
import gzip
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import experiments.compare_cnf_complete_admission as study
from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_coupled_pivots import FrontierIndex, selected_children
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import components


def restore(entry, path):
    assert study.sha(entry['path']) == entry['sha256']
    path.write_bytes(gzip.decompress(Path(entry['path']).read_bytes()))
    assert study.sha(path) == entry['database_sha256']


def diagnose(path, options, root):
    h = CompleteAdmissionInventory(path, **options); h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with study.no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('Acquisition forbidden')):
            index = FrontierIndex(h); frontier = index.frontier(root)
            selected = {}; todo = [root]
            while todo:
                key = todo.pop()
                if key in selected:
                    continue
                node = h._load(key); selected[key] = node
                todo.extend(selected_children(node))
            leaves = []
            for key, multiplicity in frontier.items():
                node = h._load(key); source = node['cnf']
                assert node['kind'] == 'unresolved'
                leaves.append(dict(key=key, key_sha256=study.key_sha(key), source=source,
                    multiplicity=multiplicity, depth=node['depth'], shape=node['profile']['shape'],
                    outcomes=node['profile']['outcomes'], components=len(components(source, Counter())),
                    profile_status={k:v['status'] for k,v in node['profile'].items()
                                    if isinstance(v,dict) and 'status' in v}))
            summary = h._load(root)['summary']
            assert sum(frontier.values()) == summary['unresolved_leaves']
            assert sum(x['multiplicity']*x['shape']['literals'] for x in leaves) == summary['unresolved_literals']
            return dict(root=root, root_sha256=study.key_sha(root), summary=summary,
                selected_nodes=len(selected), selected_kinds=dict(Counter(n['kind'] for n in selected.values())),
                distinct_unresolved=len(leaves), leaves=leaves,
                interpretation='Selected decomposition frontier, not all attempted alternatives; unknown is not UNSAT.')
    finally:
        h.close()


def validate(out):
    began = time.perf_counter(); report = study.load(out/'report.json'); frozen = study.load(out/'frozen.json')
    assert study.sha(out/'frozen.json') == report['frozen_sha256']
    assert study.sha(frozen['protocol']['path']) == frozen['protocol']['sha256']
    for path, digest in frozen['source_fingerprints'].items():
        assert study.sha(path) == digest
    protocol = study.load(frozen['protocol']['path']); checked = []; digests = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for i, sample in enumerate(report['samples']):
            assert study.sha(sample['path']) == sample['sha256']
            data = study.load(sample['path']); path = tmp/f'stream-{i}'; restore(data['archive'],path)
            replay = study.cold(path, protocol['options'], data['records'], protocol['cases'])
            for row in data['records']:
                assert len(set(row['admitted_ids'])) == row['entered']
                assert len(set(row['stored_ids'])) == row['stored']
                assert len(set(row['stored_ids'])-set(row['admitted_ids'])) == row['off_ledger']
                if sample['mode'].startswith('complete'):
                    assert row['off_ledger'] == 0
                    assert row['entered'] <= study.MODES[sample['mode']][1]
            checked.append(dict(label=f"{sample['mode']}-{sample['repeat']}", **replay))
            digests[(sample['mode'],sample['repeat'])] = data['row_digest']
        for repeat in range(2):
            assert digests[('complete32',repeat)] == digests[('legacy32',repeat)]
            assert digests[('complete4096',repeat)] == digests[('legacy4096',repeat)]
        initial = study.load(study.PARENT/'family-control/family-0/report.json')['archive']
        path = tmp/'original'; restore(initial,path)
        h = CompleteAdmissionInventory(path, **protocol['options'])
        original_rows = study.rows(h); h.close()
        resumptions = {}
        for mode, entry in report['resumptions'].items():
            assert study.sha(entry['path']) == entry['sha256']
            data = study.load(entry['path']); previous = original_rows if mode == 'prepared' else {}
            all_ids = set()
            for step in data['steps']:
                path = tmp/f"{mode}-{step['batch']}"; restore(step['archive'],path)
                replay = study.cold(path, protocol['options'], [step], protocol['cases'])
                h = CompleteAdmissionInventory(path, **protocol['options'])
                after = study.rows(h); h.close()
                assert previous.items() <= after.items()
                assert len(after)-len(previous) == step['stored']
                assert {study.key_sha(k) for k in set(after)-set(previous)} == set(step['stored_ids'])
                assert step['off_ledger'] == 0 and step['entered'] <= 32
                previous = after; all_ids.update(step['admitted_ids'])
                checked.append(dict(label=f"{mode}-{step['batch']}", **replay))
            resumptions[mode] = dict(repeated_admissions=data['entered']-len(all_ids),
                initial_patterns=data['initial_patterns'], final_patterns=len(previous),
                stored=data['stored'], entered=data['entered'], distinct_admitted=len(all_ids),
                probes=data['probes'], closed=data['closed'], capped=data['capped'],
                final_archive=data['steps'][-1]['archive'])
        data = study.load(out/'complete4096-0/report.json'); path = tmp/'frontier'
        restore(data['archive'],path)
        frontier = diagnose(path, protocol['options'], data['records'][41]['root'])
        study.write(out/'selected-frontier.json',frontier)
    result = dict(passed=True, report_sha256=study.sha(out/'report.json'),
        validator_sha256=study.sha(__file__), archives=checked, same_graphs_at_both_allowances=True,
        resumptions=resumptions, selected_frontier_sha256=study.sha(out/'selected-frontier.json'),
        distinct_unresolved=frontier['distinct_unresolved'], frontier_shapes=[x['shape'] for x in frontier['leaves']],
        next_target='Retain unfinished profile work and refine the connected 38-variable depth-zero residual; increasing this policy admission allowance alone did not close it.',
        seconds=time.perf_counter()-began)
    study.write(out/'reconstruction.json',result)
    print(json.dumps(dict(passed=True,archives=len(checked),same_graphs_at_both_allowances=True,
        resumptions={m:{k:v for k,v in r.items() if k!='final_archive'} for m,r in resumptions.items()},
        frontier_shapes=result['frontier_shapes'])))


if __name__ == '__main__':
    validate(Path(sys.argv[1]))

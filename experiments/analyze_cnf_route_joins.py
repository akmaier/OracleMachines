#!/usr/bin/env python3
"""Extract and independently check exact joins between two recorded SAT routes.

This is retrospective, acquisition-free analysis. Shared subproofs do not imply
cross-input reuse or a counterfactual saving: the original query is already
covered, and reaching a shared boundary still has to be paid for.
"""
from collections import Counter, defaultdict
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap as base


def binding(path):
    return dict(path=str(path), sha256=base.sha(path))


def bound(entry):
    assert base.sha(entry['path']) == entry['sha256'], entry['path']
    return base.load(entry['path'])


def analyze(directory, out):
    out.mkdir(exist_ok=False); started = time.perf_counter()
    cp = base.load(directory/'checkpoint.json'); report = bound(cp['report'])
    for path, digest in cp['source_fingerprints'].items():
        assert base.sha(path) == digest, path
    protocol = bound(cp['protocol']); modes = ('committed', 'pilot')
    trials = {}
    for mode in modes:
        sample = next(s for s in report['samples'] if s['mode'] == mode and s['repeat'] == 0)
        stream = bound(sample); batches = [bound(s) for s in stream['samples']]
        trials[mode] = dict(batch=batches[-1], new={k for b in batches for k in b['stored_ids']})
    maps = {m:{s['source']:s for s in trials[m]['batch']['target_proof']['steps']} for m in modes}
    new = {m:{k for k in maps[m] if base.key_sha(k) in trials[m]['new']} for m in modes}
    shared = new[modes[0]] & new[modes[1]]
    assert shared and all(maps[modes[0]][k] == maps[modes[1]][k] for k in shared)
    incoming = {}
    for mode in modes:
        parents = defaultdict(list)
        for key, step in maps[mode].items():
            for child in step['children']:
                parents[child].append(key)
        incoming[mode] = parents
    entrances = {m:{k for k in shared if any(p not in shared for p in incoming[m][k])} for m in modes}
    assert entrances[modes[0]] == entrances[modes[1]], 'Different boundaries need separate analysis'
    roots = sorted(entrances[modes[0]])

    def descendants(root):
        seen = set(); todo = [root]
        while todo:
            key = todo.pop()
            if key in seen:
                continue
            seen.add(key); todo.extend(maps[modes[0]][key]['children'])
        return seen

    regions = {k:descendants(k) for k in roots}
    reach = set.union(*regions.values())
    assert all(k in maps[modes[1]] and maps[modes[0]][k] == maps[modes[1]][k] for k in reach)
    assert reach & (new[modes[0]] | new[modes[1]]) == shared
    assert set.union(*(s & shared for s in regions.values())) == shared
    assert sum(len(s & shared) for s in regions.values()) == len(shared), 'Overlapping new regions'
    proof = dict(format=trials[modes[0]]['batch']['target_proof']['format'], roots=roots,
                 steps=[s for s in trials[modes[0]]['batch']['target_proof']['steps'] if s['source'] in reach])
    rows = []; counters = Counter()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'h'; base.restore_archive(cp['archive'], path)
        h = base.CompleteAdmissionInventory(path, **protocol['options']); h.set_admission_budget(0)
        try:
            records = dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
            with (base.no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('analysis admission')),
                  patch.object(base.split, 'discover_simplification', side_effect=AssertionError('analysis assumption'))):
                base.split.verify_positive(h, proof, roots, [base.load_json(v) for v in records.values()], counters)
                for key in roots:
                    parents = {m:[dict(source_sha256=base.key_sha(p), kind=h._load(p)['kind'],
                        shape=h._load(p)['profile']['shape']) for p in incoming[m][key] if p not in shared] for m in modes}
                    region = regions[key]; steps = [maps[modes[0]][k] for k in region]
                    rows.append(dict(source=key, source_sha256=base.key_sha(key), kind=h._load(key)['kind'],
                        shape=h._load(key)['profile']['shape'], new_steps=len(region & shared),
                        prior_steps=len(region-shared), unique_steps=len(region),
                        rule_counts=dict(Counter(s['rule']['kind'] for s in steps)), parents=parents))
                raw_patterns = sum(len(k.encode())+len(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0].encode()) for k in shared)
                split_ids = {s['rule']['id'] for s in proof['steps'] if s['rule']['kind'] == base.split.KIND}
                raw_splits = sum(len(k.encode())+len(records[k].encode()) for k in split_ids)
        finally:
            h.close(); assert base.sha(path) == cp['archive']['database_sha256']
    base.write(out/'proof.json', proof); base.write(out/'anchors.json', rows)
    result = dict(checkpoint=binding(directory/'checkpoint.json'), report=cp['report'],
        analyzer=binding('experiments/analyze_cnf_route_joins.py'), modes=modes, no_acquisition=True,
        exact_policy_depth_and_cnf_keys=True, identical_shared_steps=True,
        disjoint_new_regions=True, entrances=len(roots), shared_new_steps=len(shared),
        shared_new_nonterminal_steps=sum(maps[modes[0]][k]['rule']['kind'] != 'family' for k in shared),
        shared_new_rule_counts=dict(Counter(maps[modes[0]][k]['rule']['kind'] for k in shared)),
        unique_join_proof_steps=len(reach), inherited_join_steps=len(reach-shared),
        raw_shared_pattern_key_payload_bytes=raw_patterns, raw_shared_split_id_payload_bytes=raw_splits,
        shared_split_records=len(split_ids), check_counts=dict(counters),
        proof=binding(out/'proof.json'), anchors=binding(out/'anchors.json'), seconds=time.perf_counter()-started,
        limits=['Same original under two expansion policies, not different inputs.',
            'The original is already covered: direct root reuse supersedes re-solving it through these joins.',
            'Matching requires the full existing policy/depth/canonical-CNF key and checked boundary transformations; no approximate substitution.',
            'Raw key/payload bytes exclude SQLite pages, indexes, Python overhead and persistence copies; they are not measured memory savings.',
            'No avoided-work or cross-input speedup measurement. Discovering and checking paths to these boundaries remains charged.'])
    base.write(out/'report.json', result)
    print(base.encode({k:result[k] for k in ('entrances','shared_new_steps','shared_new_nonterminal_steps','unique_join_proof_steps','raw_shared_pattern_key_payload_bytes','raw_shared_split_id_payload_bytes','seconds')}))


if __name__ == '__main__':
    analyze(Path(sys.argv[1]), Path(sys.argv[2]))

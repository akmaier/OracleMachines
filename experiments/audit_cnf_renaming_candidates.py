"""Check signed-renaming exclusions on a hash-bound, cold-verified candidate set."""
from collections import Counter
from itertools import combinations
import hashlib
import json
from pathlib import Path
import time

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_renaming_invariant import profile, FIELDS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs(parent_path):
    parent_path = Path(parent_path)
    manifest = parent_path.with_name('manifest.json')
    hashes = json.loads(manifest.read_text())['artifacts']
    findings_path = parent_path.with_name('structural-findings.json')
    for path in (parent_path, findings_path):
        if sha(path) != hashes[str(path)]:
            raise ValueError('Changed archived candidate evidence')
    findings = json.loads(findings_path.read_text())['next_profile']
    candidates = findings['candidates']
    rows = []
    for candidate in candidates:
        if candidate['record']['source'] != findings['source']:
            raise ValueError('Candidate source mismatch')
        for value, edge in zip((False, True), candidate['record']['edges'], strict=True):
            key = edge['key']
            rows.append(dict(variable=candidate['rank'][-1], value=value,
                             key_sha256=hashlib.sha256(key.encode()).hexdigest(), cnf=json.loads(key)[-1]))
    bound = dict(parent=dict(path=str(parent_path), sha256=sha(parent_path)),
                 findings=dict(path=str(findings_path), sha256=sha(findings_path)),
                 manifest=dict(path=str(manifest), sha256=sha(manifest)),
                 source_sha256=findings['source_sha256'])
    return rows, bound


def analyze(rows, counts):
    profiles = [profile(row['cnf'], counts) for row in rows]
    signatures = [encode(p) for p in profiles]
    pairs = []
    for a, b in combinations(range(len(rows)), 2):
        field = next((f for f in FIELDS if profiles[a][f] != profiles[b][f]), None)
        counts['candidate_pairs_compared'] += 1
        pairs.append(dict(left=a, right=b, field=field))
    return dict(target_profiles=profiles, pair_exclusions=pairs,
                distinct_profiles=len(set(signatures)),
                excluded_pairs=sum(p['field'] is not None for p in pairs),
                inconclusive_pairs=sum(p['field'] is None for p in pairs))


def verify(report):
    rows, bound = inputs(report['inputs']['parent']['path'])
    if bound != report['inputs']:
        raise ValueError('Changed candidate input binding')
    labels = [{k: v for k, v in row.items() if k != 'cnf'} for row in rows]
    if labels != report['targets']:
        raise ValueError('Changed target labels')
    # Recompute every profile, then check each claimed necessary-invariant mismatch.
    checked = [profile(row['cnf']) for row in rows]
    if checked != report['analysis']['target_profiles']:
        raise ValueError('Changed occurrence profiles')
    expected = list(combinations(range(len(rows)), 2))
    if [(p['left'], p['right']) for p in report['analysis']['pair_exclusions']] != expected:
        raise ValueError('Missing or repeated candidate pair')
    for pair in report['analysis']['pair_exclusions']:
        a, b, field = pair['left'], pair['right'], pair['field']
        if field is None:
            if checked[a] != checked[b]: raise ValueError('Incorrect inconclusive result')
        elif field not in FIELDS or checked[a][field] == checked[b][field]:
            raise ValueError('Invalid exclusion witness')
    expected_analysis = analyze(rows, Counter())
    if report['analysis'] != expected_analysis:
        raise ValueError('Changed profile grouping or exclusion count')
    return dict(targets=len(rows), excluded_pairs=expected_analysis['excluded_pairs'],
                inconclusive_pairs=expected_analysis['inconclusive_pairs'], passed=True)


def run(parent_path, output):
    started = time.perf_counter(); rows, bound = inputs(parent_path)
    preparation = time.perf_counter()-started; counts = Counter(); tick = time.perf_counter()
    result = analyze(rows, counts); discovery = time.perf_counter()-tick
    report = dict(format='candidate-renaming-audit-v1', inputs=bound,
                  targets=[{k: v for k, v in r.items() if k != 'cnf'} for r in rows],
                  analysis=result, counts=dict(counts), preparation_seconds=preparation,
                  discovery_seconds=discovery,
                  scope='Necessary invariants only. A mismatch excludes signed variable bijections on normalized clause sets, not semantic equivalence. Equality is inconclusive. This audit does not acquire, solve or alter scheduling.')
    tick = time.perf_counter(); report['verification'] = verify(report)
    report['verification_seconds'] = time.perf_counter()-tick
    report['before_write_seconds'] = time.perf_counter()-started
    Path(output).write_text(encode(report)+'\n')
    return dict(path=str(output), sha256=sha(output))

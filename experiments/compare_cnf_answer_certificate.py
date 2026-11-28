#!/usr/bin/env python3
"""Fixed-trace answer projection, with separate construction and cold replay."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import gzip
import hashlib
import json
import resource
import re
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import cnf_answer_certificate as e
from experiments import cnf_watched_learning as watched
from experiments import compare_cnf_reuse_transfer as prior

PARENT = Path('experiments/results/cnf-reuse-transfer')
FILES = ('experiments/cnf_answer_certificate.py',
         'experiments/compare_cnf_answer_certificate.py',
         'experiments/validate_cnf_answer_certificate.py',
         'solver/test_cnf_answer_certificate.py')
sha, load, encode, write, binding, bound = prior.sha, prior.load, prior.encode, prior.write, prior.binding, prior.bound


def rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def freeze(out):
    out.mkdir(exist_ok=True)
    assert not (out / 'protocol.json').exists()
    cp = load(PARENT / 'checkpoint.json')
    sources = {**cp['source_fingerprints'], **{f: sha(f) for f in FILES}}
    for f, h in sources.items(): assert sha(f) == h, f
    cases = []
    for origin in ('fresh8000', 'reuse8000'):
        report = load(PARENT / (origin + '-0') / 'report.json')
        for case in report['cases']:
            cases.append(dict(key=origin + '-' + case['id'], id=case['id'], origin=origin,
                              archive=binding(PARENT / (origin + '-0') / (case['id'] + '.json')),
                              expected=case['result']))
    write(out / 'protocol.json', dict(parent=binding(PARENT / 'checkpoint.json'),
        parent_manifest=binding(PARENT / 'manifest.json'), panel=binding(PARENT / 'panel.json'),
        source_fingerprints=sources, cases=cases,
        prior_proof_hashes=[hashlib.sha256(block.encode()).hexdigest() for block in re.findall(
            r'\\begin\{proof\}.*?\\end\{proof\}',
            Path('paper/bounded_domain_sat_and_amortized_reasoning.tex').read_text(), re.S)],
        orders=[['full', 'answer'], ['answer', 'full']],
        scope='32 fixed traces on the same 16 related targets: fresh and reuse. Primary comparison is reuse (all 16 answered); fresh includes seven unknowns, reported separately. No discovery rerun or new sample.',
        accounting='Project once from each checked archive; keep every original archive. Persist both full and projected controls with identical canonical JSON and per-case gzip. Time reads, full validation, projection/output validation, encoding, compression and writes separately. Four new processes read/hash/decompress/check only their assigned certificate arm and original CNF. Process wall time includes startup; worker time excludes startup and report writing. OS caches not flushed; peak RSS is process high-water mark. Full control transcode is measurement setup, separately charged. Original discovery/acquisition, old archive storage and independent audits remain additional.',
        limitations='Current-answer projection is not archive deletion, admission tuning, a new SAT class, compact arbitrary proofs or an unrestricted polynomial-time solver. Unknown remains unknown; its empty marker gives no answer or reusable knowledge. No original source clauses are removed from checking.'))


def check_sources(protocol):
    for f in FILES: assert sha(f) == protocol['source_fingerprints'][f], f


def construct(out):
    assert not (out / 'construction.json').exists()
    started = time.perf_counter()
    p = load(out / 'protocol.json'); check_sources(p)
    rows = {r['id']: r for r in prior.source_rows(p)}
    for arm in ('full', 'answer'): (out / arm).mkdir()
    cases = []
    for case in p['cases']:
        source = rows[case['id']]['source']; phases = {}; counts = Counter()
        start = time.perf_counter(); archive = bound(case['archive'])
        phases['archive_read_hash_seconds'] = time.perf_counter() - start
        start = time.perf_counter(); answer, diag = e.project(source, archive, counts)
        phases['projection_including_both_checks_seconds'] = time.perf_counter() - start
        refs = {}; sizes = {}
        for arm, proof in (('full', archive), ('answer', answer)):
            start = time.perf_counter(); data = encode(proof).encode()
            phases[arm + '_encoding_seconds'] = time.perf_counter() - start
            start = time.perf_counter(); compressed = gzip.compress(data, mtime=0)
            phases[arm + '_compression_seconds'] = time.perf_counter() - start
            path = out / arm / (case['key'] + '.json.gz')
            start = time.perf_counter(); path.write_bytes(compressed)
            phases[arm + '_write_seconds'] = time.perf_counter() - start
            refs[arm] = binding(path)
            sizes[arm] = dict(json_bytes=len(data), gzip_bytes=len(compressed),
                              json_sha256=hashlib.sha256(data).hexdigest())
        cases.append(dict(**case, kind=archive['kind'], certificates=refs, sizes=sizes,
                          diagnostic=diag, counts=dict(counts), phases=phases))
        print(case['key'], archive['kind'], diag['original_derivations'], '->', diag['retained_derivations'], flush=True)
    write(out / 'construction.json', dict(protocol=binding(out / 'protocol.json'), cases=cases,
          complete_seconds=time.perf_counter() - started, peak_rss_bytes=rss()))


def read_certificate(ref):
    data = Path(ref['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != ref['sha256']: raise ValueError('Changed certificate bytes')
    return json.loads(gzip.decompress(data))


def replay(out, arm, repeat):
    started = time.perf_counter(); p = load(out / 'protocol.json'); check_sources(p)
    rows = {r['id']: r for r in prior.source_rows(p)}
    construction = load(out / 'construction.json'); input_seconds = time.perf_counter() - started
    cases = []; total = Counter()
    # A replay has no access to original archive reads or projection; hashes
    # identify bytes only, and the unchanged checker establishes the answer.
    with patch.object(e, 'project', side_effect=AssertionError), \
         patch.object(watched, 'search', side_effect=AssertionError), \
         patch.object(watched, 'expand', side_effect=AssertionError), \
         patch.object(watched.selective, 'transport', side_effect=AssertionError), \
         patch.object(e.resolution, 'search', side_effect=AssertionError), \
         patch.object(prior, 'parent_data', side_effect=AssertionError):
        for case in construction['cases']:
            counts = Counter(); start = time.perf_counter()
            proof = read_certificate(case['certificates'][arm])
            read_seconds = time.perf_counter() - start
            start = time.perf_counter(); result = e.resolution.check_result(rows[case['id']]['source'], proof, counts)
            checking = time.perf_counter() - start
            assert json.loads(encode(result)) == case['expected']
            cases.append(dict(key=case['key'], origin=case['origin'], kind=proof['kind'],
                              result=result, counts=dict(counts), read_seconds=read_seconds,
                              checking_seconds=checking, complete_seconds=read_seconds + checking))
            total.update(counts)
            del proof
    report = dict(arm=arm, repeat=repeat, cases=cases, counts=dict(total),
                  complete_seconds=time.perf_counter() - started, input_seconds=input_seconds,
                  peak_rss_bytes=rss(), search_transport_projection_disabled=True)
    write(out / f'replay-{arm}-{repeat}.json', report)


def run(out):
    samples = []
    for repeat, order in enumerate(load(out / 'protocol.json')['orders']):
        for arm in order:
            start = time.perf_counter()
            subprocess.run([sys.executable, __file__, 'replay', str(out), arm, str(repeat)], check=True)
            wall = time.perf_counter() - start
            samples.append(dict(report=binding(out / f'replay-{arm}-{repeat}.json'), process_wall_seconds=wall))
            print(arm, repeat, round(wall, 5), flush=True)
    write(out / 'comparisons.json', dict(samples=samples))


if __name__ == '__main__':
    action = sys.argv[1]; out = Path(sys.argv[2])
    if action == 'replay': replay(out, sys.argv[3], int(sys.argv[4]))
    else: globals()[action](out)

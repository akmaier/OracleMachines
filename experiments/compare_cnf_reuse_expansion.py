#!/usr/bin/env python3
"""Frozen budget expansion with an equal-budget fresh-search ablation."""
from collections import Counter
from pathlib import Path
import gzip, resource, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import cnf_watched_learning as e
from experiments import compare_cnf_selective_learning as previous
from experiments.compare_cnf_boundary_transfer import sha, load, encode, write, binding, bound, source_rows

PARENT = Path('experiments/results/cnf-watched-learning')
POLICIES = {'reuse2000': (True, 2000), 'fresh8000': (False, 8000), 'reuse8000': (True, 8000)}
FILES = ('experiments/compare_cnf_reuse_expansion.py', 'experiments/audit_cnf_reuse_expansion.py',
         'experiments/validate_cnf_reuse_expansion.py', 'solver/test_cnf_reuse_expansion.py')


def prepare(out):
    assert not (out / 'protocol.json').exists()
    parent = load(PARENT / 'checkpoint.json'); old = load(PARENT / 'protocol.json')
    for file, h in parent['source_fingerprints'].items():
        assert sha(file) == h, file
    write(out / 'protocol.json', dict(
        parent=binding(PARENT / 'checkpoint.json'), parent_manifest=binding(PARENT / 'manifest.json'),
        panel=old['panel'], references=old['references'], transport=old['transport'],
        baseline_records=binding(PARENT / 'watched-0/report.json'), policies=POLICIES,
        source_fingerprints={**parent['source_fingerprints'], **{f: sha(f) for f in FILES}},
        orders=[['reuse2000', 'fresh8000', 'reuse8000'], ['reuse8000', 'fresh8000', 'reuse2000']],
        limitations=[
            'Budget policy frozen before these runs: all 16 exposed edited targets, unchanged source bytes, target-only proposal and watched learner. Reuse at 2000 and 8000 contexts; fresh search at 8000. No label-dependent selection or tuning. This is exposed-policy development, not new external transfer.',
            'Every reuse run starts from the original parent proof, transports all surviving derivations and searches from an empty trail. The larger run is not a continuation of the measured smaller run; their costs are not subtracted. All retained clauses are active. No pruning, restart, admission or production-default change.',
            'Fresh8000 measures the same watched search budget without parent reads, transport, augmented clauses or retained proof. Equal context caps do not imply equal work. Reference outcomes remain audit-only; only original-target checked models or empty-clause proofs grant answers.',
            'Two reversed fresh-process orders charge input reads/hashing, required parent reads/checks, transport, proposal, augmentation, search, proof substitution, checks, writes, three compressions and warm/two reload-check rounds. Imports/startup, final report encoding, original parent acquisition, historical storage and independent audits are additional.',
            'Reload rounds called cold in inherited field names deserialize fresh objects in the same worker; OS caches are not flushed. Separate fresh workers perform target-only replay with search and transport disabled. Runtime and RSS are observations, not bounds.',
            'Retain all earlier answers and counterexamples. Coverage unions are bookkeeping, not a measured dispatcher. General recognition, alternative premise support, proof size, unrestricted expansion and uniform polynomial SAT remain open.'
        ]))


def discover(row, mode, counts):
    reuse, limit = POLICIES[mode]
    if reuse:
        source, proof = previous.parent_data(row, counts)
        return e.solve(source, proof, row['source'], counts, node_limit=limit)
    seed = e.baseline.prior.prior.proposal(row['source'], counts)
    proof, diag = e.search(row['source'], seed, counts, node_limit=limit)
    return proof, dict(expansion=diag)


def check(source, proof, counts=None):
    return e.check_result(source, proof, counts)


def trial(out, dest, mode):
    dest.mkdir(); started = time.perf_counter(); p = load(out / 'protocol.json')
    assert p['policies'] == {k: list(v) for k, v in POLICIES.items()}
    for file in FILES:
        assert sha(file) == p['source_fingerprints'][file], file
    rows = [r for r in source_rows(p) if r['expansion_case']]
    input_seconds = time.perf_counter() - started
    cases = []; proofs = []; total = Counter(); phases = Counter()
    for row in rows:
        counts = Counter(); start = time.perf_counter()
        proof, diag = discover(row, mode, counts)
        acquisition = time.perf_counter() - start; discovery_counts = dict(counts)
        start = time.perf_counter(); got = check(row['source'], proof, counts); checking = time.perf_counter() - start
        start = time.perf_counter(); write(dest / (row['id'] + '.json'), proof); writing = time.perf_counter() - start
        cases.append(dict(id=row['id'], kind=row['kind'], parent_id=row['parent_id'],
                          status='unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'),
                          result=got, diagnostic=diag, discovery_counts=discovery_counts, counts=dict(counts),
                          acquisition_seconds=acquisition, checking_seconds=checking))
        proofs.append(proof); total.update(counts)
        phases.update(dict(acquisition_seconds=acquisition, checking_seconds=checking, writing_seconds=writing))
    start = time.perf_counter(); warm = Counter()
    for row in source_rows(p):
        if row['expansion_case']: check(row['source'], load(dest / (row['id'] + '.json')), warm)
    warm_seconds = time.perf_counter() - start; start = time.perf_counter(); cold = Counter()
    for _ in range(2):
        for row in source_rows(p):
            if row['expansion_case']: check(row['source'], load(dest / (row['id'] + '.json')), cold)
    cold_seconds = time.perf_counter() - start; start = time.perf_counter(); evidence = [None] * len(proofs)
    for name, data in (('certificates', proofs), ('discovery', evidence), ('combined', dict(proofs=proofs, evidence=evidence))):
        (dest / (name + '.json.gz')).write_bytes(gzip.compress(encode(data).encode(), mtime=0))
    persistence = time.perf_counter() - start
    write(dest / 'report.json', dict(mode=mode, panel=p['panel'], cases=cases, counts=dict(total),
          warm_counts=dict(warm), cold_counts=dict(cold), input_seconds=input_seconds, phases=dict(phases),
          warm_seconds=warm_seconds, cold_seconds=cold_seconds, persistence_seconds=persistence,
          complete_seconds=time.perf_counter() - started,
          proof_bytes=sum((dest / (r['id'] + '.json')).stat().st_size for r in rows),
          compressed_bytes={n: (dest / (n + '.json.gz')).stat().st_size for n in ('certificates', 'discovery', 'combined')},
          peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run(out):
    samples = []
    for i, order in enumerate(load(out / 'protocol.json')['orders']):
        for mode in order:
            dest = out / f'{mode}-{i}'
            subprocess.run([sys.executable, __file__, 'trial', str(out), str(dest), mode], check=True)
            samples.append(dict(**binding(dest / 'report.json'), mode=mode, repeat=i))
            r = load(dest / 'report.json')
            print(mode, i, r['complete_seconds'], dict(Counter(c['status'] for c in r['cases'])), flush=True)
            write(out / 'comparisons.json', dict(samples=samples))


if __name__ == '__main__':
    action = sys.argv[1]; out = Path(sys.argv[2])
    if action == 'trial': trial(out, Path(sys.argv[3]), sys.argv[4])
    else: globals()[action](out)

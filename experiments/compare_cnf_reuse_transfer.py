#!/usr/bin/env python3
"""Frozen external parent selection and unfiltered related-target reuse audit."""
from collections import Counter
from pathlib import Path
import gzip, hashlib, io, resource, subprocess, sys, tarfile, time
from urllib.request import urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import cnf_watched_learning as e
from experiments.compare_cnf_boundary_transfer import sha, load, encode, write, binding, bound, source_rows, parse_dimacs
from experiments.acquire_cnf_linear_unit_proof import emit

PARENT = Path('experiments/results/cnf-reuse-expansion')
POLICIES = {'parent20000': (False, 20000), 'fresh8000': (False, 8000), 'reuse8000': (True, 8000)}
FILES = ('experiments/compare_cnf_reuse_transfer.py', 'experiments/validate_cnf_reuse_transfer.py',
         'solver/test_cnf_reuse_transfer.py')
PRIOR_PANELS = (
    'experiments/results/cnf-linear-unit-proof/larger/panel.json',
    'experiments/results/cnf-selective-learning/panel.json',
    'experiments/results/cnf-boundary-transfer/panel.json',
    'experiments/results/cnf-external-cutsets/panel.json',
    'experiments/results/cnf-hamming-repair/constructed-inputs.json',
    'experiments/results/cnf-verified-operators/panel.json')


def freeze(out):
    out.mkdir(exist_ok=True)
    assert not (out / 'selection.json').exists()
    parent = load(PARENT / 'checkpoint.json')
    sources = {**parent['source_fingerprints'], **{f: sha(f) for f in FILES}}
    for f, h in sources.items(): assert sha(f) == h, f
    write(out / 'selection.json', dict(parent=binding(PARENT / 'checkpoint.json'),
        parent_manifest=binding(PARENT / 'manifest.json'), source_fingerprints=sources,
        groups=[dict(archive=f'{prefix}{n}-{m}.tar.gz', publisher_answer=prefix == 'uf')
                for n, m in ((125, 538), (150, 645)) for prefix in ('uf', 'uuf')],
        indices=[60, 80], sort='(member basename, full member name), zero based',
        policies=POLICIES, orders=[['fresh8000', 'reuse8000'], ['reuse8000', 'fresh8000']],
        prior_panels=[binding(f) for f in PRIOR_PANELS],
        edit_rule='For every parent, delete the canonical original clause starting its first stored derivation; if there is no derivation delete canonical clause zero, or none for an empty base. Paired bridge target adds [smallest original variable, maximum original variable + 101] and [-(maximum original variable + 101)]. Empty variable set uses 1 and 102. Include both targets regardless of parent outcome.',
        limitations=[
            'Selection and scientific sources frozen before acquisition or evaluation. Eight external originals from four SATLIB groups; sixteen controlled proof-guided edits are related targets, not sixteen independent external samples. Same distributions as earlier development; no representative or all-history novelty claim.',
            'Single measured parent acquisition at 20000 contexts; two reversed fresh-process target comparisons at 8000 contexts. Target-only deterministic proposal, unchanged watched engine, all surviving clauses active, no model inheritance, no outcome-dependent filtering, tuning or production-default changes.',
            'Reuse independently checks the parent, transports only recorded derivations whose premises survive, searches an equivalent augmented target and substitutes premises to yield a target-only checked certificate. SAT requires a target model; UNSAT an empty clause; unknown carries no decision authority.',
            'Complete cost charges raw reads/hash checks, required parent reads/checks, proposal, transport, search, substitution, explicit checks, writes, three compressions, warm replay and two reload rounds. Parent acquisition is separate and added once to the aggregate reuse cost. Download, edit preparation, imports/startup, report encoding, references and independent audits are additional.',
            'Reload rounds named cold use fresh objects in the same worker, without flushing OS caches. Additional independent fresh-worker replays disable search and transport. Context caps are not equal work or wall time. Historical unions have no combined dispatcher timing.',
            'Separate Z3 references use timeout 10000 ms, seed zero, fresh process timeout 30 seconds. SAT models are source checked; negative reference output is not project UNSAT authority. Labels and file names never enter discovery.',
            'All earlier sources, coverage, counterexamples and proof blocks are preserved. Efficient recognition, alternative supports, compact interaction descriptions, preprocessing and unrestricted expansion remain open.'
        ]))


def acquire(out):
    assert not (out / 'parents.json').exists(); selection = load(out / 'selection.json')
    for f, h in selection['source_fingerprints'].items(): assert sha(f) == h, f
    (out / 'raw').mkdir(); rows = []; records = []; started = time.perf_counter()
    for group in selection['groups']:
        url = 'https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/' + group['archive']
        with urlopen(url, timeout=45) as response: data = response.read(25000000)
        assert len(data) < 25000000
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            members = sorted((m for m in archive.getmembers() if m.isfile() and m.name.lower().endswith('.cnf')),
                             key=lambda m: (Path(m.name).name, m.name))
            for index in selection['indices']:
                member = members[index]; raw = archive.extractfile(member).read(); key = f'p{len(rows):03}'
                source, header = parse_dimacs(raw.decode()); path = out / 'raw' / (key + '.cnf')
                path.write_text(emit(source)); zipped = Path(str(path) + '.gz'); zipped.write_bytes(gzip.compress(raw, mtime=0))
                rows.append(dict(id=key, source=source, raw=binding(path), kind='original', parent_id=None))
                records.append(dict(id=key, **group, url=url, archive_sha256=hashlib.sha256(data).hexdigest(),
                    archive_bytes=len(data), member=member.name, index=index, header=header,
                    original_sha256=hashlib.sha256(raw).hexdigest(), original_bytes=len(raw), original_gzip=binding(zipped)))
        print(group['archive'], len(members), flush=True)
    previous = {b['path']: {e.canonical(r['source'], Counter()) for r in bound(b)} for b in selection['prior_panels']}
    seen = set(); overlaps = []
    for row in rows:
        key = e.canonical(row['source'], Counter())
        matches = [p for p, keys in previous.items() if key in keys]
        overlaps.append(dict(id=row['id'], prior_matches=matches, same_panel_exact=key in seen))
        assert not matches and key not in seen; seen.add(key)
    write(out / 'parent-panel.json', rows)
    write(out / 'acquisition.json', dict(selection=binding(out / 'selection.json'), records=records,
        seconds=time.perf_counter()-started, scope='Public archives read in memory, no tar paths extracted; selected raw member bytes retained exactly in gzip.'))
    write(out / 'overlaps.json', dict(records=overlaps, prior_panels=selection['prior_panels'],
        scope='Exact normalized equality against six named retained panels only; no semantic-isomorphism claim.'))
    write(out / 'parents.json', dict(**selection, selection=binding(out / 'selection.json'), panel=binding(out / 'parent-panel.json')))


def edits(source, proof):
    base = e.canonical(source, Counter()); names = sorted({abs(v) for c in source for v in c})
    deleted = proof['derivations'][0][0] if proof['derivations'] else (0 if base else None)
    assert deleted is None or 0 <= deleted < len(base)
    target = [list(c) for i, c in enumerate(base) if i != deleted]
    first = names[0] if names else 1; fresh = (names[-1] if names else 1) + 101
    return deleted, [('deletion', target), ('bridge', target + [[first, fresh], [-fresh]])]


def targets(out):
    assert not (out / 'protocol.json').exists(); rows = []; (out / 'inputs').mkdir()
    for original in source_rows(load(out / 'parents.json')):
        cert = binding(out / 'parent20000-0' / (original['id'] + '.json')); proof = bound(cert)
        check(original['source'], proof)
        deleted, variants = edits(original['source'], proof)
        for kind, source in variants:
            key = f't{len(rows):03}'; path = out / 'inputs' / (key + '.cnf'); path.write_text(emit(source))
            rows.append(dict(id=key, source=source, raw=binding(path), kind=kind, deleted_index=deleted,
                parent_id=original['id'], parent_source=original['source'], parent_raw=original['raw'],
                parent_certificate=cert, parent_kind=proof['kind']))
    write(out / 'panel.json', rows)
    p = load(out / 'parents.json'); p.update(panel=binding(out / 'panel.json'),
        parent_acquisition=binding(out / 'parent20000-0' / 'report.json'), parents=binding(out / 'parents.json'))
    write(out / 'protocol.json', p)


def parent_data(row, counts):
    path = row['parent_raw']['path']; raw = Path(path).read_bytes()
    assert sha(path) == row['parent_raw']['sha256']; source, _ = parse_dimacs(raw.decode())
    assert source == row['parent_source']; counts['selective_parent_input_bytes'] += len(raw)
    proof = bound(row['parent_certificate']); counts['selective_parent_proof_bytes'] += Path(row['parent_certificate']['path']).stat().st_size
    return source, proof


def discover(row, mode, counts):
    reuse, limit = POLICIES[mode]
    if reuse:
        source, proof = parent_data(row, counts)
        return e.solve(source, proof, row['source'], counts, node_limit=limit)
    seed = e.baseline.prior.prior.proposal(row['source'], counts)
    proof, diag = e.search(row['source'], seed, counts, node_limit=limit)
    return proof, dict(expansion=diag)


def check(source, proof, counts=None):
    return e.check_result(source, proof, counts)


def trial(out, dest, mode):
    dest.mkdir(); started = time.perf_counter(); p = load(out / ('parents.json' if mode == 'parent20000' else 'protocol.json'))
    assert p['policies'] == {k: list(v) for k, v in POLICIES.items()}
    for file in FILES:
        assert sha(file) == p['source_fingerprints'][file], file
    rows = source_rows(p)
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
        check(row['source'], load(dest / (row['id'] + '.json')), warm)
    warm_seconds = time.perf_counter() - start; start = time.perf_counter(); cold = Counter()
    for _ in range(2):
        for row in source_rows(p):
            check(row['source'], load(dest / (row['id'] + '.json')), cold)
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

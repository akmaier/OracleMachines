"""Independent truth and adversarial audit of capacity certificates."""
from collections import Counter
from itertools import combinations, product
from pathlib import Path
from unittest.mock import patch
import json, random, time
from experiments import cnf_capacity_core as engine


def satisfiable(source):
    names = sorted({abs(v) for clause in source for v in clause})
    # Independent explicit truth table, not clique/matching reasoning.
    for bits in product((False, True), repeat=len(names)):
        values = dict(zip(names, bits))
        if all(any(values[abs(v)] == (v > 0) for v in clause) for clause in source):
            return True
    return False


def encode_domains(domains, capacity):
    clauses = [[1 + i*capacity + j for j in range(capacity) if mask >> j & 1]
               for i, mask in enumerate(domains)]
    for j in range(capacity):
        for a, b in combinations(range(len(domains)), 2):
            clauses.append([-(1 + a*capacity + j), -(1 + b*capacity + j)])
    return clauses


def audit(out):
    started = time.perf_counter(); counts = Counter(); samples = []

    def inspect(source, category):
        answer = satisfiable(source); proof, diag = engine.discover(source)
        counts[category + '_inputs'] += 1
        counts[category + ('_sat' if answer else '_unsat')] += 1
        if proof is not None:
            assert not answer
            with patch.object(engine, 'discover', side_effect=AssertionError('cold search')):
                assert engine.check(source, json.loads(json.dumps(proof)))['answer'] is False
            counts[category + '_certified'] += 1
        return proof, diag, answer

    for n, bound in ((2, 9), (3, 3)):
        clauses = [[s*v for v, s in enumerate(signs, 1) if s]
                   for signs in product((-1, 0, 1), repeat=n)]
        for k in range(bound + 1):
            for source in combinations(clauses, k):
                inspect(list(source), 'cnf' + str(n))
    for capacity in (2, 3):
        for domains in product(range(1 << capacity), repeat=3):
            inspect(encode_domains(domains, capacity), 'domains' + str(capacity))
    rng = random.Random(2711272059)
    for _ in range(1000):
        n = rng.randrange(1, 7)
        source = [[rng.choice((-1, 1))*v for v in rng.sample(range(1, n+1), rng.randrange(1, n+1))]
                  for _ in range(rng.randrange(1, 20))]
        inspect(source, 'random')
    # All single-clause deletions of this minimally UNSAT instance are SAT.
    core = encode_domains([7]*4, 3); proof, _ = engine.discover(core)
    for i in range(len(core)):
        source = core[:i] + core[i+1:]
        p, _, answer = inspect(source, 'deletion')
        assert answer and p is None
        try: engine.check(source, proof)
        except ValueError: counts['invalidated_deleted_support'] += 1
        else: raise AssertionError('deleted support accepted')
    # Renamings, added mixed/overlapping clauses, edits, and a deficient subset
    # alongside independently satisfiable components. Store the exact inputs.
    for i in range(48):
        source = encode_domains([7]*4, 3)
        if i % 3 == 1: source = source[1:]
        if i % 3 == 2: source[-1][0] *= -1
        source += [[1, -2, 3], [2, -3]] if i % 2 else [[13, 14], [-13, 14]]
        names = sorted({abs(v) for clause in source for v in clause})
        ids = rng.sample(range(31, 10000), len(names)); signs = [rng.choice((-1, 1)) for _ in names]
        mapping = {v: ids[j]*signs[j] for j, v in enumerate(names)}
        source = [[mapping[abs(v)]*(1 if v > 0 else -1) for v in clause] for clause in source]
        rng.shuffle(source)
        p, diag, answer = inspect(source, 'mixture')
        samples.append(dict(source=source, satisfiable=answer, proof=p, diagnostic=diag))
    # Explicit reuse under changes is checked, never trusted by origin labels.
    for noise in ([[[50, 51]], [[1, -3, 8]], [[1, -1]], core[:3]]):
        assert engine.check(core+noise, proof)['answer'] is False
        counts['checked_core_reuses'] += 1
    Path(out).mkdir(exist_ok=True)
    (Path(out)/'semantic-audit.json').write_text(json.dumps(dict(passed=True, counts=dict(counts),
        mixtures=samples, seconds=time.perf_counter()-started,
        scope='Explicit truth tables are independent of recognition. Exhaustive bounded CNFs and domain restrictions, not exhaustive arbitrary CNF. Cold checking disables discovery.'), indent=2)+'\n')
    print(json.dumps(dict(passed=True, counts=dict(counts), seconds=time.perf_counter()-started)))


if __name__ == '__main__':
    import sys
    audit(sys.argv[1])

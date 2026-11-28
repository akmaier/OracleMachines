#!/usr/bin/env python3
"""Independent truth audit of capped fresh and composed reuse paths after edits."""
from collections import Counter
from itertools import combinations, product
from pathlib import Path
from unittest.mock import patch
import random, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import cnf_watched_learning as e
from experiments.compare_cnf_boundary_transfer import write


def assert_prefix(small, large):
    assert large['derivations'][:len(small['derivations'])] == small['derivations']
    if small['kind'] != 'unknown': assert small == large


def models(source):
    names = sorted({abs(v) for c in source for v in c})
    result = []
    for values in product((False, True), repeat=len(names)):
        model = dict(zip(names, values))
        if all(any(model[abs(v)] == (v > 0) for v in c) for c in source): result.append(model)
    return result


def audit(out):
    counts = Counter(); rng = random.Random(202611280907)
    c2 = [list(v for v in x if v) for x in product((0, 1, -1), (0, 2, -2))]
    c3 = [list(v for v in x if v) for x in product((0, 1, -1), (0, 2, -2), (0, 3, -3))]
    inputs = [('two', [c for i, c in enumerate(c2) if m >> i & 1]) for m in range(512)]
    inputs += [('three', list(cs)) for n in range(4) for cs in combinations(c3, n)]
    mixtures = []
    for _ in range(128):
        names = rng.sample(range(11, 1000), rng.randrange(4, 8))
        source = [[rng.choice((-1, 1)) * v for v in rng.sample(names, rng.randrange(1, 4))] for _ in range(25)]
        source += [source[0], [names[0], -names[0]]]; mixtures.append(source); inputs.append(('mixture', source))
    for kind, source in inputs:
        counts[kind + '_parents'] += 1
        old = e.baseline.solve(source)[0]
        names = sorted({abs(v) for c in source for v in c})
        targets = [source[1:], source + [[-(names[0] if names else 1), 1001], [-1001]]]
        for target in targets:
            truth = models(target); counts['edited_targets'] += 1
            knowledge, _ = e.selective.transport(source, old, target)
            seed = e.baseline.prior.prior.proposal(target, Counter())
            for mode in ('fresh', 'reuse'):
                prior = None
                for cap in (0, 2, 8000):
                    proof, diag = e.search(target, seed, node_limit=cap) if mode == 'fresh' else e.expand(target, knowledge, node_limit=cap)
                    with patch.object(e, 'search', side_effect=AssertionError), patch.object(e.selective, 'transport', side_effect=AssertionError):
                        answer = e.check_result(target, proof)['answer']
                    if answer is not None: assert answer == bool(truth)
                    if cap == 8000: assert answer is not None
                    counts[proof['kind']] += 1; counts['checked_outcomes'] += 1
                    assert diag['expanded'] <= cap
                    for _, _, clause in proof['derivations']:
                        assert all(any(model[abs(v)] == (v > 0) for v in clause) for model in truth)
                        counts['consequence_checks'] += 1
                    if mode == 'reuse':
                        assert proof['derivations'][:len(knowledge['derivations'])] == knowledge['derivations']
                        counts['retained_prefix_checks'] += 1
                    if prior is not None: assert_prefix(prior, proof); counts['budget_prefix_checks'] += 1
                    prior = proof
    write(out / 'semantic-audit.json', dict(passed=True, counts=dict(counts), mixtures=mixtures,
          scope='All 512 canonical two-variable clause sets and 3304 three-variable clause sets of at most three clauses, plus 128 signed sparse mixtures with duplicates and tautologies. Each receives deletion and shared-variable-addition edits; fresh/reuse at caps 0, 2, 8000. Independent truth verifies outcomes and retained/new consequences; exact deterministic prefix checks verify completed-answer preservation. Related edits, policies and budgets are not independent samples.'))


if __name__ == '__main__': audit(Path(sys.argv[1]))

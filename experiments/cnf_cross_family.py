"""Deterministic evaluation inputs; family metadata is never passed to search.

These finite generators are probes of transfer, not an exhaustive SAT taxonomy.
The truth-table oracle is deliberately exponential and used only after timing.
"""
from itertools import product
import random


FAMILIES = ('random-three', 'coupled-parity', 'gated-horn', 'graph-colouring')
SIZES = (12, 16, 20)


def generate(family, size, sample, attempt=0):
    if family not in FAMILIES or size not in SIZES or sample not in range(4):
        raise ValueError('Unknown frozen workload configuration')
    rng = random.Random(917003 + 100003*FAMILIES.index(family) + 1009*size + 37*sample + 7919*attempt)
    n = size

    def clause(variables, width=3):
        return [v if rng.randrange(2) else -v for v in rng.sample(list(variables), width)]

    if family == 'random-three':
        density = (3.5, 4.25, 4.25, 5.0)[sample]
        source = [clause(range(1, n+1)) for _ in range(round(density*n))]
    elif family == 'coupled-parity':
        source = []
        for _ in range(n-3):
            support = rng.sample(range(1, n+1), 3); rhs = rng.randrange(2)
            for bits in product((False, True), repeat=3):
                if sum(bits) % 2 != rhs:
                    source.append([-v if b else v for v, b in zip(support, bits)])
        source += [clause(range(1, n+1)) for _ in range(n//2)]
    elif family == 'gated-horn':
        # Conditioning the last variable yields Horn or dual-Horn. Recognition
        # must discover that fact; neither the gate nor a family hint is supplied.
        source = []
        for _ in range(2*n):
            a, b, c = rng.sample(range(1, n), 3)
            source.append([-a, -b, c, n])
            a, b, c = rng.sample(range(1, n), 3)
            source.append([a, b, -c, -n])
        for _ in range(2):
            source.append([rng.choice(range(1, n)), n])
            source.append([-rng.choice(range(1, n)), -n])
    else:
        vertices = (4, 6, 7)[SIZES.index(size)]; n = 3*vertices
        source = [[3*v+c+1 for c in range(3)] for v in range(vertices)]
        source += [[-(3*v+a+1), -(3*v+b+1)] for v in range(vertices)
                   for a in range(3) for b in range(a+1, 3)]
        density = (0.4, 0.6, 0.75, 0.9)[sample]
        for v in range(vertices):
            for w in range(v+1, vertices):
                if rng.random() < density:
                    source += [[-(3*v+c+1), -(3*w+c+1)] for c in range(3)]
    labels = rng.sample(range(10, 10+17*n), n)
    flips = [1 if family == 'gated-horn' or rng.randrange(2) else -1 for _ in range(n)]
    result = [[labels[abs(l)-1] * flips[abs(l)-1] * (1 if l > 0 else -1) for l in c] for c in source]
    for c in result: rng.shuffle(c)
    rng.shuffle(result)
    return result


def truth_table(source, max_variables=22):
    """Evaluate every assignment using bitsets, independently of native SAT code."""
    if any(type(l) is not int or l == 0 for c in source for l in c):
        raise ValueError('Invalid literal')
    names = sorted({abs(l) for c in source for l in c}); n = len(names)
    if n > max_variables: raise ValueError('Truth-table budget exceeded')
    assignments = 1 << n; universe = (1 << assignments)-1
    masks = {}
    for i, name in enumerate(names):
        width = 1 << i
        masks[name] = (universe // ((1 << (2*width))-1)) * (((1 << width)-1) << width)
    accepted = universe
    for c in source:
        clause_mask = 0
        for literal in c:
            mask = masks[abs(literal)]
            clause_mask |= mask if literal > 0 else universe ^ mask
        accepted &= clause_mask
    return dict(answer=bool(accepted), satisfying_assignments=accepted.bit_count(), variables=n,
                assignments=assignments, method='exhaustive-bitset-v1')

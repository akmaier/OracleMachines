"""Necessary syntax invariants for signed variable renaming, not SAT answers.

Equality is inconclusive. Inequality excludes a bijection of variables with
independent polarity flips on normalized clause sets. It does not exclude
semantic equivalence, simplification, or a more general checked transport.
"""
from collections import Counter

from experiments.cnf_residual_dag import normalize


FORMAT = 'signed-occurrence-exclusion-v1'
FIELDS = ('variables', 'clause_widths', 'paired_occurrences')


def profile(cnf, counts=None):
    if counts is None:
        counts = Counter()
    normalized, names = normalize(cnf, counts)
    occurrences = Counter()
    widths = Counter()
    for clause in normalized:
        widths[len(clause)] += 1
        for literal in clause:
            occurrences[literal] += 1
            counts['renaming_profile_literal_visits'] += 1
    pairs = Counter(tuple(sorted((occurrences[v], occurrences[-v])))
                    for v in range(1, len(names) + 1))
    counts['renaming_profile_variables'] += len(names)
    counts['renaming_profile_clauses'] += len(normalized)
    counts['renaming_profiles'] += 1
    return dict(variables=len(names),
                clause_widths=[[width, count] for width, count in sorted(widths.items())],
                paired_occurrences=[[a, b, count] for (a, b), count in sorted(pairs.items())])


def exclusion(left, right, counts=None):
    """Return a checkable exclusion or None when this filter is inconclusive."""
    a, b = profile(left, counts), profile(right, counts)
    field = next((name for name in FIELDS if a[name] != b[name]), None)
    return None if field is None else dict(format=FORMAT, field=field, left=a, right=b)


def verify_exclusion(left, right, certificate, counts=None):
    if not isinstance(certificate, dict) or set(certificate) != {'format', 'field', 'left', 'right'}:
        raise ValueError('Invalid renaming exclusion fields')
    if certificate['format'] != FORMAT or certificate['field'] not in FIELDS:
        raise ValueError('Invalid renaming exclusion format or field')
    a, b = profile(left, counts), profile(right, counts)
    if certificate['left'] != a or certificate['right'] != b:
        raise ValueError('Renaming exclusion does not match its inputs')
    if a[certificate['field']] == b[certificate['field']]:
        raise ValueError('Equal invariants do not exclude a renaming')
    return True

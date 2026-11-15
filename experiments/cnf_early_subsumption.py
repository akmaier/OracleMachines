"""Expose an existing syntactic family before spending probe acquisitions.

This is a separate source-bound recognition rule, requiring no prepared template.
It does not perform discovery on an unrecognized reduced core.
"""
from collections import Counter

from experiments.cnf_pattern_inventory import classify, encode
from experiments.cnf_subsumption_transfer import minimal, checked_minimal

FORMAT = 'early-subsumption-family-v1'
PARITY_WIDTH = 8


def discover_family(source, counts=None):
    counts = Counter() if counts is None else counts
    core, certificate, names = minimal(source, counts)
    profile = classify(core, PARITY_WIDTH, counts)
    recognized = [name for name, value in profile['outcomes'].items() if value == 'recognized']
    if not recognized:
        counts['early_family_misses'] += 1
        return None
    counts['early_family_hits'] += 1
    return dict(format=FORMAT, subsumption=certificate, names=names, family=recognized[0])


def check_family(source, certificate, counts=None):
    counts = Counter() if counts is None else counts
    if (type(certificate) is not dict or set(certificate) != {'format', 'subsumption', 'names', 'family'}
            or certificate['format'] != FORMAT or type(certificate['family']) is not str):
        raise ValueError('Invalid early family certificate')
    core, names = checked_minimal(source, certificate['subsumption'], counts)
    if encode(names) != encode(certificate['names']):
        raise ValueError('Invalid early family variable names')
    profile = classify(core, PARITY_WIDTH, counts)
    if profile['outcomes'].get(certificate['family']) != 'recognized':
        raise ValueError('Unrecognized reduced family')
    counts['verified_early_families'] += 1
    return core

"""Self-contained conditional refutations, without donor traversal metadata.

The discarded provenance stays in the research archive. This cache certifies
individual conditional conflicts only; it contains no whole-formula cover.
"""
from copy import deepcopy
from experiments.cnf_conditional_unit_support import check_template

FORMAT_CACHE = 'conditional-unit-cache-v1'


def check_cache(cache, counts=None):
    if type(cache) is not dict or set(cache) != {'format', 'entries'}:
        raise ValueError('Invalid conditional cache fields')
    if cache['format'] != FORMAT_CACHE or type(cache['entries']) is not list:
        raise ValueError('Invalid conditional cache format')
    for entry in cache['entries']:
        if type(entry) is not dict or set(entry) != {'template'}:
            raise ValueError('Invalid conditional cache entry')
        check_template(entry['template'], counts)
    return cache


def compact(bundle, counts=None):
    cache = dict(format=FORMAT_CACHE, entries=[
        dict(template=deepcopy(entry['template'])) for entry in bundle['entries']])
    return check_cache(cache, counts)

"""Bind an open focus to specified originals in a complete checked catalog.

This read-only check does not select the globally cheapest focus or establish
complete original coverage. The caller guards its live session before use and
owns the fixed case list, policy and immutable history.
"""
from collections import Counter
import copy

from experiments.cnf_target_probe import remaining


def bind_original_focus(h, routes, cases, source, indices):
    if (type(source) is not str or not source or type(indices) is not list or
            not indices or any(type(i) is not int or not 0 <= i < len(cases) for i in indices) or
            len(set(indices)) != len(indices)):
        raise ValueError('Invalid original focus scope')
    roots = [h._canonical(cases[i]['source'], h.config['max_depth'])[2] for i in indices]
    counts = Counter()
    rows = remaining(h, [dict(source=k, target=k) for k in roots], routes, counts)
    bindings = []
    for i, root, row in zip(indices, roots, rows, strict=True):
        matches = [leaf for leaf in row['leaves'] if leaf['source'] == source]
        if row['closed'] or not matches:
            raise ValueError('Focus is not an open selected leaf of this original')
        bindings.append(dict(index=i, original_case=cases[i]['original_case'],
            root=root, leaves=copy.deepcopy(matches)))
    return dict(source=source, bindings=bindings, counts=dict(counts))

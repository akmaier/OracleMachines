"""Expose successful internal plans hidden behind positive coverage base steps.

This is a checked expansion of a proof, not a standalone semantic checker. The
original inventory validators still check their full historical dependencies.
Both verifier views (current and retained policy) belong in the cost account.
"""
from collections import Counter
import json

from experiments.cnf_pattern_inventory import FORMAT as NODE_FORMAT, encode
from experiments.cnf_route_composition import verify_plan
from experiments.cnf_selected_routes import SelectedRoutes

FORMAT = 'expanded-positive-coverage-v1'
INTERNAL = {'family', 'edge', 'components', 'conditioning', 'retained_plan'}


def verifier_views(h):
    """Walk retained-policy verifier caches once, even when connections are shared."""
    views = []; seen = set()
    name = 'current'
    while h is not None:
        if id(h) in seen:
            raise ValueError('Cyclic retained verifier views')
        seen.add(id(h)); views.append((name, h))
        h = getattr(h, 'prepared', None); name += '.prepared'
    return views


def checked_inventory(h):
    """Union actual checked pattern keys; shared SQLite does not merge caches."""
    rows = {}; per_view = {}; occurrences = 0
    for name, view in verifier_views(h):
        per_view[name] = dict(nodes=len(view.checked),
            key_bytes=sum(len(k.encode()) for k in view.checked),
            node_json_bytes=sum(len(encode(n).encode()) for n in view.checked.values()))
        occurrences += len(view.checked)
        for key, node in view.checked.items():
            if key in rows and encode(rows[key]) != encode(node):
                raise ValueError('Conflicting checked node across views')
            rows[key] = node
    return rows, dict(views=per_view, cache_occurrences=occurrences,
        unique_nodes=len(rows), duplicate_cache_entries=occurrences-len(rows),
        unique_key_bytes=sum(len(k.encode()) for k in rows),
        unique_node_json_bytes=sum(len(encode(n).encode()) for n in rows.values()))


def owner(h, source):
    if type(source) is not str:
        raise ValueError('Invalid expanded source')
    try:
        identity = json.loads(source)
    except (ValueError, TypeError) as exc:
        raise ValueError('Invalid expanded source identity') from exc
    if type(identity) is not list or len(identity) != 4 or identity[0] != NODE_FORMAT:
        raise ValueError('Invalid expanded source identity')
    matches = [view for _, view in verifier_views(h) if encode(view.config) == encode(identity[1])]
    if len(matches) != 1:
        raise ValueError('Unknown or ambiguous retained policy')
    return matches[0]


def children(h, source, rule, routes):
    """Check the exact rule and return every structural coverage premise."""
    if type(rule) is not dict or type(rule.get('kind')) is not str:
        raise ValueError('Malformed expanded rule')
    view = owner(h, source); node = view._load(source)
    if node is None:
        raise ValueError('Missing expanded source')
    kind = rule['kind']
    if kind == 'family' and rule == dict(kind='family') and node['kind'] == 'family':
        if node['summary']['closed'] is not True:
            raise ValueError('Unclosed family')
        return []
    if kind == 'retained_plan' and rule == dict(kind=kind) and node['kind'] == kind:
        return [node['reference']]
    if kind == 'components' and rule == dict(kind=kind) and node['kind'] == 'and':
        return [edge['key'] for edge in node['edges']]
    if (kind == 'conditioning' and set(rule) == {'kind', 'index'} and node['kind'] == 'or'
            and type(rule['index']) is int and 0 <= rule['index'] < len(node['alternatives'])):
        return [edge['key'] for edge in node['alternatives'][rule['index']]['edges']]
    if kind == 'edge' and rule == dict(kind=kind) and 'edge' in node:
        return [node['edge']['key']]
    if kind not in INTERNAL and kind != 'base' and view is h:
        matches = [keys for actual, keys in routes.by_source.get(source, []) if encode(actual) == encode(rule)]
        if len(matches) == 1:
            return matches[0]
    raise ValueError('Invalid expanded positive rule')


def _internal_rule(node):
    if node['summary']['closed'] is not True:
        raise ValueError('Missing explicit rule for an open node')
    kind = node['kind']
    if kind in ('family', 'retained_plan'):
        return dict(kind=kind)
    if kind == 'and':
        return dict(kind='components')
    if kind == 'or':
        return dict(kind='conditioning', index=node['selected'])
    if 'edge' in node:
        return dict(kind='edge')
    raise ValueError('Unknown closed internal plan')


def expand(h, certificate, claimed_roots, routes, counts):
    """Derive a finite proof with explicit retained and formerly hidden steps."""
    verify_plan(h, certificate, claimed_roots, routes, counts)
    old = {step['source']: step['rule'] for step in certificate['steps']}
    finished = set(); active = set(); steps = []

    def visit(source):
        if source in finished:
            counts['expanded_shared_references'] += 1
            return
        if source in active:
            raise ValueError('Cyclic expanded positive proof')
        active.add(source)
        node = owner(h, source)._load(source)
        if node is None:
            raise ValueError('Missing expanded node')
        rule = old.get(source)
        if rule is None or rule == dict(kind='base'):
            rule = _internal_rule(node)
        premises = children(h, source, rule, routes)
        for child in premises:
            visit(child)
        steps.append(dict(source=source, rule=rule, children=premises))
        active.remove(source); finished.add(source)

    for root in claimed_roots:
        visit(root)
    counts['expanded_steps'] += len(steps)
    return dict(format=FORMAT, roots=claimed_roots, steps=steps)


def verify_expanded(h, certificate, claimed_roots, evidence, counts):
    """Cold-capable replay. Historical checking is still required underneath."""
    if (type(certificate) is not dict or set(certificate) != {'format', 'roots', 'steps'} or
            certificate['format'] != FORMAT or certificate['roots'] != claimed_roots or
            type(certificate['steps']) is not list):
        raise ValueError('Invalid expanded certificate')
    routes = SelectedRoutes(h, evidence)
    justified = set()
    for step in certificate['steps']:
        if (type(step) is not dict or set(step) != {'source', 'rule', 'children'} or
                type(step['source']) is not str or type(step['children']) is not list):
            raise ValueError('Malformed expanded step')
        source, rule = step['source'], step['rule']
        if source in justified:
            raise ValueError('Repeated expanded step')
        if type(rule) is not dict or type(rule.get('kind')) is not str:
            raise ValueError('Malformed expanded rule')
        if rule['kind'] not in INTERNAL:
            if rule['kind'] == 'base':
                raise ValueError('Implicit base is not an expanded proof')
            if owner(h, source) is not h:
                raise ValueError('External route under foreign policy')
            try:
                routes.select(h, source, rule)
            except (KeyError, TypeError, IndexError) as exc:
                raise ValueError('Missing expanded external evidence') from exc
        actual = children(h, source, rule, routes)
        if step['children'] != actual or any(child not in justified for child in actual):
            raise ValueError('Missing or incorrect expanded premises')
        justified.add(source); counts['verified_expanded_steps'] += 1
    if any(root not in justified for root in claimed_roots):
        raise ValueError('Missing expanded root')
    return routes

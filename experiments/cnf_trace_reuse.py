"""Exact reductions from existing source-bound probe pairs, without new probes.

References point only to top-level attempts. A learning continuation is evidence
on an augmented formula and is deliberately ineligible. Prefix/ranking policy is
not a premise of the logical implication: the two referenced traces are checked
directly against the exact source before any common value or equivalence is used.
"""
from collections import Counter
import json

from experiments.cnf_common_consequence import first_common_pair
from experiments.cnf_probe_equivalence import first_equivalence_pair, substitute_block
from experiments.cnf_probe_exhaustion import check_clear_attempts
from experiments.cnf_probe_continuation import ContinuationRoutes, TABLE as CONTINUATIONS
from experiments.cnf_probe_window import TABLE as WINDOWS
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, restrict
from experiments.cnf_simplification import discover_simplification, check_simplification

PATTERNS = 'cnf_patterns_v1'


def record_key(record):
    return encode([record['source'], record['references']])


def read_attempt(h, source, ref, counts):
    if (type(ref) is not dict or set(ref) != {'table', 'id', 'index'} or
            ref['table'] not in (PATTERNS, WINDOWS, CONTINUATIONS) or
            type(ref['id']) is not str or type(ref['index']) is not int or ref['index'] < 0):
        raise ValueError('Invalid source-trace reference')
    table = ref['table']
    row = h.db.execute(f'SELECT payload FROM {table} WHERE id=?', (ref['id'],)).fetchone()
    if row is None:
        raise ValueError('Missing referenced trace')
    counts['trace_reference_payload_bytes'] += len(row[0].encode())
    payload = json.loads(row[0])
    if table == PATTERNS:
        if ref['id'] != source:
            raise ValueError('Foreign source profile')
        probing = payload['profile']['probing']
    else:
        identity = [source, payload['width']]
        if table == CONTINUATIONS:
            identity.append(payload['offset'])
        if payload['source'] != source or encode(identity) != ref['id']:
            raise ValueError('Foreign source window')
        probing = payload['probing']
    attempts = probing.get('attempts', [])
    if ref['index'] >= len(attempts):
        raise ValueError('Missing referenced attempt')
    counts['trace_references_loaded'] += 1
    return attempts[ref['index']]


def check_pair(cnf, attempts, counts):
    if len(attempts) != 2:
        raise ValueError('Expected exactly two attempts')
    check_clear_attempts(cnf, attempts, counts)
    low, high = attempts
    if low['variable'] != high['variable'] or low['value'] is not False or high['value'] is not True:
        raise ValueError('Expected opposite values of the same source variable')


def pair_witness(attempts, counts):
    common = first_common_pair(attempts, counts)
    if common is not None:
        return 'common', common
    equivalence = first_equivalence_pair(attempts, counts)
    return ('equivalence', equivalence) if equivalence is not None else (None, None)


def make_record(h, source, references, counts):
    node = h._load(source)
    if node is None or node['kind'] != 'unresolved':
        raise ValueError('Expected unresolved source')
    attempts = [read_attempt(h, source, ref, counts) for ref in references]
    check_pair(node['cnf'], attempts, counts)
    kind, witness = pair_witness(attempts, counts)
    if kind is None:
        raise ValueError('Pair has no common value or equivalence')
    reduction = dict(kind=kind, witness=witness)
    if kind == 'common':
        fixed = {abs(lit): lit > 0 for lit in witness['literals']}
        reduction['closure'] = discover_simplification(restrict(node['cnf'], fixed, counts), counts, pure=False)
        target, _ = check_simplification(restrict(node['cnf'], fixed, counts), reduction['closure'], counts, pure=False)
    else:
        target = substitute_block(node['cnf'], witness, counts)
    _, names, key = h._canonical(target, node['depth'])
    result = dict(source=source, references=references, reduction=reduction, edge=dict(key=key, names=names))
    verify_rewrite(h, result, counts)
    return result


def verify_rewrite(h, record, counts):
    if type(record) is not dict or set(record) != {'source', 'references', 'reduction', 'edge'}:
        raise ValueError('Invalid trace-rewrite fields')
    if type(record['source']) is not str or type(record['references']) is not list:
        raise ValueError('Invalid source or references')
    node = h._load(record['source'])
    if node is None or node['kind'] != 'unresolved':
        raise ValueError('Expected unresolved source')
    attempts = [read_attempt(h, record['source'], ref, counts) for ref in record['references']]
    check_pair(node['cnf'], attempts, counts)
    kind, witness = pair_witness(attempts, counts)
    reduction = record['reduction']
    fields = {'kind', 'witness', 'closure'} if kind == 'common' else {'kind', 'witness'}
    if (kind is None or type(reduction) is not dict or set(reduction) != fields or
            reduction['kind'] != kind or encode(reduction['witness']) != encode(witness)):
        raise ValueError('Incorrect pair consequence')
    fixed = {}
    if kind == 'common':
        fixed = {abs(lit): lit > 0 for lit in witness['literals']}
        target, closure = check_simplification(restrict(node['cnf'], fixed, counts), reduction['closure'], counts, pure=False)
        fixed.update(closure)
    else:
        target = substitute_block(node['cnf'], witness, counts)
    if not {abs(l) for c in target for l in c} < {abs(l) for c in node['cnf'] for l in c}:
        raise ValueError('Rewrite must strictly reduce support')
    _, names, key = h._canonical(target, node['depth'])
    if encode(record['edge']) != encode(dict(key=key, names=names)):
        raise ValueError('Incorrect rewritten residual binding')
    counts['verified_trace_rewrites'] += 1
    return target, fixed


def lift_rewrite(h, record, child_model, counts):
    _, fixed = verify_rewrite(h, record, counts)
    edge = record['edge']; child = h._load(edge['key'])
    if (child is None or any(i not in child_model or type(child_model[i]) is not bool
                            for i in range(1, len(edge['names']) + 1)) or not holds(child['cnf'], child_model)):
        raise ValueError('Invalid rewritten child model')
    source = h._load(record['source'])['cnf']
    result = {abs(l): False for c in source for l in c}
    result.update(fixed)
    result.update((v, child_model[i]) for i, v in enumerate(edge['names'], 1))
    if record['reduction']['kind'] == 'equivalence':
        for variable, rep in record['reduction']['witness']['mapping']:
            result[variable] = result[abs(rep)] if rep > 0 else not result[abs(rep)]
    if not holds(source, result):
        raise ValueError('Lift violates original source')
    return result


def source_attempts(h, source, counts):
    """Deterministic complete saved pairs; never enter a nested continuation."""
    node = h._load(source)
    if node is None or node['kind'] != 'unresolved':
        raise ValueError('Expected unresolved source')
    blocks = [(PATTERNS, source, node['profile']['probing'])]
    for table in (WINDOWS, CONTINUATIONS):
        saved = [(key, json.loads(payload)) for key, payload in h.db.execute(f'SELECT id,payload FROM {table}')]
        counts['trace_index_records_scanned'] += len(saved)
        for key, record in sorted(saved, key=lambda item: item[1].get('offset', 0)):
            if record['source'] == source:
                if record['probing']['status'] != 'clear':
                    raise ValueError('Scan policy expects a clear stream')
                blocks.append((table, key, record['probing']))
    attempts = []; refs = []
    for table, identity, probing in blocks:
        for index in range(len(probing.get('attempts', []))):
            ref = dict(table=table, id=identity, index=index)
            attempts.append(read_attempt(h, source, ref, counts)); refs.append(ref)
    if len(attempts) % 2:
        raise ValueError('Incomplete saved pair')
    for i in range(0, len(attempts), 2):
        check_pair(node['cnf'], attempts[i:i+2], counts)
    return attempts, refs


class TraceRoutes(ContinuationRoutes):
    """External immutable rewrite records add routes only with present children."""
    def __init__(self, h, records=()):
        super().__init__(h)
        self.rewrites = {}
        for record in records:
            self.add_rewrite(h, record)

    def add_rewrite(self, h, record):
        verify_rewrite(h, record, self.counts)
        identity = record_key(record)
        if identity in self.rewrites and encode(self.rewrites[identity]) != encode(record):
            raise ValueError('Conflicting trace rewrite')
        self.rewrites[identity] = record
        if h._load(record['edge']['key']) is None:
            self.counts['pending_trace_rewrites'] += 1
            return
        item = (dict(kind='trace_rewrite', id=identity), [record['edge']['key']])
        if item not in self.by_source[record['source']]:
            self.by_source[record['source']].append(item)

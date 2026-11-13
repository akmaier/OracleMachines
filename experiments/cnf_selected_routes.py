"""Replay a positive coverage witness using only its external route dependencies.

This is not a complete route catalog or an archive audit. Inventory nodes still
use their original recursive checker, including unselected internal alternatives.
All selected external records and policy prefixes use the existing validators.
No serialized closure bit, digest or prior in-process check substitutes for them.
"""
from collections import Counter, defaultdict
import json

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import verify_plan
from experiments.cnf_probe_window import verify_window, record_key as window_key
from experiments.cnf_probe_continuation import ContinuationRoutes, record_key as continuation_key
from experiments.cnf_pivot_alternatives import verify_trial
from experiments.cnf_coupled_pivots import verify_coupled, coupled_key
from experiments.cnf_growth_escape import verify_escape, trial_key
from experiments.cnf_trace_reuse import verify_rewrite, record_key as rewrite_key
from experiments.cnf_trace_learning import verify_learning, record_key as learning_key
from experiments.cnf_learning_continuation import LearningBlocks, record_key as block_key
from experiments.cnf_trace_split import verify as verify_split, record_key as split_key
from experiments.cnf_affine_clause import attach as attach_affine, record_key as affine_key


class _SavedRows(dict):
    """Exact-key SQL access; the callback checks identity and, where needed, proof."""
    def __init__(self, h, table, identity, counts, check=None):
        super().__init__()
        self.h, self.table, self.identity = h, table, identity
        self.counts, self.check = counts, check

    def __missing__(self, key):
        if type(key) is not str:
            raise ValueError('Invalid route identity')
        row = self.h.db.execute(f'SELECT payload FROM {self.table} WHERE id=?', (key,)).fetchone()
        self.counts['selected_sql_lookups'] += 1
        if row is None:
            raise ValueError('Missing selected route or policy prefix')
        self.counts['selected_sql_payload_bytes'] += len(row[0].encode())
        record = json.loads(row[0])
        if self.identity(record) != key:
            raise ValueError('Incorrect selected route identity')
        if self.check is not None:
            self.check(self.h, record, self.counts)
        self[key] = record
        return record

    def get(self, key, default=None):
        # A requested absent premise is an error, never an inconclusive result.
        return self[key]

    def __contains__(self, key):
        self[key]
        return True


def _index(records, identity, counts):
    result = {}
    for record in records:
        key = identity(record)
        counts['sidecar_index_records'] += 1
        counts['sidecar_index_payload_bytes'] += len(encode(record).encode())
        if key in result and encode(result[key]) != encode(record):
            raise ValueError('Conflicting sidecar identity')
        result[key] = record
    return result


class SelectedRoutes(ContinuationRoutes):
    """Subset for a supplied finite proof. Do not use as a discovery catalog."""
    def __init__(self, h, evidence):
        if len(evidence) != 5:
            raise ValueError('Expected all five evidence lists')
        self.counts = Counter()
        self.by_source = defaultdict(list)
        self.windows = _SavedRows(h, 'cnf_probe_windows_v1', window_key, self.counts, verify_window)
        self.continuations = _SavedRows(h, 'cnf_probe_continuations_v1', continuation_key, self.counts)
        self.verified = set()
        self.pivots = _SavedRows(h, 'cnf_pivot_trials_v1',
            lambda r: encode([r['source'], r['variable']]), self.counts, verify_trial)
        self.coupled = _SavedRows(h, 'cnf_coupled_trials_v1', coupled_key, self.counts)
        self.growth = _SavedRows(h, 'cnf_growth_trials_v1', trial_key, self.counts, verify_escape)
        self.rewrites = _index(evidence[0], rewrite_key, self.counts)
        self.learning = _index(evidence[1], learning_key, self.counts)
        # Build indexes without checking every unused continuation. _saved and
        # context still check the base and recursively check every clear prefix.
        self.learned_blocks = LearningBlocks(h, evidence[1])
        self.learned_blocks.records = _index(evidence[2], block_key, self.counts)
        self.splits = _index(evidence[3], split_key, self.counts)
        self.affine = _index(evidence[4], affine_key, self.counts)
        self.selected = set()

    def select(self, h, source, rule):
        if type(rule) is not dict or type(rule.get('kind')) is not str:
            raise ValueError('Invalid selected coverage rule')
        kind = rule['kind']
        if kind in ('base', 'edge', 'components', 'conditioning'):
            return  # verify_plan checks its exact shape and all ordered premises.
        if set(rule) != {'kind', 'id'} or type(rule['id']) is not str:
            raise ValueError('Invalid external coverage rule')
        token = (source, encode(rule))
        if token in self.selected:
            return
        identity = rule['id']
        if kind == 'pivot':
            record = self.pivots[identity]
        elif kind == 'coupled':
            record = self.coupled[identity]
            verify_coupled(h, record, self.pivots, self.counts)
        elif kind == 'growth':
            record = self.growth[identity]
        elif kind == 'probe_window':
            record = self.windows[identity]
        elif kind == 'probe_continuation':
            record = self._verify_saved(h, identity, self.counts)
        elif kind == 'trace_rewrite':
            record = self.rewrites[identity]
            verify_rewrite(h, record, self.counts)
        elif kind == 'trace_learning':
            record = self.learning[identity]
            verify_learning(h, record, self.counts)
        elif kind == 'learning_continuation':
            record = self.learned_blocks._saved(h, identity, self.counts)
            base = self.learned_blocks.bases[record['base_sha256']]
            if base['source'] != source:
                raise ValueError('Foreign learned continuation source')
        elif kind == 'trace_split':
            record = self.splits[identity]
            verify_split(h, record, self.counts)
        elif kind == 'affine_clause':
            record = self.affine[identity]
            if record['source'] != source:
                raise ValueError('Foreign affine source')
            attach_affine(h, self, record, self.counts)
            self.selected.add(token)
            return
        else:
            raise ValueError('Unsupported selected route kind')
        if kind != 'learning_continuation' and record['source'] != source:
            raise ValueError('Foreign selected route source')
        edges = record['edges'] if kind == 'trace_split' else [record['edge']]
        if any(edge is None or h._load(edge['key']) is None for edge in edges):
            raise ValueError('Missing selected route child')
        item = (rule, [edge['key'] for edge in edges])
        if item not in self.by_source[source]:
            self.by_source[source].append(item)
        self.selected.add(token)


def verify_selected_plan(h, certificate, claimed_roots, evidence, counts):
    """Return a checked positive-only route subset; omission proves no negative."""
    if (type(certificate) is not dict or set(certificate) != {'roots', 'steps'} or
            certificate['roots'] != claimed_roots or type(certificate['steps']) is not list):
        raise ValueError('Invalid positive coverage certificate')
    routes = SelectedRoutes(h, evidence)
    for step in certificate['steps']:
        if (type(step) is not dict or set(step) != {'source', 'rule'} or
                type(step['source']) is not str):
            raise ValueError('Invalid selected coverage step')
        try:
            routes.select(h, step['source'], step['rule'])
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError('Malformed or missing selected evidence') from exc
    verify_plan(h, certificate, claimed_roots, routes, counts)
    return routes

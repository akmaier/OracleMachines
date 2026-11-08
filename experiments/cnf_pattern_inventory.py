"""Persistent, checked pattern inventory; no new SAT decision or complexity claim.

Profiles retain overlaps. A bounded planner explores independent components and
both restrictions of candidate variables. Closed means every selected leaf has
a recognized family, not SAT. All unsuccessful alternatives remain archived.
The existing residual solver remains the decision path and is not modified.
"""
from collections import Counter
import json
import sqlite3
import time

from experiments.cnf_residual_dag import components, matching_structure, normalize, restrict


FORMAT = 'cnf-pattern-v1'
FAMILIES = ('horn', 'dual_horn', 'two_cnf', 'zero_valid', 'one_valid',
            'matching', 'single_parity')


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def classify(cnf, parity_width, counts):
    """Complete syntax tests except capped explicit single-parity recognition.

    This tests the normalized representation, not membership up to arbitrary
    semantic equivalence. The parity test recognizes the full direct encoding
    of one equation, not general conjunctions of XORs or hidden affine models.
    """
    counts['classification_calls'] += 1
    counts['classification_literal_payload'] += sum(map(len, cnf))
    outcomes, evidence = {}, {}
    predicates = {
        'horn': lambda c: sum(lit > 0 for lit in c) <= 1,
        'dual_horn': lambda c: sum(lit < 0 for lit in c) <= 1,
        'two_cnf': lambda c: len(c) <= 2,
        'zero_valid': lambda c: any(lit < 0 for lit in c),
        'one_valid': lambda c: any(lit > 0 for lit in c),
    }
    for name, predicate in predicates.items():
        violation = next((i for i, c in enumerate(cnf) if not predicate(c)), None)
        outcomes[name] = 'recognized' if violation is None else 'excluded'
        evidence[name] = dict(violating_clause=violation)
    domains = matching_structure(cnf, counts)
    outcomes['matching'] = 'recognized' if domains is not None else 'excluded'
    evidence['matching'] = None if domains is None else [
        [cid, sorted(edges.items())] for cid, edges in sorted(domains.items())]
    variables = sorted({abs(lit) for c in cnf for lit in c})
    n = len(variables)
    if n > parity_width:
        outcomes['single_parity'] = 'unresolved'
        evidence['single_parity'] = dict(reason='width_cap', width=n, cap=parity_width)
    else:
        # Distinct full-width clauses each exclude one assignment. Exactly half
        # the cube, all with the same parity, excludes precisely that parity.
        forbidden = {sum(lit < 0 for lit in c) % 2 for c in cnf}
        valid = (n > 0 and len(cnf) == 1 << (n-1) and
                 all(len(c) == n for c in cnf) and len(forbidden) == 1)
        outcomes['single_parity'] = 'recognized' if valid else 'excluded'
        evidence['single_parity'] = (dict(variables=variables, rhs=1-next(iter(forbidden)))
                                     if valid else dict(reason='not_full_single_parity_encoding'))
    positions = {c: i for i, c in enumerate(cnf)}
    pairs = []
    for i, c in enumerate(cnf):
        if len(c) == 2:
            other = positions.get(tuple(sorted(-lit for lit in c)))
            if other is not None and i < other:
                pairs.append([i, other])
    return dict(outcomes=outcomes, evidence=evidence,
                cell=''.join(outcomes[name][0].upper() for name in FAMILIES),
                equivalence_pairs=pairs,
                shape=dict(variables=n, clauses=len(cnf), literals=sum(map(len, cnf)),
                           max_clause_width=max(map(len, cnf), default=0)))


class PatternInventory:
    def __init__(self, archive=':memory:', *, max_depth=1, candidate_limit=4,
                 parity_width=8, decompose=True):
        for name, value, limit in (('max_depth', max_depth, 3),
                                   ('candidate_limit', candidate_limit, 64),
                                   ('parity_width', parity_width, 16)):
            if type(value) is not int or not 0 <= value <= limit:
                raise ValueError(f'{name} must be an integer between 0 and {limit}')
        if type(decompose) is not bool:
            raise ValueError('decompose must be Boolean')
        self.config = dict(max_depth=max_depth, candidate_limit=candidate_limit,
                           parity_width=parity_width, decompose=decompose)
        self.db = sqlite3.connect(archive)
        self.db.execute('CREATE TABLE IF NOT EXISTS cnf_patterns_v1 (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS cnf_pattern_sources_v1 (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.commit()
        self.checked, self.active, self.counts = {}, set(), Counter()

    def close(self):
        self.db.close()

    def _canonical(self, cnf, depth):
        normalized, names = normalize(cnf, self.counts)
        key = encode([FORMAT, self.config, depth, normalized])
        self.counts['key_serialized_bytes'] += len(key.encode())
        return normalized, list(names), key

    def _load(self, key):
        if key in self.checked:
            self.counts['node_memory_hits'] += 1
            return self.checked[key]
        if key in self.active:
            raise ValueError('Cyclic pattern certificate')
        self.counts['node_database_lookups'] += 1
        row = self.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (key,)).fetchone()
        if row is None:
            return None
        self.counts['node_read_bytes'] += len(row[0].encode())
        node = json.loads(row[0])
        self.active.add(key)
        try:
            self._check(key, node)
        finally:
            self.active.remove(key)
        self.checked[key] = node
        return node

    def _edge(self, cnf, depth):
        normalized, names, key = self._canonical(cnf, depth)
        if self._load(key) is None:
            node = self._discover(normalized, depth)
            self._check(key, node)
            payload = encode(node)
            with self.db:
                self.db.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)', (key, payload))
            self.counts['inserted_nodes'] += 1
            self.counts['serialized_bytes'] += len(key.encode()) + len(payload.encode())
            self.checked[key] = node
        return dict(key=key, names=names)

    def _summary(self, edges):
        children = [self._load(edge['key']) for edge in edges]
        if any(c is None for c in children):
            raise ValueError('Missing child')
        return dict(closed=all(c['summary']['closed'] for c in children),
                    unresolved_leaves=sum(c['summary']['unresolved_leaves'] for c in children),
                    unresolved_literals=sum(c['summary']['unresolved_literals'] for c in children))

    def _discover(self, cnf, depth):
        profile = classify(cnf, self.config['parity_width'], self.counts)
        node = dict(cnf=[list(c) for c in cnf], depth=depth, profile=profile)
        groups = components(cnf, self.counts) if self.config['decompose'] else [cnf]
        if len(groups) > 1:
            edges = [self._edge(group, depth) for group in groups]
            node.update(kind='and', edges=edges, summary=self._summary(edges))
        elif any(v == 'recognized' for v in profile['outcomes'].values()):
            node.update(kind='family', summary=dict(closed=True, unresolved_leaves=0, unresolved_literals=0))
        elif depth > 0 and self.config['candidate_limit']:
            frequencies = Counter(abs(lit) for c in cnf for lit in c)
            choices = sorted(frequencies, key=lambda v: (-frequencies[v], v))[:self.config['candidate_limit']]
            alternatives = []
            for variable in choices:
                self.counts['conditioning_candidates'] += 1
                edges = [self._edge(restrict(cnf, {variable: value}, self.counts), depth-1)
                         for value in (False, True)]
                summary = self._summary(edges)
                alternatives.append(dict(variable=variable, edges=edges, summary=summary))
                if summary['closed']:
                    break
            if not alternatives:
                raise ValueError('Unrecognized constant should be impossible')
            selected = min(range(len(alternatives)), key=lambda i: (
                alternatives[i]['summary']['unresolved_literals'],
                alternatives[i]['summary']['unresolved_leaves'], i))
            node.update(kind='or', alternatives=alternatives, selected=selected,
                        summary=alternatives[selected]['summary'])
        else:
            node.update(kind='unresolved', summary=dict(closed=False, unresolved_leaves=1,
                        unresolved_literals=profile['shape']['literals']))
        return node

    def _check_edge(self, edge, cnf, depth):
        _, names, key = self._canonical(cnf, depth)
        if edge != dict(key=key, names=names) or self._load(key) is None:
            raise ValueError('Incorrect residual identity or variable binding')

    def _check(self, key, node):
        depth = node.get('depth')
        if type(depth) is not int or not 0 <= depth <= self.config['max_depth']:
            raise ValueError('Invalid remaining depth')
        cnf, _, actual = self._canonical(node['cnf'], depth)
        if actual != key or node['cnf'] != [list(c) for c in cnf]:
            raise ValueError('Invalid canonical identity')
        profile = classify(cnf, self.config['parity_width'], self.counts)
        # JSON-normalize tuple evidence before comparing cold-loaded records.
        if encode(node['profile']) != encode(profile):
            raise ValueError('Invalid pattern certificate')
        base_fields = {'cnf', 'depth', 'profile', 'kind', 'summary'}
        kind = node.get('kind')
        groups = components(cnf, self.counts) if self.config['decompose'] else [cnf]
        if kind == 'and':
            if set(node) != base_fields | {'edges'} or len(groups) <= 1 or len(node['edges']) != len(groups):
                raise ValueError('Invalid independent partition')
            # Exact component derivation checks coverage, disjoint supports and
            # source identity; arbitrary overlapping clause groups are rejected.
            for edge, group in zip(node['edges'], groups):
                self._check_edge(edge, group, depth)
            # Also check the partition directly, independently of the component
            # discovery routine. Child bindings must reconstruct every parent
            # clause exactly once, with pairwise disjoint variable supports.
            rebuilt, used = [], set()
            for edge in node['edges']:
                support = set(edge['names'])
                if used.intersection(support):
                    raise ValueError('Overlapping component supports')
                used.update(support)
                for clause in self._load(edge['key'])['cnf']:
                    rebuilt.append(tuple(sorted(edge['names'][abs(lit)-1]*(1 if lit > 0 else -1)
                                                for lit in clause)))
                    self.counts['partition_verification_literals'] += len(clause)
            if tuple(sorted(rebuilt)) != cnf:
                raise ValueError('Component partition omits or duplicates clauses')
            summary = self._summary(node['edges'])
        elif kind == 'or':
            if (set(node) != base_fields | {'alternatives', 'selected'} or depth <= 0
                    or type(node['selected']) is not int or not node['alternatives']
                    or not 0 <= node['selected'] < len(node['alternatives'])):
                raise ValueError('Invalid variable partition')
            frequencies = Counter(abs(lit) for c in cnf for lit in c)
            choices = sorted(frequencies, key=lambda v: (-frequencies[v], v))[:self.config['candidate_limit']]
            if len(node['alternatives']) > len(choices):
                raise ValueError('Exceeded candidate budget')
            for attempt, variable in zip(node['alternatives'], choices):
                if (set(attempt) != {'variable', 'edges', 'summary'} or
                        type(attempt['variable']) is not int or attempt['variable'] != variable or len(attempt['edges']) != 2):
                    raise ValueError('Invalid conditioning candidate')
                for edge, value in zip(attempt['edges'], (False, True)):
                    self._check_edge(edge, restrict(cnf, {variable: value}, self.counts), depth-1)
                if encode(attempt['summary']) != encode(self._summary(attempt['edges'])):
                    raise ValueError('Invalid candidate coverage summary')
            # Require the exact deterministic search policy, not just a sound
            # subgraph that silently omits another attempted discovery.
            alternatives = node['alternatives']
            if any(a['summary']['closed'] for a in alternatives[:-1]) or (
                    not alternatives[-1]['summary']['closed'] and len(alternatives) != len(choices)):
                raise ValueError('Incomplete candidate policy trace')
            selected = min(range(len(alternatives)), key=lambda i: (
                alternatives[i]['summary']['unresolved_literals'], alternatives[i]['summary']['unresolved_leaves'], i))
            if node['selected'] != selected:
                raise ValueError('Incorrect candidate selection')
            summary = alternatives[selected]['summary']
        elif kind in ('family', 'unresolved'):
            if set(node) != base_fields:
                raise ValueError('Unexpected leaf fields')
            closed = any(v == 'recognized' for v in profile['outcomes'].values())
            if kind != ('family' if closed else 'unresolved'):
                raise ValueError('Incorrect family closure')
            if not closed and depth > 0 and self.config['candidate_limit']:
                raise ValueError('Omitted conditioning')
            summary = dict(closed=closed, unresolved_leaves=0 if closed else 1,
                           unresolved_literals=0 if closed else profile['shape']['literals'])
        else:
            raise ValueError('Unknown partition kind')
        if len(groups) > 1 and kind != 'and':
            raise ValueError('Omitted independent components')
        if kind == 'or' and any(v == 'recognized' for v in profile['outcomes'].values()):
            raise ValueError('Unexpected conditioning of recognized family')
        if encode(node['summary']) != encode(summary):
            raise ValueError('Incorrect coverage summary')
        self.counts['verified_pattern_nodes'] += 1

    def inspect(self, source):
        self.counts = Counter()
        started = time.perf_counter()
        # Materialize and validate the complete original source, even when
        # normalization subsequently collapses it to an empty-clause formula.
        source = [list(c) for c in source]
        if any(type(lit) is not int or lit == 0 for c in source for lit in c):
            raise ValueError('CNF literals must be nonzero integers')
        source_key = encode([FORMAT, self.config, source])
        edge = self._edge(source, self.config['max_depth'])
        payload = encode(dict(source=source, root=edge, config=self.config))
        self.counts['source_serialized_bytes'] += len(source_key.encode()) + len(payload.encode())
        with self.db:
            cursor = self.db.execute('INSERT OR IGNORE INTO cnf_pattern_sources_v1 VALUES (?,?)', (source_key, payload))
        self.counts['inserted_sources'] += cursor.rowcount
        # Reject a conflicting existing source record instead of trusting the
        # source lookup or allowing INSERT OR IGNORE to conceal corruption.
        actual = self.db.execute('SELECT payload FROM cnf_pattern_sources_v1 WHERE id=?', (source_key,)).fetchone()[0]
        if actual != payload:
            raise ValueError('Incorrect exact-source binding')
        node = self._load(edge['key'])
        return dict(source_id=source_key, root=edge, profile=node['profile'], summary=node['summary'],
                    seconds=time.perf_counter()-started, metrics=dict(self.counts))

    def storage(self):
        result = {}
        for table, prefix in (('cnf_patterns_v1', 'nodes'), ('cnf_pattern_sources_v1', 'sources')):
            rows, size = self.db.execute(f'SELECT count(*), coalesce(sum(length(CAST(id AS BLOB))+length(CAST(payload AS BLOB))),0) FROM {table}').fetchone()
            result[prefix], result[prefix+'_bytes'] = rows, size
        return result

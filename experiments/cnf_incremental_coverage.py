"""Reuse a complete finite coverage graph under checked, append-only updates.

The caller supplies the COMPLETE checked external-route catalog at each version,
and guarantees immutable historical pattern rows and a fixed recognition policy.
This is the same authority contract as compose(), not a partial discovery API.
Refresh compares the whole external catalog, checks changed reachable sources and
new descendants, and propagates only newly justified premises. Deletion/rebinding
requires a rebuild. Cold load rechecks the complete reachable catalog; persisted
closure flags are never trusted. Pending routes must be refreshed by the caller
when their targets are admitted, even if no new route record was inserted.
"""
from collections import defaultdict, deque
import json

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import options

FORMAT = 'incremental-finite-coverage-v1'


def catalog(routes):
    """Snapshot exact identities and ordered premises, including multiplicity."""
    result = {}
    for source, rows in routes.by_source.items():
        if rows:
            result[source] = row_map(rows)
    return result


def row_map(rows):
    result = {}
    for rule, children in rows:
        if type(rule) is not dict or any(type(c) is not str for c in children):
            raise ValueError('Invalid checked coverage rule')
        identity = encode(rule)
        if identity in result:
            raise ValueError('Duplicate coverage rule identity')
        result[identity] = tuple(children)
    return result


class CoverageIndex:
    def __init__(self, h, roots, routes, counts):
        self._empty(roots)
        self.external = catalog(routes)
        staged = self._stage(h, roots, routes, counts)
        self._install(staged, counts)

    def _empty(self, roots):
        self.roots = list(roots)
        self.keys = []; self.ids = {}; self.rules = []; self.by_source = []
        self.waiting = defaultdict(list); self.remaining = []
        self.justified = {}; self.order = []; self.external = {}

    def _rows(self, source):
        return {encode(self.rules[i][1]): tuple(self.keys[c] for c in self.rules[i][2])
                for i in self.by_source[self.ids[source]]}

    def _stage(self, h, sources, routes, counts):
        # Validate before mutating the index, including all newly reachable nodes.
        todo = deque(sources); staged = {}
        while todo:
            source = todo.popleft()
            if source in staged:
                continue
            rows = options(h, source, routes); current = row_map(rows)
            counts['checked_option_sources'] += 1
            if source in self.ids:
                old = self._rows(source)
                if any(current.get(rule) != children for rule, children in old.items()):
                    raise ValueError('Coverage rule removed or rebound; rebuild required')
            staged[source] = rows
            for _, children in rows:
                todo.extend(c for c in children if c not in self.ids and c not in staged)
        return staged

    def _install(self, staged, counts):
        for source in staged:
            if source not in self.ids:
                self.ids[source] = len(self.keys); self.keys.append(source)
                self.by_source.append([]); counts['added_nodes'] += 1
        ready = deque()
        for source, rows in staged.items():
            known = self._rows(source); sid = self.ids[source]
            for rule, children in rows:
                if encode(rule) in known:
                    continue
                i = len(self.rules); premises = tuple(self.ids[c] for c in children)
                self.rules.append((sid, json.loads(encode(rule)), premises))
                self.by_source[sid].append(i)
                missing = [c for c in premises if c not in self.justified]
                self.remaining.append(len(missing))
                for child in missing:
                    self.waiting[child].append(i)
                if not missing:
                    ready.append(i)
                counts['added_rules'] += 1; counts['added_premises'] += len(premises)
        while ready:
            i = ready.popleft(); source = self.rules[i][0]
            if source in self.justified:
                continue
            self.justified[source] = i; self.order.append(source)
            counts['newly_justified_nodes'] += 1
            # Duplicate premises have duplicate reverse entries and are discharged
            # together. A cycle without a zero-premise derivation never starts.
            for dependent in self.waiting.pop(source, ()):
                self.remaining[dependent] -= 1; counts['discharged_premises'] += 1
                if self.remaining[dependent] == 0:
                    ready.append(dependent)

    def refresh(self, h, routes, counts):
        """Extend after an immutable-history update; rescan the COMPLETE catalog.

        This deliberately still pays global external-route verification. It does
        not assert that an incomplete list of changed sources proves completeness.
        """
        current = catalog(routes); counts['catalog_sources_compared'] += len(current)
        for source, old in self.external.items():
            new = current.get(source, {})
            if any(new.get(rule) != children for rule, children in old.items()):
                raise ValueError('External rule removed or rebound; rebuild required')
        changed = [s for s in current if current[s] != self.external.get(s, {})]
        counts['changed_catalog_sources'] += len(changed)
        staged = self._stage(h, (s for s in changed if s in self.ids), routes, counts)
        self._install(staged, counts)
        self.external = current
        return self.closed()

    def closed(self):
        return [self.ids[root] in self.justified for root in self.roots]

    def certificate(self):
        roots = [r for r in self.roots if self.ids[r] in self.justified]
        todo = list(map(self.ids.__getitem__, roots)); needed = set()
        while todo:
            source = todo.pop()
            if source not in needed:
                needed.add(source); todo.extend(self.rules[self.justified[source]][2])
        steps = [dict(source=self.keys[s], rule=self.rules[self.justified[s]][1])
                 for s in self.order if s in needed]
        # Return detached descriptors: callers cannot mutate retained witnesses.
        return json.loads(encode(dict(roots=roots, steps=steps)))

    def payload(self):
        """Intern node keys once; derived flags/counters are reconstructed."""
        return dict(format=FORMAT, keys=list(self.keys),
            roots=[self.ids[r] for r in self.roots],
            rules=[[s, json.loads(encode(rule)), list(children)] for s, rule, children in self.rules],
            external=[[s, [[r, list(cs)] for r, cs in rows.items()]]
                      for s, rows in self.external.items()])

    def audit(self, h, routes, counts):
        """Check catalog completeness, including missing rules and open sources."""
        if self.external != catalog(routes):
            raise ValueError('Changed external catalog')
        todo = deque(self.roots); seen = set()
        while todo:
            source = todo.popleft()
            if source in seen:
                continue
            seen.add(source)
            if source not in self.ids:
                raise ValueError('Missing reachable source')
            actual = row_map(options(h, source, routes)); counts['audited_sources'] += 1
            if actual != self._rows(source):
                raise ValueError('Incomplete or changed reachable rule catalog')
            for children in actual.values():
                todo.extend(children)
        if seen != set(self.keys):
            raise ValueError('Unreachable extra index nodes')
        return True

    @classmethod
    def load(cls, data, h, roots, routes, counts):
        """Cold, authority-bound replay; no fast trusted-negative load path."""
        if (type(data) is not dict or set(data) != {'format','keys','roots','rules','external'}
                or data['format'] != FORMAT or type(data['keys']) is not list
                or any(type(k) is not str for k in data['keys'])
                or len(set(data['keys'])) != len(data['keys'])):
            raise ValueError('Invalid coverage index fields')
        keys = data['keys']; valid = lambda i: type(i) is int and 0 <= i < len(keys)
        if (type(data['roots']) is not list or not all(map(valid, data['roots']))
                or [keys[i] for i in data['roots']] != list(roots)):
            raise ValueError('Incorrect coverage root binding')
        obj = cls.__new__(cls); obj._empty(roots)
        obj.keys = list(keys); obj.ids = {k:i for i,k in enumerate(keys)}
        obj.by_source = [[] for _ in keys]
        staged = {k:[] for k in keys}
        if type(data['rules']) is not list or type(data['external']) is not list:
            raise ValueError('Invalid coverage catalogs')
        for entry in data['rules']:
            if (type(entry) is not list or len(entry) != 3 or not valid(entry[0])
                    or type(entry[1]) is not dict or type(entry[2]) is not list
                    or not all(map(valid, entry[2]))):
                raise ValueError('Invalid serialized rule')
            source, rule, children = entry
            staged[keys[source]].append((rule, [keys[c] for c in children]))
        for rows in staged.values():
            row_map(rows)  # Reject duplicate identities before installation.
        for entry in data['external']:
            if (type(entry) is not list or len(entry) != 2 or type(entry[0]) is not str
                    or entry[0] in obj.external or type(entry[1]) is not list or not entry[1]):
                raise ValueError('Invalid external index')
            rows = {}
            for pair in entry[1]:
                if (type(pair) is not list or len(pair) != 2 or type(pair[0]) is not str
                        or pair[0] in rows or type(pair[1]) is not list
                        or any(type(c) is not str for c in pair[1])):
                    raise ValueError('Invalid external rule')
                rows[pair[0]] = tuple(pair[1])
            obj.external[entry[0]] = rows
        obj._install(staged, counts)
        obj.audit(h, routes, counts)
        return obj

"""Reference closed, exactly source-bound plans across two fixed policies.

The prepared PolarityHornInventory is checked under its own configuration. Its
closed graph can be referenced before binary-path acquisition, without copying
the graph or requiring its choices to match the new scheduler. Preparation and
cold verification are not free. This is exact syntactic reuse, not an equivalence
oracle, a SAT decision, or a claim that every new input has a prepared plan.
"""
from collections import Counter
import json

from experiments.cnf_binary_paths import BinaryPathInventory
from experiments.cnf_pattern_inventory import FORMAT, encode
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_residual_dag import holds


class RetainedPlanInventory(BinaryPathInventory):
    def __init__(self, archive=':memory:', *, binary_path_root_limit=64, **kwargs):
        super().__init__(archive, binary_path_root_limit=binary_path_root_limit, **kwargs)
        # A separate verifier/cache, sharing this archive's connection. This also
        # handles :memory: correctly. Only _load is used on this prepared view;
        # it never discovers, records or rewrites old plans.
        self.prepared = PolarityHornInventory(**kwargs)
        self.prepared.db.close()
        self.prepared.db = self.db
        self.config['retained_plans'] = 'exact-closed-polarity-reference-v1'

    def _prepared_key(self, cnf, depth):
        key = encode([FORMAT, self.prepared.config, depth, cnf])
        self.counts['retained_plan_key_bytes'] += len(key.encode())
        return key

    def _find_closed(self, cnf, depth):
        key = self._prepared_key(cnf, depth)
        self.counts['retained_plan_lookups'] += 1
        row = self.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (key,)).fetchone()
        if row is None:
            self.counts['retained_plan_missing'] += 1
            return None
        self.counts['retained_plan_hint_read_bytes'] += len(row[0].encode())
        hint = json.loads(row[0])
        # This untrusted hint can only skip reuse. A positive must pass the full
        # original checker, including source, depth and all attempted branches.
        if hint.get('summary', {}).get('closed') is not True:
            self.counts['retained_plan_unclosed'] += 1
            self._unclosed_hint(cnf, depth, hint)
            return None
        plan = self.prepared._load(key)
        if plan is None or plan['summary']['closed'] is not True:
            raise ValueError('Invalid prepared closed-plan hint')
        self.counts['retained_plan_hits'] += 1
        return key, plan

    def _unclosed_hint(self, cnf, depth, hint):
        """Optional acquisition hint; the base policy makes no use of it."""

    def _discover(self, cnf, depth):
        found = self._find_closed(cnf, depth)
        if found is None:
            return super()._discover(cnf, depth)
        reference, plan = found
        return dict(cnf=[list(c) for c in cnf], depth=depth, kind='retained_plan',
                    reference=reference, profile=plan['profile'], summary=plan['summary'])

    def _check(self, key, node):
        if node.get('kind') != 'retained_plan':
            return super()._check(key, node)
        if set(node) != {'cnf', 'depth', 'kind', 'reference', 'profile', 'summary'}:
            raise ValueError('Invalid retained-plan fields')
        depth = node['depth']
        if type(depth) is not int or not 0 <= depth <= self.config['max_depth']:
            raise ValueError('Invalid retained-plan depth')
        cnf, _, actual = self._canonical(node['cnf'], depth)
        if actual != key or node['cnf'] != [list(c) for c in cnf]:
            raise ValueError('Invalid retained-plan source identity')
        expected = self._prepared_key(cnf, depth)
        if node['reference'] != expected:
            raise ValueError('Retained plan differs in source, depth or policy')
        plan = self.prepared._load(expected)
        if plan is None or plan['summary']['closed'] is not True:
            raise ValueError('Missing or unclosed retained plan')
        if (encode(plan['cnf']) != encode(cnf) or
                encode(node['profile']) != encode(plan['profile']) or
                encode(node['summary']) != encode(plan['summary'])):
            raise ValueError('Invalid retained-plan profile or summary')
        self.counts['retained_plan_verified_references'] += 1
        self.counts['verified_pattern_nodes'] += 1

    def inspect(self, source):
        self.prepared.counts = Counter()
        result = super().inspect(source)
        result['prepared_metrics'] = dict(self.prepared.counts)
        return result

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'retained_plan':
            return super().lift(key, child_model)
        support = {abs(lit) for c in node['cnf'] for lit in c}
        if (any(v not in child_model or type(child_model[v]) is not bool for v in support)
                or not holds(node['cnf'], child_model)):
            raise ValueError('Invalid exact retained-plan model')
        return {v: child_model[v] for v in support}

    def close(self):
        self.prepared.close()
        # sqlite3.close is idempotent; both views must clear their private caches.
        super().close()

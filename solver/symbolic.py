"""Bounded ROBDD proposals built directly from syntax and factor operations.

No truth table is constructed. Ordered Shannon apply, restriction and existential
projection use a unique table and memoized subproblems. Native factor-row and
original-answer checks remain authoritative. A node/work limit triggers the
existing checked lazy path, never a negative verdict.
"""
from solver.resources import BudgetExceeded


class BDD:
    def __init__(self, max_nodes=50000, max_work=500000):
        self.max_nodes, self.max_work = max_nodes, max_work
        self.nodes = []
        self.unique, self.memo = {}, {}
        self.work = self.hits = 0
        self.deadline = None

    def begin(self, deadline):
        self.deadline = deadline
        self.work = self.hits = 0

    def tick(self):
        self.work += 1
        if self.work > self.max_work:
            raise BudgetExceeded('Symbolic operation cap exceeded')
        if self.deadline is not None:
            self.deadline.check()

    def node(self, variable, low, high):
        self.tick()
        if low == high:
            return low
        key = (variable, low, high)
        if key not in self.unique:
            if len(self.nodes) >= self.max_nodes:
                raise BudgetExceeded('Symbolic node cap exceeded')
            self.unique[key] = len(self.nodes) + 2
            self.nodes.append(key)
        return self.unique[key]

    def cached(self, key, compute):
        self.tick()
        if key in self.memo:
            self.hits += 1
            return self.memo[key]
        value = compute()
        # Computed-table storage is bounded independently of the unique table.
        if len(self.memo) >= self.max_nodes * 4:
            self.memo.clear()
        self.memo[key] = value
        return value

    def negate(self, root):
        if root < 2:
            return 1 - root
        def compute():
            v, low, high = self.nodes[root - 2]
            return self.node(v, self.negate(low), self.negate(high))
        return self.cached(('not', root), compute)

    def apply(self, op, left, right):
        if op not in ('and', 'or'):
            raise ValueError('Unknown symbolic operation')
        if left > right:
            left, right = right, left
        if left == right:
            return left
        if op == 'and':
            if left == 0:return 0
            if left == 1:return right
        else:
            if left == 0:return right
            if left == 1:return 1
        def compute():
            lv, ll, lh = self.nodes[left - 2]
            rv, rl, rh = self.nodes[right - 2]
            v = min(lv, rv)
            if lv != v:ll = lh = left
            if rv != v:rl = rh = right
            return self.node(v, self.apply(op, ll, rl), self.apply(op, lh, rh))
        return self.cached((op, left, right), compute)

    def restrict(self, root, variable, value):
        if root < 2:return root
        v, low, high = self.nodes[root - 2]
        if v > variable:return root
        if v == variable:return high if value else low
        return self.cached(('restrict', root, variable, value),
            lambda: self.node(v, self.restrict(low, variable, value),
                             self.restrict(high, variable, value)))

    def exists(self, root, variable):
        return self.apply('or', self.restrict(root, variable, False),
                          self.restrict(root, variable, True))

    def formula(self, nodes):
        values = []
        for n in nodes:
            self.tick()
            if n[0] == 'false':value = 0
            elif n[0] == 'var':value = self.node(n[1], 0, 1)
            elif n[0] == 'not':value = self.negate(values[n[1]])
            else:value = self.apply('and', values[n[1]], values[n[2]])
            values.append(value)
        return values[-1]

    def evaluate(self, root, assignment):
        while root >= 2:
            self.tick()
            v, low, high = self.nodes[root - 2]
            root = high if assignment[v] else low
        return bool(root)

    def dump(self, root):
        numbered = {0: 0, 1: 1}
        nodes = []
        pending = [(root, False)]
        while pending:
            self.tick()
            current, ready = pending.pop()
            if current in numbered:continue
            v, low, high = self.nodes[current - 2]
            if ready:
                numbered[current] = len(nodes) + 2
                nodes.append([v, numbered[low], numbered[high]])
            else:
                pending.extend([(current, True), (high, False), (low, False)])
        return dict(version=1, root=numbered[root], nodes=nodes)

    def restore(self, value):
        if value.get('version') != 1 or len(value['nodes']) > self.max_nodes:
            raise ValueError('Invalid symbolic object')
        translated = [0, 1]
        for i, row in enumerate(value['nodes'], 2):
            self.tick()
            if len(row) != 3 or any(type(x) is not int or x < 0 for x in row):
                raise ValueError('Invalid symbolic node')
            v, low, high = row
            if low >= i or high >= i or low == high:
                raise ValueError('Invalid symbolic dependency')
            if any(child >= 2 and value['nodes'][child - 2][0] <= v for child in (low, high)):
                raise ValueError('Unordered symbolic diagram')
            translated.append(self.node(v, translated[low], translated[high]))
        root = value['root']
        if type(root) is not int or not 0 <= root < len(translated):
            raise ValueError('Invalid symbolic root')
        return translated[root]

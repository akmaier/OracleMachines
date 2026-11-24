"""Compose guard contradictions on their actual clause support, then lift.

The existing negative component certificate accepts a refuted clause subset;
no independence assumption, positive join, or new native proof kind is needed.
"""
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_witness_solver import WitnessGuardClosureSolver
from experiments.cnf_guard_interactions import compile_path


def witness_support(source, hints, graph, proof, counts):
    positions = {cl: i for i, cl in enumerate(source)}
    counts['support_position_clauses'] += len(source)
    used = {tuple(graph[cid]) for path in (proof['forward'], proof['backward'])
            for _, cid in path}
    bank = {tuple(h['clause']): h for h in hints}
    wanted = set()
    needed = []
    for clause in sorted(used):
        if clause in positions:
            wanted.add(clause)
        else:
            if clause not in bank:
                raise ValueError('Missing witness consequence')
            hint = bank[clause]
            needed.append(hint)
            for cl in hint['template']['clauses']:
                counts['support_selection_literals'] += len(cl)
                wanted.add(tuple(cl))
    if not wanted or not wanted <= positions.keys():
        raise ValueError('Witness support is not a nonempty source subset')
    ids = sorted(positions[cl] for cl in wanted)
    support = tuple(source[i] for i in ids)
    counts['support_source_clauses'] += len(source)
    counts['support_source_literals'] += sum(map(len, source))
    counts['support_selected_clauses'] += len(support)
    counts['support_selected_literals'] += sum(map(len, support))
    return support, ids, needed


class SupportGuardClosureSolver(WitnessGuardClosureSolver):
    def _compile_closure(self, cnf, hints, graph, proof, tier):
        c = self.closure_counts
        paths = (proof['forward'], proof['backward'])
        edges = sum(map(len, paths))
        if any(len(path) > self.path_limit for path in paths):
            c['path_limit_misses'] += 1
            return None
        if c['reserved_edges'] + edges > self.closure_edges:
            c['edge_limit_misses'] += 1
            return None
        support, ids, needed = witness_support(cnf, hints, graph, proof, c)
        if support == cnf:
            c['support_full_context_fallbacks'] += 1
            return super()._compile_closure(cnf, hints, graph, proof, tier)
        c['reserved_edges'] += edges
        c['support_subset_attempts'] += 1
        child, names, key = self._canonical(support)
        old = self._read(key, child, purpose='guard_support_root')
        if old is not None:
            if old['answer']:
                raise ValueError('Contradictory saved support')
            c['support_root_hits'] += 1
        else:
            v = proof['variable']
            profile = dict(clauses=graph, paths={v: proof['backward'], -v: proof['forward']})
            # compile_path uses the enclosing source coordinates; canonical
            # variables are introduced only at each native publication boundary.
            low = compile_path(self, support, needed, profile, v, c, path_limit=self.path_limit)
            if v not in names:
                # Restricting an absent premise leaves H itself. The path has
                # already refuted H, so no split on a nonexistent variable is legal.
                if low != key or self._read(key, child, purpose='guard_support_absent') is None:
                    raise ValueError('Absent premise failed to refute support')
                c['support_absent_premise_lifts'] += 1
            else:
                high = compile_path(self, support, needed, profile, -v, c, path_limit=self.path_limit)
                self._store(key, dict(format=native.FORMAT, cnf=[list(cl) for cl in child],
                    answer=False, proof=dict(kind='split', variable=names.index(v)+1, low=low, high=high)))
            c['support_root_publications'] += 1
        c['closed_' + tier] += 1
        c['support_wrappers'] += 1
        return dict(kind='component', clauses=ids, child=key)

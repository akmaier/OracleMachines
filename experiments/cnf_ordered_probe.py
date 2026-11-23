"""Reuse the canonical parent's clause invariant at private probe preparation.

Restriction preserves each clause's strict literal order and lack of tautology.
Global deduplication, support compaction and exact serialization are still needed.
This helper is private to expansion of an already canonical source; public input
normalization and every original proof checker are unchanged.
"""
from collections import Counter
from experiments.cnf_residual_dag import FORMAT, restrict, propagate, token
from experiments.cnf_whole_lookahead import (InputSafeAffineProbeSolver,
    JointBackboneMixin, discover, compile_cover, check_path, prefer_ordinary,
    force_all, TargetedBackboneMixin)


def _prepare(cnf, variable, value, counts):
    """Exact normalize(restrict(...)) for a trusted canonical parent only."""
    if type(variable) is not int or variable <= 0 or type(value) is not bool:
        raise ValueError('Positive variable and Boolean value required')
    raw = restrict(cnf, {variable: value}, counts)
    counts['ordered_probe_preparations'] += 1
    counts['ordered_probe_reused_literals'] += sum(map(len, raw))
    counts['ordered_probe_reused_clauses'] += len(raw)
    clauses = set(raw)
    if () in clauses:
        child, names = ((),), ()
    else:
        names = tuple(sorted({abs(l) for c in clauses for l in c}))
        counts['ordered_probe_support_literals'] += sum(map(len, clauses))
        rename = {v: i+1 for i, v in enumerate(names)}
        # Signed rank renaming is strictly increasing, so it preserves each
        # already ordered clause. Restriction may reorder/deduplicate clauses.
        child = tuple(sorted(tuple(rename[abs(l)]*(1 if l > 0 else -1) for l in c)
                             for c in clauses))
        counts['ordered_probe_mapped_literals'] += sum(map(len, child))
    return child, names, token(child, counts)


def _probe(solver, cnf, variable, value):
    c = solver.counts
    c['bipolar_true_probes' if value else 'bipolar_false_probes'] += 1
    child, names, key = _prepare(cnf, variable, value, c)
    old = solver._read(key, child, purpose='bipolar_cofactor') if solver.reuse else None
    if old is not None:
        c['bipolar_cached_negative' if not old['answer'] else 'bipolar_cached_positive'] += 1
        return key if old['answer'] is False else None
    local = Counter()
    fixed, trace, conflict = propagate(child, local)
    c.update({'bipolar_'+k: v for k, v in local.items()})
    c['bipolar_probe_trace_entries'] += len(trace)
    if conflict is None:
        c['bipolar_no_conflict'] += 1
        return None
    solver._store(key, dict(format=FORMAT, cnf=[list(cl) for cl in child], answer=False,
        proof=dict(kind='units', trace=trace, conflict=conflict)))
    c['bipolar_compiled_children'] += 1
    return key


def _lookahead(solver, cnf):
    c = solver.counts
    if not cnf or any(len(cl) < 2 for cl in cnf):
        c['whole_probe_unit_skips'] += 1
        return None
    size = sum(map(len, cnf)); c['whole_probe_size_literals'] += size
    if len(cnf) > 4096 or size > 16384:
        c['whole_probe_size_skips'] += 1
        return None
    frequency = Counter(abs(l) for cl in cnf for l in cl)
    c['whole_probe_ranking_literals'] += size
    if len(frequency) > 256:
        c['whole_probe_size_skips'] += 1
        return None
    variable = min(frequency, key=lambda v: (-frequency[v], v))
    c['whole_probe_candidates'] += 1
    for value in (False, True):
        excluded = _probe(solver, cnf, variable, value)
        if excluded is None: continue
        c['whole_probe_selections'] += 1
        model, live = solver._visit(restrict(cnf, {variable: not value}, c))
        if model is not None:
            c['whole_probe_positive_lifts'] += 1
            return {variable: not value, **model}, None
        return None, dict(kind='split', variable=variable,
            low=live if value else excluded, high=excluded if value else live)
    c['whole_probe_misses'] += 1
    return None


class OrderedProbeMixin(JointBackboneMixin):
    def _expand(self, cnf):
        if self.leaves:
            proof, cover, parts = discover(cnf, self.counts)
            if proof is not None: return None, proof
            if cover is not None: return None, compile_cover(self, cnf, cover)
            if parts:
                for evidence in parts: check_path(cnf, evidence, self.counts)
                preferred = prefer_ordinary(self, cnf, parts)
                if preferred is not None: return preferred
                return force_all(self, cnf, parts)
            preferred = _lookahead(self, cnf)
            if preferred is not None: return preferred
        return super(TargetedBackboneMixin, self)._expand(cnf)


class OrderedProbeSolver(InputSafeAffineProbeSolver, OrderedProbeMixin):
    pass

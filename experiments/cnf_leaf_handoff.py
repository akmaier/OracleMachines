"""Pass immutable traversal preparation directly into a missing leaf's visit.

Only the recompose call produces the frame; callers cannot supply a prepared
triple. One identity-bound use skips duplicate normalization, then restores the
ordinary method before recursion or native verification. Requires exclusive,
synchronous use of the solver, as does the existing partial composer.
"""
from collections import Counter
from copy import deepcopy
from unittest.mock import patch
import time

from experiments.cnf_learned_conditional import LearnedCoverBank, check_cover
from experiments.cnf_conditional_unit_support import check_template, fixed_pairs
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_residual_dag import FORMAT, restrict, holds, propagate
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
from experiments.cnf_unit_cover_gate import has_candidate
from experiments.cnf_probed_partition import acquire
from experiments.cnf_transported_partition import native_query


def survival(target, cover, counts):
    check_cover(cover, counts)
    members = clause_set(target, counts)
    return [check_template(t, counts) <= members for t in cover['templates']]


def recompose(solver, target, cover, budget, screen=None, counts=None):
    """Return a checked whole-target result, or an explicitly unresolved prefix."""
    if type(budget) is not int or budget < 0:
        raise ValueError('Invalid partial-cover budget')
    c = Counter() if counts is None else counts
    target = tuple(tuple(cl) for cl in target)
    cover = deepcopy(cover)
    c['prepared_partial_source_literals'] += sum(map(len, target))
    intact = survival(target, cover, c)
    c['prepared_partial_cover_clauses'] += sum(len(t['clauses']) for t in cover['templates'])
    # Reset before root preparation so normalization/key work is retained.
    solver.counts = Counter()
    cnf, names, root = solver._canonical(target)
    fixed = {}
    if screen is not None:
        if screen['root'] != root or screen['conflict'] is not None:
            raise ValueError('Invalid nonconflicting partial-cover screen')
        local = {}
        for lit, cid in screen['trace']:
            if (type(lit) is not int or not lit or type(cid) is not int or
                    not 0 <= cid < len(cnf) or abs(lit) in local):
                raise ValueError('Invalid partial-cover trace')
            reason = cnf[cid]
            c['partial_prefix_check_literals'] += len(reason)
            if lit not in reason or any(abs(x) not in local or local[abs(x)] == (x > 0) for x in reason if x != lit):
                raise ValueError('Unforced partial-cover prefix')
            local[abs(lit)] = lit > 0
        fixed = {names[v - 1]: b for v, b in local.items()}
    old_limit = solver.node_limit
    solver.node_limit = budget
    solver._negative_tried = False
    events = []
    solver.db.start()
    stopped = False

    def store_model(key, local_cnf, local_names, model):
        solver._store(key, dict(format=FORMAT, cnf=[list(cl) for cl in local_cnf],
            answer=True, model=[model.get(v, False) for v in local_names]))
        c['partial_model_publications'] += 1

    def acquire_frame(source, canonical):
        # Private call-local consumer: source and canonical were constructed
        # together by walk from the copied target, never accepted from a hint.
        original = solver._canonical
        pending = True

        def consume(raw):
            nonlocal pending
            if pending and raw is source:
                pending = False
                # Remove the wrapper before _visit checks, recurses or stores.
                solver._canonical = original
                solver.counts['leaf_handoff_reuses'] += 1
                return canonical
            return original(raw)

        with patch.object(solver, '_canonical', consume):
            return solver._visit(source)

    def walk(node, context, prepared=None):
        if prepared is None:
            source = restrict(target, context, c)
            local_cnf, local_names, key = solver._canonical(source)
            prepared = (source, local_cnf, tuple(local_names), key)
        else:
            source, local_cnf, local_names, key = prepared
            c['prepared_partial_frame_reuses'] += 1
        old = solver._read(key, local_cnf, purpose='partial_existing')
        if old is not None:
            c['partial_existing_hits'] += 1
            return ({**context, **dict(zip(local_names, old['model']))} if old['answer'] else None), key
        if 'leaf' in node:
            i = node['leaf']
            if intact[i]:
                # Containment and the unit certificate were checked against
                # the copied target once above. The frame is created only here,
                # and its context must still imply this leaf's assumptions.
                template = cover['templates'][i]
                if any(context.get(v) != bit for v, bit in fixed_pairs(template['assumptions']).items()):
                    raise ValueError('Prepared context does not imply leaf assumptions')
                if () in local_cnf:
                    proof = dict(kind='empty')
                else:
                    rename = {v: j + 1 for j, v in enumerate(local_names)}
                    positions = {cl: j for j, cl in enumerate(local_cnf)}
                    small = restrict(template['clauses'], context, c)
                    ids = sorted({positions[tuple(sorted((1 if l > 0 else -1) * rename[abs(l)] for l in cl))] for cl in small})
                    _, trace, conflict = propagate(tuple(local_cnf[j] for j in ids), c)
                    if conflict is None:
                        raise ValueError('Prepared conditional support did not refute by units')
                    proof = dict(kind='units', trace=[[l, ids[cid]] for l, cid in trace], conflict=ids[conflict])
                solver._store(key, dict(format=FORMAT, cnf=[list(cl) for cl in local_cnf], answer=False, proof=proof))
                c['conditional_publications'] += 1
                c['prepared_partial_leaf_reuses'] += 1
                events.append(dict(leaf=i, route='support', root=key, context=sorted(context.items())))
                c['partial_support_leaves'] += 1
                return None, key
            c['partial_native_leaves'] += 1
            before = solver.counts['expanded_nodes']
            event = dict(leaf=i, route='native', root=key, context=sorted(context.items()))
            events.append(event)
            try:
                model, actual = acquire_frame(source, (local_cnf, local_names, key))
                assert actual == key
                event['answer'] = model is not None
                return (None if model is None else {**context, **model}), key
            finally:
                event['expanded_nodes'] = solver.counts['expanded_nodes'] - before
        v = node['variable']
        if v in context:
            c['partial_prefix_pruned_splits'] += 1
            return walk(node['high' if context[v] else 'low'], context, prepared)
        low_model, low = walk(node['low'], {**context, v: False}, prepared if v not in local_names else None)
        if low_model is not None:
            store_model(key, local_cnf, local_names, low_model)
            return low_model, key
        if v not in local_names:
            if low != key:
                raise ValueError('Absent partial split changed target')
            c['partial_absent_splits'] += 1
            return None, key
        high_model, high = walk(node['high'], {**context, v: True})
        if high_model is not None:
            store_model(key, local_cnf, local_names, high_model)
            return high_model, key
        solver._store(key, dict(format=FORMAT, cnf=[list(cl) for cl in local_cnf],
            answer=False, proof=dict(kind='split', variable=local_names.index(v) + 1, low=low, high=high)))
        c['partial_split_publications'] += 1
        return None, key

    try:
        try:
            model, child = walk(cover['tree'], fixed, (target, cnf, tuple(names), root) if not fixed else None)
            if fixed:
                if model is None:
                    solver._store(root, dict(format=FORMAT, cnf=[list(cl) for cl in cnf], answer=False,
                        proof=dict(kind='units', trace=deepcopy(screen['trace']), child=child)))
                else:
                    store_model(root, cnf, names, model)
                c['partial_prefix_publications'] += 1
            elif child != root:
                raise ValueError('Partial-cover root mismatch')
            if model is not None and not holds(target, model):
                raise ValueError('Partial-cover full witness mismatch')
        except RuntimeError as error:
            if str(error) != BUDGET_MESSAGE:
                raise
            stopped = True
            c['partial_budget_stops'] += 1
        # All pending nodes have passed native verification. Preserve complete
        # dependency prefixes even when a later missing leaf exhausts the cap.
        solver.db.finish()
    except BaseException:
        solver.db.abort()
        raise
    finally:
        solver.db.active = False
        solver.node_limit = old_limit
    if not stopped:
        node = solver._read(root, cnf, purpose='partial_result')
        solver._admit_negative(dict(root=root, answer=node['answer'], authority='native'))
    solver._peak()
    return dict(root=root, intact=intact, leaves=events, stopped=stopped)


class PartialCoverBank(LearnedCoverBank):
    def reuse_partial(self, target, guard, budget, screen):
        fixed = sorted([[v, b] for v, b in fixed_pairs(guard).items()])
        candidates = []
        tried = 0
        for index, entry in enumerate(self.entries):
            self.counts['partial_index_entries'] += 1
            if entry['guard'] != fixed or entry['rejected']:
                continue
            if tried == self.candidate_limit:
                break
            tried += 1
            if entry['cover'] is None:
                continue
            intact = survival(target, entry['cover'], self.counts)
            self.counts['partial_candidates'] += 1
            if any(intact) and not all(intact):
                candidates.append((len(intact) - sum(intact), -sum(intact), index))
        if not candidates:
            return None
        _, _, index = min(candidates)
        entry = self.entries[index]
        result = recompose(self.solver, target, entry['cover'], budget, screen, self.counts)
        self.counts['partial_attempts'] += 1
        return dict(**result, origin=entry['origin'], guard=deepcopy(fixed), cover=deepcopy(entry['cover']))


def run_after_pool_miss(solver, prepared, guard, entries, budget, counts):
    if type(budget) is not int or budget < 0:
        raise ValueError('Invalid native expansion budget')
    bank = PartialCoverBank(solver, entries)
    screen = learned = partial = None
    if has_candidate(entries, guard, counts):
        tick = time.perf_counter()
        _, trace, conflict = propagate(prepared.cnf, counts)
        screen = dict(root=prepared.key, trace=trace, conflict=conflict)
        counts['unit_gate_screen_seconds'] += time.perf_counter() - tick
        counts['unit_gate_screens'] += 1
        if conflict is not None:
            counts['unit_gate_conflicts'] += 1
        else:
            tick = time.perf_counter()
            learned = bank.reuse(prepared.target, guard)
            counts['unit_gate_cover_seconds'] += time.perf_counter() - tick
            if learned is None:
                before = dict(solver.counts)
                tick = time.perf_counter()
                partial = bank.reuse_partial(prepared.target, guard, budget, screen)
                counts['partial_seconds'] += time.perf_counter() - tick
                if partial is not None:
                    counts.update({'preliminary_' + k: v for k, v in before.items()})
    if partial is not None or learned is not None:
        counts.update(bank.counts)
        return dict(route='partial-cover' if partial is not None else 'learned-cover',
            learned=learned, partial=partial, screen=screen, stopped=partial is not None and partial['stopped'])
    route = 'native' if screen is None else 'unit-conflict' if screen['conflict'] is not None else 'unit-fallback'
    before = dict(solver.counts)
    stopped = False
    if screen is None:
        stopped = acquire(solver, prepared.target, budget)['result'] is None
    else:
        try:
            native_query(solver, prepared.target, budget, screen)
        except RuntimeError as error:
            if str(error) != BUDGET_MESSAGE:
                raise
            stopped = True
    counts.update({'preliminary_' + k: v for k, v in before.items()})
    if not stopped:
        bank.register(prepared, guard, solver.counts.get('expanded_nodes', 0))
    counts.update(bank.counts)
    return dict(route=route, learned=None, partial=None, screen=screen, stopped=stopped)

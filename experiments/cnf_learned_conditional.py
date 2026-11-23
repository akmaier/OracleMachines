"""Bounded, lazy reuse of checked conditional unit covers in source coordinates.

Only native UNSAT outcomes with at least three expansion dispatches are proposed.
The supplied outer guard filters candidates; it never certifies an answer.
Complete checked branch coverage and source containment precede native publication.
"""
from collections import Counter
from copy import deepcopy
import json

from experiments.cnf_conditional_unit_support import extract, check_template, fixed_pairs, materialize, ExtractionBudget
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_residual_dag import FORMAT, restrict

COVER_FORMAT = 'learned-conditional-cover-v1'


def check_cover(cover, counts=None, node_limit=64):
    c = Counter() if counts is None else counts
    if type(cover) is not dict or set(cover) != {'format', 'templates', 'tree'} or cover['format'] != COVER_FORMAT:
        raise ValueError('Invalid conditional cover')
    if type(cover['templates']) is not list or not cover['templates'] or len(cover['templates']) > node_limit:
        raise ValueError('Invalid cover templates')
    members = set()
    for template in cover['templates']:
        members.update(check_template(template, c))
    visited = 0
    leaves = set()

    def walk(node, fixed):
        nonlocal visited
        visited += 1
        if visited > node_limit or type(node) is not dict:
            raise ValueError('Invalid or oversized cover tree')
        if set(node) == {'leaf'}:
            i = node['leaf']
            if type(i) is not int or not 0 <= i < len(cover['templates']):
                raise ValueError('Invalid cover leaf')
            assumptions = fixed_pairs(cover['templates'][i]['assumptions'])
            if any(fixed.get(v) != b for v, b in assumptions.items()):
                raise ValueError('Cover path does not imply leaf assumptions')
            leaves.add(i)
        elif set(node) == {'variable', 'low', 'high'}:
            v = node['variable']
            if type(v) is not int or v <= 0 or v in fixed:
                raise ValueError('Invalid or repeated split variable')
            walk(node['low'], {**fixed, v: False})
            walk(node['high'], {**fixed, v: True})
        else:
            raise ValueError('Unresolved cover branch')
    walk(cover['tree'], {})
    if leaves != set(range(len(cover['templates']))):
        raise ValueError('Unused cover template')
    c['cover_checked_nodes'] += visited
    return members


def publish_cover(solver, target, cover, counts=None):
    """Recompose the entire cofactor using ordinary split/unit certificates."""
    c = Counter() if counts is None else counts
    if not check_cover(cover, c) <= clause_set(target, c):
        raise ValueError('Conditional support clauses are missing')
    target = tuple(tuple(cl) for cl in target)
    solver.db.start()
    try:
        def walk(node, fixed):
            cnf, names, key = solver._canonical(restrict(target, fixed, c))
            old = solver._read(key, cnf, purpose='learned_cover_existing')
            if old is not None:
                if old['answer'] is not False:
                    raise ValueError('Conflicting conditional cover')
                return key
            if 'leaf' in node:
                return materialize(solver, target, cover['templates'][node['leaf']],
                                   context=[[v, b] for v, b in sorted(fixed.items())], counts=c)['root']
            v = node['variable']
            low = walk(node['low'], {**fixed, v: False})
            if v not in names:
                if low != key:
                    raise ValueError('Absent split variable changed target')
                return key
            high = walk(node['high'], {**fixed, v: True})
            proof = dict(kind='split', variable=names.index(v) + 1, low=low, high=high)
            solver._store(key, dict(format=FORMAT, cnf=[list(cl) for cl in cnf], answer=False, proof=proof))
            c['cover_split_publications'] += 1
            return key
        root = walk(cover['tree'], {})
        solver.db.finish()
    except BaseException:
        solver.db.abort()
        raise
    finally:
        solver.db.active = False
    solver._admit_negative(dict(root=root, answer=False, authority='native'))
    solver._peak()
    c['learned_cover_hits'] += 1
    return root


def origin_source(solver, entry):
    node = solver._read(entry['origin'], purpose='learned_origin')
    if node is None or node['answer'] is not False:
        raise ValueError('Missing checked negative origin')
    names = entry['names']
    variables = max((abs(l) for cl in node['cnf'] for l in cl), default=0)
    if type(names) is not list or len(names) != variables or any(type(v) is not int or v <= 0 for v in names) or names != sorted(set(names)):
        raise ValueError('Invalid source-name binding')
    return [[(1 if l > 0 else -1) * names[abs(l) - 1] for l in cl] for cl in node['cnf']]


class LearnedCoverBank:
    def __init__(self, solver, entries, *, entry_limit=16, candidate_limit=4, byte_limit=262144):
        if any(type(v) is not int or v < 1 for v in (entry_limit, candidate_limit, byte_limit)) or byte_limit < 2:
            raise ValueError('Invalid bank limits')
        self.solver, self.entries = solver, entries
        self.entry_limit, self.candidate_limit, self.byte_limit = entry_limit, candidate_limit, byte_limit
        self.counts = Counter()

    def encoded_bytes(self):
        size = len(json.dumps(self.entries, sort_keys=True, separators=(',', ':')).encode())
        self.counts['learned_bank_serialized_bytes'] += size
        return size

    def register(self, prepared, guard, expanded):
        if expanded < 3:
            return
        fixed = sorted([[v, b] for v, b in fixed_pairs(guard).items()])
        if any(e['origin'] == prepared.key and e['names'] == list(prepared.names) and e['guard'] == fixed for e in self.entries):
            return
        node = self.solver._read(prepared.key, prepared.cnf, purpose='learned_register')
        if node is None or node['answer'] is not False:
            return
        entry = dict(origin=prepared.key, names=list(prepared.names), guard=fixed, cover=None, rejected=False)
        self.entries.append(entry)
        while len(self.entries) > self.entry_limit or self.encoded_bytes() > self.byte_limit:
            self.entries.pop(0)
            self.counts['learned_bank_evictions'] += 1
        self.counts['learned_registered'] += int(any(e is entry for e in self.entries))

    def reuse(self, target, guard):
        fixed = sorted([[v, b] for v, b in fixed_pairs(guard).items()])
        tried = 0
        for entry in self.entries:
            self.counts['learned_index_entries'] += 1
            if entry['guard'] != fixed or entry['rejected']:
                continue
            if tried == self.candidate_limit:
                break
            tried += 1
            self.counts['learned_candidates'] += 1
            if entry['cover'] is None:
                source = origin_source(self.solver, entry)
                try:
                    bundle, statistics = extract(self.solver, source, node_limit=64, literal_limit=65536)
                    for k, v in statistics.items():
                        self.counts['learned_extract_' + k] += v
                    cover = dict(format=COVER_FORMAT, templates=[e['template'] for e in bundle['entries']], tree=bundle['tree'])
                    check_cover(cover, self.counts)
                except ExtractionBudget:
                    entry['rejected'] = True
                    self.counts['learned_extraction_budget_stops'] += 1
                    continue
                # Unsupported endpoints never become complete covers.
                except ValueError as error:
                    if str(error) not in ('Invalid cover templates', 'Unresolved cover branch'):
                        raise
                    entry['rejected'] = True
                    self.counts['learned_unsupported'] += 1
                    continue
                entry['cover'] = cover
                if self.encoded_bytes() > self.byte_limit:
                    entry['cover'] = None
                    entry['rejected'] = True
                    self.counts['learned_capacity_stops'] += 1
                    continue
                self.counts['learned_extractions'] += 1
            wanted = check_cover(entry['cover'], self.counts)
            if not wanted <= clause_set(target, self.counts):
                self.counts['learned_support_misses'] += 1
                continue
            root = publish_cover(self.solver, target, entry['cover'], self.counts)
            return dict(root=root, origin=entry['origin'], guard=deepcopy(fixed), cover=deepcopy(entry['cover']))
        return None


def check_bank(solver, entries, counts=None, entry_limit=16, byte_limit=262144):
    c = Counter() if counts is None else counts
    if type(entries) is not list or len(entries) > entry_limit or len(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()) > byte_limit:
        raise ValueError('Invalid persisted bank size')
    for entry in entries:
        if type(entry) is not dict or set(entry) != {'origin', 'names', 'guard', 'cover', 'rejected'} or type(entry['rejected']) is not bool:
            raise ValueError('Invalid bank entry')
        fixed_pairs(entry['guard'])
        source = origin_source(solver, entry)
        if entry['cover'] is not None and not check_cover(entry['cover'], c) <= clause_set(source, c):
            raise ValueError('Stored cover is not bound to origin')
        c['learned_bank_checked_entries'] += 1
    return entries

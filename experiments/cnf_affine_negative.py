"""Opt-in, versioned affine refutations beside unchanged native certificates.

The extension table is read only by this interface. Native search never reads
it, so existing native certificates cannot acquire hidden extension dependencies.
Sessions exclusively own their append-only database and checked-memory cache.
"""
from collections import Counter
from copy import deepcopy
import json
import time

from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_affine_clause import check_space
from experiments.cnf_guard_chain import FORMAT as CHAIN_FORMAT, make_record, check_record

FORMAT = 'cnf-affine-negative-v1'
CHAIN = 'affine-negative-chain-v1'
TABLE = 'cnf_affine_negative_v1'
FREE_LIMIT = 8


def compile_proof(evidence):
    """Copy retained discovery, without trusting its status or summary."""
    a = deepcopy(evidence['affine'])
    if evidence['status'] == 'linear-conflict':
        rows = [i for i, row in enumerate(a['reductions']) if row['mask'] == 0 and row['rhs'] == 1]
        if not rows: raise ValueError('Missing affine conflict')
        decision = dict(kind='linear-conflict', row=rows[0])
    elif evidence['status'] == 'space-exhausted':
        decision = dict(kind='exhaustion', space=deepcopy(evidence['space']), rejected=list(evidence['rejected']))
    else:
        raise ValueError('No negative affine evidence')
    return dict(affine=a, decision=decision)


def check_negative(cnf, n, proof, counts):
    """Check source extraction, row contradiction or every complete-space point.

    Candidate reconstruction uses the direct Gray coefficient vector, independent
    of the producer's incremental XOR walk. Each point needs one falsified source
    clause; neither first-clause order nor the producer's status is trusted.
    """
    if type(proof) is not dict or set(proof) != {'affine', 'decision'}:
        raise ValueError('Invalid negative affine proof')
    a = proof['affine']; summary = check_affine(cnf, a, counts); d = proof['decision']
    if type(d) is not dict: raise ValueError('Invalid affine decision')
    if d.get('kind') == 'linear-conflict':
        if set(d) != {'kind', 'row'} or type(d['row']) is not int or not 0 <= d['row'] < len(a['reductions']):
            raise ValueError('Invalid conflict row')
        row = a['reductions'][d['row']]
        if (row['mask'], row['rhs']) != (0, 1): raise ValueError('Noncontradictory row')
        counts['affine_negative_conflicts_checked'] += 1
        return summary
    if d.get('kind') != 'exhaustion' or set(d) != {'kind', 'space', 'rejected'} or summary['inconsistent']:
        raise ValueError('Invalid exhaustion decision')
    free = n - summary['rank']
    if not 0 <= free <= FREE_LIMIT: raise ValueError('Exhaustion exceeds the versioned free-dimension limit')
    rejected = d['rejected']; leftovers = set(a['leftovers'])
    if (type(rejected) is not list or len(rejected) != 1 << free
            or any(type(cid) is not int or cid not in leftovers for cid in rejected)):
        raise ValueError('Missing or invalid rejection coverage')
    space = d['space']; check_space(n, a, space, counts)
    packed = {}
    for cid in sorted(set(rejected)):
        positive = negative = 0
        for lit in cnf[cid]:
            counts['affine_negative_packed_literals'] += 1
            if lit > 0: positive |= 1 << (lit - 1)
            else: negative |= 1 << (-lit - 1)
        packed[cid] = positive, negative
    for i, cid in enumerate(rejected):
        gray = i ^ (i >> 1); mask = space['particular']
        while gray:
            bit = gray & -gray; mask ^= space['directions'][bit.bit_length() - 1]; gray ^= bit
            counts['affine_negative_direct_xors'] += 1
        positive, negative = packed[cid]
        if mask & positive or ~mask & negative: raise ValueError('Rejection clause is satisfied')
        counts['affine_negative_rejections_checked'] += 1
    counts['affine_negative_spaces_checked'] += 1
    return summary


class NegativeStore:
    """A separate certificate authority; never inject into the native table."""
    def __init__(self, solver, *, create=False):
        self.solver = solver; self.checked = {}
        if create:
            solver.db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            solver.db.commit()

    def verify(self, root, node):
        if (type(node) is not dict or set(node) != {'format', 'cnf', 'answer', 'proof'}
                or node['format'] != FORMAT or node['answer'] is not False):
            raise ValueError('Invalid affine negative node header')
        cnf, names, key = self.solver._canonical(node['cnf'])
        if key != root or node['cnf'] != [list(c) for c in cnf]:
            raise ValueError('Noncanonical or mismatched affine source')
        check_negative(cnf, len(names), node['proof'], self.solver.counts)
        self.solver.counts['affine_negative_nodes_checked'] += 1
        return node

    def read(self, root, expected=None):
        counts = self.solver.counts
        if root in self.checked:
            counts['affine_negative_memory_hits'] += 1; node = self.checked[root]
        else:
            counts['affine_negative_database_lookups'] += 1
            row = self.solver.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?', (root,)).fetchone()
            if row is None: return None
            counts['affine_negative_read_bytes'] += len(row[0].encode())
            node = self.verify(root, json.loads(row[0])); self.checked[root] = node
        if expected is not None and node['cnf'] != [list(c) for c in expected]:
            raise ValueError('Wrong affine target')
        return node

    def publish(self, source, evidence):
        started = time.perf_counter(); s = self.solver; s.counts = Counter()
        cnf, _, root = s._canonical(source)
        if evidence['root'] != root: raise ValueError('Discovery belongs to another source')
        node = dict(format=FORMAT, cnf=[list(c) for c in cnf], answer=False, proof=compile_proof(evidence))
        self.verify(root, node)
        # Verification precedes publication even when retaining an alternative to
        # an already known native proof. INSERT OR IGNORE preserves the first bytes.
        payload = json.dumps(node, sort_keys=True, separators=(',', ':'))
        s.counts['affine_negative_serialized_bytes'] += len(payload.encode())
        with s.db:
            cursor = s.db.execute(f'INSERT OR IGNORE INTO {TABLE} VALUES (?,?)', (root, payload))
        if cursor.rowcount:
            s.counts['affine_negative_inserted_nodes'] += 1
            s.counts['affine_negative_inserted_bytes'] += len(root.encode()) + len(payload.encode())
        # On duplicate insertion verify/cache the stored payload, not the proposed
        # alternative: memory and cold replay then use the same certificate.
        if cursor.rowcount: self.checked[root] = node
        else:
            self.checked.pop(root, None); self.read(root, cnf)
        return dict(root=root, answer=False, model=None, backend=FORMAT,
                    metrics=dict(s.counts), seconds=time.perf_counter()-started)

    def storage(self):
        return self.solver.db.execute(f'SELECT count(*),coalesce(sum(length(id)+length(payload)),0) FROM {TABLE}').fetchone()

    def lookup(self, source):
        """Exact-source reuse without discovery or native search; None is a miss."""
        started = time.perf_counter(); s = self.solver; s.counts = Counter()
        cnf, _, root = s._canonical(source)
        if self.read(root, cnf) is None: return None
        return dict(root=root, answer=False, model=None, backend=FORMAT,
                    metrics=dict(s.counts), seconds=time.perf_counter()-started)

    def view(self):
        return _CheckedView(self)


class _CheckedView:
    """Read-only composition adapter. It cannot be used for native acquisition."""
    def __init__(self, store): self.store = store
    def _canonical(self, source): return self.store.solver._canonical(source)
    def _read(self, root, expected=None, purpose='search'):
        native = self.store.solver._read(root, expected, purpose)
        return native if native is not None else self.store.read(root, expected)


def compose(store, source, guards, child):
    if child.get('backend') != FORMAT or child['answer'] is not False:
        raise ValueError('Expected an explicit negative affine child')
    record = make_record(store.view(), source, guards, child)
    record['format'] = CHAIN
    check_composed(store, record)
    return record


def check_composed(store, record):
    if record.get('format') != CHAIN or record.get('answer') is not False or record.get('child', {}).get('answer') is not False:
        raise ValueError('Expected a negative affine chain')
    copy = deepcopy(record); copy['format'] = CHAIN_FORMAT
    # Require the terminal extension even if a preserved native alternative exists.
    current = copy['source']
    from experiments.cnf_clause_deletion_guard import check_guard
    for guard in copy['guards']: _, current = check_guard(store.view(), current, guard)
    cnf, _, root = store.solver._canonical(current)
    if store.read(root, cnf) is None: raise ValueError('Missing affine terminal')
    return check_record(store.view(), copy)

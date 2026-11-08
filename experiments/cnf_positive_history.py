"""Research-only persistent histories of witnessed positive-clause additions.

Version IDs are local to one append-only SQLite archive, not portable content
hashes or authenticated external identities. A version denotes its stored base
and exact parent/delta sequence. Unsupported edits require a newly solved base.
The Python checker is separate from the production Lean acceptance path.
"""
from collections import Counter
import json
import time

from experiments.cnf_residual_dag import ResidualSolver, holds


BASE_FORMAT = "positive-history-base-v1"


class UnsupportedExpansion(ValueError):
    """No retained positive subset; this path supplies no verdict for the edit."""


class PositiveHistory:
    def __init__(self, archive=":memory:"):
        self.solver = ResidualSolver(archive)
        self.db = self.solver.db
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("""CREATE TABLE IF NOT EXISTS cnf_positive_bases_v1 (
            id INTEGER PRIMARY KEY, payload TEXT NOT NULL UNIQUE)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS cnf_positive_versions_v1 (
            id INTEGER PRIMARY KEY,
            base INTEGER NOT NULL REFERENCES cnf_positive_bases_v1(id),
            parent INTEGER REFERENCES cnf_positive_versions_v1(id),
            payload TEXT NOT NULL, UNIQUE(base,parent,payload))""")
        self.db.commit()
        self.bases, self.checked = {}, {}
        self.counts = Counter()

    def close(self):
        self.solver.close()

    def _begin(self):
        self.counts = Counter()
        self.solver.counts = Counter()
        return time.perf_counter()

    def _result(self, version, started):
        base = self.bases[self.checked[version][0]]
        return dict(version=version, answer=base["answer"], seconds=time.perf_counter() - started,
                    metrics=dict(self.counts), solver_metrics=dict(self.solver.counts))

    @staticmethod
    def _id(value):
        if type(value) is not int or value <= 0:
            raise ValueError("Invalid archive-local version/base ID")

    def _json(self, value):
        payload = json.dumps(value, separators=(",", ":"), sort_keys=True)
        self.counts["serialized_bytes"] += len(payload.encode())
        return payload

    def _base(self, base_id):
        self._id(base_id)
        if base_id in self.bases:
            self.counts["base_memory_hits"] += 1
            return self.bases[base_id]
        self.counts["database_lookups"] += 1
        row = self.db.execute("SELECT payload FROM cnf_positive_bases_v1 WHERE id=?", (base_id,)).fetchone()
        if row is None:
            raise ValueError("Missing history base")
        self.counts["read_bytes"] += len(row[0].encode())
        payload = json.loads(row[0])
        if payload.get("format") != BASE_FORMAT or type(payload.get("source")) is not list:
            raise ValueError("Invalid history base")
        source = tuple(tuple(c) for c in payload["source"])
        normalized, names, root = self.solver._canonical(source)
        if payload.get("root") != root:
            raise ValueError("History base root does not match its source")
        node = self.solver._read(root, normalized, purpose="history_base")
        if node is None:
            raise ValueError("History base has no checked residual certificate")
        model = ({v: node["model"][i] for i, v in enumerate(names)} if node["answer"] else None)
        if model is not None:
            self.counts["base_witness_literal_payload"] += sum(map(len, source))
            if not holds(source, model):
                raise ValueError("History base source model failed")
        positive, frequencies = [], Counter()
        for cid, clause in enumerate(source):
            self.counts["index_build_literal_payload"] += len(clause)
            if clause and all(lit > 0 for lit in clause):
                positive.append(cid)
                frequencies.update(clause)
        postings = {}
        for cid in positive:
            anchor = min(source[cid], key=lambda lit: (frequencies[lit], lit))
            postings.setdefault(anchor, []).append(cid)
        base = dict(source=source, answer=node["answer"], model=model, postings=postings)
        self.bases[base_id] = base
        self.counts["verified_bases"] += 1
        return base

    def _positive(self, clause):
        if not isinstance(clause, (tuple, list)) or not clause:
            raise ValueError("A history delta must be a nonempty positive clause")
        self.counts["delta_literal_visits"] += len(clause)
        if any(type(lit) is not int or lit <= 0 for lit in clause):
            raise ValueError("A history delta must contain positive integer literals")
        return set(clause)

    def _witness(self, base, clause, witness):
        members = self._positive(clause)
        if type(witness) is not int or not 0 <= witness < len(base["source"]):
            raise ValueError("Invalid history subset witness index")
        kept = base["source"][witness]
        self.counts["witness_literal_visits"] += len(kept)
        if not kept or any(lit <= 0 or lit not in members for lit in kept):
            raise ValueError("History delta lacks its claimed positive subset")

    def _load(self, version):
        """Iterative cold replay; cache compact records, never full version CNFs."""
        self._id(version)
        if version in self.checked:
            self.counts["version_memory_hits"] += 1
            return self.checked[version]
        pending, seen, current = [], set(), version
        while current not in self.checked:
            self._id(current)
            if current in seen:
                raise ValueError("Cyclic history certificate")
            seen.add(current)
            self.counts["database_lookups"] += 1
            row = self.db.execute(
                "SELECT base,parent,payload FROM cnf_positive_versions_v1 WHERE id=?", (current,)).fetchone()
            if row is None:
                raise ValueError("Missing history version")
            base_id, parent, encoded = row
            self._id(base_id)
            self.counts["read_bytes"] += len(encoded.encode())
            payload = json.loads(encoded)
            pending.append((current, base_id, parent, payload))
            if parent is None:
                break
            current = parent
        for current, base_id, parent, payload in reversed(pending):
            base = self._base(base_id)
            if parent is None:
                if payload != {"kind": "base"}:
                    raise ValueError("Invalid history root record")
            else:
                if parent not in self.checked or self.checked[parent][0] != base_id:
                    raise ValueError("History parent changes the fixed base")
                if type(payload) is not dict or set(payload) != {"kind", "clause", "witness"}:
                    raise ValueError("Invalid history delta record")
                if payload["kind"] != "append-positive":
                    raise ValueError("Unsupported history operation")
                self._witness(base, payload["clause"], payload["witness"])
                payload["clause"] = tuple(payload["clause"])
            self.checked[current] = (base_id, parent, payload)
            self.counts["verified_versions"] += 1
        return self.checked[version]

    def _put_version(self, base_id, parent, payload):
        encoded = self._json(payload)
        self.counts["database_writes"] += 1
        with self.db:
            cursor = self.db.execute(
                "INSERT OR IGNORE INTO cnf_positive_versions_v1(base,parent,payload) VALUES (?,?,?)",
                (base_id, parent, encoded))
        if cursor.rowcount:
            version = cursor.lastrowid
            self.counts["inserted_versions"] += 1
        else:
            self.counts["database_lookups"] += 1
            version = self.db.execute(
                "SELECT id FROM cnf_positive_versions_v1 WHERE base=? AND parent IS ? AND payload=?",
                (base_id, parent, encoded)).fetchone()[0]
        self._load(version)
        return version

    def prepare(self, cnf):
        """Acquire any base with ordinary solving; all acquisition is charged."""
        started = self._begin()
        source = [list(c) for c in cnf]
        solved = self.solver.solve(source)
        payload = self._json(dict(format=BASE_FORMAT, source=source, root=solved["root"]))
        self.counts["database_writes"] += 1
        with self.db:
            cursor = self.db.execute("INSERT OR IGNORE INTO cnf_positive_bases_v1(payload) VALUES (?)", (payload,))
        if cursor.rowcount:
            self.counts["inserted_bases"] += 1
        self.counts["database_lookups"] += 1
        base_id = self.db.execute("SELECT id FROM cnf_positive_bases_v1 WHERE payload=?", (payload,)).fetchone()[0]
        self.counts["database_lookups"] += 1
        row = self.db.execute("SELECT id FROM cnf_positive_versions_v1 WHERE base=? AND parent IS NULL", (base_id,)).fetchone()
        if row is None:
            version = self._put_version(base_id, None, {"kind": "base"})
        else:
            version = row[0]
            self._load(version)
        return self._result(version, started)

    def append(self, parent, clause):
        """Add a witnessed superset; no base/source scan on a checked warm path."""
        started = self._begin()
        base_id, _, _ = self._load(parent)
        base = self.bases[base_id]
        members = self._positive(clause)
        witness = None
        for lit in sorted(members):
            self.counts["posting_lookups"] += 1
            for cid in base["postings"].get(lit, ()):
                self.counts["candidate_tests"] += 1
                contained = True
                for other in base["source"][cid]:
                    self.counts["containment_probes"] += 1
                    if other not in members:
                        contained = False
                        break
                if contained:
                    witness = cid
                    break
            if witness is not None:
                break
        if witness is None:
            raise UnsupportedExpansion("No retained positive subset; acquire a new base for this edit")
        version = self._put_version(base_id, parent, dict(kind="append-positive", clause=list(clause), witness=witness))
        return self._result(version, started)

    def query(self, version):
        started = self._begin()
        self._load(version)
        return self._result(version, started)

    def materialize(self, version):
        """Explicitly charged source reconstruction, not part of warm append."""
        started = self._begin()
        base_id, _, _ = self._load(version)
        clauses, current = [], version
        while self.checked[current][1] is not None:
            _, parent, payload = self.checked[current]
            clauses.append(payload["clause"])
            current = parent
        source = self.bases[base_id]["source"] + tuple(reversed(clauses))
        self.counts["materialized_clauses"] += len(source)
        self.counts["materialized_literal_payload"] += sum(map(len, source))
        return dict(cnf=source, seconds=time.perf_counter() - started, metrics=dict(self.counts),
                    solver_metrics=dict(self.solver.counts))

    def witness(self, version):
        """Sparse assignment, with all omitted (including fresh) variables false."""
        started = self._begin()
        base_id, _, _ = self._load(version)
        model = self.bases[base_id]["model"]
        self.counts["copied_model_entries"] += len(model) if model is not None else 0
        return dict(model=dict(model) if model is not None else None,
                    seconds=time.perf_counter() - started, metrics=dict(self.counts),
                    solver_metrics=dict(self.solver.counts))

    def storage(self):
        """Optional full-archive scan, explicitly outside the append operation.

        Logical byte accounting includes residual text plus JSON encodings of
        integer references and history payloads. SQLite pages/indexes differ.
        """
        started = time.perf_counter()
        residual = self.db.execute("SELECT count(*), coalesce(sum(length(id)+length(payload)),0) FROM cnf_residual_v1").fetchone()
        bases = self.db.execute("SELECT id,payload FROM cnf_positive_bases_v1").fetchall()
        versions = self.db.execute("SELECT id,base,parent,payload FROM cnf_positive_versions_v1").fetchall()
        encoded_size = lambda row: len(json.dumps(row, separators=(",", ":")).encode())
        return dict(residual_nodes=residual[0], residual_bytes=residual[1], bases=len(bases), versions=len(versions),
                    logical_bytes=residual[1] + sum(map(encoded_size, bases)) + sum(map(encoded_size, versions)),
                    seconds=time.perf_counter() - started)

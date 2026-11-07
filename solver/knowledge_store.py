"""Immutable compressed objects and append-only incremental-session deltas.

Object hashes detect corruption; they do not certify clauses or SAT verdicts.
All recovered state is proposal state and accepted answers still need Lean checks.
Concurrent processes fork independent sessions rather than mixing variable IDs.
"""
import hashlib
import json
import time
import uuid
import zlib

MAX_OBJECT = 64 * 1024**2


class KnowledgeStore:
    @staticmethod
    def create(db):
        db.execute("""CREATE TABLE IF NOT EXISTS knowledge_objects (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, raw_bytes INTEGER NOT NULL,
            payload BLOB NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS incremental_sessions (
            namespace TEXT NOT NULL, session TEXT PRIMARY KEY, base TEXT,
            updated_ns INTEGER NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS incremental_deltas (
            session TEXT NOT NULL, ordinal INTEGER NOT NULL, object_id TEXT NOT NULL,
            PRIMARY KEY(session,ordinal))""")
        db.execute("CREATE INDEX IF NOT EXISTS incremental_recent ON incremental_sessions(namespace,updated_ns DESC)")
        db.execute("""CREATE TABLE IF NOT EXISTS component_entries (
            engine TEXT NOT NULL, key TEXT NOT NULL, object_id TEXT NOT NULL,
            created_ns INTEGER NOT NULL, PRIMARY KEY(engine,key))""")
        db.execute("""CREATE TABLE IF NOT EXISTS component_roots (
            engine TEXT NOT NULL, request TEXT NOT NULL, root TEXT NOT NULL,
            components INTEGER NOT NULL, PRIMARY KEY(engine,request))""")
        db.execute("""CREATE TABLE IF NOT EXISTS component_negatives (
            engine TEXT NOT NULL, key TEXT NOT NULL, instance TEXT NOT NULL,
            created_ns INTEGER NOT NULL, PRIMARY KEY(engine,key,instance))""")
        db.execute("CREATE INDEX IF NOT EXISTS component_negative_recent ON component_negatives(engine,created_ns DESC)")

    def __init__(self, db, namespace):
        self.db, self.namespace = db, namespace
        self.session = None
        self.ordinal = 0
        self.inserted_objects = 0

    def put(self, kind, value):
        raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
        if len(raw) > MAX_OBJECT:
            raise ValueError("Knowledge object exceeds the configured decoding limit")
        token = hashlib.sha256(kind.encode() + b"\0" + raw).hexdigest()
        packed = zlib.compress(raw, 1)
        cursor = self.db.execute("INSERT OR IGNORE INTO knowledge_objects VALUES (?,?,?,?)",
                                 (token, kind, len(raw), packed))
        self.inserted_objects += cursor.rowcount
        return token, len(raw), len(packed)

    def get(self, token, kind):
        row = self.db.execute("SELECT kind,raw_bytes,payload FROM knowledge_objects WHERE id=?", (token,)).fetchone()
        if row is None or row[0] != kind or not 0 <= row[1] <= MAX_OBJECT:
            raise ValueError("Missing or invalid knowledge object")
        decoder = zlib.decompressobj()
        raw = decoder.decompress(row[2], row[1] + 1)
        if len(raw) != row[1] or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError("Invalid compressed knowledge object size")
        if hashlib.sha256(kind.encode() + b"\0" + raw).hexdigest() != token:
            raise ValueError("Knowledge object integrity check failed")
        return json.loads(raw)

    def restore(self, deadline):
        """Read one stable session snapshot; previous sessions remain archived."""
        with self.db:
            self.db.execute("BEGIN")
            row = self.db.execute("SELECT * FROM incremental_sessions WHERE namespace=? ORDER BY updated_ns DESC LIMIT 1",
                                  (self.namespace,)).fetchone()
            if row is None:
                return {"nodes": [], "clauses": []}
            state = self.get(row["base"], "incremental_base") if row["base"] else {"nodes": [], "clauses": []}
            for delta in self.db.execute("SELECT object_id FROM incremental_deltas WHERE session=? ORDER BY ordinal", (row["session"],)):
                deadline.check()
                part = self.get(delta[0], "incremental_delta")
                state["nodes"].extend(part["nodes"])
                state["clauses"].extend(part["clauses"])
            return state

    def start(self, state):
        """Compact replay history once per process/reset, never delete prior deltas."""
        self.session, self.ordinal = uuid.uuid4().hex, 0
        with self.db:
            base = self.put("incremental_base", state)[0] if state["nodes"] or state["clauses"] else None
            self.db.execute("INSERT INTO incremental_sessions VALUES (?,?,?,?)",
                            (self.namespace, self.session, base, time.time_ns()))

    def append(self, nodes, clauses):
        if self.session is None:
            self.start({"nodes": [], "clauses": []})
        if not nodes and not clauses:
            return 0, 0
        with self.db:
            token, raw, packed = self.put("incremental_delta", dict(nodes=nodes, clauses=clauses))
            self.db.execute("INSERT INTO incremental_deltas VALUES (?,?,?)", (self.session, self.ordinal, token))
            self.db.execute("UPDATE incremental_sessions SET updated_ns=? WHERE session=?", (time.time_ns(), self.session))
        self.ordinal += 1
        return raw, packed

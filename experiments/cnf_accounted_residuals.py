"""Optional transactional accounting for the append-only residual archive.

Decisions, certificates and the search procedure are inherited unchanged. One
full census on opening establishes the counters; ordinary writes maintain them.
Replacement/conflict cases conservatively invalidate the counters. A later read
reconstructs them under a write lock, rather than guessing which SQL conflict
policy fired. This also works for writers using the old solver or raw SQLite.

The contract covers DML on cnf_residual_v1, not hostile changes to the accounting
schema or its private singleton. SQLite TEXT length semantics are preserved:
the historical payload_bytes field is bytes only for the generated ASCII JSON.
"""
import time

from experiments.cnf_residual_dag import ResidualSolver


TABLE = 'cnf_residual_accounting_v1'
CENSUS = ('SELECT count(*), coalesce(sum(length(payload)+length(id)),0) '
          'FROM cnf_residual_v1')
NEW = 'coalesce(length(NEW.payload)+length(NEW.id),0)'
OLD = 'coalesce(length(OLD.payload)+length(OLD.id),0)'
TRIGGERS = {
    'insert_conflict': f'''BEFORE INSERT ON cnf_residual_v1
        WHEN EXISTS (SELECT 1 FROM cnf_residual_v1 WHERE id=NEW.id OR rowid=NEW.rowid)
        BEGIN UPDATE {TABLE} SET dirty=1 WHERE singleton=1; END''',
    'insert': f'''AFTER INSERT ON cnf_residual_v1
        BEGIN UPDATE {TABLE} SET nodes=nodes+1, payload_units=payload_units+{NEW}
        WHERE singleton=1 AND dirty=0; END''',
    'update_conflict': f'''BEFORE UPDATE OF id, rowid, _rowid_, oid ON cnf_residual_v1
        WHEN EXISTS (SELECT 1 FROM cnf_residual_v1
        WHERE (id=NEW.id OR rowid=NEW.rowid) AND rowid!=OLD.rowid)
        BEGIN UPDATE {TABLE} SET dirty=1 WHERE singleton=1; END''',
    'update': f'''AFTER UPDATE ON cnf_residual_v1
        BEGIN UPDATE {TABLE} SET payload_units=payload_units+{NEW}-{OLD}
        WHERE singleton=1 AND dirty=0; END''',
    'delete': f'''AFTER DELETE ON cnf_residual_v1
        BEGIN UPDATE {TABLE} SET nodes=nodes-1, payload_units=payload_units-{OLD}
        WHERE singleton=1 AND dirty=0; END''',
}


class AccountedResidualSolver(ResidualSolver):
    def __init__(self, archive=':memory:', **kwargs):
        super().__init__(archive, **kwargs)
        started = time.perf_counter()
        self.accounting_censuses = 0
        try:
            # Serialize installation with other writers. Every open performs an
            # independent census, including existing/migrated accounting state.
            with self.db:
                self.db.execute('BEGIN IMMEDIATE')
                self.db.execute(f'''CREATE TABLE IF NOT EXISTS {TABLE} (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    nodes INTEGER NOT NULL, payload_units INTEGER NOT NULL,
                    dirty INTEGER NOT NULL CHECK(dirty IN (0,1)))''')
                for suffix, body in TRIGGERS.items():
                    name = f'{TABLE}_{suffix}'
                    sql = f'CREATE TRIGGER {name} {body}'
                    old = self.db.execute(
                        'SELECT sql FROM sqlite_master WHERE type=? AND name=?',
                        ('trigger', name)).fetchone()
                    if old is None:
                        self.db.execute(sql)
                    elif old != (sql,):
                        raise ValueError('Unrecognized residual accounting trigger: ' + name)
                self._reconstruct()
        except BaseException:
            self.close()
            raise
        self.accounting_initialization_seconds = time.perf_counter() - started

    def _reconstruct(self):
        """Caller holds a write transaction, including across the full census."""
        nodes, payload = self.db.execute(CENSUS).fetchone()
        self.accounting_censuses += 1
        old = self.db.execute(
            f'SELECT nodes,payload_units,dirty FROM {TABLE} WHERE singleton=1').fetchone()
        if old != (nodes, payload, 0):
            self.db.execute(f'''INSERT INTO {TABLE} VALUES (1,?,?,0)
                ON CONFLICT(singleton) DO UPDATE SET
                nodes=excluded.nodes,payload_units=excluded.payload_units,dirty=0''',
                (nodes, payload))
        return nodes, payload

    def archive_storage(self):
        self.counts['accounting_reads'] += 1
        row = self.db.execute(
            f'SELECT nodes,payload_units,dirty FROM {TABLE} WHERE singleton=1').fetchone()
        if row is not None and not row[2]:
            return row[:2]
        # A single SELECT above is a consistent snapshot. A dirty or missing
        # singleton needs reconstruction protected from intervening writers.
        if self.db.in_transaction:
            # Preserve caller-owned transactions and their rollback behavior.
            self.db.execute(f'UPDATE {TABLE} SET dirty=1 WHERE singleton=1')
            result = self._reconstruct()
        else:
            with self.db:
                self.db.execute('BEGIN IMMEDIATE')
                result = self._reconstruct()
        self.counts['accounting_reconstructions'] += 1
        return result

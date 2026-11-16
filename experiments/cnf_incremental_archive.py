"""Exact residual insertion deltas for an exclusively owned append-only session.

Reuse the existing transactional size ledger. TEMP guards reject local rewrites
and nonmonotone rowids; committed external/schema changes invalidate the cursor.
This is an owned-connection contract, not protection against hostile private
schema manipulation. Full parent-preservation and certificate audits remain.
"""
from collections import Counter
from experiments.cnf_accounted_residuals import AccountedResidualSolver


class ResidualAppendCursor:
    def __init__(self,solver):
        if not isinstance(solver,AccountedResidualSolver):raise TypeError('Transactional accounting is required')
        self.solver=solver;self.db=solver.db;self.stats=Counter();self.invalid=False
        if self.db.in_transaction:raise ValueError('Commit before opening an append cursor')
        self.db.execute('PRAGMA recursive_triggers=ON')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            self.db.execute('CREATE TEMP TABLE residual_append_cursor_v1(high INTEGER NOT NULL)')
            self.db.execute('INSERT INTO residual_append_cursor_v1 SELECT coalesce(max(rowid),0) FROM cnf_residual_v1')
            for operation in ('UPDATE','DELETE'):
                self.db.execute(f'''CREATE TEMP TRIGGER residual_append_no_{operation.lower()}_v1
                    BEFORE {operation} ON main.cnf_residual_v1 BEGIN
                    SELECT RAISE(ABORT,'Residual append session forbids rewrites'); END''')
            self.db.execute('''CREATE TEMP TRIGGER residual_append_insert_v1 AFTER INSERT ON main.cnf_residual_v1 BEGIN
                SELECT CASE WHEN NEW.rowid <= (SELECT high FROM residual_append_cursor_v1)
                    THEN RAISE(ABORT,'Nonmonotone residual rowid') END;
                UPDATE residual_append_cursor_v1 SET high=NEW.rowid; END''')
            self.snapshot=(*solver.archive_storage(),self.db.execute('SELECT high FROM residual_append_cursor_v1').fetchone()[0])
            self.versions=self._versions()

    def _versions(self):
        return tuple(self.db.execute('PRAGMA '+p).fetchone()[0] for p in ('data_version','schema_version','temp.schema_version'))

    def take(self):
        """Return each committed insertion exactly once; never advance on rollback."""
        if self.invalid:raise RuntimeError('Invalidated append cursor; use full comparison')
        if self.db.in_transaction:raise ValueError('Commit before consuming a delta')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self._versions()!=self.versions:
                self.invalid=True;raise RuntimeError('Changed external writer or schema; use full comparison')
            nodes,units=self.solver.archive_storage()
            high=self.db.execute('SELECT high FROM residual_append_cursor_v1').fetchone()[0]
            added=self.db.execute('''SELECT id,payload,coalesce(length(id)+length(payload),0),rowid
                FROM cnf_residual_v1 WHERE rowid>? ORDER BY rowid''',(self.snapshot[2],)).fetchall()
            result={row[0]:row[1] for row in added}
            if (len(added)!=nodes-self.snapshot[0] or len(result)!=len(added)
                    or sum(row[2] for row in added)!=units-self.snapshot[1]
                    or high!=(added[-1][3] if added else self.snapshot[2])):
                self.invalid=True;raise RuntimeError('Inconsistent append delta; use full comparison')
        self.snapshot=(nodes,units,high);self.stats['delta_reads']+=1;self.stats['delta_rows']+=len(added)
        self.stats['delta_payload_units']+=sum(row[2] for row in added)
        return result

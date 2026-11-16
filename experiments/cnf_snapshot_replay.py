"""One size census for an owned, read-only SQLite snapshot; all proofs replay.

The existing verifier and query reconstruction remain unchanged. The read
transaction pins the same database view for the census, proof loads and queries.
The authorizer forbids ending that transaction or changing the connection's
schema. As with the other experimental sessions, hostile manipulation of private
connection state (including replacing the authorizer) is outside the contract.
"""
from pathlib import Path
import sqlite3
from unittest.mock import patch
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_accounted_residuals import CENSUS
from experiments import compare_cnf_clause_witness_reuse as frozen
FROZEN_AUDIT=frozen.audit


class SnapshotResidualSolver(ResidualSolver):
    def __init__(self,archive):
        # Reuse the frozen initialization without issuing DDL against the source.
        super().__init__(':memory:');self.db.close()
        self.db=sqlite3.connect(Path(archive).resolve(strict=True).as_uri()+'?mode=ro',uri=True)
        try:
            self.db.execute('PRAGMA query_only=ON');self.db.execute('BEGIN')
            self.snapshot_totals=self.db.execute(CENSUS).fetchone()
            self.snapshot_censuses=1;self.snapshot_reads=0
            self.db.set_authorizer(self._authorize)
        except BaseException:self.db.close();raise

    @staticmethod
    def _authorize(action,first,second,database,trigger):
        if action in (sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_FUNCTION):return sqlite3.SQLITE_OK
        if action==sqlite3.SQLITE_PRAGMA and first=='query_only' and second in ('ON','1'):return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    def _snapshot(self):
        if not self.db.in_transaction:raise RuntimeError('Closed snapshot transaction')

    def _read(self,*args,**kwargs):
        self._snapshot();return super()._read(*args,**kwargs)

    def archive_storage(self):
        self._snapshot();self.snapshot_reads+=1;return self.snapshot_totals

    def _expand(self,cnf):raise RuntimeError('Fresh snapshot search is forbidden')

    def _store(self,*args,**kwargs):raise RuntimeError('Snapshot publication is forbidden')


def audit(path,records):
    """Run the frozen complete audit, substituting only the snapshot solver.

    The experiment owns this process during the scoped substitution; this is
    not an API for simultaneous audits from several threads in one interpreter.
    """
    instances=[]
    def factory(archive):
        solver=SnapshotResidualSolver(archive);instances.append(solver);return solver
    with patch.object(frozen,'ResidualSolver',factory):result=FROZEN_AUDIT(path,records)
    assert len(instances)==1
    solver=instances[0]
    result['snapshot']=dict(censuses=solver.snapshot_censuses,metadata_reads=solver.snapshot_reads,
        nodes=solver.snapshot_totals[0],payload_units=solver.snapshot_totals[1],complete_frozen_audit=True)
    return result

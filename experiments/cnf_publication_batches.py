"""Bounded publication batches for an exclusively owned experimental solver.

Proofs are still checked before their original INSERTs. A batch commits a prefix
of that dependency-ordered stream. Successful queries flush before returning;
failed queries retain committed prefixes and discard only the pending suffix.
The record/payload limits are not bounds on SQLite journals or total solver RAM.
"""
import re,sys,time
from experiments.cnf_canonical_verify import CanonicalVerifySolver
from experiments.cnf_accounted_residuals import TABLE as ACCOUNTING

NATIVE='cnf_residual_v1'
V1='cnf_binary_equivalence_v1'
V2='cnf_binary_equivalence_v2'
V3='cnf_binary_equivalence_v3'
INSERT=re.compile(r'INSERT OR IGNORE INTO (cnf_residual_v1|cnf_binary_equivalence_v[123]) (?:\(id,payload\) )?VALUES \(\?,\?\)',re.I)


class PublicationConnection:
    def __init__(self,solver,connection,rows,payload_bytes):
        self.solver=solver;self.connection=connection;self.rows=rows;self.payload_limit=payload_bytes
        self.active=False;self.depth=0;self.failed=False;self.poisoned=False;self.pending=[];self.payload=0;self.object_charge=0

    def __getattr__(self,name):
        if self.active and name in ('cursor','executemany','executescript'):
            raise RuntimeError('Untracked publication interface')
        return getattr(self.connection,name)

    def start(self):
        if self.poisoned or self.active or self.connection.in_transaction:raise RuntimeError('Publication requires an owned healthy idle connection')
        self.active=True;self.failed=False

    def _event(self,event,table=None,key=None):
        hook=self.solver.publication_hook
        if hook is not None:hook(event,table,key)

    def _commit(self):self.connection.commit()
    def _rollback(self):self.connection.rollback()

    def flush(self):
        if not self.connection.in_transaction:
            if self.pending:raise RuntimeError('Pending publication lost its transaction')
            return
        c=self.solver.counts
        try:self._commit()
        except BaseException:
            self.abort();raise
        c['batch_commits']+=1;c['batch_committed_records']+=len(self.pending);c['batch_committed_payload']+=self.payload
        if not self.pending:c['batch_metadata_commits']+=1
        self.pending=[];self.payload=0;self.object_charge=0
        self._event('after_commit')

    def abort(self):
        c=self.solver.counts;self.failed=True
        try:
            if self.connection.in_transaction:
                self._rollback();c['batch_rollbacks']+=1
        except BaseException:
            # An uncertain rollback must never make checked-memory state usable
            # again on this connection, even if SQLite has ended the transaction.
            self.poisoned=True;raise
        finally:
            s=self.solver;store=s.equivalences
            for table,key in self.pending:
                caches=([s.checked] if table==NATIVE else
                    [store.checked] if table==V3 else
                    [store.checked,store.old.checked] if table==V2 else
                    [store.checked,store.old.checked,store.old.legacy.checked])
                for cache in caches:
                    if key in cache:del cache[key];c['batch_invalidated_checks']+=1
            c['batch_discarded_checks_records']+=len(self.pending)
            self.pending=[];self.payload=0;self.object_charge=0

    def finish(self):
        if self.failed or self.depth:raise RuntimeError('Cannot finish a failed or nested publication')
        self.flush()

    def __enter__(self):
        if not self.active:return self.connection.__enter__()
        if self.failed or self.depth:raise RuntimeError('Nested or failed publication context')
        self.depth=1;self.solver.counts['batch_contexts']+=1
        return self

    def __exit__(self,kind,value,traceback):
        if not self.active:return self.connection.__exit__(kind,value,traceback)
        self.depth=0
        if kind is not None:self.abort();return False
        if len(self.pending)>=self.rows or self.payload>=self.payload_limit:self.flush()
        return False

    def execute(self,sql,parameters=()):
        if not self.active:return self.connection.execute(sql,parameters)
        if self.failed:raise RuntimeError('Publication already failed')
        statement=' '.join(sql.strip().split());match=INSERT.fullmatch(statement)
        if match:
            if self.depth!=1 or len(parameters)!=2 or any(type(v) is not str for v in parameters):
                raise ValueError('Publication requires one key/payload INSERT context')
            table=match[1].lower();key,payload=parameters;size=len(key.encode())+len(payload.encode())
            c=self.solver.counts;c['batch_insert_attempts']+=1;c['batch_sized_payload']+=size
            if self.pending and (len(self.pending)>=self.rows or self.payload+size>self.payload_limit):self.flush()
            cursor=self.connection.execute(sql,parameters)
            if cursor.rowcount:
                entry=(table,key);self.pending.append(entry);self.payload+=size
                self.object_charge+=sys.getsizeof(entry)+sys.getsizeof(table)+sys.getsizeof(key)
                c['batch_peak_records']=max(c['batch_peak_records'],len(self.pending))
                c['batch_peak_payload']=max(c['batch_peak_payload'],self.payload)
                c['batch_peak_python_bytes']=max(c['batch_peak_python_bytes'],sys.getsizeof(self.pending)+self.object_charge)
                if size>self.payload_limit:c['batch_oversized_records']+=1
                self._event('after_insert',table,key)
            else:c['batch_ignored_inserts']+=1
            return cursor
        # Existing transactional accounting can repair its singleton after an
        # ignored INSERT dirties it. These writes share the same rollback boundary.
        if (statement.upper().startswith('SELECT ') or statement.upper()=='BEGIN IMMEDIATE'
                or statement.startswith('UPDATE '+ACCOUNTING+' ')
                or statement.startswith('INSERT INTO '+ACCOUNTING+' ')):
            return self.connection.execute(sql,parameters)
        raise ValueError('Unsupported SQL inside a publication query')

    def commit(self):
        if self.active:raise RuntimeError('Direct commit would bypass the batch boundary')
        return self.connection.commit()

    def rollback(self):
        if self.active:raise RuntimeError('Direct rollback would bypass cache invalidation')
        return self.connection.rollback()

    def close(self):
        if self.active:raise RuntimeError('Cannot close an active publication query')
        return self.connection.close()


class BatchedPublicationSolver(CanonicalVerifySolver):
    def __init__(self,*args,batch_rows=32,batch_payload_bytes=256*1024,**kwargs):
        if any(type(v) is not int or v<1 for v in (batch_rows,batch_payload_bytes)):
            raise ValueError('Publication limits must be positive integers')
        super().__init__(*args,**kwargs)
        self.publication_hook=None
        self.db=PublicationConnection(self,self.db,batch_rows,batch_payload_bytes)

    def solve(self,source):
        began=time.perf_counter();self.db.start()
        try:
            result=super().solve(source);self.db.finish()
        except BaseException:
            self.db.abort();raise
        finally:self.db.active=False
        self.counts['batch_queries']+=1
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        result['publication_limits']=dict(rows=self.db.rows,payload_bytes=self.db.payload_limit)
        return result

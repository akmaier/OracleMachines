"""Retain an exclusively owned checked inventory across bounded expansion batches.

Only live in-process reuse is supported. The database rows and cached objects
remain caller-owned and immutable except for checked acquisition and maintained
route updates. A process restart must reconstruct and check its authority again.
"""
from experiments.cnf_pattern_activation import PatternActivationMaintenance
from experiments.cnf_expanded_coverage import verifier_views
from experiments.cnf_pattern_inventory import encode


class ExpansionSession:
    def __init__(self, h, evidence, bridges):
        if h.db.in_transaction or any(view.active for _, view in verifier_views(h)):
            raise ValueError('Finish acquisition before opening a session')
        self.h = h
        self.maintenance = PatternActivationMaintenance(h, evidence, bridges)
        self.config = self._config()
        self.batches = 0

    def _config(self):
        return encode([(name, view.config) for name, view in verifier_views(self.h)])

    def begin(self, limit, evidence, bridges):
        """Reset only the admission ledger after checking the retained boundary."""
        h, m, db = self.h, self.maintenance, self.h.db
        if db.in_transaction or any(view.active for _, view in verifier_views(h)):
            raise ValueError('Finish acquisition before beginning another batch')
        db.execute('BEGIN IMMEDIATE')
        try:
            if (db.execute('PRAGMA data_version').fetchone()[0] != m.version or
                    db.execute('PRAGMA schema_version').fetchone()[0] != m.schema):
                raise ValueError('Changed external writer or schema; reopen checked state')
            if (db.total_changes != m.changes or h.admitted != m.admitted or
                    encode([evidence, bridges]) != m.sidecars or self._config() != self.config):
                raise ValueError('Unmaintained session state; cannot reuse checked boundary')
            h.set_admission_budget(limit)
            m._snapshot()
            self.batches += 1
        finally:
            db.rollback()
        return m

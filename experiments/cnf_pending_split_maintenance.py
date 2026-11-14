"""Retain checked routes when an interrupted split cannot activate an edge.

The complete builder must attach trace splits only when both target roots are
present (cnf_trace_split.attach). A checked split sidecar is still retained for
scheduling. Any database write, other sidecar change or later target acquisition
takes the ordinary rebuilding path. This shares the single-writer, append-only
inventory contract of ClearProbeMaintenance; it is not a persistent trust cache.
"""
from collections import Counter
import json

from experiments.cnf_clear_probe_maintenance import ClearProbeMaintenance
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_trace_split import verify
from experiments.continue_cnf_original_splits import add_splits


class PendingSplitMaintenance(ClearProbeMaintenance):
    def refresh(self, operation, evidence, bridges):
        h, db = self.h, self.h.db
        if (db.execute('PRAGMA data_version').fetchone()[0] != self.version or
                db.execute('PRAGMA schema_version').fetchone()[0] != self.schema):
            raise ValueError('Inventory changed externally or structurally; reopen checked state')
        record = operation.get('record')
        added = operation.get('added')
        eligible = (operation.get('mode') in ('early_saved_split', 'early_closed_split',
                    'split_after_ordinary_exhaustion', 'resume_split') and
                    operation.get('pending') is True and isinstance(record, dict) and
                    operation.get('source') == record.get('source') and
                    db.total_changes == self.changes and self.admitted <= h.admitted and
                    isinstance(added, list) and all(isinstance(key, str) for key in added) and
                    len(added) == len(set(added)) and set(added) == h.admitted-self.admitted)
        if eligible:
            counts = Counter()
            verify(h, record, counts)
            old_evidence, old_bridges = json.loads(self.sidecars)
            expected = encode([add_splits(old_evidence, [record]), old_bridges])
            supplied = encode([evidence, bridges])
            missing = [edge['key'] for edge in record['edges'] if h._load(edge['key']) is None]
            if supplied == expected and missing:
                # No write can activate an earlier pending route. The only new
                # sidecar cannot activate its own route while a child is absent.
                reused = supplied == self.sidecars
                self.sidecars = supplied
                self._snapshot()
                return dict(mode='pending_split_reuse' if reused else 'pending_split_append',
                            counts=dict(counts), missing_targets=len(missing),
                            entered_unstored=len(added), sidecar_snapshot_bytes=len(supplied.encode()))
        return super().refresh(operation, evidence, bridges)

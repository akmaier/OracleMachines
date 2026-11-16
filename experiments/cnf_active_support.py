"""Check active support proofs on demand, retaining a complete cold lineage audit.

Saved proposals are search hints. They cannot publish UNSAT without an ordinary
checked negative core. This module does not certify all historical provenance
until audit_with_lineage succeeds on the same pinned, read-only proof snapshot.
The live solver is an exclusively owned append-only session, as in its baseline.
"""
from collections import Counter
from copy import deepcopy
from unittest.mock import patch
import time
from experiments.cnf_deferred_support import discover
from experiments.cnf_unsat_support import SupportExtractor,checked_subset
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_incremental_support import merge,check_proposals
from experiments.cnf_snapshot_replay import SnapshotResidualSolver,FROZEN_AUDIT,frozen


def extend_active(solver,prior,old_catalogs,new_catalogs):
    old_ids={(name,r['case']) for name,rs in old_catalogs for r in rs}
    new_ids=[(name,r['case']) for name,rs in new_catalogs for r in rs]
    if old_ids.intersection(new_ids) or len(new_ids)!=len(set(new_ids)):
        raise ValueError('Repeated source identity; provide only a new batch')
    result=merge(prior,discover(solver,new_catalogs))
    result['lineage_check']='Required in complete cold audit; proposals are not proofs'
    return result


class ActiveCoreBank:
    def __init__(self,solver,cores):
        self.solver=solver;self.counts=Counter();self.extractor=SupportExtractor(solver)
        self.cores=[(c,clause_set(c['source'],self.counts)) for c in deepcopy(cores)]

    def reuse(self,source):
        clauses=clause_set(source,self.counts)
        for index,(core,wanted) in enumerate(self.cores):
            self.counts['core_candidates']+=1;self.counts['core_containment_clauses']+=len(wanted)
            if not wanted<=clauses:continue
            cnf,_,key=self.solver._canonical(core['source'])
            if key!=core['root']:raise ValueError('Unbound active support')
            node=self.solver._read(key,cnf,purpose='active_core');self.counts['active_core_checks']+=1
            if node is None:
                self.counts['materialization_attempts']+=1;before=self.solver.counts['inserted_nodes']
                derived=self.extractor.extract(core['origin'])
                self.counts['materialization_nodes']+=self.solver.counts['inserted_nodes']-before
                if derived['root']!=key:raise ValueError('Proposal differs from checked extracted support')
                node=self.solver._read(key,cnf,purpose='materialized_core')
            else:self.counts['existing_core_proofs']+=1
            if node is None or node['answer'] is not False:raise ValueError('Checked negative support required')
            inserted,root=checked_subset(self.solver,source,core['source'],self.counts)
            return dict(core=index,inserted=inserted,root=root)
        return None


class _HeldSnapshot(SnapshotResidualSolver):
    # FROZEN_AUDIT closes in finally. Hold its owned snapshot until lineage has
    # also been checked, then unconditionally close the actual connection.
    def close(self):self.close_requested=True


def audit_with_lineage(path,records,prepared,catalogs):
    start=time.perf_counter();instances=[]
    def factory(archive):
        solver=_HeldSnapshot(archive);solver.close_requested=False;instances.append(solver);return solver
    try:
        with patch.object(frozen,'ResidualSolver',factory):result=FROZEN_AUDIT(path,records)
        if len(instances)!=1 or not instances[0].close_requested:raise RuntimeError('Unexpected frozen audit lifecycle')
        solver=instances[0];tick=time.perf_counter();lineage=check_proposals(solver,prepared,catalogs)
        result['lineage_seconds']=time.perf_counter()-tick;result['lineage']=lineage
        result['proof_query_seconds']=result['seconds'];result['seconds']=time.perf_counter()-start
        result['snapshot']=dict(censuses=solver.snapshot_censuses,metadata_reads=solver.snapshot_reads,
            nodes=solver.snapshot_totals[0],payload_units=solver.snapshot_totals[1],complete_frozen_audit=True)
        return result
    finally:
        for solver in instances:SnapshotResidualSolver.close(solver)

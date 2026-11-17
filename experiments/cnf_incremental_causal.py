"""Acquire causal hints from new origins, retaining old history and full audits.

Only new source records enter causal extraction; their proof dependencies may
include old nodes. No proof is published during discovery. Proposals still need
checked materialization, and complete old/new lineage audit remains mandatory.
"""
from unittest.mock import patch
from experiments.cnf_causal_support import discover_causal
from experiments.cnf_incremental_support import merge,check_proposals
from experiments.cnf_proof_choice import compose,ORDER
from experiments import cnf_active_support as active


def extend_causal(solver,prior,old_catalogs,new_catalogs):
    if prior.get('causal_unit_slicing') is not True or prior.get('deferred') is not True:
        raise ValueError('Causal deferred history required')
    old_ids=[(name,r['case']) for name,rs in old_catalogs for r in rs]
    new_ids=[(name,r['case']) for name,rs in new_catalogs for r in rs]
    if len(set(old_ids+new_ids))!=len(old_ids)+len(new_ids):
        raise ValueError('Repeated source identity; acquire only new records')
    expected=[(name,r['case']) for name,rs in old_catalogs for r in rs if r['answer'] is False and r['guard'] is not None]
    if [(o['catalog'],o['case']) for o in prior['origins']]!=expected:
        raise ValueError('Old catalog does not bind the prior origins')
    delta=discover_causal(solver,new_catalogs);result=merge(prior,delta)
    result.update(causal_unit_slicing=True,prior_origin_count=len(prior['origins']),delta_origin_count=len(delta['origins']),
        lineage_check='Complete old and new provenance audit required; source-bound hints are not negative certificates.',
        limitation='Only new origins extracted; old dependencies may be traversed. Containment frontier is not minimum-cost proof selection. No fresh solving or publication in discovery.')
    return result


def audit_extended_portfolio(path,records,prepared,catalogs_by_bank,indices):
    """Check both acquired histories on the same unchanged frozen snapshot."""
    if set(catalogs_by_bank)!=set(ORDER) or prepared!=compose(indices,prepared['banks']):
        raise ValueError('Unbound portfolio or lineage map')
    def check_both(solver,ignored,unused):
        return {name:check_proposals(solver,indices[name],catalogs_by_bank[name]) for name in ORDER}
    with patch.object(active,'check_proposals',check_both):
        return active.audit_with_lineage(path,records,prepared,[])

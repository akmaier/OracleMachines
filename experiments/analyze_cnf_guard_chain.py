#!/usr/bin/env python3
"""Attribute controlled guard-chain savings and regressions without timing claims."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_chain as study
from experiments.validate_cnf_unsat_support import bound
base=study.base


def analyze(out):
    report=base.load(out/'report.json');rows=[bound(e) for e in report['samples']];pairs=[]
    for cid in bound(report['protocol'])['cases']:
        arms={r['mode']:r for r in rows if r['case']==cid};a=arms['baseline'];b=arms['chain']
        assert a['answer']==b['answer']
        pairs.append(dict(case=cid,answer=a['answer'],choice=b['choice'],
            expansions={m:r['child_metrics'].get('expanded_nodes',0) for m,r in arms.items()},
            new_rows={m:r['new_nodes'] for m,r in arms.items()},
            new_payload_units={m:r['new_payload_units'] for m,r in arms.items()},
            serialized_delta_and_chain_bytes={m:r['delta_bytes']+r['chain_bytes'] for m,r in arms.items()},
            premise_inserted=b['premise_inserted'],
            query_phase_seconds={m:sum(r[k] for k in ('selection_seconds','premise_seconds','child_seconds','composition_seconds')) for m,r in arms.items()},
            preparation_seconds={m:r['preparation_seconds'] for m,r in arms.items()},cold_seconds={m:r['cold']['seconds'] for m,r in arms.items()},
            warm_bank_setup_seconds={m:r['warm_setup_seconds'] for m,r in arms.items()},warm_lookup_seconds={m:r['warm_lookup_seconds'] for m,r in arms.items()}))
    totals={m:dict(expansions=sum(p['expansions'][m] for p in pairs),new_rows=sum(p['new_rows'][m] for p in pairs),
        new_payload_units=sum(p['new_payload_units'][m] for p in pairs),serialized_delta_and_chain_bytes=sum(p['serialized_delta_and_chain_bytes'][m] for p in pairs)) for m in ('baseline','chain')}
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),cases=pairs,totals=totals,
        relative_change_percent={k:100*(totals['chain'][k]/totals['baseline'][k]-1) for k in totals['baseline']},
        expansion_regressions=[p['case'] for p in pairs if p['expansions']['chain']>p['expansions']['baseline']],
        publication_regressions=[p['case'] for p in pairs if p['new_rows']['chain']>p['new_rows']['baseline']],
        selected_cases=[p['case'] for p in pairs if p['choice'] is not None],
        limitations=['Historical post-hoc cases, exact persistent prefixes, cold live caches, one sample per arm. Operation counts are matched; timing samples are not evidence of a stable total runtime improvement.',
            'Query-phase time includes near-core selection, premise publication, child solving and chain composition; it excludes separately reported preparation, cold replay, serialization, warm-bank construction, and prefix reconstruction. Full-row snapshots/export and report overhead remain in aggregate study time, not this query-phase sum.',
            'Added native payload is identifier plus ASCII JSON length, not SQLite page bytes or peak RAM. Serialized deltas plus chain sidecars measure these retained trial files; older history and index storage remain additional costs.',
            'Warm conclusion reuse requires GuardChainBank loading and checking the bound sidecars. Native root-table lookup alone does not assert a composed conclusion. All native nodes retain the frozen certificate format.',
            'First matching ready core is a heuristic; a valid restriction may increase solving, publication or verification cost. No fresh structural coverage, optimal expansion or unrestricted-SAT guarantee.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode(dict(totals=totals,relative_change_percent=result['relative_change_percent'],expansion_regressions=result['expansion_regressions'],publication_regressions=result['publication_regressions'])))


if __name__=='__main__':analyze(Path(sys.argv[1]))

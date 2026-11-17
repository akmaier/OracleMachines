#!/usr/bin/env python3
"""Compare derivation footprints and classify the checked origin proof shapes."""
from pathlib import Path
from unittest.mock import patch
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_alternative_guard as study
from experiments.validate_cnf_unsat_support import bound
base=study.base


def analyze(out):
    report=base.load(out/'report.json');protocol=bound(report['protocol']);old=bound(protocol['historical_protocol'])
    original=bound(old['parent']);indices={n:bound(old[f]) for n,f in [('legacy','support_index'),('causal','causal_index')]}
    rows=[bound(x) for x in report['samples']];baselines={r['case']:r for r in rows if r['match'] is None};comparison=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'source';base.restore_archive(original['reference_union'],path);s=study.ResidualSolver(path)
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Fresh shape analysis')),patch.object(s,'_store',side_effect=AssertionError('Shape publication')):
                for r in rows:
                    if r['match'] is None:continue
                    match=r['match'];b=baselines[r['case']];core=indices[match['bank']]['cores'][match['index']]
                    node=s._read(core['origin']);assert node is not None and node['answer'] is False
                    proof=node['proof'];terminal_unit=proof['kind']=='units' and proof.get('conflict') is not None
                    if terminal_unit:
                        assert r['extractor_counts']['support_nodes']==1
                        assert r['materialization_counts']['inserted_nodes']<=1 and r['new_nodes']<=2
                    comparison.append(dict(case=r['case'],match=match,origin_kind=proof['kind'],terminal_unit_conflict=terminal_unit,
                        baseline_expansions=b['child_metrics']['expanded_nodes'],alternative_expansions=r['child_metrics'].get('expanded_nodes',0),
                        baseline_rows=b['new_nodes'],alternative_rows=r['new_nodes'],support_nodes=r['extractor_counts']['support_nodes'],
                        baseline_payload_units=b['new_payload_units'],alternative_payload_units=r['new_payload_units'],
                        payload_change_percent=100*(r['new_payload_units']/b['new_payload_units']-1),
                        baseline_child_seconds=b['child_seconds'],alternative_derivation_publication_child_seconds=sum(r[k] for k in ('materialization_seconds','publication_seconds','child_seconds')),
                        preparation_seconds={'baseline':b['preparation_seconds'],'alternative':r['preparation_seconds']},
                        cold_seconds={'baseline':b['cold']['seconds'],'alternative':r['cold']['seconds']},
                        repeat_seconds={'baseline':b['repeat_seconds'],'alternative':r['repeat_seconds']}))
        finally:s.close();assert base.sha(path)==original['reference_union']['database_sha256']
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),comparisons=comparison,
        terminal_unit_cases=[r['case'] for r in comparison if r['terminal_unit_conflict']],
        publication_bound='For a checked negative origin with kind units and a non-null conflict, the existing causal extractor makes no recursive extract call and publishes at most one core row. The ordinary subset step publishes at most one more row. This bounds publications for one selected core, not bytes, checking time, recognition, or optimal SAT expansion.',
        next_step='Evaluate an optional terminal-origin filter on fresh excluded queries. Recheck the actual negative origin and the derived root; do not treat an arbitrary units proof with a child as terminal. Price recognition and repeated guard selection as well as derivation.',
        limitations=['The six matches were selected after observing the old stream. Prefix replay is exact for persistent payloads, not old warm memo state. These are controlled historical costs, not new coverage.',
            'Operation counts for derivation and fresh expansion are distinct units. Row and ASCII payload differences are exact; single wall-clock samples do not establish a runtime improvement.',
            'New payload units are id plus JSON payload lengths, not SQLite pages or peak process memory. Full historical archives remain stored; independent delta reconstruction avoids duplicating each complete database.',
            'Repeat probes of alternative targets deliberately scan a newly constructed portfolio; baseline repeats read the cached target directly. They are separate interfaces, not a fair warm-speed comparison.',
            'All alternatives return checked UNSAT with zero fresh SAT search, but avoiding search alone does not minimize total work. No arbitrary-SAT polynomial or minimum-expansion theorem.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode(dict(terminal_unit_cases=result['terminal_unit_cases'],comparisons=comparison)))


if __name__=='__main__':analyze(Path(sys.argv[1]))

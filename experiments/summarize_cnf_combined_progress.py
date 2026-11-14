#!/usr/bin/env python3
"""Bind cost prefixes to cold-checked cofactor completion and repeated operations."""
import json
from pathlib import Path
import statistics
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_combined_expansion import read_archive, sha
from experiments.validate_cnf_split_cost import load_report


def summarize(out):
    r=json.loads((out/'report.json').read_text())
    replay=json.loads((out/'reconstruction.json').read_text())
    findings=json.loads((out/'structural-findings.json').read_text())
    assert replay['passed'] and replay['report_sha256']==sha(out/'report.json')
    result=dict(report_sha256=sha(out/'report.json'),reconstruction_sha256=sha(out/'reconstruction.json'),
        findings_sha256=sha(out/'structural-findings.json'),arms=[],
        scope='Cost of completing the same true cofactor, not the whole original. Prefix replay uses only then-available rows. Initial preparation and final export are excluded from expansion-prefix costs.')
    initial=[]
    costs=('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')
    for mode in ('ordinary','early_saved'):
        arms=[load_report(a) for a in r['arms'] if a['mode']==mode]
        assert len(arms)==2
        operations=[[read_archive(row['operation']) for row in arm['steps']] for arm in arms]
        assert operations[0]==operations[1]
        initial.append(operations[0][0])
        detail=next(a for a in findings['arms'] if a['mode']==mode and a['repeat']==0)
        progress=detail['prefix_progress'];completed=progress['first_common_child_completion'][1]
        assert completed is not None and progress['first_common_child_completion'][0] is None
        end=completed['step'];assert completed['common_children_closed']==[False,True]
        assert completed['admitted']==arms[0]['steps'][end]['admitted_total']
        shared=arms[0]['steps'][0]['admitted_total'];assert shared==10
        result['arms'].append(dict(mode=mode,completion_step=end,advances_including_initial=end+1,
            total_admitted_at_completion=completed['admitted'],
            new_states_after_common_split=completed['admitted']-shared,
            stored_at_completion=completed['stored_new_patterns'],
            expansion_through_completion_mean_seconds=statistics.mean(sum(sum(row[k] for k in costs) for row in arm['steps'][:end+1]) for arm in arms),
            expansion_after_common_split_mean_seconds=statistics.mean(sum(sum(row[k] for k in costs) for row in arm['steps'][1:end+1]) for arm in arms),
            repeated_operations_identical=True))
    assert initial[0]==initial[1]
    result['passed']=True
    (out/'progress-summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':summarize(Path(sys.argv[1]))

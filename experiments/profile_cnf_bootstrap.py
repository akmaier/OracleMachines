#!/usr/bin/env python3
"""Instrumented diagnostic; never mix its timings with the matched samples."""
from collections import Counter
import cProfile
from pathlib import Path
import pstats
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiments.compare_cnf_bootstrap as study


def run(out,parent):
    out.mkdir(exist_ok=False);protocol=study.load(parent/'protocol.json');seed=study.load(parent/'seed.json')
    expected=study.load(parent/'enumerate-0/report.json');stage='query';calls={'query':Counter(),'cold':Counter()}
    original_verify=study.split.verify;original_replay=study.replay
    def counted(h,record,counts):
        calls[stage][study.key_sha(study.split.record_key(record))]+=1
        return original_verify(h,record,counts)
    def cold(*args):
        nonlocal stage
        stage='cold'
        return original_replay(*args)
    profiler=cProfile.Profile()
    with patch.object(study.split,'verify',counted),patch.object(study,'replay',cold):
        profiler.enable()
        result=study.worker(out/'enumerate',protocol,seed,'enumerate')
        profiler.disable()
    assert result['pattern_digest']==expected['pattern_digest']
    for field in ('covered','final_covered','entered','stored','probes','fresh_assumptions','pairs'):
        assert result[field]==expected[field]
    profiler.dump_stats(str(out/'profile.pstats'));stats=pstats.Stats(profiler)
    functions=[]
    for (path,line,name),(primitive,total,own,cumulative,callers) in stats.stats.items():
        if path.endswith('.py') and ('/experiments/' in path or name in ('dumps','loads')):
            functions.append(dict(path=path,line=line,name=name,primitive_calls=primitive,calls=total,
                                  self_seconds=own,cumulative_seconds=cumulative))
    functions.sort(key=lambda r:-r['cumulative_seconds'])
    report=dict(parent_report_sha256=study.sha(parent/'report.json'),source_sha256=study.sha(__file__),
        diagnostic_report_sha256=study.sha(out/'enumerate/report.json'),same_graph_and_outcomes=True,
        verification_calls={phase:dict(total=sum(c.values()),distinct_records=len(c),
            repeated_calls=sum(c.values())-len(c),maximum_per_record=max(c.values(),default=0),counts=dict(c)) for phase,c in calls.items()},
        functions=functions,wall_phase_seconds={k:result[k] for k in ('setup_seconds','operation_seconds')},
        limitations=['The profiler and counting wrapper add overhead; these times are not benchmark samples.',
            'Function cumulative times overlap and must not be added. The profile includes restoration, querying, cold replay and archive writing.',
            'Query/cold call counts are separated by the replay boundary. A repeated verification is not automatically safe to skip without an exact immutable-evidence cache and correct pending-child handling.'])
    study.write(out/'report.json',report)
    print(study.encode(dict(same_graph_and_outcomes=True,verification_calls={p:{k:v for k,v in r.items() if k!='counts'} for p,r in report['verification_calls'].items()},top_functions=functions[:8])))


if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))

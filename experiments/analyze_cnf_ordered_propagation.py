#!/usr/bin/env python3
"""Profile the remaining miss after trace-preserving affected-clause propagation."""
from collections import Counter
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_ordered_propagation import MODES


def main(directory):
    target=directory/'mechanisms.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    baseline=[r for r in report['records'] if r['mode']=='baseline']
    case=max((r for r in baseline if not r['discovery']['summary']['closed']),
             key=lambda r:r['discovery']['seconds'])['case']
    source=report['cases'][case]['source'];profiles=[]
    for mode,(cls,options) in MODES.items():
        with tempfile.TemporaryDirectory() as tmp:
            h=cls(Path(tmp)/'profile.db',**options);profiler=cProfile.Profile();profiler.enable()
            result=h.inspect(source);profiler.disable()
            functions=[dict(file=f,line=line,name=name,primitive_calls=pr,calls=ca,own_seconds=own,cumulative_seconds=cu)
                for (f,line,name),(pr,ca,own,cu,_) in pstats.Stats(profiler).stats.items()]
            profiles.append(dict(mode=mode,case=case,original_case=report['cases'][case]['original_case'],
                instrumented_seconds=result['seconds'],metrics=result['metrics'],
                cache=h.probe_cache_state() if hasattr(h,'probe_cache_state') else None,
                selected_functions=[f for f in functions if f['name'] in
                    ('restrict','check_simplification','propagate','propagate_ordered','propagate_for_discovery','_check_probes','encode','dumps','loads')],
                top_own_time=sorted(functions,key=lambda f:-f['own_seconds'])[:40]))
            h.close()
    states={};counts={};unchanged={}
    for mode in MODES:
        rows=[r for r in report['records'] if r['mode']==mode]
        counts[mode]=dict(sum((Counter(r['operation_metrics']) for r in rows),Counter()))
        cache=[r['cache'] for r in rows if r['cache'] is not None]
        states[mode]=dict(max_entries=max((s['entries'] for s in cache),default=0),
            max_bytes=max((s['peak_bytes'] for s in cache),default=0))
        other={r['case']:r for r in baseline}
        unchanged[mode]=all(r['discovery']['root_hash']==other[r['case']]['discovery']['root_hash'] and
            r['discovery']['summary']==other[r['case']]['discovery']['summary'] and
            r['discovery']['dag']==other[r['case']]['discovery']['dag'] for r in rows)
    output=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        operation_metrics=counts,cache_states=states,unchanged_structure=unchanged,profiles=profiles,
        limitations=['Profiles are separate instrumented cold acquisitions, not comparable to uninstrumented operation seconds',
          'All propagation preparation/events, proof checking, cache construction and decoding costs remain charged',
          'Cache cap covers retained serialized strings only; allocator, transient inputs and original graph memory are separate',
          'No structural coverage change, new tractable family or unrestricted complexity improvement'])
    target.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(case=case,states=states,unchanged_structure=unchanged)),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))

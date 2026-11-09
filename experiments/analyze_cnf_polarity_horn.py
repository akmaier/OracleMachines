#!/usr/bin/env python3
"""Preserve root gains, recognition exclusions and the next measured cost gap."""
from collections import Counter
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_polarity_horn import PolarityHornInventory, discover_polarity, check_polarity
from experiments.cnf_residual_dag import normalize
from experiments.compare_cnf_polarity_horn import OPTIONS


def main(directory):
    target = directory/'mechanisms.json'
    if target.exists():raise FileExistsError(target)
    source_path = directory/'report.json'; report = json.loads(source_path.read_text())
    rows = [r for r in report['records'] if r['mode'] == 'polarity']
    baseline = {r['case']:r for r in report['records'] if r['mode'] == 'baseline'}
    gains = [r for r in rows if r['discovery']['summary']['closed'] and not baseline[r['case']]['discovery']['summary']['closed']]
    misses = [r for r in rows if not r['discovery']['summary']['closed']]
    worst = max(misses,key=lambda r:r['discovery']['seconds']); case = worst['case']
    with tempfile.TemporaryDirectory() as tmp:
        h = PolarityHornInventory(Path(tmp)/'profile.db', **OPTIONS)
        profiler = cProfile.Profile(); profiler.enable(); result = h.inspect(report['cases'][case]['source']); profiler.disable()
        functions = [dict(file=f,line=line,name=name,primitive_calls=pr,calls=ca,own_seconds=own,cumulative_seconds=cu)
                     for (f,line,name),(pr,ca,own,cu,_) in pstats.Stats(profiler).stats.items()]
        profile = dict(case=case,instrumented_seconds=result['seconds'],metrics=result['metrics'],
                       top_own_time=sorted(functions,key=lambda f:-f['own_seconds'])[:40],
                       selected_functions=[f for f in functions if f['name'] in
                           ('discover_polarity','check_polarity','two_cnf','normalize','reconstruct_single_pass',
                            'propagate_ordered','check_simplification','_check_probes','_discover_profile','encode','dumps','loads')])
        h.close()
    frontier = report['frontiers']['polarity']
    # Diagnostic only: recognition on original inputs, before the costly planner.
    # This does not change routing or claim saved acquisition time.
    root_probe = []; probe_counts = Counter(); started = time.perf_counter()
    for i, item in enumerate(report['cases']):
        cnf, _ = normalize(item['source'], probe_counts)
        certificate = discover_polarity(cnf, probe_counts)
        check_polarity(cnf, certificate, probe_counts)
        root_probe.append(dict(case=i, outcome=certificate['outcome'], certificate=certificate))
    probe_seconds = time.perf_counter()-started
    groups = {}
    for group in sorted({c['group'] for c in report['cases']}):
        group_rows = [r for r in rows if report['cases'][r['case']]['group']==group]
        groups[group] = dict(inputs=len(group_rows),closed=sum(r['discovery']['summary']['closed'] for r in group_rows),
            gains=sum(r in gains for r in group_rows),total_seconds=sum(r['total_seconds'] for r in group_rows))
    output = dict(report_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),profile=profile,groups=groups,
        gain_cases=[r['case'] for r in gains],gain_answers=dict(Counter('sat' if r['answer'] else 'unsat' for r in gains)),
        original_root_probe=dict(seconds=probe_seconds,counts=dict(probe_counts),rows=root_probe,
            outcomes=dict(Counter(r['outcome'] for r in root_probe)),
            recognized_remaining_misses=[r['case'] for r in root_probe
                if r['outcome']=='recognized' and not rows[r['case']]['discovery']['summary']['closed']]),
        frontier_outcomes=dict(Counter(n['polarity']['outcome'] for n in frontier)),
        frontier_widths=dict(Counter(max(map(len,n['cnf']),default=0) for n in frontier)),
        frontier_variables=dict(Counter(n['profile']['shape']['variables'] for n in frontier)),
        miss_discovery_seconds=sum(r['discovery']['seconds'] for r in misses),
        gain_discovery_seconds=dict(baseline=sum(baseline[r['case']]['discovery']['seconds'] for r in gains),
                                    polarity=sum(r['discovery']['seconds'] for r in gains)),
        limitations=['One separately instrumented acquisition, not an uninstrumented speed comparison',
                     'Nested cumulative function costs must not be added',
                     'Auxiliary exclusions are exact non-membership certificates, not original UNSAT results',
                     'Selected frontier coverage differs from all acquired alternatives and complete source coverage',
                     'Original-root probe is separate, read-only and includes normalization, recognition and checking; excludes loading and output serialization',
                     'Original-root certificates describe normalized source syntax; an empty-clause normal form is recognized without claiming every unsimplified source admits a polarity renaming',
                     'Generator groups are reporting labels only; they never choose recognition or search'])
    target.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(case=case,gains=len(gains),misses=len(misses),frontier_outcomes=output['frontier_outcomes'])),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))

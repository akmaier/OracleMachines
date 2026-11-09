#!/usr/bin/env python3
"""Retain whole-source gains/losses and shared-state ranking counterexamples."""
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
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.analyze_cnf_probe_equivalence import selected
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_learning_core import check_core_probes
from experiments.cnf_learning_core_order import CoreOrderLearningInventory
from experiments.cnf_learning_fixed_order import baseline_continuation_choices
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_closure_reuse import batch_inactive


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def analyze(directory):
    start = time.perf_counter()
    report = json.loads((directory/'report.json').read_text())
    stores = {a['mode']: load_nodes(directory, a) for a in report['archives'] if a['mode'] != 'solver_only'}
    indices = {m: {digest(k): k for k in ns} for m, ns in stores.items()}
    rows = {(r['mode'], r['case']): r for r in report['records']}
    changes = dict(gains=[], losses=[])
    stats = {}
    for mode, nodes in stores.items():
        kinds, statuses, proof_bytes = Counter(), Counter(), 0
        for k, n in nodes.items():
            kinds[n['kind']] += len(k.encode()) + len(encode(n).encode())
            statuses[n['profile']['probing']['status']] += 1
            proof_bytes += len(encode(n['profile']['probing']).encode())
        stats[mode] = dict(nodes=len(nodes), logical_bytes_by_kind=dict(kinds),
                           statuses=dict(statuses), probe_payload_bytes=proof_bytes)
    paths = {}
    frontier = set()
    for i, case in enumerate(report['cases']):
        old, new = (rows[m, i]['discovery'] for m in ('baseline', 'core_order'))
        changed = old['summary']['closed'] != new['summary']['closed']
        if changed:
            changes['gains' if new['summary']['closed'] else 'losses'].append(i)
        if changed or case.get('original_case', i) in (956, 977, 1024, 1189):
            paths[str(i)] = {}
            for mode, nodes in stores.items():
                root = indices[mode][rows[mode, i]['discovery']['root_hash']]
                paths[str(i)][mode] = [dict(key_sha256=digest(k), cnf=nodes[k]['cnf'], depth=nodes[k]['depth'],
                    kind=nodes[k]['kind'], summary=nodes[k]['summary'], probing=nodes[k]['profile']['probing'],
                    selected_variable=(nodes[k]['alternatives'][nodes[k]['selected']]['variable']
                                       if nodes[k]['kind']=='or' else None)) for k in sorted(selected(nodes, root))]
        if not new['summary']['closed']:
            nodes=stores['core_order'];root=indices['core_order'][new['root_hash']]
            frontier.update(k for k in selected(nodes,root) if nodes[k]['kind']=='unresolved')
    old_states={encode([n['cnf'],n['depth']]): n for n in stores['baseline'].values()}
    shared_changes=[];transitions=Counter()
    for n in stores['core_order'].values():
        old=old_states.get(encode([n['cnf'],n['depth']]))
        if old is None:continue
        before,after=old['profile']['probing'],n['profile']['probing']
        transitions[before['status']+' -> '+after['status']]+=1
        if before==after:continue
        counts=Counter()
        # Parent replay precedes the diagnostic fixed-point test. An inactive
        # paired closure cannot acquire a new outcome under this exact batch.
        check_core_probes(n['cnf'],before,4,4,counts)
        core_choices=probe_choices(n['cnf'],4,counts)
        old_choices=baseline_continuation_choices(n['cnf'],before.get('attempts',[]),4,4,counts)
        active=[]
        if 'batch' in before:
            for j in range(0,len(before['attempts']),2):
                pair=before['attempts'][j:j+2]
                inactive=[batch_inactive(a,before['batch'],counts) for a in pair]
                if not all(inactive):active.append(pair[0]['variable'])
        shared_changes.append(dict(cnf=n['cnf'],depth=n['depth'],before=before,after=after,
            before_summary=old['summary'],after_summary=n['summary'],
            old_choices=old_choices,core_choices=core_choices,active_core_choices=active,
            novel_old_choices=[v for v in old_choices if v not in core_choices]))
    unresolved=[dict(case=i,group=c['group'],seconds=rows['core_order',i]['discovery']['seconds'],
                     summary=rows['core_order',i]['discovery']['summary'])
                for i,c in enumerate(report['cases']) if not rows['core_order',i]['discovery']['summary']['closed']]
    unresolved.sort(key=lambda r:-r['seconds'])
    profile=None
    if unresolved:
        i=unresolved[0]['case']
        with tempfile.TemporaryDirectory() as tmp:
            h=CoreOrderLearningInventory(Path(tmp)/'profile.db',max_depth=2,probe_limit=4,learn_limit=4)
            profiler=cProfile.Profile();profiler.enable();h.inspect(report['cases'][i]['source']);profiler.disable();h.close()
        measurements=pstats.Stats(profiler)
        top=sorted(measurements.stats.items(),key=lambda pair:-pair[1][3])[:30]
        profile=dict(case=i,total_seconds=measurements.total_tt,
            cumulative=[dict(file=k[0],line=k[1],function=k[2],primitive_calls=v[0],calls=v[1],
                             own_seconds=v[2],cumulative_seconds=v[3]) for k,v in top])
    result=dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),changes=changes,
        stats=stats,paths=paths,shared_status_transitions=dict(transitions),shared_changes=shared_changes,
        frontier=[dict(cnf=stores['core_order'][k]['cnf'],depth=stores['core_order'][k]['depth'],
                       profile=stores['core_order'][k]['profile']) for k in sorted(frontier)],
        unresolved_sources=unresolved,profile=profile,diagnostic_seconds=time.perf_counter()-start,
        limitations=['Diagnostics run separately after matched operations and allocation profiles',
            'Shared normalized CNF/depth controls isolate local changes; downstream paths can differ',
            'Same local probe cap does not bound total acquired nodes or global solving work',
            'Profile timings are instrumented and must not be added to primary operation times'])
    (directory/'mechanisms.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(dict(changes=changes,shared_changes=len(shared_changes),unresolved=len(unresolved),
                         frontier=len(frontier),profile_case=profile['case'] if profile else None)))


if __name__=='__main__':analyze(Path(sys.argv[1]))

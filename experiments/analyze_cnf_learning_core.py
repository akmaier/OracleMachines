#!/usr/bin/env python3
"""Preserve parent-scoped hint effects, exact core reuse and the remaining frontier."""
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
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_learning import learning_batch, augment
from experiments.cnf_probe_closure_reuse import discover_reuse_probes, check_reuse_probes
from experiments.cnf_learning_selection import discover_selected_probes, check_selected_probes
from experiments.cnf_learning_core import CoreLearningInventory, check_core_probes
from experiments.cnf_probe_equivalence import substitute_block
from experiments.cnf_learning_fixed_order import (
    FixedOrderLearningInventory, baseline_continuation_choices,
    discover_fixed_order_probes, check_fixed_order_probes)
from experiments.cnf_residual_dag import normalize, restrict


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def path_records(nodes, root):
    records = []
    for key in sorted(selected(nodes, root)):
        n = nodes[key]; p = n['profile']['probing']
        records.append(dict(key_sha256=digest(key), cnf=n['cnf'], depth=n['depth'],
            kind=n['kind'], summary=n['summary'], outcomes=n['profile']['outcomes'], probing=p,
            selected_variable=(n['alternatives'][n['selected']]['variable'] if n['kind']=='or' else None),
            child_sha256=digest(n['edge']['key']) if 'edge' in n else None))
    return records


def analyze(directory):
    start = time.perf_counter(); report = json.loads((directory/'report.json').read_text())
    rows = {(r['mode'],r['case']):r for r in report['records']}
    stores = {a['mode']:load_nodes(directory,a) for a in report['archives'] if a['mode']!='solver_only'}
    hashes = {m:{digest(k):k for k in ns} for m,ns in stores.items()}
    stats = {}; comparisons = {}; misses = []; leaves = set(); paths = {}
    for mode, nodes in stores.items():
        sizes = Counter(); statuses = Counter()
        for k,n in nodes.items():
            sizes[n['kind']] += len(k.encode())+len(encode(n).encode())
            statuses[n['profile']['probing']['status']] += 1
        stats[mode] = dict(nodes=len(nodes), logical_bytes_by_kind=dict(sizes), statuses=dict(statuses))
    for before in ('baseline','fixed'):
        comparisons[before] = dict(gains=[], losses=[])
        for i,c in enumerate(report['cases']):
            old = rows[before,i]['discovery']; new = rows['core',i]['discovery']
            item = dict(case=i,original_case=c.get('original_case',i),group=c['group'],
                        label=c.get('label'),answer=rows['core',i]['answer'],before=old['summary'],after=new['summary'])
            if new['summary']['closed'] and not old['summary']['closed']: comparisons[before]['gains'].append(item)
            if old['summary']['closed'] and not new['summary']['closed']: comparisons[before]['losses'].append(item)
    informative = {956,1024,1189} | {item['original_case'] for comparison in comparisons.values()
                                   for direction in ('gains','losses') for item in comparison[direction]}
    for i,c in enumerate(report['cases']):
        new = rows['core',i]['discovery']
        if not new['summary']['closed']:
            misses.append(dict(case=i,original_case=c.get('original_case',i),group=c['group'],summary=new['summary']))
            leaves.update(k for k in selected(stores['core'],hashes['core'][new['root_hash']])
                          if stores['core'][k]['kind']=='unresolved')
        if c.get('original_case',i) in informative:
            paths[str(c.get('original_case',i))] = {
                m:path_records(ns,hashes[m][rows[m,i]['discovery']['root_hash']]) for m,ns in stores.items()}
    # The previously archived parent is a controlled source, even if whole-source
    # discovery now takes a different path. Check all three continuations/children.
    fixture_path = Path('experiments/results/cnf-learning-selection/selection-paths.json')
    fixtures = json.loads(fixture_path.read_text())['paths']; parent_controls = []
    policies = [('baseline',discover_reuse_probes,check_reuse_probes),
                ('fixed',discover_fixed_order_probes,check_fixed_order_probes),
                ('core',discover_fixed_order_probes,check_core_probes)]
    for fixture in fixtures:
        cnf = fixture['parent_cnf']; control = {}
        for mode,discover,check in policies:
            counts = Counter(); result = discover(cnf,4,4,counts); raw,fixed = check(cnf,result,4,4,counts)
            child,names = normalize(raw); p = result.get('continuation',result); last = p['attempts'][-1]
            with tempfile.TemporaryDirectory() as tmp:
                from experiments.compare_cnf_learning_core import MODES
                cls,options = MODES[mode]
                h = cls(Path(tmp)/'child.db',**dict(options,max_depth=fixture['depth']))
                discovered = h.inspect(raw); key = discovered['root']['key']
                child_nodes = {k:json.loads(v) for k,v in h.db.execute('SELECT * FROM cnf_patterns_v1')}
                chain = path_records(child_nodes,key); h.close()
            control[mode] = dict(result=result, raw_child=raw, child_cnf=child, child_names=names,
                fixed=fixed, first_conflict=(dict(variable=last['variable'],value=last['value'])
                                             if p['status']=='forced' else None),
                child_summary=discovered['summary'],child_path=chain,counters=dict(counts),
                child_diagnostic_seconds=discovered['seconds'])
            if p['status'] in ('forced','common'):
                # Record a possible next representation experiment without
                # executing it as a new discovery policy or claiming coverage.
                core = restrict(cnf,fixed)
                extra = sorted(set(map(tuple,raw))-set(map(tuple,core)))
                control[mode]['source_restriction'] = core
                control[mode]['retained_additions'] = extra
        parent_controls.append(dict(parent_cnf=cnf,depth=fixture['depth'],
            gained_source_paths=fixture['gained_source_paths'],lost_source_paths=fixture['lost_source_paths'],controls=control))
    # Every selected unresolved leaf retains recognition, implications and both
    # candidate lists, including no-batch cases. No unexecuted opportunity is a gain.
    frontier = []
    for key in sorted(leaves):
        n = stores['core'][key]; p = n['profile']['probing']; counts = Counter()
        pool = learning_batch(n['cnf'],p.get('attempts',[]),16,counts)
        frontier.append(dict(key_sha256=digest(key),cnf=n['cnf'],depth=n['depth'],shape=n['profile']['shape'],
            outcomes=n['profile']['outcomes'],probing=p,pool=pool,
            baseline_choices=baseline_continuation_choices(n['cnf'],p.get('attempts',[]),4,4,counts),
            selected_choices=probe_choices(augment(n['cnf'],p.get('batch',[])),4,counts),counters=dict(counts)))
    core_edges=[]; grouped={}; old_index={encode([n['cnf'],n['depth']]):n for n in stores['fixed'].values()}
    for key,n in stores['core'].items():
        p=n['profile']['probing']
        if n['kind']!='probe' or p['status']!='learned':continue
        counts=Counter();view,fixed=check_fixed_order_probes(n['cnf'],p,4,4,counts)
        core,again=check_core_probes(n['cnf'],p,4,4,counts);assert fixed==again
        normalized_view,names=normalize(view);normalized_core,core_names=normalize(core)
        assert list(map(list,normalized_core))==stores['core'][n['edge']['key']]['cnf']
        old=old_index.get(encode([n['cnf'],n['depth']]))
        if old is not None:assert old['profile']['probing']==p
        item=dict(parent_sha256=digest(key),depth=n['depth'],shape=n['profile']['shape'],
            reduction=p['continuation']['status'],core_sha256=digest(n['edge']['key']),
            normalized_view=normalized_view,view_names=names,core_names=core_names,
            changed=normalized_view!=normalized_core or names!=core_names,
            identity_changed=normalized_view!=normalized_core,transport_changed=names!=core_names,
            common_fixed_parent=old is not None,view_clauses=len(view),core_clauses=len(core),
            view_literals=sum(map(len,view)),core_literals=sum(map(len,core)),counters=dict(counts))
        if not any(not c for c in core):
            batch=tuple(tuple(b['clause']) for b in p['batch'])
            transformed=(substitute_block(batch,p['continuation']['witness'],counts)
                         if p['continuation']['status']=='equivalence' else restrict(batch,fixed,counts))
            rename={v:i for i,v in enumerate(core_names,1)};eligible=set();outside=[]
            for clause in transformed:
                literals=set(clause)
                if any(-l in literals for l in literals):continue
                if any(abs(l) not in rename for l in literals):outside.append(sorted(literals));continue
                eligible.add(tuple(sorted(rename[abs(l)]*(1 if l>0 else -1) for l in literals)))
            child=stores['core'][n['edge']['key']];cp=child['profile']['probing']
            existing={tuple(c) for c in child['cnf']};novel=eligible-existing
            child_batch={tuple(b['clause']) for b in cp.get('batch',[])}
            item['hint_transport_opportunity']=dict(eligible_clauses=sorted(eligible),already_in_core=sorted(eligible & existing),
                absent_clauses=sorted(novel),outside_core_variables=outside,
                reacquired_in_child_batch=sorted(novel & child_batch),child_probe_status=cp['status'])
        core_edges.append(item);grouped.setdefault(n['edge']['key'],[]).append(item)
    shared=[dict(core_sha256=digest(k),parents=[x['parent_sha256'] for x in items],
                 all_parents_in_fixed=all(x['common_fixed_parent'] for x in items),
                 distinct_augmented_views=len({encode([x['normalized_view'],x['depth']]) for x in items}))
            for k,items in grouped.items() if len(items)>1]
    worst=max((r for r in report['records'] if r['mode']=='core' and not r['discovery']['summary']['closed']),
              key=lambda r:r['discovery']['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=CoreLearningInventory(Path(tmp)/'profile.db',max_depth=2,probe_limit=4,learn_limit=4)
        profiler=cProfile.Profile();profiler.enable();r=h.inspect(report['cases'][worst]['source']);profiler.disable();h.close()
        functions=[dict(file=f,line=line,name=name,primitive_calls=pr,calls=ca,own_seconds=own,cumulative_seconds=cu)
                   for (f,line,name),(pr,ca,own,cu,_) in pstats.Stats(profiler).stats.items()]
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fixture_sha256=hashlib.sha256(fixture_path.read_bytes()).hexdigest(),nodes=stats,comparisons=comparisons,
        misses=misses,selected_unresolved_nodes=len(leaves),
        selected_unresolved_literals=sum(n['shape']['literals'] for n in frontier),
        selected_leaf_statuses=dict(Counter(n['probing']['status'] for n in frontier)),
        source_paths=paths,parent_controls=parent_controls,frontier=frontier,
        learned_core_edges=core_edges,shared_learned_core_children=shared,
        profile=dict(case=worst,original_case=report['cases'][worst].get('original_case',worst),
                     instrumented_seconds=r['seconds'],metrics=r['metrics'],
                     functions=sorted(functions,key=lambda f:-f['own_seconds'])[:40]),
        diagnostic_seconds=time.perf_counter()-start,
        limitations=['Parent controls and child acquisition are separate diagnostic timings',
          'Hints support the parent propagation and remain in its proof; descendants rediscover hints on the original-clause core',
          'Frontier candidates are opportunities, not additional source closures',
          'Generator labels never select discovery policies; all original sources still require exact solving'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'mechanisms.json'
    if out.exists():raise ValueError('Preserve earlier analysis')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')

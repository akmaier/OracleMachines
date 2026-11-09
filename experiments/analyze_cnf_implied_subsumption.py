#!/usr/bin/env python3
"""Explain implication exposure, pool costs and relevance-filter opportunities."""
from collections import Counter
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.analyze_cnf_signed_subsumption import selected, digest
from experiments.cnf_implied_subsumption import (
    ImpliedSubsumptionInventory, indexed_certificate, check_indexed_subsumption)
from experiments.cnf_pattern_inventory import classify, encode
from experiments.cnf_residual_dag import normalize


def filtered_control(node):
    """All origins were replayed by the full archive audit. Retain only original
    implications contained in a long clause of the original minimal core.
    This is an offline exact-model control, not the implemented planner policy.
    """
    saved=node['subsumption'];pool=saved['implied']['implications'];counts=Counter()
    long=[set(node['cnf'][j]) for j in saved['certificate']['kept'] if len(node['cnf'][j])>2]
    keep=[]
    for i,item in enumerate(pool):
        clause=set(item['clause'])
        for source in long:
            counts['relevance_subset_tests']+=1
            if clause<=source:keep.append(i);break
    augmented=node['cnf']+[pool[i]['clause'] for i in keep]
    cert=indexed_certificate(augmented,counts)
    core=check_indexed_subsumption(augmented,cert,counts)
    normalized,names=normalize(core,counts);profile=classify(normalized,8,counts)
    return dict(pool_indices=keep,certificate=cert,core=normalized,names=names,profile=profile,
        recognized=[k for k,v in profile['outcomes'].items() if v=='recognized'],counts=dict(counts))


def main(directory):
    target=directory/'mechanisms.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    rows={(r['mode'],r['case']):r for r in report['records']};stats={};current=None
    for entry in report['archives']:
        if entry['mode']=='solver_only':continue
        nodes=load_nodes(directory,entry);searches=[n for n in nodes.values() if 'subsumption' in n]
        implied=[n for n in searches if 'implied' in n['subsumption']]
        stats[entry['mode']]=dict(kinds=dict(Counter(n['kind'] for n in nodes.values())),
            logical_node_bytes=sum(len(k.encode())+len(encode(n).encode()) for k,n in nodes.items()),
            terminal_searches=len(searches),total_exposures=sum(n['kind']=='subsumption' for n in searches),
            implied_searches=len(implied),implied_exposures=sum(n['kind']=='subsumption' for n in implied),
            search_payload_bytes=sum(len(encode(n['subsumption']).encode()) for n in searches),
            implied_payload_bytes=sum(len(encode(n['subsumption']['implied']).encode()) for n in implied),
            original_pool_clauses=sum(len(n['subsumption']['implied']['implications']) for n in implied))
        if entry['mode']=='implied':current=nodes
    hashes={digest(k):k for k in current};gains=[];losses=[];misses=[];leaves=set();paths={}
    for i,c in enumerate(report['cases']):
        a=rows['baseline',i]['discovery'];b=rows['implied',i]['discovery']
        path=selected(current,hashes[b['root_hash']]);unresolved={k for k in path if current[k]['kind']=='unresolved'}
        paths[i]=unresolved
        item=dict(case=i,group=c['group'],label=c.get('label'),answer=rows['implied',i]['answer'],
            before=a['summary'],after=b['summary'],seconds=b['seconds'],
            selected_implied_exposures=sum(current[k]['kind']=='subsumption' and
                'implied' in current[k]['subsumption'] for k in path))
        if b['summary']['closed'] and not a['summary']['closed']:gains.append(item)
        if a['summary']['closed'] and not b['summary']['closed']:losses.append(item)
        if not b['summary']['closed']:misses.append(item);leaves.update(unresolved)
    controls=[];potential=set();pool_total=kept_total=old_exposed=preserved=0;local_losses=[]
    for key,n in current.items():
        data=n.get('subsumption',{}).get('implied',{})
        if not data.get('implications'):continue
        control=filtered_control(n);pool_total+=len(data['implications']);kept_total+=len(control['pool_indices'])
        before=n['kind']=='subsumption';after=bool(control['recognized'])
        old_exposed+=before;preserved+=before and after
        if before and not after:local_losses.append(digest(key))
        if key in leaves and after:potential.add(key)
        controls.append(dict(key_sha256=digest(key),source=n['cnf'],depth=n['depth'],
            before_closed=before,old_pool=data['implications'],filtered=control))
    opportunities=[dict(case=i,remaining_leaves=len(path),exposed_leaves=len(path & potential),
                        selected_plan_completable=path<=potential)
                   for i,path in paths.items() if path & potential]
    frontier=[dict(key_sha256=digest(k),cnf=current[k]['cnf'],depth=current[k]['depth'],
        shape=current[k]['profile']['shape'],probing=current[k]['profile']['probing'],
        subsumption=current[k]['subsumption']) for k in sorted(leaves)]
    worst=max(misses,key=lambda row:row['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=ImpliedSubsumptionInventory(Path(tmp)/'profile.db',max_depth=2,probe_limit=4,learn_limit=4)
        profiler=cProfile.Profile();profiler.enable();result=h.inspect(report['cases'][worst]['source']);profiler.disable();h.close()
        fs=[dict(file=f,line=line,name=name,primitive_calls=pr,calls=ca,own_seconds=own,cumulative_seconds=cu)
            for (f,line,name),(pr,ca,own,cu,_) in pstats.Stats(profiler).stats.items()]
    output=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nodes=stats,gains=gains,losses=losses,
        misses=sorted(misses,key=lambda row:-row['seconds']),frontier=frontier,
        selected_unresolved_nodes=len(leaves),selected_unresolved_literals=sum(current[k]['profile']['shape']['literals'] for k in leaves),
        filtered_controls=controls,filtered_pool_before=pool_total,filtered_pool_after=kept_total,
        filtered_old_exposures=old_exposed,filtered_preserved_exposures=preserved,filtered_local_losses=local_losses,
        filtered_exposed_frontier_leaves=len(potential),filtered_source_opportunities=opportunities,
        profile=dict(case=worst,instrumented_seconds=result['seconds'],metrics=result['metrics'],
                     functions=sorted(fs,key=lambda f:-f['own_seconds'])[:40]),
        limitations=['Original implication proofs are replayed by the full cold archive audit before these offline controls',
          'Filtering retains source-entailed clauses and checks signed subsets, but is not an integrated policy or runtime result',
          'Diagnostic compares all encountered nonempty pools, including failed alternatives; these are not independent sources',
          'Any prospective source completion is conditional on integration, exact transport and full acquisition accounting',
          'The diagnostic relevance scan itself is charged in counters; a lower pool count does not prove lower total work',
          'Profiling is separate and instrumented; no general SAT bound or industrial timing claim'])
    target.write_text(json.dumps(output,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('frontier','misses','profile','limitations','filtered_controls')}),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))

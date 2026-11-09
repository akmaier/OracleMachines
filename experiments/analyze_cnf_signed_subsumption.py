#!/usr/bin/env python3
"""Measure terminal exposure, retained failures and a proof-reuse opportunity."""
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
from experiments.cnf_signed_subsumption import (
    SignedSubsumptionInventory, subsumption_certificate, check_subsumption)
from experiments.cnf_learning_activity import check_activity_probes
from experiments.cnf_pattern_inventory import classify, encode
from experiments.cnf_residual_dag import normalize


def digest(s): return hashlib.sha256(s.encode()).hexdigest()


def selected(nodes,key):
    stack=[key];seen=set()
    while stack:
        k=stack.pop()
        if k in seen:continue
        seen.add(k);n=nodes[k]
        edges=(n['edges'] if n['kind']=='and' else n['alternatives'][n['selected']]['edges'] if n['kind']=='or'
               else [n['edge']] if n['kind'] in ('project','simplify','probe','subsumption') else [])
        stack.extend(e['key'] for e in edges)
    return seen


def implied_subset_control(node):
    """Offline: reuse all original checked unit implications, including ones
    filtered out as binary-transitive by the current batch-selection policy.
    This is a diagnostic over selected leaves, not an integrated planner gain.
    """
    cnf=node['cnf'];probing=node['profile']['probing'];counts=Counter()
    check_activity_probes(cnf,probing,4,4,counts)
    clauses={tuple(c) for c in cnf};new=[]
    for ai,attempt in enumerate(probing.get('attempts',[])):
        assumption=attempt['variable']*(1 if attempt['value'] else -1)
        for ui,(lit,_) in enumerate(attempt['certificate']['units']):
            clause=tuple(sorted((-assumption,lit)))
            if len(set(clause))!=2 or clause[0]==-clause[1] or clause in clauses:continue
            clauses.add(clause);new.append(dict(attempt=ai,unit=ui,clause=list(clause)))
    augmented=cnf+[c['clause'] for c in new]
    cert=subsumption_certificate(augmented,counts)
    core=check_subsumption(augmented,cert,counts)
    normalized,names=normalize(core,counts);profile=classify(normalized,8,counts)
    return dict(implications=new,certificate=cert,core=normalized,names=names,
        profile=profile,recognized=[k for k,v in profile['outcomes'].items() if v=='recognized'],
        counts=dict(counts))


def main(directory):
    target=directory/'mechanisms.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    rows={(r['mode'],r['case']):r for r in report['records']};stats={};current=None
    for entry in report['archives']:
        if entry['mode']=='solver_only':continue
        nodes=load_nodes(directory,entry);searches=[n for n in nodes.values() if 'subsumption' in n]
        stats[entry['mode']]=dict(kinds=dict(Counter(n['kind'] for n in nodes.values())),
            logical_node_bytes=sum(len(k.encode())+len(encode(n).encode()) for k,n in nodes.items()),
            terminal_searches=len(searches),exposures=sum(n['kind']=='subsumption' for n in searches),
            changed_searches=sum(bool(n['subsumption']['certificate']['removed']) for n in searches),
            search_payload_bytes=sum(len(encode(n['subsumption']).encode()) for n in searches),
            removed_clauses=sum(len(n['subsumption']['certificate']['removed']) for n in searches),
            removed_literals=sum(len(n['cnf'][j]) for n in searches for j,_ in n['subsumption']['certificate']['removed']))
        if entry['mode']=='subsumption':current=nodes
    hashes={digest(k):k for k in current};gains=[];losses=[];misses=[];leaves=set();source_paths={}
    for i,c in enumerate(report['cases']):
        a=rows['baseline',i]['discovery'];b=rows['subsumption',i]['discovery']
        path=selected(current,hashes[b['root_hash']]);unresolved={k for k in path if current[k]['kind']=='unresolved'}
        source_paths[i]=unresolved
        item=dict(case=i,group=c['group'],label=c.get('label'),answer=rows['subsumption',i]['answer'],
            before=a['summary'],after=b['summary'],seconds=b['seconds'],
            selected_exposures=sum(current[k]['kind']=='subsumption' for k in path))
        if b['summary']['closed'] and not a['summary']['closed']:gains.append(item)
        if a['summary']['closed'] and not b['summary']['closed']:losses.append(item)
        if not b['summary']['closed']:misses.append(item);leaves.update(unresolved)
    frontier=[];potential=set()
    for key in sorted(leaves):
        n=current[key];control=implied_subset_control(n)
        if control['recognized']:potential.add(key)
        frontier.append(dict(key_sha256=digest(key),cnf=n['cnf'],depth=n['depth'],shape=n['profile']['shape'],
            probing=n['profile']['probing'],subsumption=n['subsumption'],implied_subset_control=control))
    opportunities=[dict(case=i,remaining_leaves=len(path),exposed_leaves=len(path & potential),
                        selected_plan_completable=path<=potential)
                   for i,path in source_paths.items() if path & potential]
    worst=max(misses,key=lambda row:row['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=SignedSubsumptionInventory(Path(tmp)/'profile.db',max_depth=2,probe_limit=4,learn_limit=4)
        profiler=cProfile.Profile();profiler.enable();result=h.inspect(report['cases'][worst]['source']);profiler.disable();h.close()
        fs=[dict(file=f,line=line,name=name,primitive_calls=pr,calls=ca,own_seconds=own,cumulative_seconds=cu)
            for (f,line,name),(pr,ca,own,cu,_) in pstats.Stats(profiler).stats.items()]
    output=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nodes=stats,gains=gains,losses=losses,
        misses=sorted(misses,key=lambda row:-row['seconds']),frontier=frontier,
        selected_unresolved_nodes=len(leaves),selected_unresolved_literals=sum(current[k]['profile']['shape']['literals'] for k in leaves),
        implied_subset_exposed_leaves=len(potential),implied_subset_source_opportunities=opportunities,
        profile=dict(case=worst,instrumented_seconds=result['seconds'],metrics=result['metrics'],
                     functions=sorted(fs,key=lambda f:-f['own_seconds'])[:40]),
        limitations=['All terminal searches include unsuccessful alternatives; the selected frontier is a distinct subset',
          'Additional implied-clause controls replay original reasons and check exact subsumption but are offline diagnostics',
          'They spend no new probe pass, but materializing, finding and checking consequences still costs work and space',
          'Prospective source completions are conditional on integrating the exact reductions, not executed coverage',
          'Profiling is separate and instrumented; no general SAT bound or industrial timing claim'])
    target.write_text(json.dumps(output,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('frontier','misses','profile','limitations')}),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))

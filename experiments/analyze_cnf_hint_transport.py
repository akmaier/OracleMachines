#!/usr/bin/env python3
"""Locate local gains in the saved source plans and separate batch/order effects."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.analyze_cnf_probe_equivalence import selected
from experiments.cnf_hint_transport import HintAssistedInventory
from experiments.cnf_learning_core import CoreLearningInventory
from experiments.cnf_learning_fixed_order import baseline_continuation_choices
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_closure_reuse import batch_inactive
from experiments.cnf_probe_equivalence import discover_equivalence_probes
from experiments.cnf_pattern_inventory import encode


def sha(x):return hashlib.sha256(x).hexdigest()


def reachable(nodes,key):
    seen=set();stack=[key]
    while stack:
        k=stack.pop()
        if k in seen:continue
        seen.add(k);n=nodes[k]
        if n['kind']=='and':stack.extend(e['key'] for e in n['edges'])
        elif n['kind']=='or':stack.extend(e['key'] for a in n['alternatives'] for e in a['edges'])
        elif 'edge' in n:stack.append(n['edge']['key'])
    return seen


def main(directory):
    path=directory/'mechanisms.json'
    if path.exists():raise ValueError('Preserve earlier analysis')
    start=time.perf_counter();r=json.loads((directory/'report.json').read_text())
    s=json.loads((directory/'summary.json').read_text());rows={(x['mode'],x['case']):x for x in r['records']}
    baseline=load_nodes(directory,next(a for a in r['archives'] if a['mode']=='baseline'))
    previous=Path('experiments/results/cnf-learning-core');oldr=json.loads((previous/'report.json').read_text())
    old=load_nodes(previous,next(a for a in oldr['archives'] if a['mode']=='core'))
    oldkeys={sha(k.encode()):k for k in old};control=[];reuse=[];totals=Counter()
    for i,c in enumerate(r['cases']):
        root=baseline[rows['baseline',i]['discovery']['edge']['key']];p=root['profile']['probing']
        hints=[dict(clause=h['clause']) for h in c['transport']['hints']]
        counts=Counter();states=[]
        if hints and p['status'] in ('clear','learning_clear','learned'):
            for a in p['attempts']:
                inactive=batch_inactive(a,hints,counts)
                states.append(dict(variable=a['variable'],value=a['value'],inactive=inactive))
                totals['inactive' if inactive else 'active']+=1
            totals['eligible_parents']+=1
        reuse.append(dict(case=i,baseline_status=p['status'],hint_status=rows['hints',i]['discovery']['plan']['probing']['status'],
                          states=states,counters=dict(counts)))
    for i in s[1]['gains']+s[1]['losses']:
        c=r['cases'][i];core=tuple(tuple(x) for x in c['transport']['core'])
        parent=oldkeys.get(c['parent_sha256']);selected_sources=[];reachable_sources=[]
        if parent is not None:
            for oldrow in oldr['records']:
                if oldrow['mode']!='core':continue
                root=oldkeys[oldrow['discovery']['root_hash']]
                item=dict(case=oldrow['case'],group=oldr['cases'][oldrow['case']]['group'],summary=oldrow['discovery']['summary'])
                if parent in selected(old,root):selected_sources.append(item)
                if parent in reachable(old,root):reachable_sources.append(item)
        original=baseline[rows['baseline',i]['discovery']['edge']['key']]['profile']['probing']
        controls=[]
        if original['status'] in ('learning_clear','learned'):
            choices={'core':probe_choices(core,4,Counter()),
                     'baseline_continuation':baseline_continuation_choices(core,original['attempts'],4,4,Counter())}
            batches={'transported':[h['clause'] for h in c['transport']['hints']],
                     'rediscovered':[b['clause'] for b in original['batch']]}
            for bn,batch in batches.items():
                for cn,order in choices.items():
                    counts=Counter();t=time.perf_counter();augmented=core+tuple(tuple(x) for x in batch)
                    p=discover_equivalence_probes(augmented,4,counts,_choices=order)
                    # Reuse the core-target construction with this explicit
                    # internally supplied order, checked separately below.
                    from experiments.cnf_probe_equivalence import check_equivalence_probes, substitute_block
                    from experiments.cnf_residual_dag import restrict
                    target,fixed=check_equivalence_probes(augmented,p,4,counts,_choices=order)
                    if p['status']=='clear':target=core
                    elif not any(not cl for cl in target):
                        target=substitute_block(core,p['witness'],counts) if p['status']=='equivalence' else restrict(core,fixed,counts)
                    with tempfile.TemporaryDirectory() as tmp:
                        h=CoreLearningInventory(Path(tmp)/'child.db',max_depth=2,probe_limit=4,learn_limit=4)
                        edge=h._edge(target,c['depth']);node=h._load(edge['key']);summary=node['summary'];h.close()
                    controls.append(dict(batch=bn,order=cn,clauses=batch,choices=order,probing=p,fixed=fixed,
                                         target=target,summary=summary,seconds=time.perf_counter()-t,metrics=dict(counts)))
        control.append(dict(case=i,origin=c['origin'],parent_sha256=c['parent_sha256'],core=core,
                            selected_sources=selected_sources,reachable_sources=reachable_sources,controls=controls))
    data=dict(report_sha256=sha((directory/'report.json').read_bytes()),source_sha256=sha(Path(__file__).read_bytes()),
              reuse_totals=dict(totals),reuse=reuse,changed_local_cases=control,diagnostic_seconds=time.perf_counter()-start,
              limitations=['Post-run controls are separate from primary timings',
                'Inactive fixed-point deltas are opportunities after the original closure has been checked, not executed savings',
                'A local gain off all selected source paths is not an original-source coverage gain'])
    path.write_text(json.dumps(data,indent=2)+'\n')


if __name__=='__main__':main(Path(sys.argv[1]))

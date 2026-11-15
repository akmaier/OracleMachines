#!/usr/bin/env python3
"""Describe exact prefix reuse and class transitions without assuming closure."""
from collections import Counter
import gzip
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_materialized_checkpoint import sha
from experiments.continue_cnf_case1063_discovery import BASE, PRESERVATION, sha_key, read_archive


def load(path): return json.loads(Path(path).read_text())
def shape(cnf): return [len({abs(x) for c in cnf for x in c}),len(cnf),sum(map(len,cnf))]


def prefix_groups(findings):
    groups={};nodes={}
    for arm in findings['arms']:
        if arm['repeat']!=0:continue
        scope=arm['focus_lineage']['original_case'];keys=groups.setdefault(scope,set())
        for split in arm['splits']:
            for branch in split['branches']:
                for node in branch['prefix']['nodes']:
                    key=node['key_sha256'];keys.add(key)
                    identity={k:node[k] for k in ('kind','shape')}
                    assert key not in nodes or nodes[key]==identity
                    nodes[key]=identity
    return groups,nodes


def analyze(out):
    r=load(out/'report.json');cold=load(out/'reconstruction.json')
    assert cold['passed'] and cold['report_sha256']==sha(out/'report.json')
    assert Path(r['parent']['path'])==BASE and sha(BASE)==r['parent']['sha256']
    previous_summary=BASE.parent/'discovery-summary.json'
    assert sha(previous_summary)==load(PRESERVATION)['discovery_summary_sha256']
    previous_path=BASE.parent/'structural-findings.json'
    assert sha(previous_path)==load(previous_summary)['structural_findings_sha256']
    current_path=out/'structural-findings.json';findings=load(current_path)
    current,nodes=prefix_groups(findings);previous,_=prefix_groups(load(previous_path))
    shared=[]
    for scope,keys in sorted(current.items()):
        for old,old_keys in sorted(previous.items()):
            overlap=keys&old_keys
            shared.append(dict(current_original=scope,previous_original=old,
                shared_keys=sorted(overlap),shared_kinds=dict(Counter(nodes[k]['kind'] for k in overlap)),
                shared_shapes=[dict(key_sha256=k,**nodes[k]) for k in sorted(overlap)]))
    scope_by_batch={a['batch']:a['focus_lineage']['original_case'] for a in findings['arms'] if a['repeat']==0}
    by_scope={}
    for bound in r['arms']:
        if bound['repeat']!=0:continue
        assert sha(bound['path'])==bound['sha256'];arm=load(bound['path'])
        group=by_scope.setdefault(scope_by_batch[bound['batch']],dict(entries=Counter(),stored=set(),batches=[]))
        group['entries'].update(arm['admitted_state_sha256']);group['stored'].update(arm['completed_new_state_sha256']);group['batches'].append(bound['batch'])
    accounting=[dict(original_case=k,batches=v['batches'],entries=sum(v['entries'].values()),
        distinct_inputs=len(v['entries']),reentries=sum(v['entries'].values())-len(v['entries']),
        stored=len(v['stored']),unstored=sorted(set(v['entries'])-v['stored'])) for k,v in sorted(by_scope.items())]
    previous_findings=load(previous_path)
    previous_scope={a['batch']:a['focus_lineage']['original_case'] for a in previous_findings['arms'] if a['repeat']==0}
    combined={k:dict(entries=Counter(v['entries']),stored=set(v['stored'])) for k,v in by_scope.items()}
    previous_groups={}
    for bound in load(BASE)['arms']:
        if bound['repeat']!=0:continue
        assert sha(bound['path'])==bound['sha256'];arm=load(bound['path']);scope=previous_scope[bound['batch']]
        old=previous_groups.setdefault(scope,dict(entries=Counter(),stored=set()))
        old['entries'].update(arm['admitted_state_sha256']);old['stored'].update(arm['completed_new_state_sha256'])
    cumulative=[]
    for scope,current in combined.items():
        if scope not in previous_groups:continue
        old=previous_groups[scope]
        assert old['stored'].isdisjoint(current['stored'])
        entries=current['entries']+old['entries'];stored=current['stored']|old['stored']
        cumulative.append(dict(original_case=scope,entries=sum(entries.values()),distinct_inputs=len(entries),
            reentries=sum(entries.values())-len(entries),stored=len(stored),unstored=sorted(set(entries)-stored),
            previous_stored=len(old['stored']),new_stored=len(current['stored']),
            cross_checkpoint_reentered=len(set(old['entries'])&set(current['entries']))))
    pending=[]
    for bound in r['arms']:
        if bound['repeat']!=0:continue
        arm=load(bound['path'])
        for step in arm['steps']:
            operation=read_archive(step['operation'])
            if 'acquisition' not in operation:continue
            pending.append(dict(batch=bound['batch'],step=step['step'],source_shape=step['source_shape'],
                mode=operation['mode'],pending=operation['pending'],
                branches=[dict(pending=b['pending'],admitted=len(b['admitted'])) for b in operation['acquisition']['branches']]))
    d=r['delta'];assert sha(d['path'])==d['sha256']
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'delta';p.write_bytes(gzip.decompress(Path(d['path']).read_bytes()))
        assert sha(p)==d['database_sha256'];db=sqlite3.connect(p)
        try:stored={k:json.loads(v) for k,v in db.execute('SELECT id,payload FROM cnf_patterns_v1')}
        finally:db.close()
    positive={s['source']:s for s in read_archive(r['expanded_certificate'])['steps']}
    unresolved=[];polarities=[]
    for key,n in stored.items():
        if n['kind']=='unresolved':
            step=positive.get(key)
            unresolved.append(dict(source_sha256=sha_key(key),shape=shape(n['cnf']),
                in_final_positive_proof=step is not None,external_rule=step['rule']['kind'] if step else None,
                premises=len(step['children']) if step else None))
        if n['kind']=='polarity':
            target=stored.get(n['edge']['key']);target_shape=shape(json.loads(n['edge']['key'])[-1])
            assert shape(n['cnf'])==target_shape
            polarities.append(dict(source_sha256=sha_key(key),target_sha256=sha_key(n['edge']['key']),
                shape=shape(n['cnf']),flipped_variables=len(n['polarity']['flipped']),outcome=n['polarity']['outcome'],
                source_outcomes=n['profile']['outcomes'],target_newly_stored=target is not None,
                target_outcomes=target['profile']['outcomes'] if target else None))
    summary=dict(passed=True,report_sha256=sha(out/'report.json'),reconstruction_sha256=sha(out/'reconstruction.json'),
        source_sha256=sha(__file__),current_findings_sha256=sha(current_path),previous_findings_sha256=sha(previous_path),
        prefix_reuse_by_previous_original=shared,admission_by_original=accounting,
        same_original_across_two_checkpoints=cumulative,branch_admissions=pending,
        polarity_transitions=polarities,unresolved_records=unresolved,
        limitations=['Prefix intersections cover touched branches only, not every global alternative or possible equivalent encoding.',
            'Matching shapes and method names are not proof transport. No shared representation is inferred without an exact checked identity.',
            'Absence from the saved positive certificate is not proof that a record has no other closed route.',
            'Repeated admissions count interrupted re-entry, not its isolated runtime cost.'])
    (out/'reuse-findings.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True,shared=[dict(current_original=x['current_original'],previous_original=x['previous_original'],shared_nodes=len(x['shared_keys']),shared_kinds=x['shared_kinds']) for x in shared],
        accounting=[{k:v for k,v in x.items() if k!='unstored'}|dict(unstored=len(x['unstored'])) for x in accounting],polarities=len(polarities))))


if __name__=='__main__':analyze(Path(sys.argv[1]))

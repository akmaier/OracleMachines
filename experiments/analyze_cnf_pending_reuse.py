#!/usr/bin/env python3
"""Separate resumed-prefix reuse from transfer between original SAT instances."""
from collections import Counter
import gzip
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_materialized_checkpoint import sha
from experiments.continue_cnf_pending_discovery import BASE, PRESERVATION, sha_key, read_archive


def load(path): return json.loads(Path(path).read_text())


def shape(cnf): return [len({abs(x) for c in cnf for x in c}), len(cnf), sum(map(len,cnf))]


def analyze(out):
    r = load(out/'report.json'); cold = load(out/'reconstruction.json')
    assert cold['passed'] and cold['report_sha256']==sha(out/'report.json')
    assert Path(r['parent']['path'])==BASE and sha(BASE)==r['parent']['sha256']
    current_path=out/'structural-findings.json'; previous_path=BASE.parent/'structural-findings.json'
    manifest_path=BASE.parent/'manifest.json'
    assert sha(manifest_path)==load(PRESERVATION)['parent_manifests'][str(manifest_path)]['sha256']
    previous_manifest=load(manifest_path)
    assert sha(previous_path)==previous_manifest['artifacts'][str(previous_path)]
    current=load(current_path); previous=load(previous_path)
    kinds={}; current_keys=set(); by_previous={}
    for arm in current['arms']:
        if arm['repeat']!=0: continue
        assert arm['focus_lineage']['original_case']==1062
        for split in arm['splits']:
            for branch in split['branches']:
                for node in branch['prefix']['nodes']:
                    key=node['key_sha256'];current_keys.add(key)
                    assert key not in kinds or kinds[key]==node['kind']
                    kinds[key]=node['kind']
    for arm in previous['arms']:
        if arm['repeat']!=0: continue
        scope=arm['focus_lineage']['original_case']
        keys=by_previous.setdefault(scope,set())
        for split in arm['splits']:
            for branch in split['branches']:
                keys.update(n['key_sha256'] for n in branch['prefix']['nodes'])
    shared=[]
    for scope,keys in sorted(by_previous.items()):
        overlap=keys&current_keys
        shared.append(dict(previous_original=scope,current_original=1062,
            same_original=scope==1062,shared_keys=sorted(overlap),
            shared_kinds=dict(Counter(kinds[k] for k in overlap))))
    previous_batches={a['batch'] for a in previous['arms']
        if a['repeat']==0 and a['focus_lineage']['original_case']==1062}
    def workers(report, batches=None):
        result=[]
        for bound in report['arms']:
            if bound['repeat']!=0 or (batches is not None and bound['batch'] not in batches):continue
            assert sha(bound['path'])==bound['sha256'];result.append(load(bound['path']))
        return result
    prior_workers=workers(load(BASE),previous_batches);current_workers=workers(r)
    entries=Counter(k for a in prior_workers+current_workers for k in a['admitted_state_sha256'])
    prior_stored={k for a in prior_workers for k in a['completed_new_state_sha256']}
    current_stored={k for a in current_workers for k in a['completed_new_state_sha256']}
    assert not prior_stored & current_stored
    assert prior_stored|current_stored==set(entries)
    lifetime=dict(previous_batches=len(prior_workers),current_batches=len(current_workers),
        prior_stored=len(prior_stored),new_stored=len(current_stored),
        admission_entries=sum(entries.values()),distinct_inputs=len(entries),
        repeated_entries=sum(entries.values())-len(entries),unstored=0)
    d=r['delta'];assert sha(d['path'])==d['sha256']
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'delta';p.write_bytes(gzip.decompress(Path(d['path']).read_bytes()))
        assert sha(p)==d['database_sha256'];db=sqlite3.connect(p)
        try: nodes={k:json.loads(v) for k,v in db.execute('SELECT id,payload FROM cnf_patterns_v1')}
        finally:db.close()
    positive={s['source']:s for s in read_archive(r['expanded_certificate'])['steps']}
    unresolved=[]
    for key,n in nodes.items():
        if n['kind']!='unresolved':continue
        assert key in positive
        step=positive[key]
        unresolved.append(dict(source_sha256=sha_key(key),shape=shape(n['cnf']),
            external_rule=step['rule']['kind'],premises=len(step['children'])))
    polarities=[]
    for key,n in nodes.items():
        if n['kind']!='polarity':continue
        target=nodes[n['edge']['key']]
        assert target['kind']=='family' and target['profile']['outcomes']['horn']=='recognized'
        assert shape(n['cnf'])==shape(target['cnf'])
        assert n['profile']['outcomes']['horn']=='excluded'
        polarities.append(dict(source_sha256=sha_key(key),target_sha256=sha_key(n['edge']['key']),
            shape=shape(n['cnf']),flipped_variables=len(n['polarity']['flipped']),
            source_outcomes=n['profile']['outcomes'],target_outcomes=target['profile']['outcomes']))
    summary=dict(passed=True,report_sha256=sha(out/'report.json'),reconstruction_sha256=sha(out/'reconstruction.json'),
        source_sha256=sha(__file__),current_findings_sha256=sha(current_path),previous_findings_sha256=sha(previous_path),
        prefix_reuse_by_previous_original=shared,polarity_transitions=polarities,
        unresolved_records_in_final_positive_proof=unresolved,
        case1062_across_both_discovery_checkpoints=lifetime,
        limitations=['These intersections cover touched branch prefixes only, not every global proof alternative or possible equivalent encoding.',
            'Reuse under the same original and source identity differs from transfer between unrelated formulas. A repeated shape or method is not a shared certificate.',
            'Polarity transitions preserve shape but need their checked literal transformation. They invoke existing Horn recognition, not a new tractable class.'])
    (out/'reuse-findings.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True,shared=[{k:v for k,v in x.items() if k!='shared_keys'}|dict(shared_nodes=len(x['shared_keys'])) for x in shared],polarity_shapes=[x['shape'] for x in polarities])))


if __name__=='__main__':analyze(Path(sys.argv[1]))

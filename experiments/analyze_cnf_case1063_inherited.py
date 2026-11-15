#!/usr/bin/env python3
"""Track inherited unresolved records in the expanded original-coverage proof.

Membership is measured; absence from an earlier positive certificate does not
establish that no earlier local derivation existed.
"""
import gzip
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_case1063_discovery import BASE, PRESERVATION, read_archive, sha, sha_key


def load(path):
    return json.loads(Path(path).read_text())


def analyze(out):
    report=load(out/'report.json');cold=load(out/'reconstruction.json')
    assert cold['passed'] and cold['report_sha256']==sha(out/'report.json')
    assert report['parent']==dict(path=str(BASE),sha256=sha(BASE))
    parent=load(BASE);validation=load(PRESERVATION)
    previous_path=BASE.parent/'reuse-findings.json'
    assert sha(previous_path)==validation['reuse_findings_sha256']
    previous={n['source_sha256']:n for n in load(previous_path)['unresolved_records']}
    before={step['source']:step for step in read_archive(parent['expanded_certificate'])['steps']}
    after={step['source']:step for step in read_archive(report['expanded_certificate'])['steps']}
    delta=parent['delta'];assert sha(delta['path'])==delta['sha256']
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'delta';path.write_bytes(gzip.decompress(Path(delta['path']).read_bytes()))
        assert sha(path)==delta['database_sha256']
        with sqlite3.connect(path) as db:
            nodes=[(key,json.loads(payload)) for key,payload in db.execute('SELECT id,payload FROM cnf_patterns_v1')]
    rows=[]
    for key,node in nodes:
        if node['kind']!='unresolved':continue
        digest=sha_key(key);old=previous[digest]
        assert old['in_final_positive_proof']==(key in before)
        step=after.get(key)
        rows.append(dict(source_sha256=digest,shape=old['shape'],stored_kind=node['kind'],
            in_previous_positive_proof=key in before,in_current_positive_proof=step is not None,
            current_rule=step['rule']['kind'] if step else None,current_premises=len(step['children']) if step else None))
    assert {n['source_sha256'] for n in rows}==set(previous)
    result=dict(passed=True,source_sha256=sha(__file__),report_sha256=sha(out/'report.json'),
        reconstruction_sha256=sha(out/'reconstruction.json'),previous_reuse_sha256=sha(previous_path),records=rows,
        newly_included=sum(not n['in_previous_positive_proof'] and n['in_current_positive_proof'] for n in rows),
        limitations=['This compares the saved positive original-coverage certificates, not every earlier local derivation.',
            'Immutable unresolved payloads remain unchanged; coverage comes from checked external composition.',
            'Reuse within a resumed original does not demonstrate shared nonterminal representations across distinct originals.'])
    (out/'inherited-findings.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    analyze(Path(sys.argv[1]))

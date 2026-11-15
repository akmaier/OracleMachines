#!/usr/bin/env python3
"""Bind the completed development subset and exhaustively audit small terminals.

This does not replay the entire historical corpus or evaluate fresh holdout inputs.
"""
import gzip
import itertools
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_case1196_discovery import read_archive, sha, sha_key
from experiments.cnf_residual_dag import holds

LEGACY=Path('experiments/results/cnf-retained-plans-full/report.json')
LEGACY_SHA='6b09f04a02286d4a9ca5ac692ea0bf4d7b481f90b2ce3c2fad9490aab42ddc32'


def load(path):
    return json.loads(Path(path).read_text())


def shape(cnf):
    return [len({abs(x) for c in cnf for x in c}),len(cnf),sum(map(len,cnf))]


def assignments(cnf):
    variables=sorted({abs(x) for c in cnf for x in c})
    assert len(variables)<=16, 'Deliberately bounded exhaustive diagnostic'
    for bits in itertools.product((False,True),repeat=len(variables)):
        yield dict(zip(variables,bits))


def analyze(out):
    started=time.perf_counter();report=load(out/'report.json');cold=load(out/'reconstruction.json')
    assert cold['passed'] and cold['report_sha256']==sha(out/'report.json')
    assert all(report['final_closed']) and read_archive(report['next_selection'])['source'] is None
    for source,digest in report['fingerprints'].items():assert sha(source)==digest
    assert sha(LEGACY)==LEGACY_SHA
    legacy=load(LEGACY);retained=[r for r in legacy['records'] if r['mode']=='retained']
    assert [r['case'] for r in retained]==list(range(len(legacy['cases'])))
    misses=[r['case'] for r in retained if not r['discovery']['summary']['closed']]
    assert misses==[c['original_case'] for c in report['cases']]
    assert all(c['source']==legacy['cases'][c['original_case']]['source'] for c in report['cases'])
    corpus=dict(legacy_path=str(LEGACY),legacy_sha256=LEGACY_SHA,legacy_sources=len(legacy['cases']),
        legacy_closed=sum(r['discovery']['summary']['closed'] for r in retained),
        legacy_misses=len(misses),exactly_matched_source_indices=misses,
        current_subset_closed=sum(report['final_closed']),legacy_options=legacy['options'],current_options=report['options'],
        complete_historical_corpus_replayed=False,new_holdout_evaluated=False)
    delta=report['delta'];assert sha(delta['path'])==delta['sha256']
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'delta';path.write_bytes(gzip.decompress(Path(delta['path']).read_bytes()))
        assert sha(path)==delta['database_sha256']
        with sqlite3.connect(path) as db:nodes={k:json.loads(p) for k,p in db.execute('SELECT id,payload FROM cnf_patterns_v1')}
    families=[];models={};polarities=[]
    for key,node in nodes.items():
        if node['kind']!='family':continue
        cnf=node['cnf'];variables={abs(x) for c in cnf for x in c}
        checks=dict(horn=all(sum(x>0 for x in c)<=1 for c in cnf),
            dual_horn=all(sum(x<0 for x in c)<=1 for c in cnf),two_cnf=all(len(c)<=2 for c in cnf),
            zero_valid=holds(cnf,{v:False for v in variables}),one_valid=holds(cnf,{v:True for v in variables}))
        assert all(node['profile']['outcomes'][name]==('recognized' if value else 'excluded') for name,value in checks.items())
        count=sum(holds(cnf,model) for model in assignments(cnf));models[key]=count
        families.append(dict(source_sha256=sha_key(key),shape=shape(cnf),checked_classification=checks,
            assignments=2**len(variables),satisfying_assignments=count))
    for key,node in nodes.items():
        if node['kind']!='polarity':continue
        child_key=node['edge']['key'];child=nodes[child_key];assert child['kind']=='family'
        names=node['edge']['names'];flipped=set(node['polarity']['flipped'])
        assert len(names)==len(set(names)) and set(names)=={abs(x) for c in node['cnf'] for x in c}
        source_count=0;checked=0
        for original in assignments(node['cnf']):
            transported={i:(not original[v]) if v in flipped else original[v] for i,v in enumerate(names,1)}
            before=holds(node['cnf'],original);after=holds(child['cnf'],transported)
            assert before==after;source_count+=before;checked+=1
        assert source_count==models[child_key]
        polarities.append(dict(source_sha256=sha_key(key),target_sha256=sha_key(child_key),shape=shape(node['cnf']),
            flipped_variables=len(flipped),assignments_checked=checked,satisfying_assignments=source_count))
    assert len(families)==4 and len(polarities)==2
    result=dict(passed=True,report_sha256=sha(out/'report.json'),reconstruction_sha256=sha(out/'reconstruction.json'),
        source_sha256=sha(__file__),corpus=corpus,families=families,polarities=polarities,
        diagnostic_seconds=time.perf_counter()-started,
        limitations=['The 83 formulas are adaptively reused development misses from the historical corpus, not new holdout cases.',
            'Exact input membership does not perform a fresh combined-policy replay of all 1497 historical sources or establish its resource cost.',
            'Exhaustive terminal and polarity checks are bounded diagnostics, not an efficient algorithm for arbitrary CNFs.',
            'These diagnostics do not establish shared nonterminal representations across different original inputs.'])
    (out/'completion-findings.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True,corpus={k:v for k,v in corpus.items() if k not in ['exactly_matched_source_indices','legacy_options','current_options']},
        families=families,polarities=polarities,diagnostic_seconds=result['diagnostic_seconds'])))


if __name__=='__main__':analyze(Path(sys.argv[1]))

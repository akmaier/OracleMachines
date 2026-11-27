"""Bind exact repair coverage, preserved evidence and fixed-policy failures."""
from collections import Counter
from pathlib import Path
import hashlib,json,re,time
from experiments import cnf_hamming_repair as e


def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def binding(path):return dict(path=str(path),sha256=sha(path))
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def boundaries(out):
    started=time.perf_counter();p=load(out/'constructed-protocol.json');r=load(out/'constructed-results.json')
    for file,h in p['files'].items():assert sha(file)==h
    assert r['passed'] and r['summary']==dict(sat=22,budget=10) and p['node_limit']==20000
    rows=load(out/'constructed-inputs.json');truth=load(out/'constructed-audit-witnesses.json')
    assert len(rows)==len(truth)==len(r['records'])==32
    for row,model,record in zip(rows,truth,r['records']):
        source=row['source'];assert e.previous.check(source,model)['answer']
        counts=Counter();seed=e.proposal(source,counts);got=e.search(source,seed,len(seed['names']),counts,node_limit=p['node_limit'])
        assert got==record['result'] and dict(counts)==record['counts'] and row['id']==record['id']
    assert sum(x['result']['witness'] is None and x['result']['diagnostic']['best_failed']==1 for x in r['records'])==5
    write(out/'boundary-reproduction.json',dict(passed=True,records=32,exact_results_and_counts_reproduced=True,seconds=time.perf_counter()-started,protocol=binding(out/'constructed-protocol.json'),results=binding(out/'constructed-results.json')))


def main(out,pages,inspected):
    a=load(out/'analysis.json');p=load(out/'protocol.json');g=load(out/'gap-diagnostics.json');audit=load(out/'semantic-audit.json');d=load(out/'distance-diagnostic.json')
    assert audit['passed'] and load(out/'audit-reproduction.json')['exact_semantic_records_reproduced']
    assert sum(v for k,v in audit['counts'].items() if k.endswith('_inputs'))==5108
    assert audit['counts']['ball_queries']==25629 and audit['counts']['sat_balls']==12500 and audit['counts']['excluded_balls']==13129
    assert len(audit['fresh_records'])==64 and audit['invalidated_witnesses']==audit['checked_reuses']==30
    assert a['gains']==['e007'] and a['remaining']==[]
    assert a['coverage']['baseline']['original']['certified']==24 and a['coverage']['repair']['original']['certified']==25
    assert sum(a['coverage']['repair'][kind]['certified'] for kind in ('edit','signed-permutation'))==12
    assert min(a['paired_percent'])<0<max(a['paired_percent'])
    assert d['minimum_distance']==26 and d['closed']['expanded']==35065 and d['witness']['distance']==26
    assert e.check_exclusion(d['source'],load(out/'radius-25-exclusion.json'))==dict(no_model_within_radius=True,radius=25,global_unsat=False)
    w=load(out/'distance-26-witness.json');assert e.previous.check(d['source'],w)['answer'] and sum(x!=y for x,y in zip(w['values'],d['seed']['values']))==26
    assert g['random_source']['minimum_distance']==26 and len(g['random_source']['initial_failed_variable_support'])==39
    assert g['random_source']['radius_25_node_kinds']==dict(clause=23495,blocked=4944,packing=6626)
    assert load(out/'boundary-reproduction.json')['exact_results_and_counts_reproduced']
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2505 tests in .*\n\nOK',full) and re.search(r'Ran 20 tests in .*\n\nOK',focused)
    for name in ('latex-reviewed.log','latex-final.log'):
        assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    checks=('semantic-audit','audit-reproduction','gap-diagnostics','distance-diagnostic','constructed-protocol','constructed-results','boundary-reproduction')
    supplemental=dict(passed=True,evidence={name:binding(out/(name+'.json')) for name in checks},truth_table_inputs=5108,ball_queries=25629,sat_balls=12500,excluded_balls=13129,budget_unknowns=2860,full_tests=2505,focused_tests=20,full_test_seconds=float(re.search(r'Ran 2505 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=83,added_proofs=1,clean_final_latex_passes=2),scope='Model checking and exclusion-DAG checking are independent of discovery. Radius exclusions are not global UNSAT unless they cover the full assignment space. Supplementary diagnosis and constructed probes are outside paired timings.')
    write(out/'supplemental-checks.json',supplemental)
    docs=['research/hamming-repair.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
    decision=dict(decision='Retain optional bounded exact repair: exposed original coverage 24/25 to 25/25, derived controls 12/12 unchanged, no lost verdict. Complete time roughly unchanged with mixed paired signs; no reliable speedup claim. Defaults unchanged.',coverage=a['coverage'],gains=a['gains'],remaining=a['remaining'],comparison_percent=a['comparison_percent'],paired_percent=a['paired_percent'],documents={name:sha(name) for name in docs},supplemental_checks=binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Analyze the ten new constructed repair-only budget misses without per-source cap tuning. Full-portfolio status of these sources is unmeasured. Freeze unseen external encodings before transfer claims; retain old nonclique/domain recognition failures.',next_cost_target='Reduce coupled interactions before general repair search; reuse checked conditional structure, source incidence and negative supports while accounting for invalidation, checking, mask growth, persistence and cold replay. No compact arbitrary-SAT acquisition bound follows.')
    write(out/'decision.json',decision)
    print(json.dumps(dict(passed=True,originals=25,derived_controls=12,minimum_distance=26,constructed_repair_budget_misses=10,prior_synthetic_union_unchanged=182)))


if __name__=='__main__':
    import sys
    if sys.argv[1]=='boundaries':boundaries(Path(sys.argv[2]))
    else:main(Path(sys.argv[1]),int(sys.argv[2]),list(map(int,sys.argv[3:])))

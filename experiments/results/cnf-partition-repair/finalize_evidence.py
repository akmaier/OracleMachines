"""Bind disjoint repair costs, independent checks and preserved counterexamples."""
from pathlib import Path
import hashlib,json,re
from experiments import cnf_partition_repair as e


def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def binding(path):return dict(path=str(path),sha256=sha(path))
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def main(out,pages,inspected):
    a=load(out/'analysis.json');p=load(out/'protocol.json');g=load(out/'gap-diagnostics.json');audit=load(out/'semantic-audit.json');d=load(out/'distance-diagnostic.json')
    assert audit['passed'] and load(out/'audit-reproduction.json')['exact_semantic_records_reproduced']
    assert sum(v for k,v in audit['counts'].items() if k.endswith('_inputs'))==5108
    assert audit['counts']['ball_queries']==25534 and audit['counts']['sat_balls']==12485 and audit['counts']['excluded_balls']==13049
    assert len(audit['fresh_records'])==64 and audit['invalidated_witnesses']==audit['checked_reuses']==39
    assert a['gains']==[3,9,19,22,23,28,30] and a['remaining']==[24,25,29]
    assert a['coverage']==dict(baseline=dict(sat=22,unresolved=10),partition=dict(sat=29,unresolved=3))
    assert a['states']==dict(baseline=274481,partition=118552) and all(v<0 for v in a['paired_percent'])
    assert d['minimum_distance']==26 and d['closed']['expanded']==4307 and d['witness']['expanded']==2076
    proof=load(out/'radius-25-exclusion.json');assert e.check_exclusion(d['source'],proof)==dict(no_model_within_radius=True,radius=25,global_unsat=False)
    w=load(out/'distance-26-witness.json');assert e.previous.check(d['source'],w)['answer'] and sum(x!=y for x,y in zip(w['values'],d['seed']['values']))==26
    assert g['negative_proof']['node_kinds']==dict(split=3225,blocked=695,packing=387)
    regression=load(out/'ordering-regression.json')['record'];source=regression['source'];seed=regression['seed'];radius=len(seed['names'])
    assert e.baseline.search(source,seed,radius)==regression['baseline'] and e.search(source,seed,radius)==regression['partition']
    assert e.search(source,seed,radius,node_limit=9)==regression['partition_at_cap'] and regression['partition_at_cap']['diagnostic']['reason']=='budget'
    assert regression['baseline']['diagnostic']['expanded']==9 and regression['partition']['diagnostic']['expanded']==13
    near=load(out/'near-models.json');assert near['passed'] and near['source_sha256']==sha(e.__file__)
    assert [r['id'] for r in near['records']]==[24,25,29]
    for record,expected in zip(near['records'],(1,1,5)):
        source=record['source'];names=record['seed']['names']
        for snap in record['snapshots']:
            model=dict(zip(names,snap['values']));bad=[i for i,c in enumerate(source) if not any(model[abs(v)]==(v>0) for v in c)]
            assert bad==snap['false_original'] and bad
        assert len(record['snapshots'][-1]['false_original'])==expected and len(names)==80 and len(source)==349
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2528 tests in .*\n\nOK',full) and re.search(r'Ran 23 tests in .*\n\nOK',focused)
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    checks=('semantic-audit','audit-reproduction','gap-diagnostics','distance-diagnostic','ordering-regression','near-models','eof-normalization')
    supplemental=dict(passed=True,evidence={name:binding(out/(name+'.json')) for name in checks},truth_table_inputs=5108,ball_queries=25534,sat_balls=12485,excluded_balls=13049,full_tests=2528,focused_tests=23,full_test_seconds=float(re.search(r'Ran 2528 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=84,added_proofs=1,clean_final_latex_passes=2),scope='Independent full-source models and radius exclusions certify outcomes. Disjoint solution partitions may change subsequent branch order; a retained 9-versus-13-state case forbids universal dominance. Rejected near models carry no SAT authority.')
    write(out/'supplemental-checks.json',supplemental)
    docs=['research/disjoint-repair-partitions.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
    decision=dict(decision='Retain optional disjoint repair: exposed constructed kernel coverage 22/32 to 29/32, no lost SAT answer; complete measured kernel cost 36.65 percent lower, all paired signs favorable. Storage increases with new witnesses. No production defaults or full portfolio changes.',coverage=a['coverage'],gains=a['gains'],remaining=a['remaining'],comparison_percent=a['comparison_percent'],paired_percent=a['paired_percent'],documents={name:sha(name) for name in docs},supplemental_checks=binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Investigate exact conditional interfaces and guarded reuse around retained rejected near models for IDs 24,25,29 at fixed caps. Full-portfolio status on this constructed panel is unmeasured; freeze new external encodings before transfer claims.',next_cost_target='Reduce coupled residual constraints and reuse checked negative supports without discarding flip/keep context. Disjointness does not imply uniformly fewer states, compact arbitrary-SAT proofs or polynomial expansion.')
    write(out/'decision.json',decision);print(json.dumps(dict(passed=True,constructed_sat=29,remaining=3,minimum_distance=26,prior_external_union_unchanged=37)))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]),int(sys.argv[2]),list(map(int,sys.argv[3:])))

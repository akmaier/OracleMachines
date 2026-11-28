from collections import Counter
from pathlib import Path
import gzip,hashlib,json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_resolution_learning as s
out=Path(__file__).parent;a=s.load(out/'analysis.json');p=s.load(out/'protocol.json');v=s.load(out/'validation.json')
assert v['passed'] and a['union_counts']==dict(sat=8,unsat=8) and len(a['gains'])==11 and a['remaining']==[]
assert a['states']==dict(baseline=236197,learning=111957)
assert a['coverage']['learning']==dict(original=dict(sat=4,unsat=4),**{'signed-permutation':dict(sat=2,unsat=2),'edit':dict(sat=2,unsat=2)})
full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
assert re.search(r'Ran 2618 tests in .*\n\nOK',full) and re.search(r'Ran 26 tests in .*\n\nOK',focused)
pages=int(sys.argv[1]);inspected=list(map(int,sys.argv[2:]))
for name in ('latex-reviewed.log','latex-final.log'):
    log=(out/name).read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',log,re.M) and f'({pages} pages,' in log
rows=s.source_rows(p);probes=[]
for record in s.load(out/'development-provenance.json')['records']:
    archive=record['archive'];assert s.sha(archive['path'])==archive['sha256'];raw=gzip.decompress(Path(archive['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==record['uncompressed_sha256']
    core=gzip.decompress(Path(record['source_archive']['path']).read_bytes());assert hashlib.sha256(core).hexdigest()==record['source_sha256']
    data=json.loads(raw);assert len(data['cases'])==16
    for row,c in zip(rows,data['cases']):assert row['id']==c['id'] and json.loads(s.encode(s.e.check_result(row['source'],c['proof'])))==c['result']
    if not record['initial']:
        assert data['source']['sha256']==record['source_sha256'] and Path('experiments/cnf_resolution_learning.py').read_bytes().startswith(core)
        for c,measured in zip(data['cases'],s.load(out/'learning-0/report.json')['cases']):assert c['diagnostic']==measured['diagnostic'] and c['counts']==measured['discovery_counts']
    probes.append(dict(initial=record['initial'],outcomes=dict(Counter(c['proof']['kind'] for c in data['cases'])),archive=archive))
assert len(probes)==2
knowledge=s.load(out/'knowledge.json')['records'];transport=s.load(out/'transport.json')['records'];assert len(knowledge)==len(transport)==16
assert sum(x['learned'] for x in knowledge)==51477 and sum(x['learned_propagations'] for x in knowledge)==78745 and sum(x['nonchronological_jumps'] for x in knowledge)==6481
for entry in transport:
    r=s.bound(entry);assert r['deleted_guard_rejected'] is True;s.e.check_result(r['target'],r['proof'])
assert Counter(x['kind'] for x in transport)==dict(unsat=8,unknown=8)
support=[];widths=[]
for row,entry in zip(rows,transport):
    proof=s.load(out/'learning-0'/(row['id']+'.json'))['proof'];n=len(s.e.prior.prior.previous.capacity.canonical(row['source'],Counter()));guards=set()
    for start,steps,clause in proof['derivations']:
        widths.append(len(clause))
        if start<n:guards.add(start)
        guards.update(parent for _,parent in steps if parent<n)
    assert len(guards)==entry['guards']
    support.append(dict(id=row['id'],source_clauses=n,distinct_source_guards=len(guards),source_fraction=len(guards)/n))
import statistics
profile=dict(records=support,learned_width_median=statistics.median(widths),learned_width_max=max(widths),min_guard_fraction=min(x['source_fraction'] for x in support),max_guard_fraction=max(x['source_fraction'] for x in support),scope='Union of actually referenced original premises for each complete retained collection; not minimal support for individual learned clauses.')
assert profile['learned_width_median']==14 and profile['learned_width_max']==36 and profile['min_guard_fraction']==582/645 and profile['max_guard_fraction']==1
s.write(out/'support-profile.json',profile)
semantic=s.load(out/'semantic-audit-final.json');assert semantic==s.load(out/'semantic-audit-reproduced.json')
supp=dict(passed=True,development_proofs_checked=probes,semantic=semantic['counts'],guarded_transport_records=16,guarded_unsat=8,guarded_unknown=8,missing_guard_rejections=16,full_tests=2618,focused_tests=26,full_test_seconds=float(re.search(r'Ran 2618 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,initial_validation_setup_failure_preserved=True,support_profile=s.binding(out/'support-profile.json'),manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=88,added_proofs=1,clean_final_latex_passes=2),scope='Development proofs checked but initial search not rerun; final matched search and semantic audit reproduced. Transport timings are separate audit measurements, not fresh-acquisition speedup estimates.')
s.write(out/'supplemental-checks.json',supp)
docs=['research/checked-conflict-learning.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
s.write(out/'decision.json',dict(decision='Retain checked first-UIP learning and guarded premise transport. All eleven exposed larger-input gaps close, reaching 16/16 with eight checked refutations; growing propagation and proof costs remain explicit.',coverage=a['coverage'],union_counts=a['union_counts'],comparison_percent=a['comparison_percent'],documents={f:s.sha(f) for f in docs},supplemental_checks=s.binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Freeze unseen transfer after this policy change and investigate reusable shared interfaces, rather than treating finite panel closure as efficient arbitrary CNF coverage.',next_cost_target='Separate necessary proof retention from the growing active propagation index; retain still-valid derivation subsets when source premises disappear, and measure their useful-edit coverage without weakening source guards.'))
print(s.encode(dict(passed=True,coverage=16,gaps_closed=11,checked_negative_transports=8,full_tests=2618)))

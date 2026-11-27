"""Bind external-input audits, diagnostic census and reviewed documentation."""
from collections import Counter,defaultdict
from pathlib import Path
import json,re,statistics
from experiments import compare_cnf_external_cutsets as s
base=s.base;old=s.old


def main(out,pages,inspected):
    a=base.load(out/'analysis.json');p=base.load(out/'protocol.json');inputs=base.load(out/'input-audit.json');g=base.load(out/'gap-diagnostics.json');desc=old.bound(p['descriptions']);reports={m:[base.load(out/f'{m}-{i}'/'report.json') for i in range(4)] for m in s.MODES}
    assert inputs['passed'] and inputs['raw_files_independently_parsed']==37 and inputs['rejected_malformed_inputs']==148 and len(inputs['signed_bijections'])==6
    groups=defaultdict(lambda:dict(baseline=0.,expanded=0.));status=Counter();reasons=Counter();obstructions=Counter();records=[]
    for j,case in enumerate(reports['expanded'][0]['cases']):
        d=desc[case['id']];key=d['kind']+':'+d['group']
        for mode in reports:groups[key][mode]+=statistics.mean(r['cases'][j]['acquisition_seconds'] for r in reports[mode])
        proof=base.load(out/'expanded-0'/(case['id']+'.json'))
        for attempt,diag in zip(proof['attempts'],case['diagnostic']['expansion']):
            cert=attempt['certificate'];status['attempts']+=1;reasons[diag['reason']]+=1
            if cert is None:continue
            for entry,fd in zip(cert['entries'],diag['diagnostic']['factors']):
                factor=entry['certificate'];n=len(factor['scope']);st=factor['status'];status['factors_'+st]+=1
                if st!='cover':
                    single_false=(1<<n)-factor['bits'].bit_count()==1
                    obstructions[st]+=1;obstructions[st+'_single_false']+=single_false;obstructions[st+'_scope_'+str(n)]+=1
                    records.append(dict(id=case['id'],target=attempt['target'],factor=entry['index'],status=st,scope_size=n,single_excluded_assignment=single_false,reason=fd['reason'],spent=fd['spent']))
            for branch,bd in zip(cert['branches'],diag['diagnostic']['branches']):
                status['branch_'+(branch['terminal']['status'] if branch['terminal'] else 'unresolved')]+=1;reasons['branch_'+bd['reason']]+=1
    assert dict(groups)==g['acquisition_by_stratum'] and dict(status)==g['expansion'] and dict(reasons)==g['reasons'] and dict(obstructions)==g['noncover_factor_summary'] and records==g['noncover_factors']
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2447 tests in .*\n\nOK',full) and re.search(r'Ran 16 tests in .*\n\nOK',focused)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    assert all(x>0 for x in a['paired_percent'])
    supplemental=dict(passed=True,input_audit=old.binding(out/'input-audit.json'),input_audit_reproduction=old.binding(out/'audit_input_transport.py'),gap_diagnostics=old.binding(out/'gap-diagnostics.json'),gap_diagnostics_recomputed=True,selection=old.binding(out/'selection.json'),source_acquisition=old.binding(out/'acquisition.json'),originals=25,derived_controls=12,old_synthetic_union_unchanged=182,full_tests=2447,focused_tests=16,full_test_seconds=float(re.search(r'Ran 2447 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=82,added_proofs=0,clean_latex_passes=2),scope='Raw-source and diagnostic audits are outside matched timing. Publisher labels are never proof authority; the external and derived denominators stay separate from the old synthetic union.')
    base.write(out/'supplemental-checks.json',supplemental)
    docs=['research/external-cutset-audit.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
    decision=dict(decision='Retain a frozen external-input audit and fixed-policy adapter: original SATLIB coverage 17/25 to 19/25, derived controls 10/12 unchanged, no lost certificate. Expanded workflow costs 123.95 percent more; preserve all unresolved inputs and unchanged defaults.',coverage=a['coverage'],gains=a['gains'],remaining=a['remaining'],comparison_percent=a['comparison_percent'],paired_percent=a['paired_percent'],documents={x:base.sha(x) for x in docs},supplemental_checks=old.binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Recognize CNF-derived global capacity/injectivity deficiency, using a compact checked matching/Hall-style core. Five of six unresolved originals are pigeonhole inputs. Test renamed, edited and mixed clauses without consulting metadata; no implemented new authority claimed here.',next_cost_target='Direct classification of wide single-clause factors and heterogeneous exact representations are supporting work; repeated validated source/context preparation remains a workflow cost target. Charge construction, invalidation, conversions, model transport and cold replay. Current observations do not quantify attainable savings.')
    base.write(out/'decision.json',decision);print(base.encode(dict(passed=True,originals=25,derived=12,unresolved_originals=6,old_synthetic_union_unchanged=182)))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]),int(sys.argv[2]),list(map(int,sys.argv[3:])))

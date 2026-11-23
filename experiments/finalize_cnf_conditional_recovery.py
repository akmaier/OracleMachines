#!/usr/bin/env python3
"""Seal guarded recovery with retained regressions and cheap-pool evidence."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditional_recovery as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==1080 and v['previous_partition_records']==342 and v['partition_records']==0
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(141,12521)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==804
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='c5945963'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1519 tests in .*\n\nOK',full) and re.search(r'Ran 227 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))};assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],*([x for x in cp['conditional_recovery'].values() if isinstance(x,dict) and 'sha256' in x])):assert base.sha(b['path'])==b['sha256']
    analysis=base.load(out/'analysis.json')
    analysis['next_target']='Preserve checked negative-core and witness-pool hits before recovery preparation; then compare full native reconstruction with existing checked guard composition.'
    analysis['cheap_pool_regressions']=[dict(case=r['case'],template=r['template'],status=r['status'],before_seconds=r['before_seconds'],after_seconds=r['after_seconds'],before_metrics=r['before_metrics'],after_metrics=r['after_metrics']) for r in analysis['query_comparisons'] if r['recovery'] is not None and (r['before_metrics'].get('negative_hits',0) or r['before_metrics'].get('witness_hits',0))]
    assert {(r['case'],r['template']) for r in analysis['cheap_pool_regressions']}=={(11,4),(12,3),(12,4),(13,4),(14,4)}
    base.write(out/'analysis.json',analysis);cp['conditional_recovery']['analysis']=study.binding(out/'analysis.json')
    cp['source_fingerprints']=sources;base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=797,final_sources=804,prior_artifacts=12521,prior_manifests=141,
        full_tests=1519,focused_tests=227,warnings=warnings,warning_sites=dict(sites),manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+base.load(out/'gate-protocol.json')['limitations']+v['limitations']+base.load(out/'analysis.json')['limitations']+[
            'Recovery remains optional: fewer expansions do not repay full reconstruction on this workload. Existing negative-core and witness hits are the next priority.',
            'Full-suite unclosed SQLite warnings are retained; collection sites need not be allocation sites. Focused tests close their own databases. No new Lean refinement theorem.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=12521+len(files),next_manifests=142,final_sources=804,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))

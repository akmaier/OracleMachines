#!/usr/bin/env python3
"""Seal the supplied-candidate partition pilot after tests and paper build."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_transported_partition as study
base=study.base
EXTRA=('experiments/validate_cnf_transported_partition.py','experiments/analyze_cnf_transported_partition.py','experiments/finalize_cnf_transported_partition.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and len(parent['source_fingerprints'])==684
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(126,8539)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**p['source_fingerprints'],**{f:base.sha(f) for f in EXTRA}}
    assert len(sources)==690
    for f,h in sources.items():assert base.sha(f)==h,f
    assert v['query_audits']==90 and v['old_composed_records']==5650 and v['old_pilot_records']==444 and v['old_inventory_nodes']==624
    assert v['old_stream_counts']==dict(witness_pool_study=864,negative_edit_pool_study=864,support_plan_study=1296,affine_probe_study=1296,partial_residual_study=864,residual_transport_study=720)
    assert v['prior_tables']['cnf_residual_v1']==73835 and v['prior_tables']['cnf_affine_negative_v1']==71
    for t,n in v['preserved_tables'].items():assert n==v['prior_tables'][t]+v['new_records'].get(t,0)
    for field in parent:
        if field not in ('parent_checkpoint','reference_union','source_fingerprints'):assert cp[field]==parent[field],field
    for b in (cp['reference_union'],cp['transported_partition_study']['partitions']):assert base.sha(b['path'])==b['sha256']
    analysis=base.load(out/'analysis.json');report=base.load(out/'report.json');assert len(report['samples'])==60
    boundary=base.load(out/'next-boundary.json');source=study.bound(boundary['source_report'])
    assert boundary['allowed_addition_ids']==study.bound(source['queries'])[0]['new_ids']
    assert len(boundary['support']['missing'])==6 and boundary['solver_counts'].get('expanded_nodes',0)==0
    assert [a['terminal'] for a in boundary['attempts']]==[4,4]
    for sample in report['samples']:
        data=study.bound(sample);study.bound(data['queries']);study.bound(data['partitions']);study.read_zip(data['delta'])
    # The experiment adds checked compositions, not new mathematical proof blocks.
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','72ac6ef'],text=True).strip()
    before=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1378 tests in .*\n\nOK',full)
    match=re.search(r'Ran (\d+) tests in .*\n\nOK',focused);assert match and int(match[1])>=12
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))};assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    assert not any('cnf_transported_partition' in line for line in sites)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    cp['source_fingerprints']=sources;cp['transported_partition_study']['analysis']=study.binding(out/'analysis.json')
    cp['transported_partition_study']['next_boundary']=study.binding(out/'next-boundary.json')
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=684,final_sources=690,prior_artifacts=8539,prior_manifests=126,
        full_tests=1378,focused_tests=int(match[1]),warnings=warnings,warning_sites=dict(sites),proof_blocks_unchanged=64,manuscript_pages=pages,
        paper_sha256=base.sha(paper),source_fingerprints=sources,final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+analysis['limitations']+boundary['limitations']+[
            'The first unit-test run used an internal tuple where a canonical certificate requires JSON lists. Its failure log and source are retained; the test fixture was corrected before any timed protocol ran.',
            'Python wrapper and composition tests plus independent native/sidecar replay are not a Lean refinement proof. All prior64 manuscript proof blocks remain unchanged.',
            'The cumulative union retains every earlier authoritative payload. Different valid trial proofs remain in delta archives. Reuse a partition sidecar through PartitionBank; native lookup alone need not know the target.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8539+len(files),next_manifests=127,final_sources=690,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)

if __name__=='__main__':finalize(Path(sys.argv[1]))

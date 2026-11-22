#!/usr/bin/env python3
"""Seal the probe/six-clause experiment without changing prior artifacts."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probed_partition as study
base=study.base
EXTRA=('experiments/validate_cnf_probed_partition.py','experiments/analyze_cnf_probed_partition.py','experiments/finalize_cnf_probed_partition.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');analysis=base.load(out/'analysis.json')
    assert v['passed'] and len(parent['source_fingerprints'])==690
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(127,8866)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**p['source_fingerprints'],**{f:base.sha(f) for f in EXTRA}};assert len(sources)==696
    for f,h in sources.items():assert base.sha(f)==h,f
    assert v['query_audits']==90 and v['previous_partition_records']==36 and v['old_composed_records']==5650
    assert v['prior_tables']['cnf_residual_v1']==74204 and v['prior_tables']['cnf_affine_negative_v1']==71
    for t,n in v['preserved_tables'].items():assert n==v['prior_tables'][t]+v['new_records'].get(t,0)
    for field in parent:
        if field not in ('parent_checkpoint','reference_union','source_fingerprints'):assert cp[field]==parent[field],field
    for b in (cp['reference_union'],cp['probed_partition_study']['partitions']):assert base.sha(b['path'])==b['sha256']
    report=base.load(out/'report.json');assert len(report['samples'])==60
    for sample in report['samples']:
        data=study.bound(sample);study.bound(data['queries']);study.bound(data['partitions']);study.read_zip(data['delta'])
    branch=base.load(out/'next-branch.json');br=study.bound(branch['trial_report']);query=study.bound(br['queries'])[0]
    assert branch['extra_count']==5 and branch['measured_branch_expansions']==61
    assert query['branches'][branch['branch']]['result']['root']==branch['root']
    assert branch['extra_ids']==query['new_ids'][study.TABLES[0]][:5]
    assert branch['reader_counts'].get('expanded_nodes',0)==0 and branch['screen']['conflict'] is None
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','8ce2758'],text=True).strip()
    before=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1388 tests in .*\n\nOK',full) and re.search(r'Ran 70 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))};assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M);pages=int(re.search(r'\((\d+) pages,',latex)[1])
    cp['source_fingerprints']=sources;cp['probed_partition_study']['analysis']=study.binding(out/'analysis.json')
    cp['probed_partition_study']['next_branch']=study.binding(out/'next-branch.json');base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=690,final_sources=696,prior_artifacts=8866,prior_manifests=127,
        full_tests=1388,focused_tests=70,warnings=warnings,warning_sites=dict(sites),proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+analysis['limitations']+analysis['reuse']['limitations']+branch['limitations']+[
            'ResourceWarning sites can be collection sites, not allocation sites. Record full-suite warnings separately; focused tests must emit none.',
            'Two initial test fixtures assumed symmetric complete cubes would require many fresh nodes. Canonical residual sharing closes them sooner. The fixture failures and source are retained; asymmetric/deeper fixtures exercise the intended budget stops without changing the kernel.',
            'Both native readers recheck every cumulative native/affine/equivalence record and all old/new partition records. The earlier5650 composed records are replayed; other unchanged historical observation/inventory audits remain bound to the preceding validation manifest.',
            'The cumulative union retains every earlier authoritative payload. Alternative trial proofs remain in delta archives. The Python adapter has unit tests and independent replay, not a Lean refinement theorem.'])
    base.write(out/'checks.json',checks);files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8866+len(files),next_manifests=128,final_sources=696,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)

if __name__=='__main__':finalize(Path(sys.argv[1]))

#!/usr/bin/env python3
"""Seal canonical-clause probe preparation and its remaining structural frontier."""
from collections import Counter
from pathlib import Path
import re, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_ordered_probe as study
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_residual_dag import normalize
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json'); v=base.load(out/'validation.json')
    cp=base.load(out/'checkpoint.json'); a=base.load(out/'analysis.json')['summary']
    assert v['passed'] and v['query_audits']==1728 and v['previous_partition_records']==342
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(152,13461)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],
        'experiments/profile_cnf_ordered_probe.py':base.sha('experiments/profile_cnf_ordered_probe.py'),
        'experiments/inspect_cnf_probe_frontier.py':base.sha('experiments/inspect_cnf_probe_frontier.py'),
        'experiments/finalize_cnf_ordered_probe.py':base.sha(__file__)}
    assert len(sources)==872
    for f,h in sources.items():assert base.sha(f)==h,f
    head='5460b939';paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full,focused=[(out/f).read_text() for f in ('full-tests.log','focused-tests.log')]
    assert re.search(r'Ran 1628 tests in .*\n\nOK',full)
    assert re.search(r'Ran 37 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    pairs=[];coverage={}
    for split in study.SPLITS:
        cases=study.bound(p['cases'][split]); coverage[split]={}
        for mode in study.MODES:
            rows=base.load(out/f'{split}-{mode}-0/queries.json')
            roots={c['root'] for c,r in zip(cases,rows) if r['result'] is not None}
            allroots={c['root'] for c in cases}
            coverage[split][mode]=dict(completed_distinct_roots=len(roots),distinct_roots=len(allroots),
                unresolved_distinct_roots=sorted(allroots-roots),statuses=dict(Counter(r['status'] for r in rows)))
            assert len(roots)==(47 if split=='exposed' else (38 if mode=='current' else 39))
        assert coverage[split]['lookahead']['unresolved_distinct_roots']==coverage[split]['ordered']['unresolved_distinct_roots']
        for repeat in range(4):
            x,y=[base.load(out/f'{split}-{mode}-{repeat}/report.json')['summary'] for mode in ('lookahead','ordered')]
            pairs.append(dict(split=split,repeat=repeat,query_change=y['query_seconds']/x['query_seconds']-1,
                worker_change=y['complete_worker_seconds']/x['complete_worker_seconds']-1))
    assert len(v['equivalent_pairs'])==576
    for split in study.SPLITS:
        x,y=a[split]['lookahead'],a[split]['ordered']
        for k in ('native_nodes','native_payload','native_digest','extension_digest','affine_digest','checked_python_bytes'):
            assert x[k]==y[k],k
        assert x['counters']['expanded_nodes']==y['counters']['expanded_nodes']
        assert x['counters']['normalization_literal_visits']-y['counters']['normalization_literal_visits']==y['counters']['ordered_probe_reused_literals']
    inspection=base.load(out/'frontier-inspection.json');cases=study.bound(p['cases']['holdout'])
    for r in inspection['records']:
        cnf,names=normalize(cases[r['case']]['source'])
        assert check_affine(cnf,r['affine'],Counter())==r['summary']
        assert len(names)-r['summary']['rank']==r['free']
    assert len(inspection['records'])==9
    assert len([r for r in inspection['records'] if r['summary']['equation_count']])==1
    oldrows,newrows=[base.load(out/f'holdout-{mode}-0/queries.json') for mode in ('current','ordered')]
    assert oldrows[70]['status']=='unresolved' and newrows[70]['status']=='unsat'
    profile=base.load(out/'profiling.json');assert len(profile['records'])==6
    for r in profile['records']:
        assert base.sha(r['profile']['path'])==r['profile']['sha256']
        row=base.load(out/f"{r['split']}-{r['mode']}-0/queries.json")[r['case']]
        assert (row['status'],row['metrics'])==(r['result']['status'],r['result']['metrics'])
    frontier=dict(protocol=study.binding(out/'protocol.json'),analysis=study.binding(out/'analysis.json'),
        profiling=study.binding(out/'profiling.json'),inspection=study.binding(out/'frontier-inspection.json'),coverage=coverage,pairs=pairs,
        cases=[dict(case=cases[i],current=oldrows[i],ordered=newrows[i]) for i in (0,1,36,37,43,70)],
        decision='Retain as an optional preparation specialization. Same search and certificates as whole lookahead; evaluate measured local gains separately from its overall discovery overhead.',
        next_question='Use the checked affine description of unresolved holdout case 43 to test existing completion/projection machinery against its leftover clauses. Preserve the eight unresolved roots with no extracted equations. Further local preparation savings cannot substitute for useful structural reasoning.',
        relevant_sources=['experiments/cnf_affine_completion.py','experiments/cnf_affine_projection.py','experiments/cnf_affine_clause.py','experiments/cnf_affine_negative.py'],
        limitations=p['limitations']+profile['limitations']+inspection['limitations']+[
            'On the fresh holdout, lookahead/ordered complete 39/48 distinct roots against current 38/48. Preparation specialization changes no coverage; the extra shared-mixture refutation comes from the existing lookahead policy.',
            'General-normalizer literal visits removed are not total visits eliminated: specialized support and remapping passes remain explicitly charged.',
            'Trusted private preparation assumes canonical parents and the order-preserving scanning restriction used in these workers; it is not an unchecked normalizer for external input or a contract for arbitrary replacement restriction engines.',
            'Full-suite SQLite ResourceWarnings are pre-existing; focused tests have none. All 64 prior proof environments are unchanged.',
            'Development failures are retained: counters reset per query, and a cached affine-extension result is not a native cached negative. The corrected tests use cumulative preparation counts and an actual native certificate.'])
    base.write(out/'next-target.json',frontier)
    cp['source_fingerprints']=sources
    cp['ordered_probe'].update(next_target=study.binding(out/'next-target.json'),
        profile=study.binding(out/'profiling.json'),decision=frontier['decision'])
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=865,final_sources=len(sources),
        prior_artifacts=13461,prior_manifests=152,full_tests=1628,focused_tests=37,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out/'checkpoint.json'),limitations=frontier['limitations']+v['limitations']))
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=13461+len(files),next_manifests=153,
        sources=len(sources),pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))

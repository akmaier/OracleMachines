#!/usr/bin/env python3
"""Seal bounded affine probe results, preserved histories and resource limits."""
from collections import Counter
from pathlib import Path
import json,re,sqlite3,subprocess,sys,sysconfig,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_probe_safe as study
from experiments.cnf_residual_dag import normalize,token
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_affine_negative import check_negative
base=study.base
POSTHOC=('experiments/validate_cnf_affine_probe.py','experiments/finalize_cnf_affine_probe.py')


def check_frontier(out,p):
    f=base.load(out/'residual-frontier.json');cases=study.bound(f['cases']);queries=study.bound(f['queries'])
    assert f['cases']==p['cases']['holdout'] and len(f['records'])==len(cases)==len(queries)==108
    for c,r,q in zip(cases,f['records'],queries,strict=True):
        cnf,names=normalize(c['source']);assert r['root']==c['root']==token(cnf,Counter()) and r['case']==c['case']
        summary=check_affine(cnf,r['certificate'],Counter());assert summary==r['summary']
        assert r['free_variables']==len(names)-summary['rank'] and r['status']==q['status']
    assert f['unresolved_cases']==[c['case'] for c,q in zip(cases,queries) if q['status']=='unresolved']
    assert f['low_dimension_unknowns']==[r['case'] for r in f['records'] if r['status']=='unresolved' and not r['summary']['inconsistent'] and r['free_variables']<=8]
    return dict(inputs=108,unresolved=f['unresolved_cases'],low_dimension=f['low_dimension_unknowns'])


def common_warm(out,report):
    """Compare the same completed cases; overall warm cohort sizes differ."""
    result={}
    for split in report['summary']:
        result[split]={m:[] for m in ('pool','plan')}
        for repeat in (0,1):
            warm={m:{r['case']:r for r in base.load(Path(next(s for s in report['samples'] if s['split']==split and s['repeat']==repeat and s['mode']==m)['path']).parent/'warm.json')} for m in study.MODES}
            for m in result[split]:
                common=sorted(warm[m].keys() & warm['probe'].keys())
                result[split][m].append(dict(cases=common,baseline_solve_seconds=sum(warm[m][k]['solve_seconds'] for k in common),probe_solve_seconds=sum(warm['probe'][k]['solve_seconds'] for k in common)))
    base.write(out/'common-warm.json',result)
    return result


def partial_search_frontier(out,report):
    sample=next(s for s in report['samples'] if (s['split'],s['mode'],s['repeat'])==('holdout','probe',0))
    data=study.bound(sample);rows=study.bound(data['queries']);cases=base.load(out/'holdout-cases.json');records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';base.restore_archive(data['archive'],path);con=sqlite3.connect(path)
        try:
            available={key for table in study.TABLES for key, in con.execute(f'SELECT id FROM {table}')}
            for c,r in zip(cases,rows,strict=True):
                if r['status']!='unresolved':continue
                answers=Counter();kinds=Counter();small=0
                for key in r['new_ids']['cnf_residual_v1']:
                    node=json.loads(con.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone()[0])
                    answers[node['answer']]+=1
                    if node['answer'] is False:
                        kinds[node['proof']['kind']]+=1
                        small+=int(sum(map(len,node['cnf']))<=4096 and node['cnf']!=[[]])
                records.append(dict(case=c['case'],family=c['family'],variant=c['variant'],root=c['root'],seconds=r['seconds'],
                    committed_negative=answers[False],committed_positive=answers[True],negative_kinds=dict(kinds),
                    small_negative_candidates=small,root_known_at_end=c['root'] in available,
                    discarded_pending=r['metrics'].get('batch_discarded_checks_records',0)))
        finally:con.close()
    missing={c['root'] for c in cases if c['root'] not in available};baseline_roots={}
    for mode in ('pool','plan'):
        entry=next(s for s in report['samples'] if (s['split'],s['mode'],s['repeat'])==('holdout',mode,0))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';base.restore_archive(study.bound(entry)['archive'],path);con=sqlite3.connect(path)
            try:
                absent={c['root'] for c in cases if all(con.execute(f'SELECT 1 FROM {table} WHERE id=?',(c['root'],)).fetchone() is None for table in study.TABLES)}
            finally:con.close()
        baseline_roots[mode]=dict(missing_distinct_roots=len(absent),newly_available=len(absent-missing),newly_missing=len(missing-absent))
    result=dict(archive=data['archive'],records=records,baseline_roots=baseline_roots,
        missing_distinct_roots=len(missing),
        negative_records=sum(r['committed_negative'] for r in records),small_candidates=sum(r['small_negative_candidates'] for r in records),
        unknown_query_seconds=sum(r['seconds'] for r in records),limitations=[
        'Committed proofs refute their canonical residual CNFs, not their unconditioned source queries. Source/assumption transport or checked containment at the current residual is required.',
        'Literal-size eligibility alone does not predict retrieval cost or useful reuse. Exact residual reuse is already present; this is evidence for a bounded broader candidate policy, not a measured additional saving.'])
    base.write(out/'partial-search-frontier.json',result)
    return {k:v for k,v in result.items() if k not in ('archive','records','limitations')}


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    assert len(parent['source_fingerprints'])==664 and v['passed']
    for ledger in (parent['source_fingerprints'],p['source_fingerprints'],v['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(123,8332)
    assert (v['query_audits'],v['old_composed_records'],v['old_pilot_records'],v['old_larger_queries'],v['old_inventory_nodes'],v['old_witness_observations'],v['old_negative_observations'],v['old_support_plan_observations'])==(1296,5650,444,108,624,864,864,1296)
    assert v['list_only_comparisons']==1296
    assert v['tiny']['formulas']==512 and v['tiny']['statuses']==dict(sat=95,unsat=417)
    assert v['prior_tables']['cnf_residual_v1']==45061 and v['prior_tables']['cnf_affine_negative_v1']==26
    for t,n in v['preserved_tables'].items():assert n==v['prior_tables'][t]+v['new_records'].get(t,0)
    assert v['novelty']['holdout']==dict(distinct_roots=72,known_queries=0,queries=108)
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    for sample in report['samples']:
        data=study.bound(sample);study.bound(data['queries']);assert base.sha(data['archive']['path'])==data['archive']['sha256']
        if sample['mode'] in ('plan','probe'):
            assert data['summary']['negative_peak_entries']<=16 and data['summary']['negative_peak_literals']<=16*4096
            assert data['reconstruction']['negative_seed_entries']==0
    analysis=base.load(out/'analysis.json')
    for split,arms in report['summary'].items():
        for mode,arm in arms.items():
            assert sum(arm['statuses'].values())==108
            if mode!='probe':assert arm['affine_nodes']==0
        assert arms['probe']['counters'].get('affine_probe_conflicts',0)==arms['probe']['affine_nodes']
        assert arms['probe']['affine_nodes']>0
        assert arms['probe']['plan_peak_bytes']<=p['plan_byte_limit']
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==672
    frontier=check_frontier(out,p)
    warm=common_warm(out,report)
    partial=partial_search_frontier(out,report)
    cp=base.load(out/'checkpoint.json')
    for field in ('larger_mixtures','witness_pool_study','negative_edit_pool_study','support_plan_study'):assert cp[field]==parent[field]
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    cp['affine_probe_study']['common_warm']=study.binding(out/'common-warm.json')
    cp['affine_probe_study']['partial_frontier']=study.binding(out/'partial-search-frontier.json')
    cp['source_fingerprints']=sources
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','be570b0'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1347 tests in .*\n\nOK',full) and re.search(r'Ran 208 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    def sites(text):return Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in text.splitlines() if 'ResourceWarning: unclosed database' in line)
    current=sites(full);repo=str(Path.cwd())+'/';stdlib=Path(sysconfig.get_path('stdlib')).resolve()
    warning_origins=Counter()
    for site in current:
        filename=site.split(':',1)[0]
        if filename.startswith(repo):
            assert filename[len(repo):] in parent['source_fingerprints'];warning_origins['unchanged_project_files']+=current[site]
        else:
            # GC reports where collection occurs, not necessarily where a DB
            # was opened. Retain new stdlib sites rather than misattribute them.
            assert Path(filename).resolve().is_relative_to(stdlib);warning_origins['stdlib_collection_sites']+=current[site]
    assert warnings['focused']==0
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M);pages=int(re.search(r'\((\d+) pages,',latex)[1])
    base.write(out/'checkpoint.json',cp)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=664,final_sources=672,prior_artifacts=8332,prior_manifests=123,
        full_tests=1347,focused_tests=208,exhaustive_formulas=512,warnings=warnings,warning_sites=dict(current),warning_origins=dict(warning_origins),
        proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),final_union_tables=v['preserved_tables'],frontier=frontier,partial_frontier=partial,
        source_fingerprints=sources,final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=['The original reusable-sequence kernel consumed one-shot outer iterators before fallback. A separate adapter snapshots finite outer/inner inputs; all twelve workers were rerun including this cost. Original runs and identical proof/outcome comparisons remain preserved.',
        'Bounded top-level direct-XOR contradiction discovery uses the existing separate authority. Native certificates still have only native dependencies.',
        'Only normalized source size and discovery row XORs are capped; canonicalization, exact stored-proof checking, publication, fallback, full cache and stream storage are not capped by this probe.',
        'A consistent/incomplete/budget-stopped subsystem gives no verdict for the remaining CNF. No uniform polynomial arbitrary-SAT result or complete tractable taxonomy follows.',
        'Two mode orders on six designed generators, including a fresh larger holdout, do not establish representative performance. Sidecars, setup, misses, checking, persistence and cold replay are charged as documented.',
        'The all-input residual frontier is posthoc and does not change timed decisions. Earlier unknown observations remain valid historical observations.',
        'Initial test fixtures incorrectly expected a fresh miss for an already cached root and a stop at exactly the sufficient XOR budget. Failed test source/log are retained; independent fixtures now exercise both conditions.',
        'SQLite ResourceWarnings and their sites are retained in this record. Focused tests emit none.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8332+len(files),next_manifests=124,final_sources=672,pages=pages,warnings=warnings,frontier=frontier)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))

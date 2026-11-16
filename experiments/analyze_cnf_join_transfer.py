#!/usr/bin/env python3
"""Post-hoc attribution for the frozen matched-history experiment, no solving."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_join_transfer as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');seeds=base.load(out/'seeds.json');cases=base.load(out/'cases.json')
    trials={m:[base.load(s['path']) for s in report['samples'] if s['mode']==m] for m in study.MODES}
    a,b=(trials[m][0] for m in study.MODES);records=[]
    for c,x,y in zip(cases,a['records'],b['records'],strict=False):
        assert x['case']==y['case']==c['case'] and not x['visit'] and not y['visit']
        assert x['proof']==y['proof'],c['case']
        records.append(dict(case=c['case'],anchor_variables=c['anchor_variables'],variant=c['variant'],edited=c['edited'],
            base_stored=x['stored'],joins_stored=y['stored'],base_probes=x['probes'],joins_probes=y['probes'],
            saved_patterns=x['stored']-y['stored'],saved_probes=x['probes']-y['probes'],
            anchor_entries=y['join_entries'],shared_steps=y['join_steps'],identical_proof=True))
    groups=[]
    for n in sorted({c['anchor_variables'] for c in cases}):
        for edited in (False,True):
            selected=[r for r in records if r['anchor_variables']==n and r['edited']==edited]
            groups.append(dict(anchor_variables=n,edited=edited,queries=len(selected),
                **{k:sum(r[k] for r in selected) for k in ('base_stored','joins_stored','base_probes','joins_probes','saved_patterns','saved_probes')}))
    with tempfile.TemporaryDirectory() as td:
        rows={}
        for tag,entry in [('seed-base',seeds['seeds']['base']),('seed-joins',seeds['seeds']['joins']),('final-base',a),('final-joins',b)]:
            path=Path(td)/tag;base.restore_archive(entry['archive'],path)
            h=base.CompleteAdmissionInventory(path,**base.OPTIONS)
            try:rows[tag]=base.rows(h)
            finally:h.close();assert base.sha(path)==entry['archive']['database_sha256']
        seed_delta=set(rows['seed-joins'])-set(rows['seed-base'])
        new_base=set(rows['final-base'])-set(rows['seed-base']);new_joins=set(rows['final-joins'])-set(rows['seed-joins'])
        assert new_joins<=new_base and new_base-new_joins==seed_delta&new_base
        assert rows['final-base'].items()<=rows['final-joins'].items()
        unused=seed_delta-set(rows['final-base']);unused_details=[]
        for key in sorted(unused):
            cnf=base.load_json(key)[-1];node=base.load_json(rows['seed-joins'][key])
            unused_details.append(dict(key_sha256=base.key_sha(key),variables=len({abs(l) for c in cnf for l in c}),clauses=len(cnf),literals=sum(map(len,cnf)),node_kind=node.get('kind')))
    savings={k:100*(report['summary']['base'][k]-report['summary']['joins'][k])/report['summary']['base'][k] for k in ('entered','probes','mean_solve_and_bookkeeping_seconds','mean_stream_wall_seconds','mean_peak_rss_raw','database_bytes','compressed_bytes')}
    result=dict(report=study.binding(out/'report.json'),seeds=study.binding(out/'seeds.json'),analyzer=study.binding(__file__),
        cases=records,groups=groups,all_first_visit_proofs_equal=True,joins_new_is_subset_of_base_new=True,
        avoided_acquisitions_exactly_preloaded_rows=len(new_base-new_joins),preloaded_rows=len(seed_delta),unused_preloaded_rows=unused_details,
        savings_percent=savings,paired_stream_seconds={m:[t['summary']['stream_wall_seconds'] for t in trials[m]] for m in study.MODES},
        limitations=['Post-hoc descriptive attribution. No policy or workload changes.',
            'Negative savings denote increased resource use. Two pairs do not establish a reliable small runtime effect.',
            'Shared proof steps include the inherited contradiction; use avoided acquisitions for attributable saved work.'])
    base.write(out/'analysis.json',result)
    print(base.encode(dict(avoided=len(new_base-new_joins),unused=len(unused),savings_percent=savings)))


if __name__=='__main__':analyze(Path(sys.argv[1]))

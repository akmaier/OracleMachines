#!/usr/bin/env python3
"""Post-hoc attribution; does not alter timed workers or acquired answers."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_witness_signatures as study
base=study.base


def run(out):
    report=base.load(out/'report.json');catalog=base.load(out/'cases.json');summary=report['summary'];trials={m:[] for m in study.MODES}
    for sample in report['samples']:trials[sample['mode']].append(base.load(sample['path']))
    control=summary['active'];comparison={};paired={}
    for mode in ('signatures','rotate'):
        current=summary[mode]
        comparison[mode]={k+'_change_percent':100*(current[k]/control[k]-1) for k in ('mean_complete_worker_seconds','mean_complete_peak_rss_bytes','mean_query_seconds')}
        comparison[mode]['gzip_plus_raw_sidecars_bytes']=current['compressed_bytes']+sum(current['sidecar_bytes'])/len(current['sidecar_bytes'])
        paired[mode]=[dict(repeat=i,complete_change_percent=100*(trials[mode][i]['summary']['complete_worker_seconds']/trials['active'][i]['summary']['complete_worker_seconds']-1),
            peak_rss_change_percent=100*(trials[mode][i]['summary']['complete_peak_rss_bytes']/trials['active'][i]['summary']['complete_peak_rss_bytes']-1)) for i in range(3)]
    queries=base.load(trials['active'][0]['queries']['path']);remaining=[];by_template=Counter();by_answer=Counter()
    for row in queries:
        if row['visit']:continue
        case=catalog['cases'][row['case']];expanded=row['child']['metrics'].get('expanded_nodes',0);by_template[case['template_case']]+=expanded;by_answer[str(row['answer'])]+=expanded
        if expanded:remaining.append(dict(case=row['case'],template_case=case['template_case'],answer=row['answer'],expansions=expanded,
            splits=row['child']['metrics'].get('split_nodes',0),removed=case['removed'],guard_clause=row['guard']['removed_clause'] if row['guard'] else None))
    banks={}
    for mode in ('signatures','rotate'):
        state=base.load(trials[mode][0]['witness_bank']['path']);b=study.WitnessSignatures.restore(state)
        banks[mode]=dict(counts=state['counts'],check=trials[mode][0]['witness_check'],raw_bytes=Path(trials[mode][0]['witness_bank']['path']).stat().st_size,
            lookup_calls=len(base.load(trials[mode][0]['transfers']['path'])),per_template=[dict(case=t0['case'],states=len(t['states']),signatures=len(c['representatives']),
                seed_states=sum(s['origin']['kind']=='seed' for s in t['states']),attempts=len(t['attempts']),rejected=sum(not a['accepted'] for a in t['attempts']),
                duplicates=sum(a['accepted'] and not a['fresh'] for a in t['attempts'])) for t0,t,c in zip(base.load(base.load(out/'protocol.json')['template_catalog']['path'])['templates'],b.templates,b.compiled)])
    result=dict(report=study.binding(out/'report.json'),sources={__file__:base.sha(__file__)},comparison=comparison,paired=paired,banks=banks,
        control_gzip_plus_raw_sidecars_bytes=control['compressed_bytes']+sum(control['sidecar_bytes'])/len(control['sidecar_bytes']),
        remaining_by_template=dict(by_template),remaining_by_answer=dict(by_answer),remaining=sorted(remaining,key=lambda r:(-r['expansions'],r['case'])),
        byte_identical_proof_archives=len({r['archive']['database_sha256'] for rs in trials.values() for r in rs})==1,
        control_cold_percent=100*control['mean_cold_seconds']/control['mean_complete_worker_seconds'],
        control_compression_percent=100*control['mean_compression_seconds']/control['mean_complete_worker_seconds'],
        limitation='No extra transfers on this fresh stream; all 96 SAT cases already use the old witness route. All remaining expansions are negative. Historical SAT gains do not establish fresh-stream benefit; keep exploration optional.')
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('comparison','remaining_by_template','remaining_by_answer','byte_identical_proof_archives','control_cold_percent','control_compression_percent')}))


if __name__=='__main__':run(Path(sys.argv[1]))

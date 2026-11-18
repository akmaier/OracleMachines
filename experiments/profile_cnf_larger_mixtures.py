#!/usr/bin/env python3
"""Posthoc identical-decision profiles and cost ranking on the frozen larger stream."""
from collections import Counter,defaultdict
from pathlib import Path
import cProfile,json,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_larger_mixtures as study
from experiments.cnf_larger_mixtures import attempt
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);report=base.load(out/'report.json');profiles={}
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    for mode in study.MODES:
        expected=base.load(out/f'{mode}-0/queries.json');prof=cProfile.Profile()
        with tempfile.TemporaryDirectory() as td:
            s=study.CLASSES[mode](Path(td)/'db',node_limit=p['node_limit'])
            try:
                prof.enable();results=[attempt(s,c['source']) for c in cases];prof.disable()
                for a,b in zip(results,expected):
                    for key in ('status','metrics','reason'):assert a[key]==b[key]
                    if a['result'] is not None:
                        for key in ('answer','model','root','authority','quotient_choice'):
                            assert json.loads(base.encode(a['result'][key]))==b['result'][key]
                for name,rows in (('native',study.prior.native_rows(s)),('extension',study.prior.extension_rows(s))):
                    assert base.key_sha(base.encode(sorted(rows.items())))==report['summary'][mode][name+'_digest']
            finally:s.close()
        stats=pstats.Stats(prof);entries=[]
        for (f,line,name),(primitive,total,own,cumulative,parents) in stats.stats.items():
            try:f=str(Path(f).relative_to(Path.cwd()))
            except ValueError:pass
            entries.append(dict(file=f,line=line,function=name,total_calls=total,self_seconds=own,cumulative_seconds=cumulative))
        profiles[mode]=dict(outputs_and_counters_identical=True,total_profiled_seconds=stats.total_tt,functions=sorted(entries,key=lambda x:-x['self_seconds']))
    groups={};costly=[]
    for mode in study.MODES:
        for dimension in ('family','size','variant'):
            grouped=defaultdict(Counter)
            for repeat in range(2):
                for c,r in zip(cases,base.load(out/f'{mode}-{repeat}/queries.json')):
                    g=grouped[str(c[dimension])];g['queries']+=0.5;g[r['status']]+=0.5
                    g['query_seconds']+=r['seconds']/2;g['solve_seconds']+=r['solve_seconds']/2
                    g['new_native_nodes']+=len(r['new_ids'][study.TABLES[0]])/2
                    for key in ('expanded_nodes','propagation_literal_visits','normalization_literal_visits','split_nodes','search_memory_hits','batch_rollbacks'):
                        g[key]+=r['metrics'].get(key,0)/2
            groups[mode+'_'+dimension]={k:dict(v) for k,v in grouped.items()}
    control=[base.load(out/f'batch32-{i}/queries.json') for i in range(2)]
    for c,rows in zip(cases,zip(*control)):
        costly.append(dict(case=c['case'],family=c['family'],size=c['size'],variant=c['variant'],status=rows[0]['status'],
            mean_query_seconds=sum(r['seconds'] for r in rows)/2,expanded_nodes=rows[0]['metrics'].get('expanded_nodes',0),
            split_nodes=rows[0]['metrics'].get('split_nodes',0),new_native_nodes=len(rows[0]['new_ids'][study.TABLES[0]]),retained=rows[0]['retained']))
    base.write(out/'profile.json',dict(source=study.binding(__file__),profiles=profiles,groups=groups,cases_by_cost=sorted(costly,key=lambda r:-r['mean_query_seconds']),
        limitations=['Profiling is a separate solve-only replay; inclusive costs overlap and instrumentation changes relative timings.',
        'Group costs use original matched workers, not profiles. Generator labels describe design, not certified semantic classes.',
        'No representative arbitrary-SAT or statistical runtime claim from two short repeats.']))
    print(base.encode({m:pr['functions'][:5] for m,pr in profiles.items()}),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))

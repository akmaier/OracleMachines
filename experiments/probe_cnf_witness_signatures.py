#!/usr/bin/env python3
"""Historical held-out discovery probe; no new solver acquisition or timing claim."""
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_witness_signatures as study
from experiments.cnf_residual_dag import holds
base=study.base


def run(out):
    out.mkdir(exist_ok=False);parent=base.load(study.PARENT/'checkpoint.json');protocol=base.load(study.PARENT/'protocol.json')
    templates=base.load(protocol['template_catalog']['path'])['templates'];fields=study.SEED_FIELDS[:-1]
    catalogs=[(f,base.load(parent[f]['path'])) for f in fields];targets=base.load(parent['active_support_decisions']['path']);samples=[]
    diagnostic_ids=(2,137,29,140,116,149);checks=[]
    seeds=study.seed_bank(templates,catalogs,0)
    for d in targets:
        if d['case'] not in diagnostic_ids:continue
        violations=[];one_flip=[]
        for ti,t in enumerate(seeds.templates):
            if not {tuple(sorted(c)) for c in d['source']}<={tuple(c) for c in t['source']}:continue
            for si,s in enumerate(t['states']):
                model={v:bool(s['bits']>>i&1) for i,v in enumerate(t['names'])};bad=[c for c in d['source'] if not holds([c],model)];violations.append(len(bad))
                for v in sorted({abs(l) for c in bad for l in c}):
                    if holds(d['source'],{**model,v:not model[v]}):one_flip.append(dict(template=ti,state=si,variable=v))
        checks.append(dict(case=d['case'],answer=d['answer'],minimum_violated_clauses=min(violations),one_flip_repairs=one_flip))
    for budget in (0,64,256,1024,4096):
        tick=time.perf_counter();b=study.seed_bank(templates,catalogs,budget);saved=b.state();base.write(out/f'bank-{budget}.json',saved)
        checked=study.check_saved(base.load(out/f'bank-{budget}.json'),templates,catalogs);hits=[]
        for d in targets:
            for ti,(t,c) in enumerate(zip(b.templates,b.compiled)):
                query={tuple(sorted(clause)) for clause in d['source']}
                if not query<=c['members'].keys():continue
                present=sum(1<<c['members'][clause] for clause in query)
                matches=[si for bad,si in c['representatives'].items() if not bad&present]
                if matches:
                    si=matches[0];m={v:bool(t['states'][si]['bits']>>i&1) for i,v in enumerate(t['names'])}
                    assert d['answer'] is True and holds(d['source'],m)
                    hits.append(dict(case=d['case'],template=ti,state=si));break
        samples.append(dict(budget=budget,checked=checked,state=study.binding(out/f'bank-{budget}.json'),hits=hits,diagnostic_hits=[h['case'] for h in hits if h['case'] in diagnostic_ids],
            seconds=time.perf_counter()-tick,per_template=[dict(states=len(t['states']),signatures=len(c['representatives']),attempts=len(t['attempts'])) for t,c in zip(b.templates,b.compiled)]))
    result=dict(parent=study.binding(study.PARENT/'checkpoint.json'),templates=protocol['template_catalog'],seeds=[dict(field=f,**parent[f]) for f in fields],
        targets=parent['active_support_decisions'],one_flip=checks,samples=samples,sources={f:base.sha(f) for f in study.FILES},
        limitation='Historical held-out screen excluding the entire active-support answer catalog from seeds. No acquisition, publication, end-to-end timing or general coverage claim. Diagnostic IDs refer to that historical catalog only.')
    base.write(out/'report.json',result);print(base.encode({str(s['budget']):dict(hits=len(s['hits']),diagnostic=s['diagnostic_hits'],**s['checked']) for s in samples}))


if __name__=='__main__':run(Path(sys.argv[1]))

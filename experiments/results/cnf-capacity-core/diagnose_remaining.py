"""Retain missed bounded cores and the failed external recognition attempts."""
from itertools import product
from pathlib import Path
import json
from experiments import audit_cnf_capacity_core as audit
from experiments import cnf_capacity_core as core


def run(out):
    load=lambda p:json.loads(Path(p).read_text())
    report=load(out/'capacity-0/report.json'); missed=[]
    for capacity in (2,3):
        for domains in product(range(1<<capacity),repeat=3):
            source=audit.encode_domains(domains,capacity)
            if audit.satisfiable(source):continue
            proof,diagnostic=core.discover(source)
            if proof is None:missed.append(dict(capacity=capacity,domains=list(domains),source=source,diagnostic=diagnostic))
    mixtures=[r for r in load(out/'semantic-audit.json')['mixtures'] if not r['satisfiable'] and r['proof'] is None]
    records=[]
    for row in report['cases']:
        p=load(out/'capacity-0'/(row['id']+'.json'))
        r=dict(id=row['id'],kind=p['kind'],status=row['status'],capacity_diagnostic=row['diagnostic']['capacity'])
        if p['kind']=='capacity':
            r.update(demands=len(p['proof']['demands']),groups=len(p['proof']['groups']),pairs=sum(len(g)*(len(g)-1)//2 for g in p['proof']['groups']))
        records.append(r)
    result=dict(missed_small_domain_cores=missed,missed_mixtures=mixtures,external=records,
                scope='Search failures are retained without claiming absence of capacity cores. Pair counts are checker obligations before implicit complement exclusions; catalog groups never reach recognition.')
    (out/'gap-diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(missed_domain_cores=len(missed),missed_mixtures=len(mixtures),external_new_capacity_certificates=sum(r['kind']=='capacity' for r in records))))


if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]))

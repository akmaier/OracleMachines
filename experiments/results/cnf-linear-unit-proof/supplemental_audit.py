"""Recheck signed model transport and retain exact benchmark summaries."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_linear_unit_proof as s
out=Path(__file__).parent;larger=out/'larger';rows=s.load(larger/'panel.json');byid={x['id']:x for x in rows};checked=[]
for t in s.load(larger/'transports.json'):
    for mode in ('explicit','linear','z3','portfolio'):
        if mode in ('explicit','linear'):
            p=s.load(larger/(mode+'-0')/(t['id']+'.json'));got=s.check(byid[t['id']]['source'],p)
        else:got=s.load(larger/'references'/(t['id']+'-'+mode+'.json'))['result']
        if got['answer'] is True:
            model={int(k):v for k,v in got['model'].items()};mapping={int(k):v for k,v in t['mapping'].items()};names=sorted(mapping)
            witness=dict(format=s.e.prior.prior.previous.FORMAT,names=names,values=[model[abs(mapping[v])]^(mapping[v]<0) for v in names])
            assert s.e.prior.prior.previous.check(byid[t['original']]['source'],witness)['answer']
            checked.append(dict(id=t['id'],mode=mode,original=t['original'],witness=witness))
a=s.load(out/'semantic-audit.json');assert a==s.load(out/'semantic-audit-reproduced.json')
s.write(out/'supplemental-checks.json',dict(passed=True,signed_transports=checked,semantic_reproduced=True,truth_queries=a['counts']['queries'],truncated_refutations_rejected=a['counts']['truncations_rejected'],scope='Signed witnesses transport back to the original source. Z3 negative reference claims are not promoted to project certificates.'))
print('Signed model transports checked:',len(checked))

#!/usr/bin/env python3
"""Read-only explanation of the finite wide/deep contrast and proof sharing."""
from collections import Counter
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_nested_refinement as study
base=study.base


def explain(out):
    protocol=base.load(out/'protocol.json');report=base.load(out/'report.json')
    assert base.sha(out/'protocol.json')==report['protocol_sha256']
    target=base.load(protocol['target']['path']);queries=base.load(protocol['queries']['path'])
    root=queries[target['case']]['roots'][0];results={};bindings={}
    with tempfile.TemporaryDirectory() as td:
        for mode in study.MODES:
            stream=base.load(out/f'{mode}-0/report.json');last=stream['samples'][-1]
            assert base.sha(last['path'])==last['sha256'];data=base.load(last['path']);bindings[mode]=last
            path=Path(td)/mode;base.restore_archive(data['archive'],path)
            h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
            try:
                h.db.execute('PRAGMA query_only=ON')
                with base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')):
                    evidence=[base.load_json(r[0]) for r in h.db.execute(f'SELECT payload FROM {base.split.TABLE} ORDER BY rowid')]
                    routes=base.routes_for(h,evidence)
                    if mode=='flat':
                        source=target['source'];support=sorted({abs(l) for c in h._load(source)['cnf'] for l in c})
                        pairs=[r for r in evidence if r['source']==source]
                        assert sorted(r['variable'] for r in pairs)==support
                        rows=[]
                        for record in pairs:
                            present=[h._load(b['edge']['key']) is not None for b in record['branches']]
                            assert all(present)
                            closed=[base.compose(h,[b['edge']['key']],routes,Counter())[0][0] for b in record['branches']]
                            rows.append(dict(variable=record['variable'],present=present,closed=closed))
                        assert not any(all(r['closed']) for r in rows)
                        results[mode]=dict(source=source,variables=len(support),pairs=rows,root_closed=False,
                            limitation='No single-variable pair closes under this fixed recognizer and this flat history; this is not a lower bound for SAT or other preprocessing.')
                    else:
                        closed,plan=base.compose(h,[root],routes,Counter());assert closed==[True]
                        proof=base.expand(h,plan,[root],routes,Counter())
                        base.split.verify_positive(h,proof,[root],evidence,Counter())
                        base.write(out/'case16-proof.json',proof)
                        steps={s['source']:s for s in proof['steps']};multiplicity=Counter({root:1});depth={root:0}
                        for step in reversed(proof['steps']):
                            count=multiplicity[step['source']]
                            for child in step['children']:
                                multiplicity[child]+=count
                                depth[child]=max(depth.get(child,0),depth[step['source']]+(step['rule']['kind']==base.split.KIND))
                        kinds=Counter(s['rule']['kind'] for s in proof['steps']);families=[];reductions=Counter();shared=[]
                        for step in proof['steps']:
                            node=base.owner(h,step['source'])._load(step['source'])
                            if step['rule']['kind']=='family':
                                families.append(dict(source_sha256=base.key_sha(step['source']),shape=node['profile']['shape'],
                                    recognized=[k for k,v in node['profile']['outcomes'].items() if v=='recognized'],
                                    multiplicity=multiplicity[step['source']]))
                            elif step['rule']['kind']=='edge':reductions[node['kind']]+=1
                            if multiplicity[step['source']]>1:
                                shared.append(dict(source_sha256=base.key_sha(step['source']),kind=node['kind'],
                                    rule=step['rule']['kind'],multiplicity=multiplicity[step['source']],shape=node['profile']['shape']))
                        results[mode]=dict(proof=dict(path=str(out/'case16-proof.json'),sha256=base.sha(out/'case16-proof.json')),
                            root_closed=True,unique_steps=len(steps),rule_counts=dict(kinds),reduction_counts=dict(reductions),
                            unfolded_step_occurrences=sum(multiplicity.values()),max_external_depth=max(depth.values()),
                            unique_family_leaves=len(families),family_occurrences=sum(f['multiplicity'] for f in families),
                            families=families,shared_nodes=shared,
                            limitation='Depth counts branch-dependent choices in changing local coordinates, interleaved with reductions; it is not a fixed backdoor of that many original variables.')
            finally:h.close();assert base.sha(path)==data['archive']['database_sha256']
    result=dict(report_sha256=base.sha(out/'report.json'),source_sha256=base.sha(__file__),sample_bindings=bindings,
        flat=results['flat'],nested=results['nested'])
    base.write(out/'explanation.json',result)
    print(base.encode(dict(flat_variables=results['flat']['variables'],nested={k:v for k,v in results['nested'].items() if k in
        ('unique_steps','rule_counts','reduction_counts','unfolded_step_occurrences','max_external_depth','unique_family_leaves','family_occurrences','shared_nodes')})))


if __name__=='__main__':explain(Path(sys.argv[1]))

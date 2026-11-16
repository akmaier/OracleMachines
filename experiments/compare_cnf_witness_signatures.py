#!/usr/bin/env python3
"""Matched current-union witness-signature lookup and bounded exploration."""
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_active_support as previous
from experiments.cnf_active_support import ActiveCoreBank,audit_with_lineage
from experiments.cnf_witness_signatures import WitnessSignatures
eager=previous.eager;base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-active-support');MODES=('active','signatures','rotate')
OLD_FIELDS=previous.FIELDS;FIELDS=OLD_FIELDS+('active_support_decisions',)
SEED_FIELDS=('model_rotation_decisions',)+FIELDS
FILES=['experiments/cnf_witness_signatures.py','solver/test_cnf_witness_signatures.py',
       'experiments/compare_cnf_witness_signatures.py','experiments/validate_cnf_witness_signatures.py','experiments/probe_cnf_witness_signatures.py']


def seed_bank(templates,catalogs,limit):
    bank=WitnessSignatures(templates,attempt_limit=limit,max_bad=2)
    for field,records in catalogs:
        for row in records:
            if row['answer'] is True:
                bank.observe(row['source'],{int(k):v for k,v in row['model'].items()},dict(kind='seed',field=field,case=row['case']))
    bank.drain();return bank


def check_saved(saved,templates,catalogs):
    # Reconstruct seed identities and all exploration; independently rescan each
    # stored assignment and replay failed/duplicate flips on restoration.
    expected=seed_bank(templates,catalogs,saved['attempt_limit']);restored=WitnessSignatures.restore(saved)
    assert expected.templates==restored.templates
    return dict(templates=len(restored.templates),states=sum(len(t['states']) for t in restored.templates),
        signatures=sum(len(c['representatives']) for c in restored.compiled),attempts=sum(len(t['attempts']) for t in restored.templates))


def worker(out,protocol,catalog,mode):
    tick=time.perf_counter();original_bank=eager.CoreBank;original_propose=eager.propose;state={};events=[]
    def prepare(solver,catalogs):
        prior=base.load(protocol['support_index']['path']);assert base.sha(protocol['support_index']['path'])==protocol['support_index']['sha256']
        state.update(prepared=prior,catalogs=catalogs[:len(OLD_FIELDS)],cores=prior['cores'])
        if mode!='active':
            state['templates']=base.load(protocol['template_catalog']['path'])['templates']
            state['seeds']=[(f,base.load(e['path'])) for f,e in zip(SEED_FIELDS,protocol['seed_catalogs'])]
            state['witnesses']=seed_bank(state['templates'],state['seeds'],0 if mode=='signatures' else protocol['attempt_limit'])
        return prior
    def bank(solver,cores):return ActiveCoreBank(solver,cores) if cores is state.get('cores') else original_bank(solver,cores)
    def propose(solver,extensions,source,counts):
        if mode!='active':
            hit=state['witnesses'].reuse(solver,source);events.append(dict(source=source,hit=hit))
            if hit is not None:return None
        return original_propose(solver,extensions,source,counts)
    def cold(path,records):
        result=audit_with_lineage(path,records,state['prepared'],state['catalogs'])
        if mode!='active':
            started=time.perf_counter();saved=state['witnesses'].state();base.write(out/'witness-bank.json',saved)
            checked=check_saved(base.load(out/'witness-bank.json'),state['templates'],state['seeds'])
            state['witness_check']=dict(**checked,seconds=time.perf_counter()-started)
        return result
    with ExitStack() as stack:
        for name,value in [('FIELDS',FIELDS),('prepare',prepare),('CoreBank',bank),('propose',propose),('audit',cold)]:stack.enter_context(patch.object(eager,name,value))
        eager.worker(out,protocol,catalog,'cofactor')
    base.write(out/'transfers.json',events)
    report=base.load(out/'report.json');summary=report['summary'];summary.update(mode=mode,complete_worker_seconds=time.perf_counter()-tick,
        complete_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        model_transfers=sum(e['hit'] is not None for e in events),model_attempts=0 if mode=='active' else sum(len(t['attempts']) for t in state['witnesses'].templates),
        materialization_nodes=report['cofactor_counts'].get('materialization_nodes',0),
        witness_check_seconds=state.get('witness_check',{}).get('seconds',0))
    summary['sidecar_bytes']+=(out/'transfers.json').stat().st_size
    if mode!='active':summary['sidecar_bytes']+=(out/'witness-bank.json').stat().st_size
    report.update(transfers=binding(out/'transfers.json'),witness_bank=None if mode=='active' else binding(out/'witness-bank.json'),witness_check=state.get('witness_check'))
    base.write(out/'report.json',report)


def run(out):
    out.mkdir(exist_ok=False);old=base.load(PARENT/'protocol.json');parent=base.load(PARENT/'checkpoint.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});prior=[]
    for field in FIELDS:
        entry=parent[field];assert base.sha(entry['path'])==entry['sha256'];prior+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',prior)
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,support_index=parent['active_support_proposals'],
        template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],previous_decisions=binding(out/'previous-decisions.json'),
        prior_decision_catalogs=[parent[f] for f in FIELDS],seed_catalogs=[parent[f] for f in SEED_FIELDS],node_limit=100000,per_template=64,visits=2,attempt_limit=4096,
        orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        selection='Same salted order excluding 1344 prior sidecar answers and all complete roots in the latest 17532-key union; next 64 per template, interleaved.',
        limitations=['All modes actively load the same acquired 170-entry negative-support index; no additional negative discovery. Complete cold proof/query and six-catalog negative-lineage audit remain charged.',
            'Signatures uses all prior checked SAT models, completing absent template variables with False. Rotate adds at most 4096 flip attempts per template with at most two false template clauses. Failed attempts and all distinct accepted assignments persist.',
            'Seed batch is fixed before exploration. One representative per signature compresses lookup only, not exploration; false-clause signatures do not preserve flip transitions. Misses and exhausted budgets never mean UNSAT.',
            'New lookup runs after old whole-query core and one-clause witness misses, before guarding. Every hit publishes an ordinary fully checked SAT root; old query audit remains unchanged.',
            'Cold reconstruction independently rescans stored states and replays the complete bounded transcript; seed identities and every rejected or duplicate flip are checked. State serialization and this check are included in complete time.',
            'Three balanced fresh-process triples with no overlapping tests/builds/profiles. Complete clock includes restoration, preparation, lookup/publication, persistence, full cold checks, compression, row digest and transfer serialization; imports, CLI reads and final wrapper rewrite excluded.',
            'Constructed two-deletion neighbours in three shared-coordinate templates, not arbitrary SAT or unrestricted pattern coverage. Historical seed acquisition remains separately charged; the 4096 cap was selected by a historical held-out probe, not these new answers.'])
    base.write(out/'protocol.json',protocol);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path);solver=ResidualSolver(path)
        try:catalog=eager.previous.inputs(solver,protocol)
        finally:solver.close()
    base.write(out/'cases.json',catalog);base.write(out/'preflight.json',dict(seconds=time.perf_counter()-tick,selection=catalog['selection']))
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True,stdout=subprocess.DEVNULL)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')));print(mode,repeat,flush=True)
    summary={}
    for mode in MODES:
        trials=[base.load(x['path'])['summary'] for x in samples if x['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k.endswith('peak_rss_bytes')];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary))
    print(base.encode({m:{k:v for k,v in s.items() if k in ('expanded_nodes','model_transfers','new_nodes','mean_complete_worker_seconds','mean_complete_peak_rss_bytes')} for m,s in summary.items()}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))

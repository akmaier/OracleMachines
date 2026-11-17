#!/usr/bin/env python3
"""Fresh matched ordinary, core-first chain, and prepared premise-first policies."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_chain as prior
from experiments import compare_cnf_alternative_guard as ordinary
from experiments.cnf_premise_guard import PremiseGuardSelector
from experiments.cnf_guard_chain import propose_missing_clause,publish_guard,make_record,GuardChainBank
from experiments.cnf_incremental_archive import ResidualAppendCursor
from experiments.validate_cnf_unsat_support import bound
base=prior.base;binding=prior.binding;rows=prior.rows;ResidualSolver=prior.ResidualSolver
PARENT=Path('experiments/results/cnf-guard-chain');FIELDS=prior.FIELDS;OLD_FIELDS=prior.OLD_FIELDS
MODES=('plain','core-first','premise-first')
FILES=('experiments/cnf_premise_guard.py','solver/test_cnf_premise_guard.py','experiments/compare_cnf_premise_guard.py','experiments/validate_cnf_premise_guard.py')


def setup(s,p):
    bank=ordinary.CoreBank(s,bound(p['cores']));extensions=ordinary.ExtensionBank(bound(p['bank_catalog'])['bank'])
    bindings=dict(legacy=p['support_index'],causal=p['causal_index']);indices={n:bound(e) for n,e in bindings.items()}
    prepared=ordinary.compose(indices,bindings);cofactors=ordinary.ProofChoiceBank(s,indices['legacy'],indices['causal'])
    return bank,extensions,indices,prepared,cofactors


def prepare(s,source,p,bank,extensions,cofactors,selector):
    counts=Counter();cnf,_,key=s._canonical(source);known=s._read(key,cnf,purpose='direct_query')
    support=bank.reuse(source) if known is None else None
    witness=ordinary.reuse_witness(s,extensions,source,counts) if known is None and support is None else None
    guard=ordinary.propose(s,extensions,source,counts) if known is None and support is None and witness is None else None
    target=source if guard is None else ordinary.check_guard(s,source,guard,counts)[1]
    target_known=False;cofactor=None;trace=None
    if guard is not None:
        cnf,_,key=s._canonical(target);target_known=s._read(key,cnf,purpose='guard_target') is not None
        if not target_known:cofactor=cofactors.reuse(target)
    if guard is not None and not target_known and cofactor is None:
        selected,trace=selector.select(s,extensions,source,guard,cofactors)
        if selected is not None:
            guard=selected;_,target=ordinary.check_guard(s,source,guard,counts)
            cnf,_,key=s._canonical(target);target_known=s._read(key,cnf,purpose='guard_target') is not None
            if not target_known:cofactor=cofactors.reuse(target)
    return target,dict(source=source,guard=guard,core=support,witness=witness,guard_choice=trace,cofactor=cofactor,target_known=target_known),counts


def worker(out,p,catalog,mode):
    out.mkdir();start=time.perf_counter();parent=bound(p['parent']);records=[];warm=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'proofs';base.restore_archive(parent['reference_union'],path);s=ordinary.AccountedResidualSolver(path,node_limit=p['node_limit']);initial=rows(s);cursor=ResidualAppendCursor(s)
        try:
            tick=time.perf_counter()
            with patch.object(s,'_expand',side_effect=AssertionError('Preparation search')):
                bank,extensions,indices,prepared,cofactors=setup(s,p);cores=prepared['cores'];selector=ordinary.AlternativeGuardSelector(p['alternative_budget'])
                retained=GuardChainBank(s,bound(parent['guard_chain_decisions']))
                near=PremiseGuardSelector(cores) if mode=='premise-first' else None
            prepare_seconds=time.perf_counter()-tick;near_setup_counts={} if near is None else dict(near.counts);assert not cursor.take()
            setup_seconds=time.perf_counter()-start
            for case in catalog['cases']:
                tick=time.perf_counter();s.counts=Counter();counts=Counter();source=case['source'];assert retained.lookup(source) is None
                target,normal,normal_counts=prepare(s,source,p,bank,extensions,cofactors,selector);early=cursor.take()
                guards=[] if normal['guard'] is None else [normal['guard']];choice=None;extra_seconds=0.;before=Counter(s.counts)
                eligible=normal['guard'] is not None and not normal['target_known'] and normal['cofactor'] is None
                if eligible and mode!='plain':
                    extra_start=time.perf_counter()
                    with patch.object(s,'_expand',side_effect=AssertionError('Near-premise search')):
                        if near is None:
                            choice=propose_missing_clause(s,target,cores,counts)
                            if choice is not None:
                                guard,_,target,inserted=publish_guard(s,target,cores[choice['core']],choice['missing_clause'],counts)
                                choice.update(path='core-first',inserted=inserted);guards.append(guard)
                        else:
                            old=Counter(near.counts);choice,guard,target=near.select(s,target);counts.update(near.counts-old)
                            if guard is not None:guards.append(guard)
                    extra_seconds=time.perf_counter()-extra_start
                extra_solver_counts=dict(s.counts-before);child=s.solve(target);chain=make_record(s,source,guards,child);added=cursor.take()
                records.append(dict(case=case['case'],template_case=case['template_case'],chain=chain,ordinary=normal,eligible=eligible,choice=choice,
                    early_ids=sorted(map(base.key_sha,early)),new_ids=sorted(map(base.key_sha,list(early)+list(added))),new_nodes=len(early)+len(added),
                    child_metrics=child['metrics'],counts=dict(counts),normal_counts=dict(normal_counts),extra_solver_counts=extra_solver_counts,extra_seconds=extra_seconds,seconds=time.perf_counter()-tick))
            tick=time.perf_counter();retained=GuardChainBank(s,bound(parent['guard_chain_decisions'])+[r['chain'] for r in records]);warm_setup_seconds=time.perf_counter()-tick
            with patch.object(s,'_expand',side_effect=AssertionError('Warm search')),patch.object(s,'_store',side_effect=AssertionError('Warm publication')):
                for case in catalog['cases']:
                    tick=time.perf_counter();answer=retained.lookup(case['source']);assert answer is not None
                    warm.append(dict(case=case['case'],result=answer,seconds=time.perf_counter()-tick))
            assert not cursor.take();final=rows(s);assert initial.items()<=final.items();census=s.archive_storage()
        except BaseException:
            s.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:s.close()
        used=[(n,bound(parent[n])) for n in OLD_FIELDS]
        cold=prior.audit_chain(path,[r['chain'] for r in records]+bound(parent['guard_chain_decisions']),prepared,used,indices)
        tick=time.perf_counter();base.write(out/'queries.json',records);base.write(out/'warm.json',warm);serialization_seconds=time.perf_counter()-tick;archive=base.archive(path,out)
    summary=dict(mode=mode,queries=len(records),positive=sum(r['chain']['answer'] for r in records),new_nodes=len(final)-len(initial),nodes=len(final),
        new_payload_units=sum(len(k)+len(v) for k,v in final.items() if k not in initial),expanded_nodes=sum(r['child_metrics'].get('expanded_nodes',0) for r in records),
        split_nodes=sum(r['child_metrics'].get('split_nodes',0) for r in records),eligible=sum(r['eligible'] for r in records),extra_guards=sum(r['choice'] is not None for r in records),
        premise_publications=sum(bool(r['choice'] and r['choice']['inserted']) for r in records),known_premise_choices=sum(bool(r['choice'] and r['choice']['path']=='known-premise') for r in records),
        setup_seconds=setup_seconds,prepare_seconds=prepare_seconds,query_seconds=sum(r['seconds'] for r in records),extra_seconds=sum(r['extra_seconds'] for r in records),
        warm_setup_seconds=warm_setup_seconds,warm_query_seconds=sum(r['seconds'] for r in warm),serialization_seconds=serialization_seconds,cold_seconds=cold['seconds'],compression_seconds=archive['seconds'],
        database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],sidecar_bytes=sum((out/f).stat().st_size for f in ('queries.json','warm.json')),
        row_digest=base.key_sha(base.encode(sorted(final.items()))),repeat_new_nodes=0,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))
    result=dict(summary=summary,queries=binding(out/'queries.json'),warm=binding(out/'warm.json'),archive=archive,cold=cold,
        near_setup_counts=near_setup_counts,near_counts={} if near is None else dict(near.counts),census=census,cursor_counts=dict(cursor.stats))
    base.write(out/'report.json',result);result['summary']['complete_worker_seconds']=time.perf_counter()-start;base.write(out/'report.json',result)


def run(out):
    out.mkdir(exist_ok=False);parent=base.load(PARENT/'checkpoint.json');old=base.load('experiments/results/cnf-terminal-guard/protocol.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});previous=sum((bound(parent[f]) for f in FIELDS),[])+bound(parent['guard_chain_decisions']);base.write(out/'previous-decisions.json',previous)
    p=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,support_index=parent['extended_support_proposals'],causal_index=parent['causal_support_proposals'],
        template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],previous_decisions=binding(out/'previous-decisions.json'),prior_decision_catalogs=[parent[f] for f in FIELDS],
        node_limit=100000,alternative_budget=1,per_template=64,orders=[MODES,MODES[::-1]],
        limitations=['192 new neighbouring CNFs, excluding prior ordinary and chain sidecars and native roots in the current 20666-key union. Same fixed acquired banks, no support discovery. Two reversed-order triplets in fresh processes; no concurrent tests/builds/profiles.',
            'All policies share ordinary recognition and checked chain persistence. Plain adds no extra guard; core-first uses the previous raw scan; premise-first uses prepared postings and accepts a checked strengthened premise before reading the support proof. This can admit pending-core hints when the actual strengthened premise is checked negative.',
            'One extra guard after an ordinary miss; no optimal-cost assumption. Warm second visits use a checked conclusion bank in every arm; setup and cold replay are charged. Full time includes archive restore, setup, query/chain work, serialization, cold audit, compression and report generation; imports, initial CLI reads and final timing rewrite excluded.',
            'This implementation experiment does not establish unrestricted SAT bounds, peak live-space savings from operation counts, or generalization outside the selected neighbouring-input families.'])
    base.write(out/'protocol.json',p);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'initial';base.restore_archive(parent['reference_union'],path);s=ResidualSolver(path)
        try:catalog=ordinary.eager.previous.inputs(s,p)
        finally:s.close()
    base.write(out/'cases.json',catalog);base.write(out/'preflight.json',dict(seconds=time.perf_counter()-tick,selection=catalog['selection']));samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True,stdout=subprocess.DEVNULL)
            samples.append(dict(repeat=repeat,mode=mode,**binding(dest/'report.json')));print(mode,repeat,flush=True)
    summary={}
    for mode in MODES:
        data=[bound(e)['summary'] for e in samples if e['mode']==mode];a=data[0];timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in data[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(x[k] for x in data)/len(data) for k in timed},'sidecar_bytes':[x['sidecar_bytes'] for x in data]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary));print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))

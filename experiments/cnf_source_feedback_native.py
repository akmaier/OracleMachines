"""Compile checked feedback on a fresh CNF without historical derived banks.

Only original source clauses, conditions and checked failed probes are origins.
All output records use the existing native residual format and its verifier.
This removes an interface restriction; it does not bound certificate expansion.
"""
from copy import deepcopy
from experiments import cnf_iterated_cross_pivot as feedback
from experiments import cnf_residual_dag as native
from experiments.cnf_probe_support import slice_trace
from experiments.cnf_prepared_publication import prepare_frame
from experiments.cnf_direct_unit_closure import DirectUnits,checked_options


def prepare(source,chain,counts,*,order_source=None):
    # Copy once so origins and proofs cannot be changed during publication.
    chain=deepcopy(chain)
    seed,_,_=feedback.validate(source,chain,counts,order_source=order_source)
    if chain['status']!='refuted':raise ValueError('Refuted source feedback required')
    banks=[seed];origins=[[('source',) for _ in seed]];branches={}
    for level,summary in enumerate(chain['levels']):
        grown=dict(zip(banks[-1],origins[-1]))
        for index,lemma in enumerate(summary['lemmas']):
            lit=lemma['assumption'];sat=lemma['saturation']
            local=dict(zip(banks[-1],origins[-1]));local.setdefault((lit,),('condition',))
            clauses=tuple(sorted(local))
            bb=banks[:-1]+[clauses];oo=origins[:-1]+[[local[cl] for cl in clauses]]
            for i,row in enumerate(sat['rounds']):
                local=dict(zip(bb[-1],oo[-1]))
                for j,probe in enumerate(row['search']['program']['probes']):
                    local.setdefault((-probe['assumption'],),('probe',i,j))
                clauses=tuple(sorted(local));bb.append(clauses);oo.append([local[cl] for cl in clauses])
            if sat['reason']=='units':proof=sat['proof']
            else:
                _,units,conflict=native.propagate(bb[-1],counts)
                if conflict is None:raise ValueError('Branch lacks a unit contradiction')
                proof=dict(units=units,conflict=conflict)
            feedback.k.frozen.check_trace(seed,bb[-1],None,proof,counts,max(sat['trace_limit'],len(proof['units'])))
            branches[level,index]=(bb,oo,sat,proof,lit)
            grown.setdefault((-lit,),('cross',level,index))
        clauses=tuple(sorted(grown));banks.append(clauses);origins.append([grown[cl] for cl in clauses])
    counts['source_feedback_prepared_levels']+=len(chain['levels'])
    return seed,chain,banks,origins,branches


def compile_program(solver,source,chain,counts,*,order_source=None,shortcut='all',unit_work_limit=262144,unit_trace_limit=256):
    checked_options(shortcut,unit_work_limit,unit_trace_limit)
    source,chain,root_banks,root_origins,branches=prepare(source,chain,counts,order_source=order_source)
    direct=DirectUnits(counts,unit_work_limit,unit_trace_limit);slices={}
    def frame(context):return prepare_frame(solver,native.restrict_scan(source,context,counts),counts)
    root_frame=frame({});root_cnf,_,root,_=root_frame
    old=solver._read(root,root_cnf,purpose='source_feedback_root')
    if old is not None:
        if old['answer'] is not False:raise ValueError('Contradictory source feedback root')
        counts['source_feedback_root_hits']+=1;return root
    def environment(env):
        return (root_banks,root_origins) if env is None else branches[env][:2]
    def leaf(env,stage,cid,context):
        banks,origins=environment(env);origin=origins[stage][cid];kind=origin[0]
        if kind=='source':
            if any(context.get(abs(l))!=(l<0) for l in banks[stage][cid]):
                raise ValueError('Source clause is not falsified')
            cnf,_,key,publish=frame(context)
            if () not in cnf:raise ValueError('Missing source conflict')
            publish(dict(kind='empty'));counts['source_feedback_source_leaves']+=1;return key
        if kind=='condition':raise ValueError('Branch condition cannot justify its excluded context')
        if kind=='cross':
            level,index=origin[1:];target=(level,index)
            if env is not None and level>=env[0]:raise ValueError('Non-decreasing feedback dependency')
            bb,_,sat,proof,lit=branches[target]
            if context.get(abs(lit))!=(lit>0):raise ValueError('Missing feedback branch premise')
            counts['source_feedback_cross_expansions']+=1
            return trace(target,len(bb)-1,proof,context)
        if kind!='probe' or env is None:raise ValueError('Unknown source feedback origin')
        i,j=origin[1:];lower=env[0]+i
        if lower>=stage:raise ValueError('Non-decreasing local probe dependency')
        row=branches[env][2]['rounds'][i]['search']['program']['probes'][j];lit=row['assumption']
        if context.get(abs(lit))!=(lit>0):raise ValueError('Missing local probe premise')
        counts['source_feedback_probe_expansions']+=1
        return trace(env,lower,row['proof'],context,lit)
    def trace(env,stage,proof,context,assumption=None,offered=None):
        banks,_=environment(env)
        key=(env,stage,assumption,tuple(map(tuple,proof['units'])),proof['conflict'])
        counts['source_feedback_slice_key_steps']+=len(proof['units'])
        if key not in slices:
            slices[key]=slice_trace(banks[stage],proof,assumption,counts)[0]
            counts['source_feedback_unique_slices']+=1
        else:counts['source_feedback_slice_hits']+=1
        proof=slices[key]
        def walk(i,context,offered=None):
            prepared=frame(context) if offered is None else offered
            cnf,names,key,publish=prepared
            old=solver._read(key,cnf,purpose='source_feedback_existing')
            if old is not None:
                if old['answer'] is not False:raise ValueError('Contradictory source feedback cache')
                counts['source_feedback_native_hits']+=1;return key
            if () in cnf:publish(dict(kind='empty'));return key
            if shortcut!='off' and (shortcut=='all' or i==0) and direct.close(prepared):return key
            if i==len(proof['units']):return leaf(env,stage,proof['conflict'],context)
            lit,cid=proof['units'][i];v=abs(lit);bit=lit>0
            if v in context:
                counts['source_feedback_fixed_steps']+=1
                return walk(i+1,context,prepared) if context[v]==bit else leaf(env,stage,cid,context)
            excluded=leaf(env,stage,cid,{**context,v:not bit})
            if v not in names:
                if excluded!=key:raise ValueError('Changed absent variable residual')
                counts['source_feedback_absent_lifts']+=1;return key
            live=walk(i+1,{**context,v:bit})
            publish(dict(kind='split',variable=names.index(v)+1,low=excluded if bit else live,high=live if bit else excluded))
            counts['source_feedback_splits']+=1;return key
        return walk(0,context,offered)
    result=trace(None,len(chain['levels']),chain['levels'][-1]['proof'],{},offered=root_frame)
    if result!=root:raise ValueError('Changed source feedback root')
    return result

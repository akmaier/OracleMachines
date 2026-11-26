"""Reuse one owned local checking context during source-event reconstruction.

Every source coordinate, conditioned-subset boundary and template is checked.
Transported reasons are checked against one exact immutable local CNF instead
of normalizing that same CNF separately for every accepted hint. Prefix replay
and downstream search/checking remain the frozen implementations.
"""
from copy import deepcopy
from experiments import cnf_guard_interactions as frozen,cnf_wide_guard_probes as prefix
from experiments.cnf_guard_context_solver import LocalContext
from experiments.cnf_shortening_transport import transport_state
native=frozen.native


def local_hints(source,templates,event,counts):
    source,templates,event=deepcopy((source,templates,event));counts['replay_owned_copies']+=1
    source=tuple(map(tuple,source));local=frozen.decode_key(event['root'])
    if native.normalize(source,counts)[0]!=source:raise ValueError('Canonical source required')
    fixed=frozen.fixed_pairs(event['fixed']);mapping=dict(event['mapping'])
    variables={abs(l) for cl in source for l in cl};local_vars={abs(l) for cl in local for l in cl}
    if (len(mapping)!=len(event['mapping']) or set(mapping)!=local_vars or
            any(type(v) is not int or type(w) is not int or w not in variables for v,w in mapping.items()) or
            len(set(mapping.values()))!=len(mapping) or not fixed.keys()<=variables or
            set(mapping.values())&fixed.keys()):raise ValueError('Invalid local coordinates')
    image={tuple(sorted(mapping[abs(l)]*(1 if l>0 else -1) for l in cl)) for cl in local}
    residual=set(native.restrict_scan(source,fixed,counts))
    if not image<=residual:raise ValueError('Not a conditioned source subset')
    inverse={v:k for k,v in mapping.items()};members=set(source);out=[];context=None
    for index,t in enumerate(templates):
        counts['template_candidates']+=1
        support=frozen.check_template(t,counts);guard=frozen.fixed_pairs(t['assumptions'])
        if not support<=members:counts['deleted_supports']+=1;continue
        if any(v in fixed and fixed[v]!=b for v,b in guard.items()):counts['incompatible_guards']+=1;continue
        missing=[(v,b) for v,b in guard.items() if v not in fixed]
        counts['compatible_width_'+str(len(missing))]+=1
        if any(v not in inverse for v,b in missing):counts['absent_guard_variables']+=1;continue
        if context is None:
            context=LocalContext.prepare(local,dict(cnf=local,mapping=mapping,fixed=fixed),counts)
            counts['replay_local_contexts']+=1
        hint=transport_state(context,t,missing,counts)
        if hint is None:continue
        out.append(dict(origin_template=index,**hint));counts['accepted_width_'+str(len(hint['clause']))]+=1
    return local,out,image==residual


def bind(source,templates,row,event,counts):
    # Prefix payload is owned too; no externally prepared state is accepted.
    program=deepcopy(row['program'])
    local,hints,_=local_hints(source,templates,event,counts)
    lifted=[h['template'] for h in hints]
    _,state=prefix.bind_prefix(local,lifted,program,counts)
    return local,lifted,state

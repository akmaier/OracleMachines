"""Checked later probe blocks on an exactly justified augmented CNF.

The digest identifies a complete base learning record, not an unverified source
claim. Base clauses and probes are checked before a continuation. Clear prefix
blocks never become coverage routes. All successful routes bind exact children.
"""
from collections import Counter
import hashlib

from experiments.cnf_trace_learning import (LearnedTraceRoutes,checked_augmentation,
    verify_learning,PROBE_LIMIT)
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_equivalence import discover_equivalence_probes,check_equivalence_probes
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds

WIDTH=PROBE_LIMIT


def base_id(record):return hashlib.sha256(encode(record).encode()).hexdigest()


def record_key(record):return encode([record['base_sha256'],record['width'],record['offset']])


class LearningBlocks:
    def __init__(self,h,bases,records=()):
        self.bases={};self.records={};self.contexts={};self.verified=set();self.counts=Counter()
        for base in bases:
            identity=base_id(base)
            if identity in self.bases and encode(self.bases[identity])!=encode(base):
                raise ValueError('Colliding learning base identity')
            self.bases[identity]=base
        for record in records:
            identity=record_key(record)
            if identity in self.records and encode(self.records[identity])!=encode(record):
                raise ValueError('Conflicting learning continuation')
            self.records[identity]=record
        for identity in self.records:self._saved(h,identity,self.counts)

    def context(self,h,identity,counts):
        base=self.bases.get(identity)
        if base is None or base_id(base)!=identity:raise ValueError('Missing or changed learning base')
        counts['learning_base_identity_bytes']+=len(encode(base).encode())
        if identity not in self.contexts:
            verify_learning(h,base,counts)
            if base['probing']['status']!='clear':raise ValueError('Continuation requires a clear learning base')
            node,expanded=checked_augmentation(h,base,counts)
            self.contexts[identity]=(node,expanded,probe_choices(expanded,64,counts))
        else:counts['reused_checked_learning_contexts']+=1
        return self.contexts[identity]

    def _saved(self,h,identity,counts):
        if identity not in self.records:raise ValueError('Missing learned prefix block')
        if identity not in self.verified:
            self.verify(h,self.records[identity],counts);self.verified.add(identity)
        else:counts['reused_checked_learning_blocks']+=1
        return self.records[identity]

    def verify(self,h,record,counts):
        if type(record) is not dict or set(record)!={'base_sha256','width','offset','probing','edge'}:
            raise ValueError('Invalid learning continuation fields')
        identity,width,offset=record['base_sha256'],record['width'],record['offset']
        if (type(identity) is not str or type(width) is not int or width!=WIDTH or
                type(offset) is not int or not 0<offset<64 or offset%WIDTH):
            raise ValueError('Invalid learning continuation policy')
        node,expanded,ranked=self.context(h,identity,counts)
        parent=(self.bases[identity] if offset==WIDTH else
                self._saved(h,encode([identity,WIDTH,offset-WIDTH]),counts))
        if parent['probing']['status']!='clear' or len(parent['probing']['attempts'])!=2*WIDTH:
            raise ValueError('Incomplete or successful learned prefix')
        selected=ranked[offset:offset+WIDTH]
        if not selected:raise ValueError('Exhausted learned candidate pool')
        target,fixed=check_equivalence_probes(expanded,record['probing'],WIDTH,counts,_choices=selected)
        if record['probing']['status']=='clear':
            if record['edge'] is not None:raise ValueError('Clear learned block cannot create a route')
        else:
            if not {abs(l) for c in target for l in c} < {abs(l) for c in node['cnf'] for l in c}:
                raise ValueError('Learned continuation must strictly reduce support')
            _,names,key=h._canonical(target,node['depth'])
            if encode(record['edge'])!=encode(dict(key=key,names=names)):
                raise ValueError('Incorrect learned continuation target')
        counts['verified_learning_continuations']+=1
        return target,fixed

    def advance(self,h,identity,counts):
        node,expanded,ranked=self.context(h,identity,counts)
        offset=WIDTH
        while offset<len(ranked):
            key=encode([identity,WIDTH,offset])
            if key not in self.records:break
            record=self._saved(h,key,counts)
            if record['probing']['status']!='clear':
                counts['reused_successful_learning_blocks']+=1
                return record,self.verify(h,record,counts)[0]
            counts['reused_learning_prefix_attempts']+=len(record['probing']['attempts'])
            offset+=len(record['probing']['attempts'])//2
        if offset>=len(ranked):
            counts['exhausted_learning_sources']+=1;return None,None
        probing=discover_equivalence_probes(expanded,WIDTH,counts,_choices=ranked[offset:offset+WIDTH])
        target,_=check_equivalence_probes(expanded,probing,WIDTH,counts,_choices=ranked[offset:offset+WIDTH]);edge=None
        if probing['status']!='clear':
            _,names,key=h._canonical(target,node['depth']);edge=dict(key=key,names=names)
        record=dict(base_sha256=identity,width=WIDTH,offset=offset,probing=probing,edge=edge)
        self.verify(h,record,counts);key=record_key(record);self.records[key]=record;self.verified.add(key)
        counts['new_learning_continuations']+=1
        return record,target

    def attach(self,h,routes):
        for record in self.records.values():
            if record['edge'] is None or h._load(record['edge']['key']) is None:continue
            source=self.bases[record['base_sha256']]['source']
            item=(dict(kind='learning_continuation',id=record_key(record)),[record['edge']['key']])
            if item not in routes.by_source[source]:routes.by_source[source].append(item)

    def lift(self,h,record,child_model):
        _,fixed=self.verify(h,record,Counter());edge=record['edge']
        if edge is None:raise ValueError('No successful learned continuation')
        child=h._load(edge['key'])
        if (child is None or any(i not in child_model or type(child_model[i]) is not bool for i in range(1,len(edge['names'])+1))
                or not holds(child['cnf'],child_model)):
            raise ValueError('Invalid learned continuation child model')
        source=h._load(self.bases[record['base_sha256']]['source'])['cnf']
        model={abs(l):False for c in source for l in c};model.update(fixed)
        model.update((v,child_model[i]) for i,v in enumerate(edge['names'],1))
        if record['probing']['status']=='equivalence':
            for v,rep in record['probing']['witness']['mapping']:
                model[v]=model[abs(rep)] if rep>0 else not model[abs(rep)]
        if not holds(source,model):raise ValueError('Learned continuation lift violates source')
        return model


class ContinuedLearningRoutes(LearnedTraceRoutes):
    def __init__(self,h,rewrites=(),learning=(),continuations=()):
        super().__init__(h,rewrites,learning)
        self.learned_blocks=LearningBlocks(h,learning,continuations)
        self.learned_blocks.attach(h,self)

    def refresh_learning(self,h):self.learned_blocks.attach(h,self)

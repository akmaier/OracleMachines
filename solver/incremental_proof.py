"""Persistent assumption-aware proof proposals, checked by native Lean LRAT.

Only Tseitin definitions are permanent. Stable source/derived references survive
restarts; a negative certificate contains its entire reachable proof, plus the
formulas needed to reconstruct the shared graph. Unsupported trace events cause
a checked fallback. Archived clauses are never accepted as axioms by the checker.
"""
import hashlib
import json
import subprocess

from solver.incremental import DEFAULT_INCREMENTAL
from solver.resources import BudgetExceeded,exchange,stop_process


def clause_key(clause):
    if not isinstance(clause,list) or any(type(x) is not int or x==0 for x in clause):
        raise ValueError('Invalid proof clause')
    return tuple(sorted(set(clause)))


def dimacs_clauses(text):
    clauses=[];current=[]
    for line in text.splitlines():
        if not line or line[0] in 'cp':continue
        for item in line.split():
            literal=int(item)
            if literal:current.append(literal)
            else:clauses.append(current);current=[]
    if current or not clauses or len(clauses[0])!=1:raise ValueError('Invalid native incremental CNF')
    return clauses


class ProofIncremental:
    certificate_format = "incremental_lrat"
    def __init__(self,service,max_bytes=64*1024**2,store=None,max_replay_clauses=20000):
        self.service=service;self.max_bytes=max_bytes;self.store=store
        self.max_replay_clauses=max_replay_clauses
        self.process=None;self.worker=None;self.loaded=False
        self.restored_nodes=self.restored_clauses=0
        self.history=[];self.steps=[];self.local={};self.sent=set();self.by_clause={}
        self.restored_nodes=0;self.restored_clauses=0

    def close(self):
        stop_process(self.process);self.process=None;self.worker=None;self.loaded=False
        self.restored_nodes=self.restored_clauses=0
        self.history=[];self.steps=[];self.local={};self.sent=set();self.by_clause={}

    def core_id(self,bits):
        return hashlib.sha256(bits.encode()).hexdigest()

    def reuse_checked(self,bits):
        """Native-session refutations survive query changes, never assumptions.

        After restart a selected archived proof is checked once before reuse.
        The bounded syntactic filter is only a proposal; the native checker
        establishes that the refuted formula is a conjunct of the new query.
        """
        rows=self.service.db.execute("SELECT * FROM proofs WHERE engine=? ORDER BY rowid DESC LIMIT 8",
            (self.service.engine_id,)).fetchall()
        parse_work=0
        for row in rows:
            self.service._check_deadline()
            if row['bits'] not in bits:continue
            certificate=self.service._validate_proof(row)
            if not isinstance(certificate,dict) or certificate.get('format')!='incremental_lrat':continue
            token=self.core_id(row['bits'])
            request=dict(mode='negative_reuse',id=token,bits=bits)
            checked=self.service._request(request);parse_work+=checked['parse_work']
            replayed=False
            if not checked['known']:
                registered=self.service._request(dict(mode='negative_register',id=token,
                    bits=row['bits'],certificate=certificate))
                if not registered['valid']:raise ValueError('Archived negative core rejected')
                checked=self.service._request(request);parse_work+=checked['parse_work'];replayed=True
            if checked['valid']:
                return dict(answer=False,witness=None,certificate=dict(format='conjunct',bits=row['bits'],proof=certificate),
                    fast=True,reuse_kind='refutation',backend='incremental_core',nodes=None,core_work=None,
                    parse_work=parse_work,counted_work=None,counted_complete=False,
                    incremental=dict(checked_core_reuse=True,core_revalidated=replayed))
        return None

    def verify_live(self,bits,certificate):
        # A reset/dead worker requires full standalone replay instead.
        if self.worker is not self.service.process or self.worker is None or self.worker.poll() is not None:
            return self.service._request(dict(mode='verify_certificate',bits=bits,certificate=certificate))
        return self.service._request(dict(mode='incremental_verify',bits=bits,text=certificate['text'],id=self.core_id(bits)))

    def load(self,deadline):
        if self.loaded and self.worker is self.service.process and self.worker is not None and self.worker.poll() is None:return
        self.close()
        saved=self.store.restore(deadline) if self.store else dict(nodes=[],clauses=[])
        self.history=saved['nodes'];self.steps=saved['clauses']
        if len(self.history)>=512 or len(self.steps)>100000:
            self.history=[];self.steps=[]  # retain the old archive, start a bounded branch
        self.service._request(dict(mode='incremental_reset'))
        for bits in self.history:
            deadline.check()
            response=self.service._request(dict(mode='incremental_prepare',bits=bits))
            self.restored_nodes=response['nodes']
        for i,step in enumerate(self.steps):
            key=clause_key(step['clause'])
            for parent in step['parents']:
                if parent[0]=='s' and (type(parent[1]) is not int or not 0<=parent[1]<i):
                    raise ValueError('Non-backward saved proof dependency')
                if parent[0] not in ('s','b'):raise ValueError('Unknown proof dependency kind')
            self.by_clause[key]=['s',i]
        if self.store:self.store.start(dict(nodes=self.history,clauses=self.steps))
        self.worker=self.service.process;self.loaded=True

    def certificate(self,root,clauses,deadline):
        base={clause_key(c):i+1 for i,c in enumerate(clauses) if i>0}
        target=self.by_clause.get((-root,)) or self.by_clause.get(())
        if target is None and (-root,) in base:target=['b',[-root]]
        if target is None:return None
        numbered={};lines=[];stack=[(target,False)]
        def number(ref):
            return base.get(clause_key(ref[1])) if ref[0]=='b' else numbered.get(ref[1])
        while stack:
            deadline.check()
            ref,ready=stack.pop()
            if number(ref) is not None:continue
            if ref[0]=='b':return None
            index=ref[1]
            if not 0<=index<len(self.steps):return None
            step=self.steps[index]
            if not ready:
                stack.append((ref,True))
                stack.extend((p,False) for p in reversed(step['parents']) if number(p) is None)
            else:
                parents=[number(p) for p in step['parents']]
                if any(i is None for i in parents):return None
                idx=len(clauses)+len(lines)+1;numbered[index]=idx
                lines.append(' '.join(map(str,[idx]+step['clause']+[0]+parents+[0])))
        final=number(target)
        # Under this query's root assumption, the permanent proof of its negation
        # closes the proof. No old query assumption enters the permanent base.
        lines.append(' '.join(map(str,[len(clauses)+len(lines)+1,0,1,final,0])))
        return dict(format='incremental_lrat',history=list(self.history),text='\n'.join(lines)+'\n')

    def propose(self,bits,deadline):
        try:
            self.load(deadline)
            compiled=self.service._request(dict(mode='incremental_prepare',bits=bits))
            clauses=dimacs_clauses(compiled['dimacs']);root=clauses[0][0]
            base_keys={clause_key(c) for c in clauses[1:]}
            commands=[]
            if self.process is None:
                self.process=subprocess.Popen([str(DEFAULT_INCREMENTAL),'--proof'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
                replay=sorted((k for k in self.by_clause if 0<len(k)<=64),key=lambda k:(len(k),k))[:self.max_replay_clauses]
                for clause in replay:commands.append('ADD '+' '.join(map(str,clause))+' 0')
                self.restored_clauses=len(replay)
            new_definitions=0
            for clause in clauses[1:]:
                key=clause_key(clause)
                if key not in self.sent:
                    commands.append('ADD '+' '.join(map(str,clause))+' 0');self.sent.add(key);new_definitions+=1
            model=[2*i+1 for i in range(compiled['width'])]
            # Native CNF need not mention unused original indices; ADD a tautology
            # reserves them for model extraction without restricting any assignment.
            for v in model:
                key=(-v,v)
                if key not in self.sent:
                    commands.append(f'ADD {v} {-v} 0');self.sent.add(key)
            commands.append('SOLVE '+str(root)+' '+' '.join(map(str,model))+' 0')
            response=json.loads(exchange(self.process,('\n'.join(commands)+'\n').encode(),deadline,self.max_bytes))
            events=response.pop('proof_events',[]);response.pop('learned_export',None)
            new_steps=[];unsupported=0
            for identifier,original,clause,hints in events:
                deadline.check();key=clause_key(clause)
                if original:
                    if key in base_keys:self.local[identifier]=['b',list(key)]
                    elif key in self.by_clause:self.local[identifier]=self.by_clause[key]
                    else:unsupported+=1
                elif all(i in self.local for i in hints) and hints:
                    step=dict(clause=clause,parents=[self.local[i] for i in hints])
                    index=len(self.steps);self.steps.append(step);new_steps.append(step)
                    self.local[identifier]=['s',index];self.by_clause[key]=['s',index]
                else:unsupported+=1
            self.history.append(bits)
            raw,packed=self.store.append([bits],new_steps) if self.store else (0,0)
            certificate=None
            if response['verdict']==20 and not response.get('proof_overflow'):
                certificate=self.certificate(root,clauses,deadline)
            response.update(certificate=certificate,new_definition_clauses=new_definitions,
                shared_nodes=compiled['nodes'],restored_nodes=self.restored_nodes,
                restored_clauses=self.restored_clauses,archived_new_clauses=len(new_steps),
                archived_clauses=len(self.steps),delta_raw_bytes=raw,delta_compressed_bytes=packed,
                unsupported_events=unsupported,proof_history_queries=len(self.history),
                proof_bytes=len(json.dumps(certificate)) if certificate else 0)
            if response['verdict']==10:
                values=response['values']
                if len(values)!=len(model) or any(abs(v)!=i for v,i in zip(values,model)):
                    raise ValueError('Malformed incremental proof model')
                response['witness']=''.join('1' if v>0 else '0' for v in values)
            if len(self.history)>=512 or len(self.steps)>100000 or response.get('proof_overflow'):
                self.close()
            return response
        except BaseException:
            self.close();raise

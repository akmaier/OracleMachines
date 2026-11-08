"""Persistent affine append histories checked by the Lean coefficient solver.

Each append adds a fresh width-b block. Equation coefficients address the old
boundary followed by that fresh block. A saved boundary is never accepted as a
replay certificate: restart replays original equation batches from the archive.
"""
from copy import deepcopy
import time
from solver.knowledge_store import KnowledgeStore


class AffineGrowth:
    @staticmethod
    def create(db):
        db.execute('''CREATE TABLE IF NOT EXISTS affine_states (
            engine TEXT NOT NULL,id TEXT NOT NULL,evidence TEXT NOT NULL,
            answer INTEGER NOT NULL,steps INTEGER NOT NULL,created_ns INTEGER NOT NULL,
            PRIMARY KEY(engine,id))''')

    def __init__(self,service):
        self.service=service
        self.store=KnowledgeStore(service.db,service.engine_id)
        self.worker=None
        self.verified=set()

    def ensure(self,token):
        if self.worker is not self.service.process:
            self.verified.clear();self.worker=self.service.process
        pending=[];seen=set();current=token
        while current not in self.verified:
            self.service._check_deadline()
            if current in seen:raise ValueError('Cyclic affine history')
            if len(pending)>=4096:raise ValueError('Affine replay exceeds native version capacity')
            seen.add(current)
            node=self.store.get(current,'affine_version')
            self.validate_node(node)
            pending.append((current,node))
            if node['base'] is None:break
            current=node['base']
        for name,node in reversed(pending):
            if node['base'] is None:
                request=dict(mode='affine_init',id=name,width=node['width'])
            else:
                parent=self.store.get(node['base'],'affine_version')
                if parent['width']!=node['width']:raise ValueError('Affine history width changed')
                request=dict(mode='affine_append',id=name,base=node['base'],equations=node['equations'])
            self.service._request(request)
            self.verified.add(name)
            self.worker=self.service.process
        return len(pending)

    @classmethod
    def validate_node(cls,node):
        if not isinstance(node,dict) or set(node)!={'width','base','equations'}:
            raise ValueError('Invalid affine history node')
        if type(node['width']) is not int or not 1<=node['width']<=128:
            raise ValueError('Invalid affine history width')
        if node['base'] is None:
            if node['equations']!=[]:raise ValueError('Affine initial node cannot contain equations')
        elif not isinstance(node['base'],str):raise ValueError('Invalid affine history parent')
        cls.validate_equations(node['width'],node['equations'])

    @staticmethod
    def validate_equations(width,equations):
        if not isinstance(equations,list) or len(equations)>4096:
            raise ValueError('Expected at most 4096 affine equations')
        for equation in equations:
            if not isinstance(equation,dict) or set(equation)!={'coefficients','rhs'}:
                raise ValueError('Each affine equation needs coefficients and rhs')
            coefficients=equation['coefficients']
            if not isinstance(coefficients,list) or len(coefficients)!=2*width or any(type(c) is not bool for c in coefficients):
                raise ValueError('Affine coefficients must be 2*width Boolean values')
            if type(equation['rhs']) is not bool:raise ValueError('Affine rhs must be Boolean')

    def run(self,width,equations,base,summary):
        if type(summary) is not bool:raise ValueError('Summary option must be Boolean')
        replayed=registered=0
        before={field:getattr(self.store,field) for field in
                ('inserted_objects','serialized_bytes','inserted_raw_bytes','inserted_packed_bytes','object_reads','read_packed_bytes')}
        try:
            with self.service.db:
                if base is None:
                    if type(width) is not int or not 1<=width<=128:
                        raise ValueError('Affine width must be 1 to 128')
                    base=self.store.put('affine_version',dict(width=width,base=None,equations=[]))[0]
                else:
                    if width is not None:raise ValueError('An affine append keeps the saved width')
                    previous=self.store.get(base,'affine_version')
                    self.validate_node(previous)
                    width=previous['width']
                if equations is not None:self.validate_equations(width,equations)
                replayed=self.ensure(base)
                state=base
                if equations is not None:
                    state=self.store.put('affine_version',dict(width=width,base=base,equations=deepcopy(equations)))[0]
                    registered=self.ensure(state)
                result=self.service._request(dict(mode='affine_query',root=state,summary=summary))
                evidence=self.store.put('affine_result',dict(state=state,result=result))[0]
                self.service.db.execute('INSERT OR IGNORE INTO affine_states VALUES (?,?,?,?,?,?)',
                    (self.service.engine_id,state,evidence,int(result['answer']),result['steps'],time.time_ns()))
            metrics={field:getattr(self.store,field)-value for field,value in before.items()}
            return dict(result,state=state,source='affine_growth',
                        affine_updates=dict(replayed_versions=replayed,registered_versions=registered,**metrics))
        except BaseException:
            self.verified.clear();self.worker=None
            raise

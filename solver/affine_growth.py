"""Persistent affine append histories checked by the Lean coefficient solver.

Each append adds a fresh width-b block. Equation coefficients address the old
boundary followed by that fresh block. A saved boundary is never accepted as a
replay certificate: restart replays original equation batches from the archive.
"""
from copy import deepcopy
from collections import OrderedDict
import time
from solver.affine_archive import AffineArchive


class AffineGrowth:
    @staticmethod
    def create(db):
        db.execute('''CREATE TABLE IF NOT EXISTS affine_states (
            engine TEXT NOT NULL,id TEXT NOT NULL,evidence TEXT NOT NULL,
            answer INTEGER NOT NULL,steps INTEGER NOT NULL,created_ns INTEGER NOT NULL,
            PRIMARY KEY(engine,id))''')

    def __init__(self,service):
        self.service=service
        self.store=AffineArchive(service.db,service.engine_id,service.affine_share_batches)
        self.worker=None
        self.verified=OrderedDict()
        self.dirty=False
        self.evicted_versions=0
        self.native_resets=0
        self.cache_worker=None
        self.cache_slots=None
        self.cache_deduplicate=None
        self.kernel_totals=dict(kernel_hits=0,kernel_misses=0,kernel_evictions=0,
            kernel_key_cells=0,kernel_compare_cell_bound=0,
            executed_reference_cells=0,uncached_reference_cells=0,
            input_rows=0,normalized_rows=0,batch_preparation_hits=0,
            preparation_key_cells=0,preparation_compare_cell_bound=0,normalization_input_cells=0)

    def invalidate(self):
        # A failed transaction may leave newly checked native nodes. Reset on
        # the next request, under its own deadline, before trusting residency.
        self.verified.clear()
        self.dirty=True
        self.worker=self.service.process
        self.store.reset_candidates()

    def ensure(self,token):
        if self.worker is not self.service.process:
            self.verified.clear();self.worker=self.service.process;self.dirty=False
        if self.service.process is None or self.cache_worker is not self.service.process or self.cache_slots!=self.service.affine_kernel_slots or self.cache_deduplicate!=self.service.affine_deduplicate:
            self.service._request(dict(mode='affine_cache_config',slots=self.service.affine_kernel_slots,
                                       deduplicate=self.service.affine_deduplicate))
            self.cache_worker=self.service.process
            self.cache_slots=self.service.affine_kernel_slots
            self.cache_deduplicate=self.service.affine_deduplicate
            self.worker=self.service.process
        if self.dirty:
            if self.service.process is not None:
                self.service._request(dict(mode='affine_reset'))
                self.native_resets+=1
            self.verified.clear();self.dirty=False
        pending=[];seen=set();current=token
        # Only names are retained while walking backwards. Equation batches are
        # reread one at a time in forward order. The replay plan still uses O(T)
        # identifiers; this is not a whole-process constant-memory claim.
        while current not in self.verified:
            self.service._check_deadline()
            if current in seen:raise ValueError('Cyclic affine history')
            seen.add(current)
            node=self.store.get(current,'affine_version')
            self.validate_node(node)
            pending.append(current)
            if node['base'] is None:break
            current=node['base']
        for name in reversed(pending):
            self.service._check_deadline()
            node=self.store.get(name,'affine_version')
            if node['base'] is None:
                request=dict(mode='affine_init',id=name,width=node['width'])
            else:
                parent=self.store.get(node['base'],'affine_version')
                if parent['width']!=node['width']:raise ValueError('Affine history width changed')
                if node['base'] not in self.verified:raise ValueError('Affine replay parent is not resident')
                self.verified.move_to_end(node['base'])
                request=dict(mode='affine_append',id=name,base=node['base'],equations=node['equations'])
            if len(self.verified)>=self.service.native_affine_versions:
                oldest=next(iter(self.verified))
                if oldest==node['base']:raise RuntimeError('Affine retention would evict the required parent')
                self.service._request(dict(mode='affine_drop',ids=[oldest]))
                del self.verified[oldest];self.evicted_versions+=1
            result=self.service._request(request)
            if node['base'] is not None:
                self.kernel_totals['kernel_hits']+=int(result['kernel_cache_hit'])
                self.kernel_totals['kernel_misses']+=int(not result['kernel_cache_hit'])
                self.kernel_totals['kernel_evictions']+=int(result['kernel_evicted'])
                for field in ('kernel_key_cells','kernel_compare_cell_bound'):
                    self.kernel_totals[field]+=result[field]
                self.kernel_totals['executed_reference_cells']+=result['reference_cell_charge']
                self.kernel_totals['uncached_reference_cells']+=result['uncached_reference_cell_charge']
                for field in ('input_rows','normalized_rows','preparation_key_cells',
                              'preparation_compare_cell_bound','normalization_input_cells'):
                    self.kernel_totals[field]+=result['batch_preparation'][field]
                self.kernel_totals['batch_preparation_hits']+=int(result['batch_preparation']['batch_preparation_hit'])
            self.verified[name]=None
            self.worker=self.service.process
        self.verified.move_to_end(token)
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
        old_evictions,old_resets=self.evicted_versions,self.native_resets
        old_kernel=dict(self.kernel_totals)
        before={field:getattr(self.store,field) for field in
                ('inserted_objects','serialized_bytes','inserted_raw_bytes','inserted_packed_bytes','object_reads','read_packed_bytes',
                 'batch_admissions','batch_references','inline_versions')}
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
                result.update(result.pop('batch_preparation'))
                evidence=self.store.put('affine_result',dict(state=state,result=result))[0]
                self.service.db.execute('INSERT OR IGNORE INTO affine_states VALUES (?,?,?,?,?,?)',
                    (self.service.engine_id,state,evidence,int(result['answer']),result['steps'],time.time_ns()))
            metrics={field:getattr(self.store,field)-value for field,value in before.items()}
            metrics.update({field:value-old_kernel[field] for field,value in self.kernel_totals.items()})
            return dict(result,state=state,source='affine_growth',
                        affine_updates=dict(replayed_versions=replayed,registered_versions=registered,
                            evicted_versions=self.evicted_versions-old_evictions,
                            native_resets=self.native_resets-old_resets,
                            resident_versions=len(self.verified),resident_version_cap=self.service.native_affine_versions,**metrics))
        except BaseException:
            self.invalidate()
            raise

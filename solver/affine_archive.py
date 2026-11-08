"""Adaptive lossless sharing of original affine batches.

Logical version identities keep the legacy canonical JSON hash. Existing rows
are never rewritten. Only observed, repeated batches with enough payload saving
are admitted. References preserve row order/multiplicity; they are not semantic
normalization or trusted SAT certificates.
"""
from collections import OrderedDict
import hashlib
import json
import zlib

from solver.knowledge_store import KnowledgeStore


class AffineArchive(KnowledgeStore):
    def __init__(self,db,namespace,share=True):
        super().__init__(db,namespace)
        self.share=share
        self.candidates=OrderedDict()
        self.batch_references=0
        self.batch_admissions=0
        self.inline_versions=0

    def put(self,kind,value):
        if kind!='affine_version' or not self.share or not isinstance(value,dict) or set(value)!={'width','base','equations'} or value['base'] is None:
            return super().put(kind,value)
        raw=json.dumps(value,separators=(',',':'),sort_keys=True).encode()
        token=hashlib.sha256(kind.encode()+b'\0'+raw).hexdigest()
        old=self.db.execute('SELECT payload,codec FROM knowledge_objects WHERE id=?',(token,)).fetchone()
        if old is not None:
            if self.get_raw(token,kind)!=raw:raise ValueError('Affine version content differs')
            return self.put_raw(kind,raw,packed=old[0],codec=old[1])
        compressed=zlib.compress(raw,1)
        packed,codec=(compressed,'zlib') if len(compressed)<len(raw) else (raw,'raw')
        link_template=json.dumps(dict(width=value['width'],base=value['base'],batch='0'*64),
                                 separators=(',',':'),sort_keys=True).encode()
        if len(packed)-len(link_template)<128:
            self.inline_versions+=1
            return self.put_raw(kind,raw,packed=packed,codec=codec)
        # Canonical key order is base/equations/width. Reuse its serialized
        # equation bytes instead of serializing the entire batch a second time.
        prefix=b'{"base":'+json.dumps(value['base'],separators=(',',':')).encode()+b','
        batch_raw=b'{'+raw[len(prefix):]
        key=hashlib.sha256(b'affine_batch\0'+batch_raw).hexdigest()
        repeated=key in self.candidates
        self.candidates[key]=None;self.candidates.move_to_end(key)
        while len(self.candidates)>256:self.candidates.popitem(last=False)
        link=json.dumps(dict(width=value['width'],base=value['base'],batch=key),
                        separators=(',',':'),sort_keys=True).encode()
        # Admit only when each later reference saves at least 128 payload bytes.
        # This is a workload heuristic, not a theorem about SQLite page savings.
        eligible=len(packed)-len(link)>=128
        existing=None
        if eligible:
            existing=self.db.execute('SELECT 1 FROM knowledge_objects WHERE id=? AND kind=?',
                                     (key,'affine_batch')).fetchone()
        if eligible and (repeated or existing):
            # Revalidate any old batch instead of treating its hash as a verdict
            # or silently accepting corrupted/forged content.
            if existing:
                if self.get_raw(key,'affine_batch')!=batch_raw:
                    raise ValueError('Affine batch content differs')
            else:
                self.put_raw('affine_batch',batch_raw)
                self.batch_admissions+=1
            self.batch_references+=1
            return self.put_raw(kind,raw,packed=link,codec='affine_batch_ref_v1')
        self.inline_versions+=1
        return self.put_raw(kind,raw,packed=packed,codec=codec)

    def reset_candidates(self):
        # A rolled-back admission must not count as a completed occurrence.
        self.candidates.clear()

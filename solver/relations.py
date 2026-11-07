"""Exact small-scope relations. Unknown rows remain unknown, never false.

Row bit i refers to the lexicographic Boolean assignment with numeric index i.
Stored relation identity includes arity but not variable names or provenance.
"""
import base64
import itertools
import json
from collections import Counter


def assignments(width):
    return itertools.product((False, True), repeat=width)


def row_index(scope, assignment):
    index = 0
    for variable in scope:
        index = (index << 1) | bool(assignment[variable])
    return index


def dense_pack(rows):
    """Two bitmaps: known and true. Hash sharing cannot erase unknown states."""
    known = bytearray((len(rows)+7)//8)
    values = bytearray(len(known))
    for i, value in enumerate(rows):
        if value is not None:
            if type(value) is not bool:
                raise ValueError('Relation entry must be Boolean or unknown')
            known[i//8] |= 1 << (i%8)
            if value:
                values[i//8] |= 1 << (i%8)
    return dict(rows=len(rows), known=base64.b64encode(known).decode(), values=base64.b64encode(values).decode())


def dense_unpack(value, width):
    n = 1 << width
    if value['rows'] != n:
        raise ValueError('Wrong relation arity')
    known = base64.b64decode(value['known'], validate=True)
    values = base64.b64decode(value['values'], validate=True)
    if len(known) != (n+7)//8 or len(values) != len(known):
        raise ValueError('Wrong relation bitmap size')
    if n%8 and (known[-1] | values[-1]) >> (n%8):
        raise ValueError('Nonzero relation padding')
    if any(v & ~k for k,v in zip(known,values)):
        raise ValueError('Unknown relation row has a truth value')
    return [bool(values[i//8] & (1 << (i%8))) if known[i//8] & (1 << (i%8)) else None for i in range(n)]


def project(inputs, variable, deadline, metrics):
    scope = sorted(set(v for f in inputs for v in f['scope']) - {variable})
    rows, choices = [], []
    for bits in assignments(len(scope)):
        deadline.check()
        assignment = dict(zip(scope,bits))
        possible, unknown, choice = False, False, None
        for value in (False,True):
            assignment[variable] = value
            values = [f['rows'][row_index(f['scope'],assignment)] for f in inputs]
            metrics['table_probes'] += len(values)
            if all(v is True for v in values):
                possible, choice = True, value
                break
            if not any(v is False for v in values):
                unknown = True
        rows.append(True if possible else None if unknown else False)
        choices.append(choice)
        metrics['combination_rows'] += 1
    return scope,rows,choices


def pack(rows):
    """Select an exact representation by serialized bytes, not by its name.

    Reduced ordered decision diagrams are an optional encoding, not a promise
    of polynomial size. Their construction cost is charged to acquisition.
    """
    n=len(rows)
    if not n or n&(n-1):raise ValueError('Relation length must be a power of two')
    dense=dense_pack(rows)
    counts=Counter(rows);default=counts.most_common(1)[0][0]
    candidates=[dense,dict(encoding='sparse',rows=n,default=default,
                         exceptions=[[i,v] for i,v in enumerate(rows) if v is not default])]
    if len(counts)==1:candidates.append(dict(encoding='constant',rows=n,value=default))
    nodes=[];intern={}
    def build(start,length,level):
        if length==1:return 2 if rows[start] is None else int(rows[start])
        left=build(start,length//2,level+1);right=build(start+length//2,length//2,level+1)
        if left==right:return left
        key=(level,left,right)
        if key not in intern:
            intern[key]=len(nodes)+3;nodes.append(list(key))
        return intern[key]
    root=build(0,n,0)
    candidates.append(dict(encoding='bdd',rows=n,root=root,nodes=nodes))
    return min(candidates,key=lambda x:len(json.dumps(x,separators=(',',':'),sort_keys=True)))


def unpack(value,width):
    n=1<<width
    if value.get('rows')!=n:raise ValueError('Wrong relation arity')
    def valid(v):return v is None or type(v) is bool
    encoding=value.get('encoding','dense')
    if encoding=='dense':return dense_unpack(value,width)
    if encoding=='constant':
        if not valid(value['value']):raise ValueError('Invalid constant relation')
        return [value['value']]*n
    if encoding=='sparse':
        if not valid(value['default']):raise ValueError('Invalid sparse default')
        rows=[value['default']]*n;seen=set()
        for i,v in value['exceptions']:
            if type(i) is not int or not 0<=i<n or i in seen or not valid(v):raise ValueError('Invalid sparse row')
            seen.add(i);rows[i]=v
        return rows
    if encoding=='bdd':
        nodes=value['nodes']
        if len(nodes)>n-1:raise ValueError('Oversized relation diagram')
        for i,node in enumerate(nodes,3):
            if len(node)!=3 or any(type(x) is not int for x in node):raise ValueError('Invalid diagram node')
            level,left,right=node
            if not 0<=level<width or not 0<=left<i or not 0<=right<i:raise ValueError('Invalid diagram order')
            if any(child>=3 and nodes[child-3][0]<=level for child in (left,right)):raise ValueError('Non-increasing diagram level')
        if type(value['root']) is not int or not 0<=value['root']<len(nodes)+3:raise ValueError('Invalid diagram root')
        rows=[]
        for i in range(n):
            node=value['root']
            while node>=3:
                level,left,right=nodes[node-3]
                node=right if i & (1 << (width-level-1)) else left
            rows.append(None if node==2 else bool(node))
        return rows
    raise ValueError('Unknown relation representation')

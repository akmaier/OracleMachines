"""Checked wide-clause deletion using shared paths in the retained binary core.

If a path proves -a -> b and a,b occur in a wide clause, the binary core entails
that clause. Binary reasons are never deleted. This is a restricted established
binary-implication simplification, not a new SAT class. Failure is inconclusive.
"""
from collections import deque

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_residual_dag import holds


def _source(cnf, counts):
    for clause in cnf:
        if any(type(lit) is not int or lit == 0 for lit in clause):
            raise ValueError('Invalid binary-path source literal')
        literals=set(clause)
        if len(literals)!=len(clause) or any(-l in literals for l in literals):
            raise ValueError('Binary-path source requires normalized clauses')
        counts['binary_path_source_literals']+=len(clause)


def _limit(limit):
    if type(limit) is not int or limit<0:raise ValueError('Invalid binary-path root limit')


def discover_binary_paths(cnf, counts, *, root_limit=64):
    _limit(root_limit);_source(cnf,counts)
    graph={}
    for cid,clause in enumerate(cnf):
        if len(clause)==2:
            a,b=clause
            graph.setdefault(-a,[]).append((b,cid));graph.setdefault(-b,[]).append((a,cid))
            counts['binary_path_graph_edges']+=2
    reached={};proof=[];ids={};removed=[]

    def reach(root):
        if root in reached:
            counts['binary_path_reach_hits']+=1;return reached[root]
        if root not in graph:return {}
        if len(reached)>=root_limit:
            counts['binary_path_budget_skips']+=1;return {}
        parents={root:None};queue=deque([root])
        while queue:
            vertex=queue.popleft()
            for target,cid in graph.get(vertex,()):
                counts['binary_path_edge_visits']+=1
                if target not in parents:
                    parents[target]=(vertex,cid);queue.append(target)
        reached[root]=parents;counts['binary_path_reach_roots']+=1
        counts['binary_path_reached_entries']+=len(parents)
        return parents

    def save(root,target,parents):
        pending=[];current=target
        while (root,current) not in ids:
            parent=parents[current]
            if parent is None:
                ids[root,current]=len(proof);proof.append([root]);break
            previous,cid=parent;pending.append((current,previous,cid));current=previous
        for current,previous,cid in reversed(pending):
            ids[root,current]=len(proof);proof.append([ids[root,previous],current,cid])
        return ids[root,target]

    for cid,clause in enumerate(cnf):
        if len(clause)<=2:continue
        found=False
        for a in clause:
            parents=reach(-a)
            if not parents:continue
            for b in clause:
                counts['binary_path_pair_queries']+=1
                if b in parents:
                    removed.append([cid,save(-a,b,parents)]);found=True;break
            if found:break
    counts['binary_path_discoveries']+=1;counts['binary_path_proof_nodes']+=len(proof)
    counts['binary_path_removed_clauses']+=len(removed)
    counts['binary_path_removed_literals']+=sum(len(cnf[cid]) for cid,_ in removed)
    return dict(proof=proof,removed=removed)


def check_binary_paths(cnf, certificate, counts, *, root_limit=64):
    """Validate every shared path and retained reason, without reachability search.

    An empty proposal proves no completeness or nonmembership claim. Positive
    witnesses must be source-bound; all omitted clauses retain binary reasons.
    """
    _limit(root_limit);_source(cnf,counts)
    if type(certificate) is not dict or set(certificate)!={'proof','removed'}:
        raise ValueError('Invalid binary-path certificate fields')
    proof,removed=certificate['proof'],certificate['removed']
    if type(proof) is not list or type(removed) is not list:raise ValueError('Invalid binary-path lists')
    labels=[];roots=set();used=set()
    for i,step in enumerate(proof):
        if type(step) is not list or any(type(v) is not int for v in step):
            raise ValueError('Invalid binary-path proof node')
        if len(step)==1:
            root=step[0]
            if root==0 or root in roots:raise ValueError('Invalid binary-path root')
            roots.add(root);labels.append((root,root))
        elif len(step)==3:
            parent,target,cid=step
            if not 0<=parent<i or not 0<=cid<len(cnf) or len(cnf[cid])!=2:
                raise ValueError('Invalid retained binary reason or parent')
            root,previous=labels[parent];a,b=cnf[cid]
            if not ((a==-previous and b==target) or (b==-previous and a==target)):
                raise ValueError('Invalid binary implication edge')
            labels.append((root,target));used.add(parent)
        else:raise ValueError('Invalid binary-path proof arity')
        counts['binary_path_checked_proof_nodes']+=1
    if len(roots)>root_limit:raise ValueError('Exceeded binary-path root limit')
    discarded=set();last=-1
    for witness in removed:
        if type(witness) is not list or len(witness)!=2 or any(type(v) is not int for v in witness):
            raise ValueError('Invalid binary-path removal')
        cid,end=witness
        if not last<cid<len(cnf) or len(cnf[cid])<=2 or not 0<=end<len(labels):
            raise ValueError('Invalid removed wide clause or endpoint')
        root,target=labels[end];clause=cnf[cid]
        if -root not in clause or target not in clause:raise ValueError('Path does not entail removed clause')
        counts['binary_path_checked_clause_literals']+=len(clause)
        last=cid;discarded.add(cid);used.add(end)
    if used!=set(range(len(proof))):raise ValueError('Unused binary-path proof nodes')
    counts['binary_path_checks']+=1
    return tuple(tuple(c) for i,c in enumerate(cnf) if i not in discarded)


class BinaryPathInventory(PolarityHornInventory):
    def __init__(self,*args,binary_path_root_limit=64,**kwargs):
        _limit(binary_path_root_limit);super().__init__(*args,**kwargs)
        self.config.update(binary_paths='retained-binary-shared-prefix-v1',binary_path_root_limit=binary_path_root_limit)

    def _eligible_binary_paths(self,profile,groups):
        return (len(groups)<=1 and not self._recognized(profile)
                and not self._uses_simplification(profile,groups)
                and not self._uses_projection(profile,groups) and not self._uses_probe(profile))

    def _discover_profile(self,cnf,depth,profile,groups):
        if not self._eligible_binary_paths(profile,groups):
            return super()._discover_profile(cnf,depth,profile,groups)
        certificate=discover_binary_paths(cnf,self.counts,root_limit=self.config['binary_path_root_limit'])
        target=check_binary_paths(cnf,certificate,self.counts,root_limit=self.config['binary_path_root_limit'])
        if certificate['removed']:
            edge=self._edge(target,depth)
            return dict(cnf=[list(c) for c in cnf],depth=depth,profile=profile,kind='binary_paths',
                        binary_paths=certificate,edge=edge,summary=self._summary([edge]))
        node=super()._discover_profile(cnf,depth,profile,groups);node['binary_paths']=certificate
        return node

    def _check_profile(self,key,node,cnf,profile,groups):
        if not self._eligible_binary_paths(profile,groups):
            if 'binary_paths' in node:raise ValueError('Unexpected binary-path proposal')
            return super()._check_profile(key,node,cnf,profile,groups)
        certificate=node.get('binary_paths')
        target=check_binary_paths(cnf,certificate,self.counts,root_limit=self.config['binary_path_root_limit'])
        if not certificate['removed']:
            return super()._check_profile(key,{k:v for k,v in node.items() if k!='binary_paths'},cnf,profile,groups)
        if set(node)!={'cnf','depth','profile','kind','binary_paths','edge','summary'} or node['kind']!='binary_paths':
            raise ValueError('Missing binary-path reduction edge')
        if len(target)>=len(cnf):raise ValueError('Binary-path reduction must remove clauses')
        self._check_edge(node['edge'],target,node['depth'])
        if encode(node['summary'])!=encode(self._summary([node['edge']])):
            raise ValueError('Invalid binary-path coverage summary')

    def lift(self,key,child_model):
        node=self._load(key)
        if node['kind']!='binary_paths':return super().lift(key,child_model)
        edge=node['edge'];child=self._load(edge['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool for i in range(1,len(edge['names'])+1))
                or not holds(child['cnf'],child_model)):
            raise ValueError('Invalid binary-path child model')
        model={abs(lit):False for c in node['cnf'] for lit in c}
        model.update((v,child_model[i]) for i,v in enumerate(edge['names'],1))
        if not holds(node['cnf'],model):raise ValueError('Lift violates binary-path source')
        return model

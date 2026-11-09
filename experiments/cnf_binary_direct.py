"""Direct-subsumption control for the binary-path acquisition experiment."""
from experiments.cnf_binary_paths import BinaryPathInventory, check_binary_paths, _source, _limit
from experiments.cnf_polarity_horn import PolarityHornInventory


def discover_direct_paths(cnf,counts,*,root_limit=64):
    _limit(root_limit);_source(cnf,counts)
    graph={}
    for cid,clause in enumerate(cnf):
        if len(clause)==2:
            a,b=clause
            graph.setdefault(-a,{})[b]=cid;graph.setdefault(-b,{})[a]=cid
            counts['binary_direct_graph_edges']+=2
    proof=[];ids={};roots={};removed=[]
    for cid,clause in enumerate(cnf):
        if len(clause)<=2:continue
        found=False
        for a in clause:
            root=-a
            for b in clause:
                counts['binary_direct_pair_queries']+=1
                reason=graph.get(root,{}).get(b)
                if reason is None:continue
                if root not in roots:
                    if len(roots)>=root_limit:continue
                    roots[root]=len(proof);proof.append([root])
                if (root,b) not in ids:
                    ids[root,b]=len(proof);proof.append([roots[root],b,reason])
                removed.append([cid,ids[root,b]]);found=True;break
            if found:break
    counts['binary_direct_removed_clauses']+=len(removed)
    return dict(proof=proof,removed=removed)


class BinaryDirectInventory(BinaryPathInventory):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.config['binary_paths']='retained-binary-direct-control-v1'

    def _discover_profile(self,cnf,depth,profile,groups):
        if not self._eligible_binary_paths(profile,groups):
            return PolarityHornInventory._discover_profile(self,cnf,depth,profile,groups)
        certificate=discover_direct_paths(cnf,self.counts,root_limit=self.config['binary_path_root_limit'])
        target=check_binary_paths(cnf,certificate,self.counts,root_limit=self.config['binary_path_root_limit'])
        if certificate['removed']:
            edge=self._edge(target,depth)
            return dict(cnf=[list(c) for c in cnf],depth=depth,profile=profile,kind='binary_paths',
                        binary_paths=certificate,edge=edge,summary=self._summary([edge]))
        node=PolarityHornInventory._discover_profile(self,cnf,depth,profile,groups)
        node['binary_paths']=certificate;return node

"""Exact first-witness subsumption via one required-literal posting per clause.

A retained clause can subsume a target only if its selected anchor occurs there.
Candidate ranks preserve the old deterministic first-witness policy. Independent
checking rebuilds its own index from the actual source; there is no proposal cache.
"""
from collections import Counter, defaultdict
from experiments.cnf_implied_subsumption import (
    ImpliedSubsumptionInventory, indexed_certificate, original_implications)
from experiments.cnf_additive_elimination import AdditiveEliminationInventory
from experiments.cnf_clause_bound_elimination import ClauseBoundEliminationInventory
from experiments.cnf_pattern_inventory import encode


def anchored_certificate(cnf, counts, *, phase='discovery'):
    widths=[len(c) for c in cnf]
    if len(set(widths))<=1:
        # The old exact-duplicate lookup already avoids every strict subset
        # test on uniform-width normalized input. Do not build postings here.
        counts['anchor_uniform_width_fallbacks']+=1
        return indexed_certificate(cnf,counts,phase=phase)
    sets=[frozenset(c) for c in cnf]
    counts['anchor_preparation_literals']+=sum(widths)
    if any(len(s)!=w for s,w in zip(sets,widths)):
        counts['anchor_repeated_literal_fallbacks']+=1
        return indexed_certificate(cnf,counts,phase=phase)
    frequencies=Counter(l for c in cnf for l in c)
    postings=defaultdict(list); kept=[]; removed=[]; exact={}; empty=None
    counts['anchor_'+phase+'_calls']+=1
    for j in sorted(range(len(cnf)),key=lambda j:(widths[j],j)):
        witness=empty if widths[j] else None
        if witness is None:
            candidates=[]
            for literal in sets[j]:
                counts['anchor_posting_lookups']+=1
                bucket=postings.get(literal,())
                counts['anchor_posting_entries']+=len(bucket)
                candidates.extend(rank for rank in bucket if widths[kept[rank]]<widths[j])
            # Each retained nonempty clause has one anchor, so no deduplication
            # is needed. Numeric ranks preserve the old width/source order.
            counts['anchor_candidate_ranks']+=len(candidates)
            for rank in sorted(candidates):
                k=kept[rank]; counts['anchor_'+phase+'_subset_tests']+=1
                if sets[k]<=sets[j]: witness=k; break
        if witness is None:
            counts['anchor_exact_lookups']+=1; witness=exact.get(sets[j])
        if witness is None:
            rank=len(kept); kept.append(j); exact[sets[j]]=j
            if sets[j]:
                anchor=min(sets[j],key=lambda l:(frequencies[l],l))
                postings[anchor].append(rank); counts['anchor_retained_postings']+=1
            else: empty=j
        else: removed.append([j,witness])
    return dict(kept=sorted(kept),removed=removed)


def check_anchored_subsumption(cnf, certificate, counts, *, phase='check'):
    if not isinstance(certificate,dict) or set(certificate)!={'kept','removed'}:
        raise ValueError('Invalid anchored subsumption fields')
    kept,removed=certificate['kept'],certificate['removed']
    if (not isinstance(kept,list) or not isinstance(removed,list) or
        any(type(i) is not int or not 0<=i<len(cnf) for i in kept) or
        any(not isinstance(pair,list) or len(pair)!=2 or
            any(type(i) is not int or not 0<=i<len(cnf) for i in pair) for pair in removed)):
        raise ValueError('Invalid anchored source indices')
    if sorted(kept+[j for j,_ in removed])!=list(range(len(cnf))):
        raise ValueError('Anchored subsumption must cover every clause exactly once')
    retained=set(kept); sets=[set(c) for c in cnf]
    for j,k in removed:
        counts['anchor_verified_witnesses']+=1
        if k not in retained or not sets[k]<=sets[j]:
            raise ValueError('Invalid retained anchored subset witness')
    # Rebuild independently, including exact first-witness order. Discovery's
    # index and any returned mutable certificate are not reused by the checker.
    if certificate!=anchored_certificate(cnf,counts,phase=phase):
        raise ValueError('Incorrect anchored subsumption policy')
    return tuple(tuple(cnf[i]) for i in kept)


class AnchoredSubsetMixin:
    """Same persisted policy and certificates; only the search index changes."""
    def _find_core(self, cnf, profile, saved=None):
        if saved is not None and (not isinstance(saved,dict) or
                not {'certificate','core_profile'}<=set(saved)):
            raise ValueError('Missing original subset search')
        if saved is None:
            cert=anchored_certificate(cnf,self.counts); core=tuple(cnf[i] for i in cert['kept'])
        else:
            cert=saved['certificate']; core=check_anchored_subsumption(cnf,cert,self.counts)
        core_profile=self._core_profile(core); data=dict(certificate=cert,core_profile=core_profile)
        if saved is not None and encode(saved['core_profile'])!=encode(core_profile):
            raise ValueError('Invalid original subset profile')
        if self.reuse_implications and not self._recognized(core_profile):
            implications=original_implications(cnf,profile['probing'].get('attempts',[]),self.counts)
            if implications:
                augmented=tuple(tuple(c) for c in cnf)+tuple(tuple(c['clause']) for c in implications)
                if saved is None:
                    augmented_cert=anchored_certificate(augmented,self.counts,phase='implied_discovery')
                    core=tuple(augmented[i] for i in augmented_cert['kept'])
                else:
                    proposed=saved.get('implied',{})
                    if not isinstance(proposed,dict) or encode(proposed.get('implications'))!=encode(implications):
                        raise ValueError('Invalid original implication origins or clauses')
                    augmented_cert=proposed.get('certificate')
                    core=check_anchored_subsumption(augmented,augmented_cert,self.counts,phase='implied_check')
                core_profile=self._core_profile(core)
                data['implied']=dict(implications=implications,certificate=augmented_cert,core_profile=core_profile)
            else: data['implied']=dict(implications=[])
        if saved is not None and encode(data)!=encode(saved):
            raise ValueError('Invalid implication-subset search or classification')
        return core,core_profile,data


class AnchoredImpliedInventory(AnchoredSubsetMixin,ImpliedSubsumptionInventory): pass
class AnchoredClauseInventory(AnchoredSubsetMixin,ClauseBoundEliminationInventory): pass
class AnchoredAdditiveInventory(AnchoredSubsetMixin,AdditiveEliminationInventory): pass

"""Bounded reuse of successful, exactly source-bound probe checks.

This changes neither discovery nor the persistent proof format. The cache is
private, ephemeral and empty on restart. Full source/proof/policy serialization
is charged on every lookup; a hit returns a fresh decoded result. There is no
reuse by object identity, partial signature, assumption alone or unverified hint.
"""
from collections import OrderedDict
import json

from experiments.cnf_implied_subsumption import ImpliedSubsumptionInventory
from experiments.cnf_pattern_inventory import encode


class CheckedProbeReuseInventory(ImpliedSubsumptionInventory):
    def __init__(self, *args, checked_probe_bytes=1024 * 1024, **kwargs):
        if type(checked_probe_bytes) is not int or checked_probe_bytes < 0:
            raise ValueError('Checked probe cache budget must be a nonnegative integer')
        super().__init__(*args, **kwargs)
        # Deliberately no config/persistent identity change: same proofs/policy.
        self._probe_cache_limit = checked_probe_bytes
        self._probe_cache = OrderedDict()
        self._probe_cache_bytes = 0
        self._probe_cache_peak = 0

    def probe_cache_state(self):
        """Logical serialized bytes, not Python allocator or process RSS bytes."""
        return dict(entries=len(self._probe_cache), bytes=self._probe_cache_bytes,
                    peak_bytes=self._probe_cache_peak, limit_bytes=self._probe_cache_limit)

    def _check_probes(self, cnf, result):
        if not self._probe_cache_limit:
            return super()._check_probes(cnf, result)
        # JSON identifies lists and tuples. The old checker specifically requires
        # its original attempts container to be a list, unlike its iterable unit
        # traces/CNF containers. Do not let an encoded hit bypass that obligation.
        if not isinstance(result.get('attempts'), list):
            self.counts['checked_probe_uncacheable_inputs'] += 1
            return super()._check_probes(cnf, result)
        # encode emits ASCII JSON. Exact strings avoid hash-collision acceptance
        # and distinguish bools from integers. All inputs affecting this fixed
        # checker are bound; tuple/list CNF containers have the same semantics.
        key = encode([self.config, cnf, result])
        self.counts['checked_probe_lookup_calls'] += 1
        self.counts['checked_probe_key_bytes'] += len(key)
        saved = self._probe_cache.get(key)
        if saved is not None:
            self._probe_cache.move_to_end(key)
            self.counts['checked_probe_hits'] += 1
            self.counts['checked_probe_decoded_bytes'] += len(saved)
            target, fixed = json.loads(saved)
            return tuple(tuple(c) for c in target), dict(fixed)
        self.counts['checked_probe_misses'] += 1
        # Only the existing checker can admit a result. Exceptions admit nothing.
        target, fixed = super()._check_probes(cnf, result)
        saved = encode([target, sorted(fixed.items())])
        self.counts['checked_probe_result_bytes'] += len(saved)
        size = len(key) + len(saved)
        if size > self._probe_cache_limit:
            self.counts['checked_probe_oversize'] += 1
            return target, fixed
        while self._probe_cache_bytes + size > self._probe_cache_limit:
            old_key, old_value = self._probe_cache.popitem(last=False)
            self._probe_cache_bytes -= len(old_key) + len(old_value)
            self.counts['checked_probe_evictions'] += 1
        self._probe_cache[key] = saved
        self._probe_cache_bytes += size
        self._probe_cache_peak = max(self._probe_cache_peak, self._probe_cache_bytes)
        self.counts['checked_probe_admissions'] += 1
        self.counts['checked_probe_admitted_bytes'] += size
        return target, fixed

    def close(self):
        self._probe_cache.clear()
        self._probe_cache_bytes = 0
        super().close()

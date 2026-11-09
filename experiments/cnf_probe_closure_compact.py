"""Same checked closure reuse with a replacement, rather than additive, tag.

Full exact keys repeat policy metadata on every node and edge. Replacing the
local-learning policy version preserves namespace separation without storing an
extra option on every key. The verbose trial remains independently replayable.
"""
from experiments.cnf_probe_closure_reuse import ProbeClosureReuseInventory


class CompactProbeClosureInventory(ProbeClosureReuseInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.config['probe_closure_reuse']
        self.config['probe_learning'] = 'inactive-closure-ref-v2'

# Preserved generator preflight failure

The producer failed before freezing the protocol or running acquisition. It tried
to remove a compacted minimal-core clause from the original template, whose variable
coordinates differ after two irrelevant variables disappear. `producer-source.py`
is the exact failed source; `failure.txt` is the traceback. The correction maps
clause selection back to the original normalized source. This was not a failure
of the signed-subsumption equivalence checker. No measured outcome was used to
select replacement inputs.

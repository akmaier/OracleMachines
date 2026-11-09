# Activity-based continuation pilot

The four controls are previous source IDs 956, 977, 1024 and 1189. Both the
existing core policy and the new activity policy close 956 and 1024, while 977
and 1189 remain open. The core-order regression on 956 is therefore recovered.
Source 977's selected unresolved part shrinks from two leaves / 138 literals to
one leaf / 22 literals. This is reduced remaining interaction, not a new closure.

Local caps, learned batch selection, core children and the independent solver
are unchanged. All three archives replay byte-identically, and warm replay adds
no records. Selected pilot times are not a full-workload performance claim. See
the [full activity experiment](../cnf-activity/README.md).

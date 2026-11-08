import OracleMachines.LayeredSource
import OracleMachines.SourceUpdates
import OracleMachines.AffineProtocol
import OracleMachines.SourceInvariant
import OracleMachines.LayeredCosts
import OracleMachines.FragmentProtocol
import OracleMachines.ChainProtocol
import OracleMachines.Scaling
import OracleMachines.InterfaceCosts
import OracleMachines.IncrementalProof
import OracleMachines.Invariant
import OracleMachines.Limits
import OracleMachines.Reuse
import OracleMachines.Cache
import OracleMachines.Restricted
import OracleMachines.StackMachine
import OracleMachines.Canonical
import OracleMachines.Knowledge
import OracleMachines.BoundedSearch
import OracleMachines.CompactExpansion
import OracleMachines.SearchMachine
import OracleMachines.InterfaceProtocol
import Lean.Util.CollectAxioms

/-!
# Axiom audit

Check every declaration in the project namespace, including transitive proof
dependencies. Reject admitted proofs, custom axioms, and native-decision axioms.
Only Lean's standard propositional extensionality, choice, and quotient axioms
are permitted. This audit is included in the default `lake build` target.
-/

open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let allowed := #[``propext, ``Classical.choice, ``Quot.sound]
  let mut declarations := 0
  let mut theorems := 0
  for (name, info) in env.constants.toList do
    if (`OracleMachines).isPrefixOf name then
      declarations := declarations + 1
      if info matches .thmInfo _ then
        theorems := theorems + 1
      for axiomName in ← collectAxioms name do
        unless allowed.contains axiomName do
          throwError "Unapproved axiom {axiomName} in {name}"
  if theorems == 0 then
    throwError "The project namespace contains no theorem declarations"
  logInfo m!"Axiom audit passed: {declarations} declarations, {theorems} theorem declarations."

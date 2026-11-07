import OracleMachines.CDCL

/-! Permanent Tseitin definitions for every node of a shared graph. Query roots
are assumptions, never permanent unit clauses. The graph may include arbitrary
previous queries: its definitions have an extension for every input valuation. -/
namespace OracleMachines.SAT
open Std.Sat Std.Sat.AIG

def stableVariable {aig : AIG Nat} : CNFVar aig → Nat
  | .inl i => 2 * i
  | .inr i => 2 * i.val + 1

theorem stableVariable_injective {aig : AIG Nat} :
    Function.Injective (@stableVariable aig) := by
  intro a b h
  cases a <;> cases b <;> simp only [stableVariable] at h
  · congr; omega
  · omega
  · omega
  · congr; apply Fin.ext; omega

/- Adapted from Lean Std.Sat.AIG.CNF toCNF.go, copyright 2024 Lean FRO,
Apache-2.0, author Henrik Böving. The upstream local helper is not exported. -/
def collectDefinitions (aig : AIG Nat) (upper : Nat) (h : upper < aig.decls.size) (state : toCNF.State aig) :
    { out : toCNF.State aig // toCNF.State.IsExtensionBy state out upper h } :=
  if hmarked : state.cache.marks[upper]'(by have := state.cache.hmarks; omega) then
    ⟨state, by apply toCNF.State.IsExtensionBy_rfl <;> assumption⟩
  else
    let decl := aig.decls[upper]
    match heq : decl with
    | .false => state.addFalse upper h heq
    | .atom _ => state.addAtom upper h heq
    | .gate lhs rhs =>
      have := aig.hdag h heq
      let ⟨lstate, hlstate⟩ := collectDefinitions aig lhs.gate (by omega) state
      let ⟨rstate, hrstate⟩ := collectDefinitions aig rhs.gate (by omega) lstate

      have : toCNF.State.IsExtensionBy state rstate lhs.gate (by omega) := by
        apply toCNF.State.IsExtensionBy_trans_left
        · exact hlstate
        · exact hrstate

      let ⟨ret, hretstate⟩ := rstate.addGate upper h heq this.trueAt hrstate.trueAt
      ⟨
        ret,
        by
          apply toCNF.State.IsExtensionBy_trans_right
          · exact hlstate
          · apply toCNF.State.IsExtensionBy_trans_right
            · exact hrstate
            · exact hretstate
      ⟩

def allDefinitions (aig : AIG Nat) : toCNF.State aig :=
  (List.finRange aig.decls.size).foldl
    (fun state i => (collectDefinitions aig i.val i.isLt state).val) (.empty aig)

def incrementalCNF (entry : Entrypoint Nat) : CNF Nat :=
  let root : CNF.Clause (CNFVar entry.aig) :=
    [(.inr ⟨entry.ref.gate, entry.ref.hgate⟩, !entry.ref.invert)]
  CNF.relabel stableVariable (root :: (allDefinitions entry.aig).cnf)

theorem incrementalCNF_unsat (entry : Entrypoint Nat)
    (h : (incrementalCNF entry).Unsat) : entry.Unsat := by
  have hu := (CNF.unsat_relabel_iff
    (fun _ _ he => stableVariable_injective he)).mp h
  intro v
  have hd : (allDefinitions entry.aig).cnf.eval (toCNF.cnfSatAssignment entry.aig v) = true :=
    (allDefinitions entry.aig).inv v
  have hf := hu (toCNF.cnfSatAssignment entry.aig v)
  rcases entry with ⟨aig, ⟨gate, inv, hgate⟩⟩
  cases inv <;> simpa [CNF.sat_def, hd] using hf

def checkIncrementalLRAT (f : Formula) (previous : AIG Nat)
    (proof : Array Std.Tactic.BVDecide.LRAT.IntAction) : Bool :=
  Std.Tactic.BVDecide.LRAT.check proof (incrementalCNF (compileCircuit f previous).entry)

theorem checkIncrementalLRAT_sound (f : Formula) (previous : AIG Nat)
    (proof : Array Std.Tactic.BVDecide.LRAT.IntAction)
    (h : checkIncrementalLRAT f previous proof = true) : ¬ Satisfiable f := by
  have hu := incrementalCNF_unsat _ (Std.Tactic.BVDecide.LRAT.check_sound _ _ h)
  rintro ⟨v, hv⟩
  have hn := hu v
  rw [(compileCircuit f previous).correct v, hv] at hn
  contradiction

end OracleMachines.SAT

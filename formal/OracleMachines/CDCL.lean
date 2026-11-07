import OracleMachines.Knowledge
import Std.Sat.AIG.CachedGatesLemmas
import Std.Sat.AIG.CNF
import Std.Tactic.BVDecide.LRAT.Checker

/-!
# A verified boundary for an external CDCL solver

AIG construction shares identical gates and simplifies constants. The standard
library's CNF translation and LRAT checker supply the remaining proof chain.
No external solver verdict is trusted. These are semantic guarantees, not the
reference solver's operation-count bounds.
-/
namespace OracleMachines.SAT
open Std.Sat
open Std.Sat.AIG

private theorem prefix_trans {a b c : Array (Decl Nat)}
    (hab : IsPrefix a b) (hbc : IsPrefix b c) : IsPrefix a c := by
  refine { size_le := Nat.le_trans hab.size_le hbc.size_le, idx_eq := ?_ }
  intro i hi
  rw [hbc.idx_eq i (Nat.lt_of_lt_of_le hi hab.size_le), hab.idx_eq i hi]

structure Compiled (f : Formula) (aig : AIG Nat) where
  entry : Entrypoint Nat
  extendsGraph : IsPrefix aig.decls entry.aig.decls
  correct : ∀ v, ⟦entry, v⟧ = f.eval v

def compileCircuit : (f : Formula) → (aig : AIG Nat) → Compiled f aig
  | .falsum, aig =>
    ⟨⟨aig, aig.mkConstCached false⟩, IsPrefix.rfl, by
      intro v; simp [Formula.eval]⟩
  | .var i, aig =>
    ⟨aig.mkAtomCached i, LawfulOperator.isPrefix_aig (f := mkAtomCached) aig i, by
      intro v; simp [Formula.eval]⟩
  | .neg f, aig =>
    let child := compileCircuit f aig
    ⟨child.entry.aig.mkNotCached child.entry.ref, child.extendsGraph, by
      intro v
      simp only [denote_mkNotCached, child.correct, Formula.eval]⟩
  | .conj f g, aig =>
    let left := compileCircuit f aig
    let right := compileCircuit g left.entry.aig
    let pair : BinaryInput right.entry.aig :=
      ⟨left.entry.ref.cast right.extendsGraph.size_le, right.entry.ref⟩
    ⟨right.entry.aig.mkAndCached pair,
      prefix_trans (prefix_trans left.extendsGraph right.extendsGraph)
        (LawfulOperator.isPrefix_aig right.entry.aig pair), by
      intro v
      simp only [denote_mkAndCached]
      have hl := denote.eq_of_isPrefix left.entry right.entry.aig right.extendsGraph (assign := v)
      simpa [pair, Ref.cast, left.correct v, right.correct v, Formula.eval] using
        congrArg (fun b => b && ⟦right.entry, v⟧) hl⟩

def compiledCircuit (f : Formula) : Entrypoint Nat := (compileCircuit f AIG.empty).entry

def compiledCNF (f : Formula) : CNF Nat := AIG.toCNF (compiledCircuit f)

theorem compiledCircuit_correct (f : Formula) (v : Nat → Bool) :
    ⟦compiledCircuit f, v⟧ = f.eval v := (compileCircuit f AIG.empty).correct v

def circuitFalse (f : Formula) : Bool :=
  let e := compiledCircuit f
  e.aig.getConstant e.ref == some false

theorem circuitFalse_sound (f : Formula) (h : circuitFalse f = true) : ¬ Satisfiable f := by
  have hc : (compiledCircuit f).aig.getConstant (compiledCircuit f).ref = some false := by
    simpa [circuitFalse] using h
  intro ⟨v, hv⟩
  have hn := denote_getConstant (assign := v) hc
  rw [compiledCircuit_correct, hv] at hn
  contradiction

theorem compiledCNF_unsat (f : Formula) (h : (compiledCNF f).Unsat) : ¬ Satisfiable f := by
  have hu := (AIG.toCNF_equisat (compiledCircuit f)).mp h
  intro ⟨v, hv⟩
  have hf := compiledCircuit_correct f v
  have hn := hu v
  rw [hf, hv] at hn
  contradiction

def checkLRAT (f : Formula) (proof : Array Std.Tactic.BVDecide.LRAT.IntAction) : Bool :=
  Std.Tactic.BVDecide.LRAT.check proof (compiledCNF f)

theorem checkLRAT_sound (f : Formula) (proof : Array Std.Tactic.BVDecide.LRAT.IntAction)
    (h : checkLRAT f proof = true) : ¬ Satisfiable f :=
  compiledCNF_unsat f (Std.Tactic.BVDecide.LRAT.check_sound proof (compiledCNF f) h)

end OracleMachines.SAT

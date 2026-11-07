import OracleMachines.Components
import Mathlib.Data.List.Dedup

/-!
# Local interface elimination and its evidence boundary

A factor stores the feasible assignments to an ordered finite scope. Existential
elimination joins only the factors mentioning a variable and forgets that
variable. The output is an exact relation, and is in particular entailed by the
inputs. Unknown proposal entries must be represented as possible, never false.
-/
namespace OracleMachines.SAT

structure InterfaceFactor where
  scope : List Nat
  allowed : List Word
  deriving DecidableEq, Repr

def observe (scope : List Nat) (v : Nat → Bool) : Word := scope.map v

def scopeVal : List Nat → Word → Nat → Bool
  | [], _, _ => false
  | i :: ids, bits, j => if j = i then bits.headD false else scopeVal ids bits.tail j

theorem scopeVal_observe (scope : List Nat) (v : Nat → Bool) (i : Nat)
    (hi : i ∈ scope) : scopeVal scope (observe scope v) i = v i := by
  induction scope with
  | nil => simp at hi
  | cons j rest ih =>
    by_cases h : i = j
    · subst i; simp [scopeVal, observe]
    · simp only [List.mem_cons] at hi
      simpa [scopeVal, observe, h] using ih (hi.resolve_left h)

def InterfaceFactor.eval (f : InterfaceFactor) (v : Nat → Bool) : Bool :=
  decide (observe f.scope v ∈ f.allowed)

theorem factor_eval_agrees (f : InterfaceFactor) (v w : Nat → Bool)
    (agree : ∀ i ∈ f.scope, v i = w i) : f.eval v = f.eval w := by
  have h : observe f.scope v = observe f.scope w := List.map_congr_left agree
  simp only [InterfaceFactor.eval, h]

def tabulate (scope : List Nat) (p : (Nat → Bool) → Bool) : InterfaceFactor :=
  ⟨scope, (words scope.length).filter (fun a => p (scopeVal scope a))⟩

theorem tabulate_exact (scope : List Nat) (p : (Nat → Bool) → Bool)
    (depends : ∀ v w, (∀ i ∈ scope, v i = w i) → p v = p w) (v : Nat → Bool) :
    (tabulate scope p).eval v = p v := by
  have agree : p (scopeVal scope (observe scope v)) = p v :=
    depends _ _ (fun i hi => scopeVal_observe scope v i hi)
  simpa [InterfaceFactor.eval, tabulate, observe] using agree

theorem eval_occurs_agrees (f : Formula) (v w : Nat → Bool)
    (agree : ∀ i ∈ occurs f, v i = w i) : f.eval v = f.eval w := by
  induction f with
  | falsum => rfl
  | var i => exact agree i (by simp [occurs])
  | neg f ih => simp only [Formula.eval, ih agree]
  | conj f g ihf ihg =>
    simp only [Formula.eval]
    rw [ihf (fun i hi => agree i (List.mem_append_left _ hi)),
        ihg (fun i hi => agree i (List.mem_append_right _ hi))]

def formulaFactor (f : Formula) (scope : List Nat) : InterfaceFactor :=
  tabulate scope f.eval

theorem formulaFactor_exact (f : Formula) (scope : List Nat)
    (covers : ∀ i ∈ occurs f, i ∈ scope) (v : Nat → Bool) :
    (formulaFactor f scope).eval v = f.eval v := by
  apply tabulate_exact
  intro v w agree
  exact eval_occurs_agrees f v w (fun i hi => agree i (covers i hi))

def factorsEval (fs : List InterfaceFactor) (v : Nat → Bool) : Bool :=
  fs.all (fun f => f.eval v)

def projectPred (fs : List InterfaceFactor) (x : Nat) (v : Nat → Bool) : Bool :=
  factorsEval fs (Function.update v x false) || factorsEval fs (Function.update v x true)

def projectScope (fs : List InterfaceFactor) (x : Nat) : List Nat :=
  ((fs.flatMap InterfaceFactor.scope).filter (fun i => i != x)).dedup

theorem mem_projectScope (fs : List InterfaceFactor) (x i : Nat) :
    i ∈ projectScope fs x ↔ (∃ f ∈ fs, i ∈ f.scope) ∧ i ≠ x := by
  simp [projectScope, List.mem_flatMap]

theorem projectPred_agrees (fs : List InterfaceFactor) (x : Nat) (v w : Nat → Bool)
    (agree : ∀ i ∈ projectScope fs x, v i = w i) :
    projectPred fs x v = projectPred fs x w := by
  have upd : ∀ b, factorsEval fs (Function.update v x b) =
      factorsEval fs (Function.update w x b) := by
    intro b
    have point : ∀ f ∈ fs, f.eval (Function.update v x b) = f.eval (Function.update w x b) := by
      intro f hf
      apply factor_eval_agrees
      intro i hi
      by_cases hx : i = x
      · subst i; simp
      · simp only [Function.update_of_ne hx]
        exact agree i ((mem_projectScope fs x i).mpr ⟨⟨f, hf, hi⟩, hx⟩)
    have mapped := List.map_congr_left point
    have all := congrArg (fun bs : List Bool => bs.all id) mapped
    simpa only [List.all_map, Function.comp_def, id_eq, factorsEval] using all
  simp only [projectPred, upd]

def projectFactor (fs : List InterfaceFactor) (x : Nat) : InterfaceFactor :=
  tabulate (projectScope fs x) (projectPred fs x)

theorem projectFactor_exact (fs : List InterfaceFactor) (x : Nat) (v : Nat → Bool) :
    (projectFactor fs x).eval v = projectPred fs x v :=
  tabulate_exact _ _ (projectPred_agrees fs x) v

theorem projectFactor_entails (fs : List InterfaceFactor) (x : Nat) (v : Nat → Bool)
    (h : factorsEval fs v = true) : (projectFactor fs x).eval v = true := by
  rw [projectFactor_exact, projectPred]
  have same : Function.update v x (v x) = v := Function.update_eq_self x v
  cases hx : v x with
  | false => rw [hx] at same; simp [same, h]
  | true => rw [hx] at same; simp [same, h]

/-- A checked empty relation excludes every assignment, regardless of scope. -/
theorem empty_factor_refutes (q : InterfaceFactor) (empty : q.allowed = [])
    (f : Formula) (entailed : ∀ v, f.eval v = true → q.eval v = true) : ¬ Satisfiable f := by
  rintro ⟨v, hv⟩
  have h := entailed v hv
  simp [InterfaceFactor.eval, empty] at h

/-- Updating a valuation outside a factor's scope cannot affect the factor. -/
theorem factor_update_outside (q : InterfaceFactor) (x : Nat) (b : Bool)
    (v : Nat → Bool) (outside : x ∉ q.scope) : q.eval (Function.update v x b) = q.eval v := by
  apply factor_eval_agrees
  intro i hi
  have ne : i ≠ x := by intro h; subst i; exact outside hi
  exact Function.update_of_ne ne b v

/-- Exact bucket elimination, including the unaffected factors. -/
theorem eliminate_sat_iff (bucket rest : List InterfaceFactor) (x : Nat)
    (outside : ∀ q ∈ rest, x ∉ q.scope) :
    (∃ v, factorsEval (bucket ++ rest) v = true) ↔
    ∃ v, factorsEval (projectFactor bucket x :: rest) v = true := by
  constructor
  · rintro ⟨v, hv⟩
    simp only [factorsEval, List.all_append, Bool.and_eq_true] at hv
    exact ⟨v, by simp [factorsEval, projectFactor_entails bucket x v hv.1, hv.2]⟩
  · rintro ⟨v, hv⟩
    simp only [factorsEval, List.all_cons, Bool.and_eq_true, projectFactor_exact,
      projectPred, Bool.or_eq_true] at hv
    have unchanged : ∀ b, factorsEval rest (Function.update v x b) = true := by
      intro b
      apply List.all_eq_true.mpr
      intro q hq
      rw [factor_update_outside q x b v (outside q hq)]
      exact List.all_eq_true.mp hv.2 q hq
    rcases hv.1 with h | h
    · exact ⟨Function.update v x false, by simpa only [factorsEval, List.all_append, h, Bool.true_and] using unchanged false⟩
    · exact ⟨Function.update v x true, by simpa only [factorsEval, List.all_append, h, Bool.true_and] using unchanged true⟩

/-- A cached node may be reused only when its checked inputs and interface are
unchanged. This is semantic substitution, not a hash-collision assumption. -/
theorem replace_equal_factor (fs : List InterfaceFactor) (a b : InterfaceFactor)
    (same : ∀ v, a.eval v = b.eval v) (v : Nat → Bool) :
    factorsEval (a :: fs) v = factorsEval (b :: fs) v := by
  simp [factorsEval, same v]

/-- All phases are charged; enumeration is the exponential part only. -/
structure InterfaceCosts where
  input : Nat
  decomposition : Nat
  matching : Nat
  acquisition : Nat
  combination : Nat
  verification : Nat
  storage : Nat
  deriving Repr

def InterfaceCosts.total (c : InterfaceCosts) : Nat :=
  c.input + c.decomposition + c.matching + c.acquisition + c.combination + c.verification + c.storage

def expansionWork (cs : List InterfaceCosts) : Nat := (cs.map InterfaceCosts.total).sum

theorem expansionWork_append (cs : List InterfaceCosts) (c : InterfaceCosts) :
    expansionWork (cs ++ [c]) = expansionWork cs + c.total := by simp [expansionWork]

/-- q affected nodes of bag width at most w, per-row budget s, and all remaining
phases H. This does not assume that finding or maintaining the width is free. -/
theorem affected_budget (H q w s actual : Nat) (bound : actual ≤ q * (2 ^ w * s)) :
    H + actual ≤ H + q * (2 ^ w * s) := Nat.add_le_add_left bound H

end OracleMachines.SAT

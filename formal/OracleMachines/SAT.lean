import OracleMachines.Expansion
import Mathlib.Data.List.OfFn

/-!
# A concrete exhaustive SAT solver

Formulas use false, variables, negation, and conjunction. These suffice to
express arbitrary propositional formulas. Variables are natural-number indices;
`width` is one more than the largest index that occurs. The solver enumerates
finite assignments and is proved equivalent to the ordinary valuation semantics.
No exact-solver hypothesis is needed in this module.
-/

namespace OracleMachines.SAT

inductive Formula where
  | falsum
  | var (index : Nat)
  | neg (body : Formula)
  | conj (left right : Formula)
  deriving DecidableEq, Repr

def Formula.eval : Formula → (Nat → Bool) → Bool
  | .falsum, _ => false
  | .var i, v => v i
  | .neg f, v => !(f.eval v)
  | .conj f g, v => f.eval v && g.eval v

def Formula.width : Formula → Nat
  | .falsum => 0
  | .var i => i + 1
  | .neg f => f.width
  | .conj f g => max f.width g.width

def valuation (assignment : Word) (i : Nat) : Bool := assignment.getD i false

def Satisfiable (f : Formula) : Prop := ∃ v : Nat → Bool, f.eval v = true

theorem eval_agrees (f : Formula) (v w : Nat → Bool)
    (agree : ∀ i, i < f.width → v i = w i) : f.eval v = f.eval w := by
  induction f with
  | falsum => rfl
  | var i => exact agree i (by simp [Formula.width])
  | neg f ih => simp only [Formula.eval]; rw [ih agree]
  | conj f g ihf ihg =>
    have hf : ∀ i, i < f.width → v i = w i := fun i hi =>
      agree i (Nat.lt_of_lt_of_le hi (Nat.le_max_left _ _))
    have hg : ∀ i, i < g.width → v i = w i := fun i hi =>
      agree i (Nat.lt_of_lt_of_le hi (Nat.le_max_right _ _))
    simp only [Formula.eval, ihf hf, ihg hg]

theorem valuation_ofFn (n : Nat) (v : Nat → Bool) (i : Nat) (hi : i < n) :
    valuation (List.ofFn (fun j : Fin n => v j)) i = v i := by
  simp [valuation, List.getD, hi]

def solve (f : Formula) : Bool :=
  (words f.width).any (fun a => f.eval (valuation a))

theorem solve_correct (f : Formula) : solve f = true ↔ Satisfiable f := by
  simp only [solve, List.any_eq_true]
  constructor
  · rintro ⟨a, _, ha⟩
    exact ⟨valuation a, ha⟩
  · rintro ⟨v, hv⟩
    let a := List.ofFn (fun i : Fin f.width => v i)
    refine ⟨a, ?_, ?_⟩
    · simp [a]
    · have heq : f.eval (valuation a) = f.eval v :=
        eval_agrees f (valuation a) v (fun i hi => valuation_ofFn f.width v i hi)
      exact heq.trans hv

theorem solve_false_iff (f : Formula) : solve f = false ↔ ¬ Satisfiable f := by
  rw [← solve_correct]
  cases solve f <;> simp

theorem assignment_count (f : Formula) : (words f.width).length = 2 ^ f.width :=
  length_words f.width

def findWitness (f : Formula) : Option Word :=
  (words f.width).find? (fun a => f.eval (valuation a))

theorem witness_sound (f : Formula) (a : Word) (h : findWitness f = some a) :
    f.eval (valuation a) = true :=
  List.find?_some (p := fun b => f.eval (valuation b)) h

theorem no_witness_iff (f : Formula) : findWitness f = none ↔ ¬ Satisfiable f := by
  rw [← solve_false_iff]
  simp [findWitness, solve]

/-- Append exact answers for a chosen finite batch. Retention and correctness
follow without assuming the batch is a complete bounded domain. -/
def extend (old : List (Formula × Bool)) (batch : List Formula) : List (Formula × Bool) :=
  old ++ batch.map (fun f => (f, solve f))

def Exact (entries : List (Formula × Bool)) : Prop :=
  ∀ f b, (f, b) ∈ entries → (b = true ↔ Satisfiable f)

theorem extend_exact (old : List (Formula × Bool)) (batch : List Formula)
    (hold : Exact old) : Exact (extend old batch) := by
  intro f b h
  simp only [extend, List.mem_append, List.mem_map] at h
  rcases h with h | ⟨g, _, hgb⟩
  · exact hold f b h
  · cases hgb
    exact solve_correct f

theorem extend_preserves (old : List (Formula × Bool)) (batch : List Formula)
    (entry : Formula × Bool) (h : entry ∈ old) : entry ∈ extend old batch := by
  exact List.mem_append_left _ h

end OracleMachines.SAT

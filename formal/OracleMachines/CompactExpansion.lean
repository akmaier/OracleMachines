import OracleMachines.Canonical
import OracleMachines.Invariant

/-!
# Uniform compact expansion on a restricted family

The state records coverage, not a table of precomputed answers. Queries still
pay for the restricted solver. Construction uses one unary cell per stage;
the polynomial query bound is the established parser/core ledger, not a claim
about compiled execution or about the cost of the coverage guard itself.
-/
namespace OracleMachines.SAT

abbrev CoverageState := List Unit

def coverageState : Nat → CoverageState
  | 0 => []
  | n + 1 => () :: coverageState n

@[simp] theorem coverageState_length (n : Nat) : (coverageState n).length = n := by
  induction n <;> simp_all [coverageState]

def RestrictedInput (bits : Word) : Prop :=
  ∃ f, decode bits = some f ∧ f.width ≤ Nat.log 2 (bits.length + 1)

def compactAnswer (state : CoverageState) (bits : Word) : Option Bool :=
  if bits.length ≤ state.length then
    match decode bits with
    | none => none
    | some f => if f.width ≤ Nat.log 2 (bits.length + 1) then (decideRun bits).1 else none
  else none

theorem compactAnswer_on_domain (n : Nat) (bits : Word)
    (size : bits.length ≤ n) (restricted : RestrictedInput bits) :
    compactAnswer (coverageState n) bits = (decideRun bits).1 := by
  rcases restricted with ⟨f, valid, cap⟩
  simp [compactAnswer, size, valid, cap]

theorem compactAnswer_preserves (n : Nat) (bits : Word) (size : bits.length ≤ n) :
    compactAnswer (coverageState (n + 1)) bits = compactAnswer (coverageState n) bits := by
  simp [compactAnswer, size, show bits.length ≤ n + 1 by omega]

theorem compactAnswer_eventually (bits : Word) (restricted : RestrictedInput bits) :
    compactAnswer (coverageState bits.length) bits = (decideRun bits).1 :=
  compactAnswer_on_domain bits.length bits le_rfl restricted

theorem compactAnswer_sat (state : CoverageState) (bits : Word)
    (accepted : compactAnswer state bits = some true) : EncodedSAT bits := by
  unfold compactAnswer at accepted
  split at accepted
  · split at accepted
    · contradiction
    · split at accepted
      · exact (decideRun_sat bits).mp accepted
      · contradiction
  · contradiction

theorem compactAnswer_unsat (state : CoverageState) (bits : Word)
    (accepted : compactAnswer state bits = some false) : EncodedUNSAT bits := by
  unfold compactAnswer at accepted
  split at accepted
  · split at accepted
    · contradiction
    · split at accepted
      · exact (decideRun_unsat bits).mp accepted
      · contradiction
  · contradiction

theorem compactAnswer_query_bound (bits : Word) (restricted : RestrictedInput bits) :
    (decideRun bits).2 ≤ 24 * (bits.length + 1) ^ 2 := by
  rcases restricted with ⟨f, valid, cap⟩
  exact decideRun_valid_logarithmic_width bits f valid cap

/-- Explicit unary construction, each transition allocates one cell. -/
inductive CoverageSteps : Nat → CoverageState → CoverageState → Prop where
  | refl (s) : CoverageSteps 0 s s
  | step {n s t} : CoverageSteps n s t → CoverageSteps (n + 1) s (() :: t)

theorem coverage_construction (n : Nat) : CoverageSteps n [] (coverageState n) := by
  induction n with
  | zero => exact .refl []
  | succ n ih => exact .step ih

theorem coverage_space {n : Nat} {s t : CoverageState} (h : CoverageSteps n s t) :
    t.length = s.length + n := by
  induction h <;> simp_all
  omega

theorem compact_acquisition_and_query (bits : Word) (restricted : RestrictedInput bits) :
    bits.length + (decideRun bits).2 ≤ 25 * (bits.length + 1) ^ 2 := by
  have bound := compactAnswer_query_bound bits restricted
  nlinarith [Nat.zero_le bits.length]

end OracleMachines.SAT

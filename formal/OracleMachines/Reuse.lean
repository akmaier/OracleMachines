import OracleMachines.Resources
import Mathlib.Analysis.SpecificLimits.Basic

/-!
# Staged reuse

All query work is charged, including verification and delivery. The identities
hold for real ledgers; their interpretation as work requires nonnegative actual
costs. The comparison is with a fixed restarted solver. No complexity-class
assumption appears in any statement.
-/

namespace OracleMachines

/-- Query indices inside a phase are zero-based; phases start at 1. -/
def phaseWork (Q : Nat → Nat) (r : Nat → Nat → ℝ) (j : Nat) : ℝ :=
  ∑ t ∈ Finset.range (Q j), r j t

def queryWork (Q : Nat → Nat) (r : Nat → Nat → ℝ) (m : Nat) : ℝ :=
  stageSum (phaseWork Q r) m

def totalWork (base : ℝ) (a : Nat → ℝ) (Q : Nat → Nat)
    (r : Nat → Nat → ℝ) (m : Nat) : ℝ :=
  cumulative base (fun j => a j + phaseWork Q r j) m

theorem totalWork_eq (base : ℝ) (a : Nat → ℝ) (Q : Nat → Nat)
    (r : Nat → Nat → ℝ) (m : Nat) :
    totalWork base a Q r m = base + stageSum a m + queryWork Q r m := by
  simp [totalWork, cumulative_eq, stageSum, queryWork, Finset.sum_add_distrib, add_assoc]

theorem queryWork_le (Q : Nat → Nat) (r : Nat → Nat → ℝ) (ell : Nat → ℝ) (m : Nat)
    (bound : ∀ j, 1 ≤ j → j ≤ m → ∀ t, t < Q j → r j t ≤ ell j) :
    queryWork Q r m ≤ stageSum (fun j => (Q j : ℝ) * ell j) m := by
  unfold queryWork stageSum
  apply Finset.sum_le_sum
  intro i hi
  have hi' := Finset.mem_range.mp hi
  calc
    phaseWork Q r (i + 1) ≤ ∑ _t ∈ Finset.range (Q (i + 1)), ell (i + 1) := by
      apply Finset.sum_le_sum
      intro t ht
      exact bound (i + 1) (by omega) (by omega) t (Finset.mem_range.mp ht)
    _ = (Q (i + 1) : ℝ) * ell (i + 1) := by simp

theorem totalWork_le (base : ℝ) (a : Nat → ℝ) (Q : Nat → Nat)
    (r : Nat → Nat → ℝ) (ell : Nat → ℝ) (m : Nat)
    (bound : ∀ j, 1 ≤ j → j ≤ m → ∀ t, t < Q j → r j t ≤ ell j) :
    totalWork base a Q r m ≤ base + stageSum (fun j => a j + (Q j : ℝ) * ell j) m := by
  rw [totalWork_eq]
  have h := queryWork_le Q r ell m bound
  simp only [stageSum, Finset.sum_add_distrib] at *
  linarith

/-- Actual savings are equivalent to saved query work repaying construction. -/
theorem strict_savings_iff (base : ℝ) (a : Nat → ℝ) (Q : Nat → Nat)
    (r s : Nat → Nat → ℝ) (m : Nat) :
    totalWork base a Q r m < queryWork Q s m ↔
      base + stageSum a m < queryWork Q (fun j t => s j t - r j t) m := by
  rw [totalWork_eq]
  simp only [queryWork, stageSum, phaseWork, Finset.sum_sub_distrib]
  constructor <;> intro h <;> linarith

/-- An upper bound on retrieval gives a sufficient, not necessary, criterion. -/
theorem savings_of_upper_bound (base : ℝ) (a : Nat → ℝ) (Q : Nat → Nat)
    (r s : Nat → Nat → ℝ) (ell : Nat → ℝ) (m : Nat)
    (bound : ∀ j, 1 ≤ j → j ≤ m → ∀ t, t < Q j → r j t ≤ ell j)
    (savings : base + stageSum a m <
      queryWork Q s m - stageSum (fun j => (Q j : ℝ) * ell j) m) :
    totalWork base a Q r m < queryWork Q s m := by
  rw [totalWork_eq]
  have h := queryWork_le Q r ell m bound
  linarith

/-- Algebraically true also at zero; only positive query counts have an average
cost interpretation. The asymptotic theorem below makes that explicit. -/
theorem average_identity (base : ℝ) (a : Nat → ℝ) (Q : Nat → Nat)
    (r : Nat → Nat → ℝ) (m : Nat) :
    totalWork base a Q r m / ((stageSum Q m : Nat) : ℝ) -
        queryWork Q r m / ((stageSum Q m : Nat) : ℝ) =
      (base + stageSum a m) / ((stageSum Q m : Nat) : ℝ) := by
  rw [totalWork_eq, add_div]
  ring

open Filter in
theorem amortization_iff (base : ℝ) (a : Nat → ℝ) (Q : Nat → Nat)
    (r : Nat → Nat → ℝ) :
    Tendsto (fun m => totalWork base a Q r m / ((stageSum Q m : Nat) : ℝ) -
      queryWork Q r m / ((stageSum Q m : Nat) : ℝ)) atTop (nhds 0) ↔
    Tendsto (fun m => (base + stageSum a m) / ((stageSum Q m : Nat) : ℝ)) atTop (nhds 0) := by
  simp only [average_identity]

open Filter in
theorem eventually_positive_queries (Q : Nat → Nat)
    (unbounded : Tendsto (fun m => stageSum Q m) atTop atTop) :
    ∀ᶠ m in atTop, 0 < stageSum Q m := by
  filter_upwards [(tendsto_atTop.mp unbounded) 1] with m hm
  omega

end OracleMachines

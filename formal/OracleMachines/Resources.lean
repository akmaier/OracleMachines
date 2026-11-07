import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic

/-!
# Construction budgets

These are theorems about explicitly charged costs. They do not identify those
costs with the runtime of a Turing machine, a RAM, Lean's evaluator, or a SAT
solver. That connection is an additional implementation obligation.
-/

namespace OracleMachines

/-- Stages are numbered 1 through n; stage zero is the separate base cost. -/
def stageSum {α : Type*} [AddCommMonoid α] (f : Nat → α) (n : Nat) : α :=
  ∑ i ∈ Finset.range n, f (i + 1)

@[simp] theorem stageSum_zero {α : Type*} [AddCommMonoid α] (f : Nat → α) :
    stageSum f 0 = 0 := by simp [stageSum]

@[simp] theorem stageSum_succ {α : Type*} [AddCommMonoid α] (f : Nat → α) (n : Nat) :
    stageSum f (n + 1) = stageSum f n + f (n + 1) := by
  simp [stageSum, Finset.sum_range_succ]

def cumulative {α : Type*} [AddCommMonoid α] (base : α) (a : Nat → α) : Nat → α
  | 0 => base
  | n + 1 => cumulative base a n + a (n + 1)

theorem cumulative_eq {α : Type*} [AddCommMonoid α] (base : α) (a : Nat → α) (n : Nat) :
    cumulative base a n = base + stageSum a n := by
  induction n with
  | zero => simp [cumulative]
  | succ n ih => simp [cumulative, ih, add_assoc]

/-- Uniform stage budgets sum to the bound used in Corollary 12.2. -/
theorem polynomial_stage_sum (a : Nat → Nat) (c k n : Nat)
    (budget : ∀ j, 1 ≤ j → a j ≤ c * (j + 1) ^ k) :
    stageSum a n ≤ c * n * (n + 1) ^ k := by
  calc
    stageSum a n ≤ ∑ _i ∈ Finset.range n, c * (n + 1) ^ k := by
      apply Finset.sum_le_sum
      intro i hi
      have hi' : i < n := Finset.mem_range.mp hi
      exact (budget (i + 1) (by omega)).trans
        (Nat.mul_le_mul_left c (pow_le_pow_left' (by omega : i + 1 + 1 ≤ n + 1) k))
    _ = c * n * (n + 1) ^ k := by simp; ring

/-- A single monomial bounds input reading, base, expansion, and evaluation.
The constants and exponents are shared across all input lengths. -/
theorem full_polynomial_bound (readCost base c d k r n : Nat) :
    readCost * (n + 1) + base + c * n * (n + 1) ^ k + d * (2 * n + 1) ^ r ≤
      (readCost + base + c + d * 2 ^ r) * (n + 1) ^ (k + r + 1) := by
  have hone : 1 ≤ n + 1 := by omega
  have hread : n + 1 ≤ (n + 1) ^ (k + r + 1) := by
    simpa using pow_le_pow_right' hone (by omega : 1 ≤ k + r + 1)
  have hbase : 1 ≤ (n + 1) ^ (k + r + 1) := one_le_pow₀ hone
  have hstage : n * (n + 1) ^ k ≤ (n + 1) ^ (k + r + 1) := by
    calc
      n * (n + 1) ^ k ≤ (n + 1) * (n + 1) ^ k := Nat.mul_le_mul_right _ (by omega)
      _ = (n + 1) ^ (k + 1) := by ring
      _ ≤ (n + 1) ^ (k + r + 1) := pow_le_pow_right' hone (by omega)
  have heval : (2 * n + 1) ^ r ≤ 2 ^ r * (n + 1) ^ (k + r + 1) := by
    calc
      (2 * n + 1) ^ r ≤ (2 * (n + 1)) ^ r := pow_le_pow_left' (by omega) r
      _ = 2 ^ r * (n + 1) ^ r := mul_pow _ _ _
      _ ≤ 2 ^ r * (n + 1) ^ (k + r + 1) :=
        Nat.mul_le_mul_left _ (pow_le_pow_right' hone (by omega))
  nlinarith [Nat.mul_le_mul_left readCost hread, Nat.mul_le_mul_left base hbase,
    Nat.mul_le_mul_left c hstage, Nat.mul_le_mul_left d heval]

/-- A cost predicate, not a formal definition of the complexity class P. -/
def PolynomiallyBounded (f : Nat → Nat) : Prop :=
  ∃ C k : Nat, ∀ n, f n ≤ C * (n + 1) ^ k

/-- A polynomial coverage schedule preserves a polynomial stage-cost bound.
This is arithmetic composition, not a claim that the schedule is computable. -/
theorem polynomiallyBounded_comp (f g : Nat → Nat)
    (hf : PolynomiallyBounded f) (hg : PolynomiallyBounded g) :
    PolynomiallyBounded (fun n => f (g n)) := by
  rcases hf with ⟨C, k, hf⟩
  rcases hg with ⟨D, r, hg⟩
  refine ⟨C * (D + 1) ^ k, r * k, ?_⟩
  intro n
  have hp : 1 ≤ (n + 1) ^ r := one_le_pow₀ (by omega)
  have hg' : g n + 1 ≤ (D + 1) * (n + 1) ^ r := by nlinarith [hg n]
  calc
    f (g n) ≤ C * (g n + 1) ^ k := hf (g n)
    _ ≤ C * ((D + 1) * (n + 1) ^ r) ^ k :=
      Nat.mul_le_mul_left C (pow_le_pow_left' hg' k)
    _ = C * (D + 1) ^ k * (n + 1) ^ (r * k) := by rw [mul_pow, pow_mul]; ring

theorem bounded_expansion_cost (a : Nat → Nat) (readCost base c d k r : Nat)
    (budget : ∀ j, 1 ≤ j → a j ≤ c * (j + 1) ^ k) :
    PolynomiallyBounded (fun n =>
      readCost * (n + 1) + cumulative base a n + d * (2 * n + 1) ^ r) := by
  refine ⟨readCost + base + c + d * 2 ^ r, k + r + 1, ?_⟩
  intro n
  dsimp only
  rw [cumulative_eq]
  have hs := polynomial_stage_sum a c k n budget
  have ht := full_polynomial_bound readCost base c d k r n
  omega

/-- Exact exponential costs, even though each stage has a finite cost. -/
theorem exponential_stage_sum (n : Nat) :
    stageSum (fun j => 2 ^ j) n + 2 = 2 ^ (n + 1) := by
  induction n with
  | zero => simp
  | succ n ih => rw [stageSum_succ, pow_succ]; omega

end OracleMachines

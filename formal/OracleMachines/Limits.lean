import OracleMachines.Expansion
import OracleMachines.Resources
import Mathlib.Analysis.SpecificLimits.Normed

/-!
# The missing implication is false without a resource invariant

Exponential storage and expansion are not polynomially bounded. These are
limitations of the explicit construction, not lower bounds for all SAT solvers.
-/

namespace OracleMachines

open Filter Topology

/-- Relate the real-valued limits below to the natural query counts in Reuse. -/
theorem stageSum_natCast (f : Nat → Nat) (n : Nat) :
    ((stageSum f n : Nat) : ℝ) = stageSum (fun j => (f j : ℝ)) n := by
  simp [stageSum]

theorem one_query_count (n : Nat) : stageSum (fun _ => (1 : Nat)) n = n := by
  simp [stageSum]

theorem shifted_polynomial_over_exponential (k : Nat) :
    Tendsto (fun n : Nat => ((n : ℝ) + 1) ^ k / (2 : ℝ) ^ n) atTop (𝓝 0) := by
  have h := (tendsto_pow_const_div_const_pow_of_one_lt k (by norm_num : (1 : ℝ) < 2)).comp
    (tendsto_add_atTop_nat 1)
  have h' := h.const_mul 2
  convert h' using 1
  · funext n
    simp only [Function.comp_apply, Nat.cast_add, Nat.cast_one, pow_succ]
    field_simp
  · norm_num

theorem exponential_not_polynomial : ¬ PolynomiallyBounded (fun n => 2 ^ n) := by
  rintro ⟨C, k, bound⟩
  have hlim := (shifted_polynomial_over_exponential k).const_mul (C : ℝ)
  have lower (n : Nat) : (1 : ℝ) ≤ (C : ℝ) * (((n : ℝ) + 1) ^ k / (2 : ℝ) ^ n) := by
    have hb : (2 : ℝ) ^ n ≤ (C : ℝ) * ((n : ℝ) + 1) ^ k := by
      exact_mod_cast bound n
    rw [← mul_div_assoc]
    exact (le_div_iff₀ (by positivity)).2 (by simpa using hb)
  have impossible : (1 : ℝ) ≤ 0 := by
    simpa using ge_of_tendsto hlim (Eventually.of_forall lower)
  norm_num at impossible

theorem exponential_expansion_not_polynomial :
    ¬ PolynomiallyBounded (stageSum (fun j => 2 ^ j)) := by
  rintro ⟨C, k, bound⟩
  apply exponential_not_polynomial
  refine ⟨C + 2, k, ?_⟩
  intro n
  have hsum := exponential_stage_sum n
  have hp : 1 ≤ (n + 1) ^ k := one_le_pow₀ (by omega)
  have hg : 2 ^ n ≤ 2 ^ (n + 1) := pow_le_pow_right' (by norm_num) (by omega)
  have hb := bound n
  nlinarith

theorem explicit_table_not_polynomial (solver : Word → Bool) :
    ¬ PolynomiallyBounded (fun n => (table solver n).length) := by
  rintro ⟨C, k, bound⟩
  apply exponential_not_polynomial
  refine ⟨C + 1, k, ?_⟩
  intro n
  have hsize := table_answer_count solver n
  have hp : 1 ≤ (n + 1) ^ k := one_le_pow₀ (by omega)
  have hg : 2 ^ n ≤ 2 ^ (n + 1) := pow_le_pow_right' (by norm_num) (by omega)
  have hb := bound n
  dsimp only at hb
  nlinarith

/-- Exact cumulative expansion cost over the reals. -/
theorem exponential_stage_sum_real (n : Nat) :
    stageSum (fun j => (2 : ℝ) ^ j) n = 2 ^ (n + 1) - 2 := by
  induction n with
  | zero => simp
  | succ n ih => rw [stageSum_succ, ih, pow_succ]; ring

/-- The exact query count in the many-query example. -/
theorem geometric_queries (n : Nat) :
    stageSum (fun j => (4 : ℝ) ^ j) n = (4 ^ (n + 1) - 4) / 3 := by
  induction n with
  | zero => simp
  | succ n ih => rw [stageSum_succ, ih, pow_succ]; ring

/-- With one query per stage, exponential expansion cannot be amortized. -/
theorem one_query_expansion_diverges (base : ℝ) :
    Tendsto (fun n => (base + stageSum (fun j => (2 : ℝ) ^ j) n) / (n : ℝ))
      atTop atTop := by
  have hsmall := tendsto_pow_const_div_const_pow_of_one_lt 1 (by norm_num : (1 : ℝ) < 2)
  simp only [pow_one] at hsmall
  have hpos : ∀ᶠ n : Nat in atTop, 0 < (n : ℝ) / (2 : ℝ) ^ n := by
    filter_upwards [eventually_ge_atTop 1] with n hn
    have : 0 < (n : ℝ) := by exact_mod_cast (by omega : 0 < n)
    positivity
  have hgrowth := tendsto_inv_nhdsGT_zero.comp (tendsto_nhdsWithin_iff.mpr ⟨hsmall, hpos⟩)
  change Tendsto (fun n : Nat => ((n : ℝ) / (2 : ℝ) ^ n)⁻¹) atTop atTop at hgrowth
  simp only [inv_div] at hgrowth
  have hconstant := tendsto_const_div_atTop_nhds_zero_nat (base - 2)
  have h := (Tendsto.const_mul_atTop (by norm_num : (0 : ℝ) < 2) hgrowth).atTop_add hconstant
  convert h using 1
  funext n
  dsimp only
  rw [exponential_stage_sum_real, pow_succ]
  ring

/-- With 4^j queries after stage j, the same expansion cost per query vanishes. -/
theorem many_queries_amortize_real (base : ℝ) :
    Tendsto (fun n => (base + stageSum (fun j => (2 : ℝ) ^ j) n) /
      stageSum (fun j => (4 : ℝ) ^ j) n) atTop (𝓝 0) := by
  have htwo : Tendsto (fun n : Nat => (1 / (2 : ℝ)) ^ n) atTop (𝓝 0) :=
    tendsto_pow_atTop_nhds_zero_of_lt_one (by norm_num) (by norm_num)
  have hfour : Tendsto (fun n : Nat => (1 / (4 : ℝ)) ^ n) atTop (𝓝 0) :=
    tendsto_pow_atTop_nhds_zero_of_lt_one (by norm_num) (by norm_num)
  have hnum := (hfour.const_mul (base - 2)).add (htwo.const_mul 2)
  have hden := ((tendsto_const_nhds (x := (1 : ℝ))).sub hfour).const_mul (4 / 3 : ℝ)
  have h := hnum.div hden (by norm_num : (4 / 3 : ℝ) * (1 - 0) ≠ 0)
  convert h using 1
  · funext n
    dsimp only [Pi.div_apply]
    rw [exponential_stage_sum_real, geometric_queries]
    have hp2 : (2 : ℝ) ^ n ≠ 0 := by positivity
    have hp4 : (4 : ℝ) ^ n ≠ 0 := by positivity
    have hp : (4 : ℝ) ^ n = (2 ^ n) ^ 2 := by rw [← pow_mul, mul_comm n 2, pow_mul]; norm_num
    simp only [div_pow, one_pow, pow_succ]
    rw [hp]
    field_simp
    ring
  · norm_num

/-- The same result with an integer-valued number of queries in each phase. -/
theorem many_queries_amortize (base : ℝ) :
    Tendsto (fun n => (base + stageSum (fun j => (2 : ℝ) ^ j) n) /
      ((stageSum (fun j => (4 : Nat) ^ j) n : Nat) : ℝ)) atTop (𝓝 0) := by
  simpa only [stageSum_natCast, Nat.cast_pow, Nat.cast_ofNat] using
    many_queries_amortize_real base

end OracleMachines

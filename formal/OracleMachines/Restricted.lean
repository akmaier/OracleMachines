import OracleMachines.Parsing
import Mathlib.Data.Nat.Log

/-!
# A growing-variable restriction

The variable width need not be constant if the encoded input is sufficiently
long relative to its assignment space. This is a promised-family bound in the
same explicit parser/core cost model, not a reduction from general SAT.
-/

namespace OracleMachines.SAT

theorem decideRun_small_assignment_space (f : Formula)
    (small : 2 ^ f.width ≤ (encode f).length + 1) :
    (decideRun (encode f)).2 ≤ 24 * ((encode f).length + 1) ^ 2 := by
  have hp := decodeRun_bound (encode f)
  have hs := solveRun_bound f
  have hw := weight_le_encoding f
  have hm := Nat.mul_le_mul_right (weight f + 13) small
  simp only [decideRun, decodeRun_value, decode_encode]
  nlinarith [Nat.zero_le (encode f).length]

theorem decideRun_logarithmic_width (f : Formula)
    (small : f.width ≤ Nat.log 2 ((encode f).length + 1)) :
    (decideRun (encode f)).2 ≤ 24 * ((encode f).length + 1) ^ 2 := by
  apply decideRun_small_assignment_space f
  exact Nat.pow_le_of_le_log (Nat.succ_ne_zero _) small

/-- Enforcing the small-space premise by padding already entails exponential
encoded length in the variable width. It is not a polynomial SAT reduction. -/
theorem small_assignment_space_requires_length (f : Formula)
    (small : 2 ^ f.width ≤ (encode f).length + 1) :
    2 ^ f.width - 1 ≤ (encode f).length := by omega

end OracleMachines.SAT

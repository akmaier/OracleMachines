import OracleMachines.InterfaceCosts
import OracleMachines.InterfaceProtocol
import OracleMachines.Resources

/-! Restricted scaling obligations. These bounds include a declared overhead
and archive ledger. They do not assert that the native service satisfies a
polynomial bound, or that unrestricted SAT has bounded elimination width. -/
namespace OracleMachines.SAT

/-- A tree reference for symbolic Boolean operations. Sharing and ordering are
implementation optimizations; the Python ROBDD remains a checked proposal. -/
inductive SymbolicTree where
  | value : Bool → SymbolicTree
  | branch : Nat → SymbolicTree → SymbolicTree → SymbolicTree

def SymbolicTree.eval : SymbolicTree → (Nat → Bool) → Bool
  | .value b, _ => b
  | .branch x lo hi, v => if v x then hi.eval v else lo.eval v

def SymbolicTree.restrict (x : Nat) (b : Bool) : SymbolicTree → SymbolicTree
  | .value a => .value a
  | .branch y lo hi =>
    if x = y then if b then hi.restrict x b else lo.restrict x b
    else .branch y (lo.restrict x b) (hi.restrict x b)

theorem SymbolicTree.restrict_correct (tree : SymbolicTree) (x : Nat) (b : Bool) (v : Nat → Bool) :
    (tree.restrict x b).eval v = tree.eval (Function.update v x b) := by
  induction tree with
  | value a => rfl
  | branch y lo hi ihl ihr =>
    by_cases h : x = y
    · subst y; cases b <;> simp [restrict, eval, ihl, ihr]
    · have h' : y ≠ x := Ne.symm h
      simp [restrict, eval, h, Function.update_of_ne h', ihl, ihr]

def SymbolicTree.combine (op : Bool → Bool → Bool) : SymbolicTree → SymbolicTree → SymbolicTree
  | .value a, .value b => .value (op a b)
  | .value a, .branch x lo hi =>
    .branch x (combine op (.value a) lo) (combine op (.value a) hi)
  | .branch x lo hi, other => .branch x (combine op lo other) (combine op hi other)

theorem SymbolicTree.combine_correct (op : Bool → Bool → Bool) (left right : SymbolicTree)
    (v : Nat → Bool) : (combine op left right).eval v = op (left.eval v) (right.eval v) := by
  induction left with
  | value a =>
    induction right with
    | value b => simp [combine, eval]
    | branch x lo hi ihl ihr => cases h : v x <;> simp [combine, eval, h, ihl, ihr]
  | branch x lo hi ihl ihr => cases h : v x <;> simp [combine, eval, h, ihl, ihr]

def SymbolicTree.project (tree : SymbolicTree) (x : Nat) : SymbolicTree :=
  combine (· || ·) (tree.restrict x false) (tree.restrict x true)

theorem SymbolicTree.project_correct (tree : SymbolicTree) (x : Nat) (v : Nat → Bool) :
    (tree.project x).eval v =
      (tree.eval (Function.update v x false) || tree.eval (Function.update v x true)) := by
  simp [project, combine_correct, restrict_correct]

/-- The native session may reuse a checked refutation only with a newly checked
conjunct relation. Removing an assumption supplies no such implication. -/
theorem checked_conjunct_unsat (f core : Formula) (checked : ¬ Satisfiable core)
    (included : formulaIsConjunct f core = true) : ¬ Satisfiable f := by
  rintro ⟨v, hv⟩
  exact checked ⟨v, formulaIsConjunct_entails f core v included hv⟩

/-- Upper envelope when each affected node has at most `fanout` successors and
the remaining dependency depth is at most `depth`. Reconvergence may reduce it. -/
def affectedEnvelope (delta fanout : Nat) : Nat → Nat
  | 0 => delta
  | depth + 1 => delta + fanout * affectedEnvelope delta fanout depth

theorem affectedEnvelope_bound (delta fanout depth : Nat) :
    affectedEnvelope delta fanout depth ≤ delta * (fanout + 1) ^ depth := by
  induction depth with
  | zero => simp [affectedEnvelope]
  | succ depth ih =>
    have hp : 1 ≤ (fanout + 1) ^ depth := one_le_pow₀ (by omega)
    simp only [affectedEnvelope, pow_succ]
    nlinarith

structure UpdateLedger where
  affected : Nat
  rowCapacity : Nat
  rowCost : Nat
  overhead : Nat
  archiveAdded : Nat

def UpdateLedger.work (r : UpdateLedger) : Nat := r.overhead + r.affected * r.rowCapacity * r.rowCost

/-- A simple common-degree bound makes every needed premise visible. `overhead`
includes indexing, copying, matching, proof/restart, conversion and persistence. -/
theorem conditional_update_polynomial (r : UpdateLedger) (n C k : Nat)
    (ha : r.affected ≤ C * (n + 1) ^ k)
    (hw : r.rowCapacity ≤ C * (n + 1) ^ k)
    (hc : r.rowCost ≤ C * (n + 1) ^ k)
    (hh : r.overhead ≤ C * (n + 1) ^ k) :
    r.work ≤ (C + C ^ 3) * (n + 1) ^ (3 * k) := by
  have hp : 1 ≤ (n + 1) ^ k := one_le_pow₀ (by omega)
  have hm := Nat.mul_le_mul (Nat.mul_le_mul ha hw) hc
  have he : (n + 1) ^ (3 * k) = ((n + 1) ^ k) ^ 3 := by
    rw [Nat.mul_comm 3 k, pow_mul]
  rw [he]
  have hp3 : (n + 1) ^ k ≤ ((n + 1) ^ k) ^ 3 := by
    simpa using pow_le_pow_right' hp (by decide : 1 ≤ 3)
  have hC := Nat.mul_le_mul_left C hp3
  dsimp [UpdateLedger.work]
  calc
    r.overhead + r.affected * r.rowCapacity * r.rowCost ≤
        C * (n + 1) ^ k + (C * (n + 1) ^ k) ^ 3 := by nlinarith [hm]
    _ ≤ C * ((n + 1) ^ k) ^ 3 + C ^ 3 * ((n + 1) ^ k) ^ 3 := by
      rw [mul_pow]; exact Nat.add_le_add_right hC _
    _ = (C + C ^ 3) * ((n + 1) ^ k) ^ 3 := by ring

theorem stream_work_bound (rs : List UpdateLedger) (B : Nat)
    (bounded : ∀ r ∈ rs, r.work ≤ B) :
    (rs.map UpdateLedger.work).sum ≤ rs.length * B := by
  induction rs with
  | nil => simp
  | cons r rs ih =>
    have hr := bounded r (by simp)
    have ht := ih (fun s hs => bounded s (by simp [hs]))
    simp only [List.map_cons, List.sum_cons, List.length_cons, Nat.add_mul, Nat.one_mul]
    omega

theorem retained_archive_bound (initial B : Nat) (rs : List UpdateLedger)
    (bounded : ∀ r ∈ rs, r.archiveAdded ≤ B) :
    initial + (rs.map UpdateLedger.archiveAdded).sum ≤ initial + rs.length * B := by
  induction rs with
  | nil => simp
  | cons r rs ih =>
    have hr := bounded r (by simp)
    have ht := ih (fun s hs => bounded s (by simp [hs]))
    simp only [List.map_cons, List.sum_cons, List.length_cons, Nat.add_mul, Nat.one_mul]
    omega

theorem logarithmic_interface_capacity (width n : Nat)
    (small : width ≤ Nat.log 2 (n + 1)) : 2 ^ width ≤ n + 1 :=
  Nat.pow_le_of_le_log (Nat.succ_ne_zero _) small

/-- Retaining at least one new storage unit per distinct acquisition cannot fit
in one fixed finite archive for an unbounded acquisition stream. -/
theorem archive_capacity_obstruction (initial cap : Nat) (rs : List UpdateLedger)
    (positive : ∀ r ∈ rs, 1 ≤ r.archiveAdded)
    (fits : initial + (rs.map UpdateLedger.archiveAdded).sum ≤ cap) : rs.length ≤ cap := by
  have lower : rs.length ≤ (rs.map UpdateLedger.archiveAdded).sum := by
    clear fits
    induction rs with
    | nil => simp
    | cons r rs ih =>
      have hr := positive r (by simp)
      have ht := ih (fun s hs => positive s (by simp [hs]))
      simp only [List.length_cons, List.map_cons, List.sum_cons]
      omega
  omega

end OracleMachines.SAT

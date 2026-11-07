import OracleMachines.Layered

/-! Executable reference accounting: count tested intermediate states and
materialized Boolean cells. Allocation bytes, hashing, IPC, persistence and
compiled instructions remain outside these counters. -/
namespace OracleMachines.Layered
variable {q : Nat}
variable {α : Type}

def anyRun (p : α → Bool) : List α → Bool × Nat
  | [] => (false,0)
  | a::as => if p a then (true,1) else
      let tail := anyRun p as
      (tail.1,tail.2+1)

theorem anyRun_value (p : α → Bool) (xs : List α) : (anyRun p xs).1 = xs.any p := by
  induction xs with
  | nil => rfl
  | cons x xs ih => cases h : p x <;> simp [anyRun,h,ih]

theorem anyRun_tests (p : α → Bool) (xs : List α) : (anyRun p xs).2 ≤ xs.length := by
  induction xs with
  | nil => simp [anyRun]
  | cons x xs ih => cases h : p x <;> simp [anyRun,h]; omega

@[noinline] def tableRun (a b : Relation q) : Vector (Vector (Bool × Nat) q) q :=
  Vector.ofFn fun x => Vector.ofFn fun z => anyRun (fun y => a x y && b y z) (List.finRange q)

def tableValue (calls : Vector (Vector (Bool × Nat) q) q) : Relation q :=
  fun x y => (calls[x][y]).1

def tableTests (calls : Vector (Vector (Bool × Nat) q) q) : Nat :=
  ∑ x : Fin q, ∑ y : Fin q, (calls[x][y]).2

theorem tableRun_value (a b : Relation q) : tableValue (tableRun a b) = compose a b := by
  funext x z
  simp [tableValue, tableRun, anyRun_value, compose]

theorem tableRun_tests (a b : Relation q) : tableTests (tableRun a b) ≤ q^3 := by
  have bound : ∀ x z : Fin q, ((tableRun a b)[x][z]).2 ≤ q := by
    intro x z
    simpa [tableRun] using anyRun_tests (fun y => a x y && b y z) (List.finRange q)
  calc
    tableTests (tableRun a b) ≤ ∑ _x : Fin q, ∑ _z : Fin q, q :=
      Finset.sum_le_sum (fun x _ => Finset.sum_le_sum (fun z _ => bound x z))
    _ = q^3 := by simp; ring

def joinRun {h : Nat} (l r : Tree q h) : Tree q (h+1) × Nat :=
  let calls := tableRun l.summary r.summary
  (.branch (tableValue calls) l r, tableTests calls)

theorem joinRun_value {h : Nat} (l r : Tree q h) : (joinRun l r).1 = join l r := by
  change Tree.branch (tableValue (tableRun l.summary r.summary)) l r =
    Tree.branch (freeze (compose l.summary r.summary)) l r
  congr 1
  change tableValue (tableRun l.summary r.summary) = freeze (compose l.summary r.summary)
  rw [tableRun_value,freeze_eq]

def replaceRun : {h : Nat} → Tree q h → (Fin h → Bool) → Relation q → Tree q h × Nat
  | 0, .leaf _, _, value => (.leaf value,1)
  | h+1, .branch _ l r, path, value =>
    if path 0 then
      let changed := replaceRun r (fun i : Fin h => path i.succ) value
      let joined := joinRun l changed.1
      (joined.1, changed.2+joined.2+1)
    else
      let changed := replaceRun l (fun i : Fin h => path i.succ) value
      let joined := joinRun changed.1 r
      (joined.1, changed.2+joined.2+1)

theorem replaceRun_value {h : Nat} (t : Tree q h) (path : Fin h → Bool) (value : Relation q) :
    (replaceRun t path value).1 = replace t path value := by
  induction t with
  | leaf r => rfl
  | branch r l t il ir =>
    simp only [replaceRun,replace]; split <;> simp [joinRun_value,il,ir]

theorem replaceRun_tests {h : Nat} (t : Tree q h) (path : Fin h → Bool) (value : Relation q) :
    (replaceRun t path value).2 ≤ replacementBudget q h := by
  induction t with
  | leaf r => simp [replaceRun,replacementBudget]
  | @branch h r l t il ir =>
    have jl : ∀ (a b : Tree q h), (joinRun a b).2 ≤ q^3 :=
      fun a b => tableRun_tests a.summary b.summary
    simp only [replaceRun]
    split
    · have hh := ir (fun i => path i.succ)
      have jj := jl l (replaceRun t (fun i => path i.succ) value).1
      simp only [replacementBudget,Nat.add_mul,Nat.one_mul] at *; omega
    · have hh := il (fun i => path i.succ)
      have jj := jl (replaceRun l (fun i => path i.succ) value).1 t
      simp only [replacementBudget,Nat.add_mul,Nat.one_mul] at *; omega
end OracleMachines.Layered

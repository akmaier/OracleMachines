import OracleMachines.Interfaces

/-! A costed reference for local acquisition. Counts refer to formula/list
operations, not compiled CPU instructions. Parsing, ordering, hashing, proof
checking, persistence and restart are explicit extra ledger phases. -/
namespace OracleMachines.SAT

def scopeReadRun : List Nat → Word → Nat → Run Bool
  | [], _, _ => (false, 1)
  | i :: rest, bits, j =>
    if j = i then (bits.headD false, 1)
    else let r := scopeReadRun rest bits.tail j; (r.1, r.2 + 1)

theorem scopeReadRun_value (scope : List Nat) (bits : Word) (i : Nat) :
    (scopeReadRun scope bits i).1 = scopeVal scope bits i := by
  induction scope generalizing bits with
  | nil => rfl
  | cons j rest ih =>
    by_cases h : i = j <;> simp [scopeReadRun, scopeVal, h, ih]

theorem scopeReadRun_bound (scope : List Nat) (bits : Word) (i : Nat) :
    (scopeReadRun scope bits i).2 ≤ scope.length + 1 := by
  induction scope generalizing bits with
  | nil => simp [scopeReadRun]
  | cons j rest ih =>
    by_cases h : i = j
    · simp [scopeReadRun, h]
    · simpa [scopeReadRun, h] using Nat.add_le_add_right (ih bits.tail) 1

def syntaxSize : Formula → Nat
  | .falsum => 1
  | .var _ => 1
  | .neg f => syntaxSize f + 1
  | .conj f g => syntaxSize f + syntaxSize g + 1

def localEvalRun : Formula → List Nat → Word → Run Bool
  | .falsum, _, _ => (false, 1)
  | .var i, scope, bits => let r := scopeReadRun scope bits i; (r.1, r.2 + 1)
  | .neg f, scope, bits => let r := localEvalRun f scope bits; (!r.1, r.2 + 1)
  | .conj f g, scope, bits =>
    let r := localEvalRun f scope bits
    let s := localEvalRun g scope bits
    (r.1 && s.1, r.2 + s.2 + 1)

theorem localEvalRun_value (f : Formula) (scope : List Nat) (bits : Word) :
    (localEvalRun f scope bits).1 = f.eval (scopeVal scope bits) := by
  induction f <;> simp_all [localEvalRun, Formula.eval, scopeReadRun_value]

theorem localEvalRun_bound (f : Formula) (scope : List Nat) (bits : Word) :
    (localEvalRun f scope bits).2 ≤ syntaxSize f * (scope.length + 2) := by
  induction f with
  | falsum => simp [localEvalRun, syntaxSize]
  | var i => simpa [localEvalRun, syntaxSize] using Nat.add_le_add_right (scopeReadRun_bound scope bits i) 1
  | neg f ih => simp only [localEvalRun, syntaxSize, Nat.add_mul, Nat.one_mul]; omega
  | conj f g ihf ihg => simp only [localEvalRun, syntaxSize, Nat.add_mul, Nat.one_mul]; omega

def localAcquisitionWork (f : Formula) (scope : List Nat) (requested : List Word) : Nat :=
  (requested.map (fun row => (localEvalRun f scope row).2)).sum

theorem localAcquisitionWork_bound (f : Formula) (scope : List Nat) (rows : List Word) :
    localAcquisitionWork f scope rows ≤ rows.length * (syntaxSize f * (scope.length + 2)) := by
  induction rows with
  | nil => simp [localAcquisitionWork]
  | cons row rest ih =>
    have h := localEvalRun_bound f scope row
    simp only [localAcquisitionWork, List.map_cons, List.sum_cons, List.length_cons, Nat.add_mul, Nat.one_mul] at *
    omega

theorem completeLocalAcquisition_bound (f : Formula) (scope : List Nat) :
    localAcquisitionWork f scope (words scope.length) ≤
      2 ^ scope.length * (syntaxSize f * (scope.length + 2)) := by
  simpa using localAcquisitionWork_bound f scope (words scope.length)

theorem relation_rows_bound (scope : List Nat) (p : (Nat → Bool) → Bool) :
    (tabulate scope p).allowed.length ≤ 2 ^ scope.length := by
  exact (List.length_filter_le _ _).trans_eq (length_words scope.length)

/-- Charged short-circuit conjunction of already-retrieved row values. -/
def rowProbeRun : List Bool → Run Bool
  | [] => (true, 1)
  | b :: bs => if b then let r := rowProbeRun bs; (r.1, r.2 + 1) else (false, 1)

theorem rowProbeRun_value (bs : List Bool) : (rowProbeRun bs).1 = bs.all id := by
  induction bs with
  | nil => rfl
  | cons b bs ih => cases b <;> simp [rowProbeRun, ih]

theorem rowProbeRun_bound (bs : List Bool) : (rowProbeRun bs).2 ≤ bs.length + 1 := by
  induction bs with
  | nil => simp [rowProbeRun]
  | cons b bs ih => cases b <;> simp [rowProbeRun]; omega

def projectRowRun (lo hi : List Bool) : Run Bool :=
  let l := rowProbeRun lo
  if l.1 then (true, l.2 + 1)
  else let r := rowProbeRun hi; (r.1, l.2 + r.2 + 1)

theorem projectRowRun_value (lo hi : List Bool) :
    (projectRowRun lo hi).1 = lo.all id || hi.all id := by
  simp only [projectRowRun, rowProbeRun_value]
  cases lo.all id <;> cases hi.all id <;> rfl

theorem projectRowRun_bound (lo hi : List Bool) :
    (projectRowRun lo hi).2 ≤ lo.length + hi.length + 3 := by
  have hl := rowProbeRun_bound lo
  have hr := rowProbeRun_bound hi
  dsimp only [projectRowRun]
  split <;> simp only <;> omega

/-- Unknown is false in a lower bound and true in an upper bound. -/
def rowLower (row : Option Bool) : Bool := row.getD false
def rowUpper (row : Option Bool) : Bool := row.getD true

theorem known_row_bounds (row : Option Bool) (actual : Bool)
    (checked : ∀ b, row = some b → b = actual) :
    (rowLower row = true → actual = true) ∧ (rowUpper row = false → actual = false) := by
  cases row with
  | none => simp [rowLower, rowUpper]
  | some b => have h := checked b rfl; subst b; simp [rowLower, rowUpper]

/-- Retrieval/evaluation costs accumulate once per requested row in this ledger;
restart rechecks and all graph-wide work stay in H. No constant-time RAM premise
is silently extended to a bit-machine or to list-backed native relations. -/
theorem lazy_acquisition_budget (f : Formula) (scope : List Nat) (rows : List Word) (H : Nat) :
    H + localAcquisitionWork f scope rows ≤
      H + rows.length * (syntaxSize f * (scope.length + 2)) :=
  Nat.add_le_add_left (localAcquisitionWork_bound f scope rows) H

end OracleMachines.SAT

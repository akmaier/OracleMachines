import Mathlib.Data.Nat.Log
import Mathlib.Tactic

/-! Exact summaries for supplied bounded-width layers. A state encodes one
Boolean layer; q = 2^width. Counts exclude source conversion and service costs. -/
namespace OracleMachines.Layered
abbrev Relation (q : Nat) := Fin q → Fin q → Bool
variable {q : Nat}

def compose (a b : Relation q) : Relation q := fun x z =>
  (List.finRange q).any fun y => a x y && b y z

def identity : Relation q := fun x y => x == y

-- Return data, so arity expansion cannot delay construction until lookup.
@[noinline] def materialize (r : Relation q) : Vector (Vector Bool q) q :=
  Vector.ofFn (fun x : Fin q => Vector.ofFn (r x))

def freeze (r : Relation q) : Relation q :=
  fun x y => (materialize r)[x][y]

theorem freeze_eq (r : Relation q) : freeze r = r := by
  funext x y; simp [freeze, materialize]

theorem compose_exact (a b : Relation q) (x z : Fin q) :
    compose a b x z = true ↔ ∃ y, a x y = true ∧ b y z = true := by
  simp [compose, List.any_eq_true]

theorem compose_assoc (a b c : Relation q) : compose (compose a b) c = compose a (compose b c) := by
  funext x z
  apply Bool.eq_iff_iff.mpr
  simp only [compose_exact]
  constructor
  · rintro ⟨y, ⟨w, haw, hbw⟩, hc⟩; exact ⟨w, haw, y, hbw, hc⟩
  · rintro ⟨w, haw, y, hbw, hc⟩; exact ⟨y, ⟨w, haw, hbw⟩, hc⟩

theorem compose_identity (a : Relation q) : compose a identity = a := by
  funext x y
  apply Bool.eq_iff_iff.mpr
  simp [compose_exact, identity]

theorem identity_compose (a : Relation q) : compose identity a = a := by
  funext x y
  apply Bool.eq_iff_iff.mpr
  simp [compose_exact, identity]

inductive Tree (q : Nat) : Nat → Type where
  | leaf : Relation q → Tree q 0
  | branch {h : Nat} : Relation q → Tree q h → Tree q h → Tree q (h+1)

def Tree.summary : {h : Nat} → Tree q h → Relation q
  | _, .leaf r => r
  | _, .branch r _ _ => r

def Tree.Valid : {h : Nat} → Tree q h → Prop
  | _, .leaf _ => True
  | _, .branch r l t => l.Valid ∧ t.Valid ∧ r = compose l.summary t.summary

def Tree.Accepts : {h : Nat} → Tree q h → Fin q → Fin q → Prop
  | _, .leaf r, x, y => r x y = true
  | _, .branch _ l r, x, z => ∃ y, l.Accepts x y ∧ r.Accepts y z

def join {h : Nat} (l r : Tree q h) : Tree q (h+1) :=
  let rows := materialize (compose l.summary r.summary)
  .branch (fun x y => rows[x][y]) l r

theorem join_valid {h : Nat} (l r : Tree q h) (hl : l.Valid) (hr : r.Valid) :
    (join l r).Valid := ⟨hl, hr, freeze_eq _⟩

theorem summary_exact {h : Nat} (t : Tree q h) (valid : t.Valid) (x y : Fin q) :
    t.summary x y = true ↔ t.Accepts x y := by
  induction t generalizing x y with
  | leaf r => rfl
  | branch r l t il ir =>
    rcases valid with ⟨hl, hr, same⟩
    change r x y = true ↔ ∃ z, l.Accepts x z ∧ t.Accepts z y
    rw [same, compose_exact]
    exact exists_congr (fun z => and_congr (il hl x z) (ir hr z y))

def padding : (h : Nat) → Tree q h
  | 0 => .leaf identity
  | h+1 => let child := padding h; join child child

theorem padding_summary (h : Nat) : (padding h : Tree q h).summary = identity := by
  induction h with
  | zero => rfl
  | succ h ih =>
    change freeze (compose (padding h).summary (padding h).summary) = identity
    rw [freeze_eq, ih, compose_identity]

def replace : {h : Nat} → Tree q h → (Fin h → Bool) → Relation q → Tree q h
  | 0, .leaf _, _, value => .leaf value
  | h+1, .branch _ l r, path, value =>
    if path 0 then join l (replace r (fun i : Fin h => path i.succ) value)
    else join (replace l (fun i : Fin h => path i.succ) value) r

theorem replace_valid {h : Nat} (t : Tree q h) (path : Fin h → Bool) (value : Relation q)
    (valid : t.Valid) : (replace t path value).Valid := by
  induction t with
  | leaf r => trivial
  | branch r l t il ir =>
    rcases valid with ⟨hl,hr,_⟩
    simp only [replace]; split
    · exact join_valid _ _ hl (ir _ hr)
    · exact join_valid _ _ (il _ hl) hr

def Tree.at : {h : Nat} → Tree q h → (Fin h → Bool) → Relation q
  | 0, .leaf r, _ => r
  | h+1, .branch _ l r, path =>
    if path 0 then r.at (fun i : Fin h => path i.succ)
    else l.at (fun i : Fin h => path i.succ)

theorem replace_at {h : Nat} (t : Tree q h) (path : Fin h → Bool) (value : Relation q) :
    (replace t path value).at path = value := by
  induction t with
  | leaf r => rfl
  | branch v l r il ir =>
    simp only [replace]
    split <;> simp_all [Tree.at, join]

theorem replace_other {h : Nat} (t : Tree q h) (path other : Fin h → Bool) (value : Relation q)
    (different : path ≠ other) : (replace t path value).at other = t.at other := by
  induction t with
  | leaf r => exact False.elim (different (funext (fun i => Fin.elim0 i)))
  | @branch h v l r il ir =>
    have tails : path 0 = other 0 → (fun i : Fin h => path i.succ) ≠ (fun i : Fin h => other i.succ) := by
      intro same eq
      apply different
      funext i
      refine Fin.cases same (fun j => congrFun eq j) i
    cases hp : path 0 <;> cases ho : other 0 <;>
      simp [replace, Tree.at, join, hp, ho, il, ir, tails]

def replacementWork : {h : Nat} → Tree q h → (Fin h → Bool) → Nat
  | 0, .leaf _, _ => 1
  | h+1, .branch _ l r, path =>
    1+q^3 + if path 0 then replacementWork r (fun i : Fin h => path i.succ)
      else replacementWork l (fun i : Fin h => path i.succ)

def replacementBudget (q h : Nat) : Nat := h+1+h*q^3

theorem replacement_work_exact {h : Nat} (t : Tree q h) (path : Fin h → Bool) :
    replacementWork t path = replacementBudget q h := by
  induction t with
  | leaf r => simp [replacementWork, replacementBudget]
  | branch r l t il ir =>
    simp only [replacementWork]; split <;>
      simp_all [replacementBudget, Nat.add_mul] <;> omega

theorem replacement_budget_log (q h : Nat) :
    replacementBudget q h = Nat.log 2 (2^h)+1+Nat.log 2 (2^h)*q^3 := by
  simp [replacementBudget, Nat.log_pow (by decide : 1 < 2)]

theorem boolean_layer_cells (width : Nat) : (2^width)^2 = 2^(2*width) := by
  rw [← Nat.pow_mul]; congr 1; omega
end OracleMachines.Layered

import Mathlib.Data.Nat.Log
import Mathlib.Tactic

/-! Perfect-tree binary Boolean chain summaries. Counts cover compositions and
copied nodes, not parsing, persistence, IPC or complete witness output. -/
namespace OracleMachines.Chain
abbrev Relation := Bool → Bool → Bool

def compose (a b : Relation) : Relation := fun x z =>
  (a x false && b false z) || (a x true && b true z)
def identity : Relation := fun x y => x == y

/-- Force all four entries now, rather than retaining a composition closure. -/
@[noinline] def freeze (r : Relation) : Relation :=
  let ff := r false false
  let ft := r false true
  let tf := r true false
  let tt := r true true
  fun x y => if x then (if y then tt else tf) else (if y then ft else ff)

theorem freeze_eq (r : Relation) : freeze r = r := by
  funext x y; cases x <;> cases y <;> rfl

theorem compose_exact (a b : Relation) (x z : Bool) :
    compose a b x z = true ↔ ∃ y, a x y = true ∧ b y z = true := by
  simp only [compose, Bool.or_eq_true, Bool.and_eq_true]
  constructor
  · rintro (h | h)
    · exact ⟨false, h⟩
    · exact ⟨true, h⟩
  · rintro ⟨y, h⟩
    cases y
    · exact Or.inl h
    · exact Or.inr h

theorem compose_assoc (a b c : Relation) : compose (compose a b) c = compose a (compose b c) := by
  funext x z
  apply Bool.eq_iff_iff.mpr
  simp only [compose_exact]
  constructor
  · rintro ⟨y, ⟨w, haw, hbw⟩, hc⟩
    exact ⟨w, haw, y, hbw, hc⟩
  · rintro ⟨w, haw, y, hbw, hc⟩
    exact ⟨y, ⟨w, haw, hbw⟩, hc⟩

theorem compose_identity (a : Relation) : compose a identity = a := by
  funext x y; cases y <;> simp [compose, identity]
theorem identity_compose (a : Relation) : compose identity a = a := by
  funext x y; cases x <;> simp [compose, identity]

inductive Tree : Nat → Type where
  | leaf : Relation → Tree 0
  | branch {h : Nat} : Relation → Tree h → Tree h → Tree (h+1)

def Tree.summary : {h : Nat} → Tree h → Relation
  | _, .leaf r => r
  | _, .branch r _ _ => r
def Tree.denote : {h : Nat} → Tree h → Relation
  | _, .leaf r => r
  | _, .branch _ l r => compose l.denote r.denote
def Tree.Valid : {h : Nat} → Tree h → Prop
  | _, .leaf _ => True
  | _, .branch v l r => l.Valid ∧ r.Valid ∧ v = compose l.summary r.summary

def join {h : Nat} (l r : Tree h) : Tree (h+1) :=
  let summary := compose l.summary r.summary
  let ff := summary false false
  let ft := summary false true
  let tf := summary true false
  let tt := summary true true
  .branch (fun x y => if x then (if y then tt else tf) else (if y then ft else ff)) l r

theorem join_valid {h : Nat} (l r : Tree h) (hl : l.Valid) (hr : r.Valid) :
    (join l r).Valid := ⟨hl, hr, freeze_eq _⟩
theorem summary_exact {h : Nat} (t : Tree h) (ht : t.Valid) : t.summary = t.denote := by
  induction t with
  | leaf r => rfl
  | branch v l r il ir =>
    rcases ht with ⟨hl, hr, hv⟩
    change v = compose l.denote r.denote
    rw [hv, il hl, ir hr]

def padding : (h : Nat) → Tree h
  | 0 => .leaf identity
  | h+1 => let child := padding h; join child child

theorem padding_valid (h : Nat) : (padding h).Valid := by
  induction h with
  | zero => trivial
  | succ h ih => exact join_valid _ _ ih ih
theorem padding_summary (h : Nat) : (padding h).summary = identity := by
  induction h with
  | zero => rfl
  | succ h ih =>
    change freeze (compose (padding h).summary (padding h).summary) = identity
    rw [freeze_eq, ih, compose_identity]

/-- Path length is exactly the tree height, enforced by the type. -/
def replace : {h : Nat} → Tree h → (Fin h → Bool) → Relation → Tree h
  | 0, .leaf _, _, value => .leaf value
  | h+1, .branch _ l r, path, value =>
    let tail := fun i : Fin h => path i.succ
    if path 0 then join l (replace r tail value) else join (replace l tail value) r

theorem replace_valid {h : Nat} (t : Tree h) (path : Fin h → Bool) (value : Relation)
    (ht : t.Valid) : (replace t path value).Valid := by
  induction t with
  | leaf r => trivial
  | branch v l r il ir =>
    rcases ht with ⟨hl, hr, _⟩
    simp only [replace]
    split
    · exact join_valid _ _ hl (ir _ hr)
    · exact join_valid _ _ (il _ hl) hr

def Tree.at : {h : Nat} → Tree h → (Fin h → Bool) → Relation
  | 0, .leaf r, _ => r
  | h+1, .branch _ l r, path =>
    if path 0 then r.at (fun i : Fin h => path i.succ)
    else l.at (fun i : Fin h => path i.succ)

theorem replace_at {h : Nat} (t : Tree h) (path : Fin h → Bool) (value : Relation) :
    (replace t path value).at path = value := by
  induction t with
  | leaf r => rfl
  | branch v l r il ir =>
    simp only [replace]
    split <;> simp_all [Tree.at, join]

theorem replace_other {h : Nat} (t : Tree h) (path other : Fin h → Bool) (value : Relation)
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

/-- One leaf allocation and one composition/copy at each ancestor. -/
def replaceCost : {h : Nat} → Tree h → (Fin h → Bool) → Nat
  | 0, .leaf _, _ => 1
  | h+1, .branch _ l r, path =>
    1 + if path 0 then replaceCost r (fun i : Fin h => path i.succ)
        else replaceCost l (fun i : Fin h => path i.succ)

theorem replace_cost_exact {h : Nat} (t : Tree h) (path : Fin h → Bool) :
    replaceCost t path = h+1 := by
  induction t with
  | leaf r => rfl
  | branch v l r il ir => simp only [replaceCost]; split <;> simp_all <;> omega

theorem logarithmic_replacement {h : Nat} (t : Tree h) (path : Fin h → Bool) :
    replaceCost t path = Nat.log 2 (2^h) + 1 := by
  rw [replace_cost_exact, Nat.log_pow (by decide : 1 < 2)]

theorem grow_preserves {h : Nat} (t : Tree h) :
    (join t (padding h)).summary = t.summary := by
  change freeze (compose t.summary (padding h).summary) = t.summary
  rw [freeze_eq, padding_summary, compose_identity]

/-- Functional update leaves a separately retained old root unchanged. -/
theorem old_version_preserved {h : Nat} (t : Tree h) (path : Fin h → Bool) (r : Relation) :
    (t, replace t path r).1 = t := rfl

theorem archive_nodes_bound (initial h updates : Nat) :
    initial + (List.replicate updates (h+1)).sum = initial + updates*(h+1) := by simp
end OracleMachines.Chain

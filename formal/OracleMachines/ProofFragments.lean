import OracleMachines.IncrementalProof
import Mathlib.Tactic

/-! Small RUP fragments under explicit permanent-clause dependencies. Query
assumptions are supplied only to the final check, never retained as lemmas. -/
namespace OracleMachines.Fragments
abbrev Literal := Nat × Bool
abbrev Clause := List Literal
abbrev Valuation := Nat → Bool

def Holds (v : Valuation) (c : Clause) : Prop := ∃ l ∈ c, v l.1 = l.2
def Compatible (v : Valuation) (trail : Clause) : Prop := ∀ l ∈ trail, v l.1 = l.2
def negate (l : Literal) : Literal := (l.1, !l.2)
def residual (c trail : Clause) : Clause := c.filter (fun l => !(trail.contains (negate l)))

def walk (trail : Clause) : List Clause → Bool
  | [] => false
  | c :: rest =>
    match residual c trail with
    | [] => true
    | [l] => walk (l :: trail) rest
    | _ => false

def check (target : Clause) (hints : List Clause) : Bool := walk (target.map negate) hints

theorem residual_holds (v : Valuation) (c trail : Clause)
    (hc : Holds v c) (ht : Compatible v trail) : Holds v (residual c trail) := by
  rcases hc with ⟨l, hl, hv⟩
  have hn : negate l ∉ trail := by
    intro hn
    have bad := ht (negate l) hn
    simp only [negate] at bad
    rw [hv] at bad
    cases hb : l.2 <;> simp [hb] at bad
  exact ⟨l, by simpa [residual, hl] using hn, hv⟩

theorem walk_sound (trail : Clause) (hints : List Clause) (v : Valuation)
    (ht : Compatible v trail) (hh : ∀ c ∈ hints, Holds v c)
    (accepted : walk trail hints = true) : False := by
  induction hints generalizing trail with
  | nil => simp [walk] at accepted
  | cons c rest ih =>
    have hc := residual_holds v c trail (hh c (by simp)) ht
    simp only [walk] at accepted
    split at accepted
    · rename_i empty
      simp [Holds, empty] at hc
    · rename_i l single
      have hl : v l.1 = l.2 := by simpa [Holds, single] using hc
      apply ih (l :: trail) _ (fun d hd => hh d (by simp [hd])) accepted
      intro x hx
      rcases List.mem_cons.mp hx with same | old
      · simpa [same] using hl
      · exact ht x old
    · contradiction

theorem check_sound (target : Clause) (hints : List Clause) (v : Valuation)
    (hh : ∀ c ∈ hints, Holds v c) (accepted : check target hints = true) : Holds v target := by
  by_contra hn
  apply walk_sound (target.map negate) hints v _ hh accepted
  intro l hl
  rcases List.mem_map.mp hl with ⟨q, hq, heq⟩
  subst l
  have hqv : v q.1 ≠ q.2 := fun same => hn ⟨q, hq, same⟩
  simp only [negate]
  cases hv : v q.1 <;> cases hsign : q.2 <;> simp_all

def Entails (base : List Clause) (c : Clause) : Prop :=
  ∀ v, (∀ b ∈ base, Holds v b) → Holds v c

theorem extend_sound (base hints : List Clause) (target : Clause)
    (valid : ∀ h ∈ hints, Entails base h) (accepted : check target hints = true) :
    Entails base target := by
  intro v hv
  exact check_sound target hints v (fun c hc => valid c hc v hv) accepted

theorem weaken (old new : List Clause) (c : Clause)
    (included : ∀ b ∈ old, b ∈ new) (valid : Entails old c) : Entails new c := by
  intro v hv
  exact valid v (fun b hb => hv b (included b hb))

/-- A checked permanent fact can close a query with a fresh root assumption. -/
theorem query_unsat (base : List Clause) (facts : List Clause) (root : Clause)
    (valid : ∀ c ∈ facts, Entails base c)
    (accepted : check [] (root :: facts) = true) :
    ¬ ∃ v, (∀ b ∈ base, Holds v b) ∧ Holds v root := by
  rintro ⟨v, hb, hr⟩
  have he := check_sound [] (root :: facts) v (by
    intro c hc
    rcases List.mem_cons.mp hc with same | old
    · simpa [same] using hr
    · exact valid c old v hb) accepted
  simp [Holds] at he

theorem holds_iff_eval (c : Clause) (v : Valuation) :
    Holds v c ↔ Std.Sat.CNF.Clause.eval v c = true := by
  simp [Holds, Std.Sat.CNF.Clause.eval, List.any_eq_true]

/-- Compose fragment checking with the existing verified circuit-to-CNF result. -/
theorem incremental_fragment_unsat (f : OracleMachines.SAT.Formula) (previous : Std.Sat.AIG Nat)
    (root : Clause) (base facts : List Clause)
    (context : OracleMachines.SAT.incrementalCNF (OracleMachines.SAT.compileCircuit f previous).entry = root :: base)
    (valid : ∀ c ∈ facts, Entails base c) (accepted : check [] (root :: facts) = true) :
    ¬ OracleMachines.SAT.Satisfiable f := by
  have hu : Std.Sat.CNF.Unsat (root :: base) := by
    intro v
    apply Bool.eq_false_iff.mpr
    intro sat
    have clauses : ∀ c ∈ root :: base, Holds v c := by
      simpa only [Std.Sat.CNF.eval, List.all_eq_true, ← holds_iff_eval] using sat
    exact query_unsat base facts root valid accepted
      ⟨v, (fun c hc => clauses c (by simp [hc])), clauses root (by simp)⟩
  rw [← context] at hu
  have entry := OracleMachines.SAT.incrementalCNF_unsat _ hu
  rintro ⟨v,hv⟩
  have bad := entry v
  rw [(OracleMachines.SAT.compileCircuit f previous).correct v, hv] at bad
  contradiction

end OracleMachines.Fragments

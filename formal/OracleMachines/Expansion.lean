import Mathlib.Data.List.Basic
import Mathlib.Tactic

/-!
# Exact finite expansion

An executable list implementation of the coverage induction. A supplied total
Boolean solver labels each word; this module supplies neither that solver's
correctness for SAT nor a runtime bound. List lookup is sequential, not the
paper's random-access implementation.
-/

namespace OracleMachines

abbrev Word := List Bool

/-- All binary words of exactly the given length, in lexicographic order. -/
def words : Nat → List Word
  | 0 => [[]]
  | n + 1 => (words n).map (false :: ·) ++ (words n).map (true :: ·)

@[simp] theorem mem_words (x : Word) (n : Nat) : x ∈ words n ↔ x.length = n := by
  induction n generalizing x with
  | zero => simp [words]
  | succ n ih =>
    cases x with
    | nil => simp [words]
    | cons b xs => cases b <;> simp [words, ih]

@[simp] theorem length_words (n : Nat) : (words n).length = 2 ^ n := by
  induction n with
  | zero => simp [words]
  | succ n ih => simp [words, ih, pow_succ]; omega

/-- The empty word is present at stage zero; each step appends one length. -/
def domain : Nat → List Word
  | 0 => [[]]
  | n + 1 => domain n ++ words (n + 1)

@[simp] theorem mem_domain (x : Word) (n : Nat) : x ∈ domain n ↔ x.length ≤ n := by
  induction n with
  | zero => simp [domain]
  | succ n ih => simp only [domain, List.mem_append, ih, mem_words]; omega

/-- Written without natural subtraction to include the base case cleanly. -/
theorem length_domain (n : Nat) : (domain n).length + 1 = 2 ^ (n + 1) := by
  induction n with
  | zero => simp [domain]
  | succ n ih => simp only [domain, List.length_append, length_words, pow_succ] at *; omega

abbrev Table := List (Word × Bool)

/-- Store both a key and its answer. Key-storage overhead is not suppressed. -/
def table (solver : Word → Bool) (n : Nat) : Table :=
  (domain n).map fun x => (x, solver x)

def lookup (x : Word) : Table → Option Bool
  | [] => none
  | (y, b) :: rest => if x = y then some b else lookup x rest

theorem lookup_map (solver : Word → Bool) (xs : List Word) (x : Word) :
    lookup x (xs.map fun y => (y, solver y)) =
      if x ∈ xs then some (solver x) else none := by
  induction xs with
  | nil => simp [lookup]
  | cons y ys ih =>
    by_cases h : x = y
    · subst y; simp [lookup]
    · simp [lookup, h, ih]

/-- Exact coverage, and explicit refusal outside the covered domain. -/
theorem table_lookup (solver : Word → Bool) (n : Nat) (x : Word) :
    lookup x (table solver n) =
      if x.length ≤ n then some (solver x) else none := by
  simp [table, lookup_map]

theorem table_append (solver : Word → Bool) (n : Nat) :
    table solver (n + 1) = table solver n ++
      (words (n + 1)).map (fun x => (x, solver x)) := by
  simp [table, domain]

theorem preserves_answers (solver : Word → Bool) (n : Nat) (x : Word)
    (hx : x.length ≤ n) :
    lookup x (table solver (n + 1)) = lookup x (table solver n) := by
  simp [table_lookup, hx, Nat.le_trans hx (Nat.le_succ n)]

theorem eventually_covered (solver : Word → Bool) (x : Word) :
    lookup x (table solver x.length) = some (solver x) := by
  simp [table_lookup]

/-- Each entry carries one answer bit. The explicit keys require extra storage. -/
theorem table_answer_count (solver : Word → Bool) (n : Nat) :
    (table solver n).length + 1 = 2 ^ (n + 1) := by
  simpa [table] using length_domain n

/-- Logical correctness is inherited from the supplied exact solver. -/
theorem exact_on_domain (L : Word → Prop) (solver : Word → Bool)
    (correct : ∀ x, solver x = true ↔ L x) (n : Nat) (x : Word)
    (hx : x.length ≤ n) : lookup x (table solver n) = some true ↔ L x := by
  simpa [table_lookup, hx] using correct x

end OracleMachines

import OracleMachines.CDCL

/-!
# A bounded search proposal before external CDCL

The remaining budget counts visited nodes, including unsuccessful attempts.
Exhaustion returns no proposal, never UNSAT. Accepted proposals are checked by
the existing witness/refutation validators; this module needs no new trust.
-/
namespace OracleMachines.SAT

def boundedSearch (f : Formula) : List Nat → Sparse → Nat → Option SearchResult × Nat
  | pending, s, budget =>
    match budget with
    | 0 => (none, 0)
    | fuel + 1 =>
      match (partialRun f s).1 with
      | some true => (some ⟨some s, .conflict, 0, 1⟩, fuel)
      | some false => (some ⟨none, .conflict, 0, 1⟩, fuel)
      | none => match pending with
        | [] => (none, fuel)
        | i :: rest =>
          let low := boundedSearch f rest ((i, false) :: s) fuel
          match low.1 with
          | none => (none, low.2)
          | some l => match l.assignment with
            | some _ => (some { l with nodes := l.nodes + 1 }, low.2)
            | none =>
              let high := boundedSearch f rest ((i, true) :: s) low.2
              match high.1 with
              | none => (none, high.2)
              | some h => (some ⟨h.assignment, .split i l.proof h.proof, 0,
                                  l.nodes + h.nodes + 1⟩, high.2)

theorem boundedSearch_remaining_le (f : Formula) (xs : List Nat) (s : Sparse) (budget : Nat) :
    (boundedSearch f xs s budget).2 ≤ budget := by
  induction xs generalizing s budget with
  | nil =>
    cases budget with
    | zero => simp [boundedSearch]
    | succ fuel => cases ht : (partialRun f s).1 with
      | none => simp [boundedSearch, ht]
      | some b => cases b <;> simp [boundedSearch, ht]
  | cons i rest ih =>
    cases budget with
    | zero => simp [boundedSearch]
    | succ fuel =>
      have lo := ih ((i, false) :: s) fuel
      have hi := ih ((i, true) :: s) (boundedSearch f rest ((i, false) :: s) fuel).2
      cases ht : (partialRun f s).1 with
      | some b => cases b <;> simp [boundedSearch, ht]
      | none =>
        simp only [boundedSearch, ht]
        split
        · omega
        · split
          · omega
          · split <;> omega

end OracleMachines.SAT

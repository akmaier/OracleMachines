import OracleMachines.AffineCosts
import Mathlib.Data.Erased

/-! Resident summaries retain original-history semantics as erased data. The
ordinary reference State stores its history literally; using it in the native
store would keep every ancestor alive even after deleting their map entries. -/
namespace OracleMachines.Affine

structure Resident (b : Nat) where
  past : Erased (History b)
  summary : List (Row b)
  exact : ∀ v, Holds summary v ↔ past.out.Holds v
  compact : summary.length ≤ b+1

noncomputable def Resident.history {b : Nat} (state : Resident b) : History b := state.past.out

def residentInitial (b : Nat) : Resident b :=
  ⟨Erased.mk .empty,[],by intro v; simp [Holds,History.Holds],by simp⟩

theorem residentInitial_history (b : Nat) : (residentInitial b).history = .empty := by
  simp [residentInitial,Resident.history]

def Resident.answer {b : Nat} (state : Resident b) : Bool := decide state.summary

theorem Resident.answer_exact {b : Nat} (state : Resident b) :
    state.answer = true ↔ ∃ v, state.history.Holds v := by
  rw [Resident.answer,decide_exact]
  exact exists_congr state.exact

theorem Resident.answer_false {b : Nat} (state : Resident b) :
    state.answer = false ↔ ¬ ∃ v, state.history.Holds v := by
  rw [← state.answer_exact]
  cases state.answer <;> decide

def Resident.appendRun {b : Nat} (state : Resident b) (equations : List (Row (b+b))) : Resident b × Nat :=
  let result := extendRun state.summary equations
  (⟨state.past.map (fun old => .append old equations),result.1,by
      intro v
      rw [extendRun_value,extend_exact,Erased.map_out]
      exact exists_congr (fun u => and_congr_left (fun _ => state.exact u)),by
      rw [extendRun_value]; exact extend_size _ _⟩,result.2)

theorem Resident.appendRun_history {b : Nat} (state : Resident b) (equations : List (Row (b+b))) :
    (state.appendRun equations).1.history = .append state.history equations := by
  simp [Resident.appendRun,Resident.history]

theorem Resident.appendRun_bound {b : Nat} (state : Resident b) (equations : List (Row (b+b))) :
    (state.appendRun equations).2 + (decideRun (state.appendRun equations).1.summary).2 ≤
      appendBudget b equations.length := extendRun_bound _ _ state.compact

theorem Resident.summary_cells {b : Nat} (state : Resident b) :
    state.summary.length*(b+1) ≤ (b+1)^2 := by
  simpa [pow_two] using Nat.mul_le_mul_right (b+1) state.compact

end OracleMachines.Affine

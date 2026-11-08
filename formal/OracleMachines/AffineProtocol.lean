import OracleMachines.AffineResident
import Lean.Data.Json

/-! Native affine growth. The executed algebra carries exact history semantics.
JSON decoding, hashes, Python replay and SQLite are tested integration boundaries,
not additional consequences of the algebraic proof. -/
namespace OracleMachines.Affine
open Lean

structure Node where
  width : Nat
  state : Resident width
  steps : Nat
  steps_exact : steps = state.history.steps
  answer : Bool
  answer_exact : answer = state.answer
  body : Json
  budget : Nat
  charge : Nat
  charge_bound : charge ≤ budget

abbrev Store := Std.HashMap String Node

def parseRow (n : Nat) (body : Json) : Except String (Row n) := do
  let coefficients ← body.getObjValAs? (Array Bool) "coefficients"
  let rhs ← body.getObjValAs? Bool "rhs"
  if size : coefficients.size = n then
    let values : Vector Bool n := ⟨coefficients,size⟩
    return ⟨values.map (fun value => if value then 1 else 0),if rhs then 1 else 0⟩
  else throw "Affine coefficient dimension differs"

def parseRows (n : Nat) (body : Json) : Except String (List (Row n)) := do
  let raw ← body.getObjValAs? (Array Json) "equations"
  if raw.size > 4096 then throw "Affine equation batch exceeds capacity"
  raw.toList.mapM (parseRow n)

def rowJson {n : Nat} (r : Row n) : Json := Json.mkObj
  [("coefficients",toJson (r.coeff.toArray.map (fun value => value.val != 0))),
   ("rhs",toJson (r.rhs.val != 0))]

def report (node : Node) (includeSummary : Bool) : Json := Json.mkObj
  [("answer",toJson node.answer),("width",toJson node.width),("steps",toJson node.steps),
   ("summary_rows",toJson node.state.summary.length),
   ("summary_cells",toJson (node.state.summary.length*(node.width+1))),
   ("summary_cell_bound",toJson ((node.width+1)^2)),
   ("reference_cell_budget",toJson node.budget),("reference_cell_charge",toJson node.charge),("counted_complete",toJson false),
   ("summary",if includeSummary then toJson (node.state.summary.map rowJson) else Json.null)]

theorem report_answer (node : Node) (includeSummary : Bool) :
    (report node includeSummary).getObjValAs? Bool "answer" = .ok node.answer := by
  cases answer : node.answer <;> simp only [report,answer] <;> rfl

theorem report_charge (node : Node) (includeSummary : Bool) :
    (report node includeSummary).getObjValAs? Nat "reference_cell_charge" = .ok node.charge := by
  rfl

theorem report_charge_bound (node : Node) (includeSummary : Bool) :
    ∃ charge, (report node includeSummary).getObjValAs? Nat "reference_cell_charge" = .ok charge ∧
      charge ≤ node.budget := ⟨node.charge,report_charge _ _,node.charge_bound⟩

theorem report_semantics (node : Node) (includeSummary : Bool) :
    ∃ answer, (report node includeSummary).getObjValAs? Bool "answer" = .ok answer ∧
      (answer = true ↔ ∃ v, node.state.history.Holds v) ∧
      (answer = false ↔ ¬ ∃ v, node.state.history.Holds v) := by
  exact ⟨node.answer,report_answer node includeSummary,
    node.answer_exact ▸ node.state.answer_exact,node.answer_exact ▸ node.state.answer_false⟩

/-- Identities are immutable. The function returns a new store only after all
parsing and algebra succeed; errors leave the caller's store unchanged. -/
def define (store : Store) (request : Json) : Except String (Store × Json) := do
  let id ← request.getObjValAs? String "id"
  if let some previous := store[id]? then
    if previous.body == request then return (store,report previous true)
    else throw "Affine identity changed"
  if store.size ≥ 4096 then throw "Affine native version capacity exceeded"
  let mode ← request.getObjValAs? String "mode"
  let node ← if mode == "affine_init" then do
      let width ← request.getObjValAs? Nat "width"
      if width == 0 || width > 128 then throw "Affine width must be 1 to 128"
      let state := residentInitial width
      pure (Node.mk width state 0 (by change 0 = (residentInitial width).history.steps; rw [residentInitial_history]; rfl) state.answer rfl request 0 0 (by omega))
    else if mode == "affine_append" then do
      let base ← request.getObjValAs? String "base"
      let some previous := store[base]? | throw "Unknown affine base"
      let equations ← parseRows (previous.width+previous.width) request
      let result := previous.state.appendRun equations
      let state := result.1
      let decision := decideRun state.summary
      pure (Node.mk previous.width state (previous.steps+1)
        (by rw [Resident.appendRun_history]; change previous.steps+1 = previous.state.history.steps+1; rw [previous.steps_exact])
        decision.1 (decideRun_value _) request (appendBudget previous.width equations.length)
        (result.2+decision.2) (previous.state.appendRun_bound equations))
    else throw "Unknown affine definition mode"
  return (store.insert id node,report node true)

def query (store : Store) (request : Json) : Except String Json := do
  let root ← request.getObjValAs? String "root"
  let some node := store[root]? | throw "Unknown affine root"
  let includeSummary ← request.getObjValAs? Bool "summary"
  return report node includeSummary

/-- A computed affine child contains no live reference to its parent's map name.
Its exact original history is erased proof data; eviction cannot change that
child's summary, answer or semantic history. -/
def dropNames (store : Store) : List String → Store
  | [] => store
  | name::rest => dropNames (store.erase name) rest

theorem dropNames_preserves (store : Store) (names : List String) (name : String)
    (retained : name ∉ names) : (dropNames store names)[name]? = store[name]? := by
  induction names generalizing store with
  | nil => rfl
  | cons head rest ih =>
    simp only [List.mem_cons,not_or] at retained
    simp only [dropNames,ih _ retained.2]
    simp [Std.HashMap.getElem?_erase,Ne.symm retained.1]

def drop (store : Store) (request : Json) : Except String (Store × Json) := do
  let names ← request.getObjValAs? (Array String) "ids"
  if names.size > 4096 then throw "Affine eviction batch exceeds capacity"
  let next := dropNames store names.toList
  return (next,Json.mkObj [("valid",toJson true),("resident_versions",toJson next.size)])

def stats (store : Store) : Json := Json.mkObj [("resident_versions",toJson store.size)]

end OracleMachines.Affine

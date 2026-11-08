import OracleMachines.AffineResident
import Lean.Data.Json

/-! Native affine growth. The executed algebra carries exact history semantics.
Decoded field certificates connect native definitions, queries and eviction to
those histories. Raw byte transport, hashing, Python replay and SQLite remain
separate integration boundaries. -/
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

/-- Raw Boolean fields and dimensions, before any affine elimination. -/
def DecodedRow (n : Nat) (body : Json) (row : Row n) : Prop :=
  ∃ (coefficients : Array Bool) (rhs : Bool) (size : coefficients.size = n),
    body.getObjValAs? (Array Bool) "coefficients" = .ok coefficients ∧
    body.getObjValAs? Bool "rhs" = .ok rhs ∧
    row = ⟨(⟨coefficients,size⟩ : Vector Bool n).map (fun value => if value then 1 else 0),
      if rhs then 1 else 0⟩

theorem parseRow_decoded (n : Nat) (body : Json) (row : Row n)
    (accepted : parseRow n body = .ok row) : DecodedRow n body row := by
  cases coefficientsField : body.getObjValAs? (Array Bool) "coefficients" with
  | error message => simp [parseRow,coefficientsField,bind,Except.bind] at accepted
  | ok coefficients =>
    cases rhsField : body.getObjValAs? Bool "rhs" with
    | error message => simp [parseRow,coefficientsField,rhsField,bind,Except.bind] at accepted
    | ok rhs =>
      by_cases size : coefficients.size = n
      · have same : (⟨(⟨coefficients,size⟩ : Vector Bool n).map
            (fun value => if value then 1 else 0),if rhs then 1 else 0⟩ : Row n) = row := by
          simpa [parseRow,coefficientsField,rhsField,size,bind,Except.bind,pure,Except.pure] using accepted
        exact ⟨coefficients,rhs,size,coefficientsField,rhsField,same.symm⟩
      · simp [parseRow,coefficientsField,rhsField,size,bind,Except.bind] at accepted

theorem parseRowList_decoded (n : Nat) (raw : List Json) (rows : List (Row n))
    (accepted : raw.mapM (parseRow n) = .ok rows) : List.Forall₂ (DecodedRow n) raw rows := by
  induction raw generalizing rows with
  | nil =>
    have same : rows = [] := by simpa [List.mapM_nil,pure,Except.pure] using accepted.symm
    subst rows
    exact .nil
  | cons body rest ih =>
    cases first : parseRow n body with
    | error message => simp [List.mapM_cons,first,bind,Except.bind] at accepted
    | ok row =>
      cases tail : rest.mapM (parseRow n) with
      | error message => simp [List.mapM_cons,first,tail,bind,Except.bind] at accepted
      | ok parsed =>
        have same : row::parsed = rows := by
          simpa [List.mapM_cons,first,tail,bind,Except.bind,pure,Except.pure] using accepted
        subst rows
        exact .cons (parseRow_decoded n body row first) (ih parsed tail)

def DecodedRows (n : Nat) (request : Json) (rows : List (Row n)) : Prop :=
  ∃ raw : Array Json, request.getObjValAs? (Array Json) "equations" = .ok raw ∧
    raw.size ≤ 4096 ∧ List.Forall₂ (DecodedRow n) raw.toList rows

theorem parseRows_decoded (n : Nat) (request : Json) (rows : List (Row n))
    (accepted : parseRows n request = .ok rows) : DecodedRows n request rows := by
  cases field : request.getObjValAs? (Array Json) "equations" with
  | error message => simp [parseRows,field,bind,Except.bind] at accepted
  | ok raw =>
    by_cases capacity : raw.size > 4096
    · simp [parseRows,field,capacity,bind,Except.bind] at accepted
    · have parsed : raw.toList.mapM (parseRow n) = .ok rows := by
        simpa [parseRows,field,capacity,bind,Except.bind] using accepted
      exact ⟨raw,field,by omega,parseRowList_decoded n raw.toList rows parsed⟩

structure ParsedField (α : Type) [FromJson α] (body : Json) (field : String) where
  value : α
  exact : body.getObjValAs? α field = .ok value

def readField (α : Type) [FromJson α] (body : Json) (field : String) :
    Except String (ParsedField α body field) :=
  match decoded : body.getObjValAs? α field with
  | .error message => .error message
  | .ok value => .ok ⟨value,decoded⟩

def readRows (n : Nat) (request : Json) : Except String {rows : List (Row n) // DecodedRows n request rows} :=
  match decoded : parseRows n request with
  | .error message => .error message
  | .ok rows => .ok ⟨rows,parseRows_decoded n request rows decoded⟩

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

def initialNode (width : Nat) (request : Json) : Node :=
  let state := residentInitial width
  Node.mk width state 0 (by rw [residentInitial_history]; rfl)
    state.answer rfl request 0 0 (by omega)

def appendNode (previous : Node) (rows : List (Row (previous.width+previous.width)))
    (request : Json) : Node :=
  let result := previous.state.appendRun rows
  let state := result.1
  let decision := decideRun state.summary
  Node.mk previous.width state (previous.steps+1)
    (by rw [Resident.appendRun_history]; change previous.steps+1 = previous.state.history.steps+1; rw [previous.steps_exact])
    decision.1 (decideRun_value _) request (appendBudget previous.width rows.length)
    (result.2+decision.2) (previous.state.appendRun_bound rows)

theorem initialNode_history (width : Nat) (request : Json) :
    (initialNode width request).state.history = .empty := residentInitial_history width

theorem appendNode_history (previous : Node) (rows : List (Row (previous.width+previous.width)))
    (request : Json) : (appendNode previous rows request).state.history = .append previous.state.history rows :=
  previous.state.appendRun_history rows

/-- A fresh definition is linked to the actual decoded fields and predecessor
lookup. A retry is specified separately because that parent name may now differ. -/
def Created (store : Store) (request : Json) (node : Node) : Prop :=
  (∃ width, request.getObjValAs? String "mode" = .ok "affine_init" ∧
    request.getObjValAs? Nat "width" = .ok width ∧ 1 ≤ width ∧ width ≤ 128 ∧
    node = initialNode width request) ∨
  (∃ base previous rows, request.getObjValAs? String "mode" = .ok "affine_append" ∧
    request.getObjValAs? String "base" = .ok base ∧ store[base]? = some previous ∧
    DecodedRows (previous.width+previous.width) request rows ∧ node = appendNode previous rows request)

def buildNode (store : Store) (request : Json) : Except String {node : Node // Created store request node} := do
  let mode ← readField String request "mode"
  if init : mode.value = "affine_init" then
    let width ← readField Nat request "width"
    if valid : 1 ≤ width.value ∧ width.value ≤ 128 then
      return ⟨initialNode width.value request,Or.inl ⟨width.value,by simpa [init] using mode.exact,
        width.exact,valid.1,valid.2,rfl⟩⟩
    else throw "Affine width must be 1 to 128"
  else if append : mode.value = "affine_append" then
    let base ← readField String request "base"
    match found : store[base.value]? with
    | none => throw "Unknown affine base"
    | some previous =>
      let rows ← readRows (previous.width+previous.width) request
      return ⟨appendNode previous rows.val request,Or.inr ⟨base.value,previous,rows.val,
        by simpa [append] using mode.exact,base.exact,found,rows.property,rfl⟩⟩
  else throw "Unknown affine definition mode"

/-- Compare the parsed source fields as well as the existing JSON identity
check. Thus sound reuse does not assume a theorem about Lean's partial JSON BEq. -/
def SameInput (width : Nat) (old request : Json) : Prop :=
  (old.getObjValAs? String "mode" = .ok "affine_init" ∧
   request.getObjValAs? String "mode" = .ok "affine_init" ∧
   ∃ size, old.getObjValAs? Nat "width" = .ok size ∧ request.getObjValAs? Nat "width" = .ok size) ∨
  (old.getObjValAs? String "mode" = .ok "affine_append" ∧
   request.getObjValAs? String "mode" = .ok "affine_append" ∧
   ∃ base rows, old.getObjValAs? String "base" = .ok base ∧
     request.getObjValAs? String "base" = .ok base ∧
     DecodedRows (width+width) old rows ∧ DecodedRows (width+width) request rows)

def checkSameInput (node : Node) (request : Json) : Except String (PLift (SameInput node.width node.body request)) := do
  let before ← readField String node.body "mode"
  let after ← readField String request "mode"
  if same : before.value = after.value then
    if init : before.value = "affine_init" then
      let oldWidth ← readField Nat node.body "width"
      let newWidth ← readField Nat request "width"
      if width : oldWidth.value = newWidth.value then
        return ⟨Or.inl ⟨by simpa [init] using before.exact,by simpa [← same,init] using after.exact,
          oldWidth.value,oldWidth.exact,by simpa [← width] using newWidth.exact⟩⟩
      else throw "Affine identity changed"
    else if append : before.value = "affine_append" then
      let oldBase ← readField String node.body "base"
      let newBase ← readField String request "base"
      if base : oldBase.value = newBase.value then
        let oldRows ← readRows (node.width+node.width) node.body
        let newRows ← readRows (node.width+node.width) request
        if rows : oldRows.val = newRows.val then
          return ⟨Or.inr ⟨by simpa [append] using before.exact,by simpa [← same,append] using after.exact,
            oldBase.value,oldRows.val,oldBase.exact,by simpa [← base] using newBase.exact,
            oldRows.property,by simpa [← rows] using newRows.property⟩⟩
        else throw "Affine identity changed"
      else throw "Affine identity changed"
    else throw "Unknown affine definition mode"
  else throw "Affine identity changed"

def DefinitionResponse (store next : Store) (request reply : Json) : Prop :=
  ∃ id node, request.getObjValAs? String "id" = .ok id ∧ next[id]? = some node ∧
    reply = report node true ∧
    ((next = store ∧ store[id]? = some node ∧ SameInput node.width node.body request) ∨
     (store[id]? = none ∧ Created store request node ∧ next = store.insert id node))

/-- Only a completed definition updates the map. Repeating a live identity
returns its existing history, rather than reinterpreting a reused parent name. -/
def defineChecked (store : Store) (request : Json) :
    Except String {result : Store × Json // DefinitionResponse store result.1 request result.2} := do
  let id ← readField String request "id"
  match found : store[id.value]? with
  | some previous =>
    if previous.body == request then
      let same ← checkSameInput previous request
      return ⟨(store,report previous true),id.value,previous,id.exact,found,rfl,
        Or.inl ⟨rfl,found,same.down⟩⟩
    else throw "Affine identity changed"
  | none =>
    if store.size ≥ 4096 then throw "Affine native version capacity exceeded"
    let node ← buildNode store request
    return ⟨(store.insert id.value node.val,report node.val true),id.value,node.val,id.exact,
      by simp only [Std.HashMap.getElem?_insert_self],rfl,Or.inr ⟨found,node.property,rfl⟩⟩

def define (store : Store) (request : Json) : Except String (Store × Json) :=
  (defineChecked store request).map Subtype.val

theorem define_success (store next : Store) (request reply : Json)
    (accepted : define store request = .ok (next,reply)) : DefinitionResponse store next request reply := by
  cases checked : defineChecked store request with
  | error message => simp [define,checked,Except.map] at accepted
  | ok certified =>
    have same : certified.val = (next,reply) := by simpa [define,checked,Except.map] using accepted
    simpa only [same] using certified.property

def QueryResponse (store : Store) (request reply : Json) : Prop :=
  ∃ root node includeSummary, request.getObjValAs? String "root" = .ok root ∧
    store[root]? = some node ∧ request.getObjValAs? Bool "summary" = .ok includeSummary ∧
    reply = report node includeSummary

def queryChecked (store : Store) (request : Json) : Except String {reply : Json // QueryResponse store request reply} := do
  let root ← readField String request "root"
  match found : store[root.value]? with
  | none => throw "Unknown affine root"
  | some node =>
    let includeSummary ← readField Bool request "summary"
    return ⟨report node includeSummary.value,root.value,node,includeSummary.value,root.exact,found,includeSummary.exact,rfl⟩

def query (store : Store) (request : Json) : Except String Json := (queryChecked store request).map Subtype.val

theorem query_success (store : Store) (request reply : Json)
    (accepted : query store request = .ok reply) : QueryResponse store request reply := by
  cases checked : queryChecked store request with
  | error message => simp [query,checked,Except.map] at accepted
  | ok certified =>
    have same : certified.val = reply := by simpa [query,checked,Except.map] using accepted
    exact same ▸ certified.property

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

theorem dropNames_submap (store : Store) (names : List String) (name : String) (node : Node)
    (found : (dropNames store names)[name]? = some node) : store[name]? = some node := by
  induction names generalizing store with
  | nil => exact found
  | cons head rest ih =>
    have present := ih (store.erase head) found
    by_cases same : head = name
    · simp [same] at present
    · simpa [Std.HashMap.getElem?_erase,same] using present

def DropResponse (store next : Store) (request reply : Json) : Prop :=
  ∃ names : Array String, request.getObjValAs? (Array String) "ids" = .ok names ∧
    names.size ≤ 4096 ∧ next = dropNames store names.toList ∧
    reply = Json.mkObj [("valid",toJson true),("resident_versions",toJson next.size)]

def dropChecked (store : Store) (request : Json) :
    Except String {result : Store × Json // DropResponse store result.1 request result.2} := do
  let names ← readField (Array String) request "ids"
  if capacity : names.value.size ≤ 4096 then
    let next := dropNames store names.value.toList
    return ⟨(next,Json.mkObj [("valid",toJson true),("resident_versions",toJson next.size)]),
      names.value,names.exact,capacity,rfl,rfl⟩
  else throw "Affine eviction batch exceeds capacity"

def drop (store : Store) (request : Json) : Except String (Store × Json) :=
  (dropChecked store request).map Subtype.val

theorem drop_success (store next : Store) (request reply : Json)
    (accepted : drop store request = .ok (next,reply)) : DropResponse store next request reply := by
  cases checked : dropChecked store request with
  | error message => simp [drop,checked,Except.map] at accepted
  | ok certified =>
    have same : certified.val = (next,reply) := by simpa [drop,checked,Except.map] using accepted
    simpa only [same] using certified.property

def stats (store : Store) : Json := Json.mkObj [("resident_versions",toJson store.size)]

end OracleMachines.Affine

import OracleMachines.AffineProtocol

/-! Executed affine request histories, with decoded original-equation provenance.
Names have event-specific meanings. Erasure keeps all trace and origin evidence
out of resident runtime states. Bytes, Python and database lineage are separate. -/
namespace OracleMachines.AffineHistory
open Lean OracleMachines.Affine

inductive Kind where
  | define | query | drop | stats | reset | config
  deriving DecidableEq

def kind (request : Json) : Except String Kind := do
  let mode ← request.getObjValAs? String "mode"
  if mode == "affine_init" || mode == "affine_append" then return .define
  else if mode == "affine_query" then return .query
  else if mode == "affine_drop" then return .drop
  else if mode == "affine_stats" then return .stats
  else if mode == "affine_reset" then return .reset
  else if mode == "affine_cache_config" then return .config
  else throw "Unknown affine operation"

def run (store : Store) (request : Json) : Kind → Except String (Store × Json)
  | .define => OracleMachines.Affine.define store request
  | .query => (OracleMachines.Affine.query store request).map (fun reply => (store,reply))
  | .drop => OracleMachines.Affine.drop store request
  | .stats => .ok (store,OracleMachines.Affine.stats store)
  | .config => OracleMachines.Affine.configure store request
  | .reset => .ok (OracleMachines.Affine.reset store,Json.mkObj [("valid",toJson true)])

def Meaning (store next : Store) (request : Json) (operation : Kind) (reply : Json) : Prop :=
  match operation with
  | .define => DefinitionResponse store next request reply
  | .query => next = store ∧ QueryResponse store request reply
  | .drop => DropResponse store next request reply
  | .stats => next = store ∧ reply = OracleMachines.Affine.stats store
  | .config => ConfigResponse store next request
  | .reset => next = OracleMachines.Affine.reset store ∧ reply = Json.mkObj [("valid",toJson true)]

theorem run_meaning (store next : Store) (request reply : Json) (operation : Kind)
    (accepted : run store request operation = .ok (next,reply)) : Meaning store next request operation reply := by
  cases operation with
  | define => exact define_success store next request reply accepted
  | config => exact configure_success store next request reply accepted
  | drop => exact drop_success store next request reply accepted
  | stats => simpa [run,Meaning,eq_comm] using accepted
  | reset => simpa [run,Meaning,eq_comm] using accepted
  | query =>
    cases returned : OracleMachines.Affine.query store request with
    | error message => simp [run,returned,Except.map] at accepted
    | ok output =>
      have same : store = next ∧ output = reply := by simpa [run,returned,Except.map] using accepted
      exact ⟨same.1.symm,query_success store request reply (same.2 ▸ returned)⟩

def dispatch (store : Store) (request : Json) : Except String (Store × Json) := do
  let operation ← kind request
  run store request operation

/-- This handler is executed by the worker; rejected operations are atomic. -/
def handle (store : Store) (request : Json) : Store × Except String Json :=
  match dispatch store request with
  | .error message => (store,.error message)
  | .ok (next,reply) => (next,.ok reply)

structure Event where
  before : Store
  request : Json
  after : Store
  reply : Except String Json

def Event.Valid (event : Event) : Prop :=
  match event.reply with
  | .error message => event.after = event.before ∧ dispatch event.before event.request = .error message
  | .ok reply => ∃ operation, kind event.request = .ok operation ∧
      run event.before event.request operation = .ok (event.after,reply) ∧
      Meaning event.before event.after event.request operation reply

theorem handle_valid (store : Store) (request : Json) :
    (Event.mk store request (handle store request).1 (handle store request).2).Valid := by
  cases decoded : kind request with
  | error message => simp [Event.Valid,handle,dispatch,decoded,bind,Except.bind]
  | ok operation =>
    cases result : run store request operation with
    | error message => simp [Event.Valid,handle,dispatch,decoded,result,bind,Except.bind]
    | ok output =>
      obtain ⟨next,reply⟩ := output
      simp only [handle,dispatch,decoded,Except.bind,bind,result,Event.Valid]
      exact ⟨operation,rfl,result,run_meaning store next request reply operation result⟩

/-- Mathematical trace only; the running worker does not accumulate snapshots. -/
def execute (store : Store) : List Json → Store × List Event
  | [] => (store,[])
  | request::rest =>
    let result := handle store request
    let suffix := execute result.1 rest
    (suffix.1,⟨store,request,result.1,result.2⟩::suffix.2)

theorem execute_valid (store : Store) (requests : List Json) :
    ∀ event ∈ (execute store requests).2, event.Valid := by
  induction requests generalizing store with
  | nil => simp [execute]
  | cons request rest ih =>
    intro event member
    simp only [execute,List.mem_cons] at member
    rcases member with rfl|member
    · exact handle_valid store request
    · exact ih (handle store request).1 event member

theorem execute_append (store : Store) (first rest : List Json) :
    execute store (first++rest) =
      let front := execute store first
      let suffix := execute front.1 rest
      (suffix.1,front.2++suffix.2) := by
  induction first generalizing store with
  | nil => simp [execute]
  | cons request first ih => simp [execute,ih]

theorem earlier_event_retained (store : Store) (first rest : List Json) (event : Event)
    (earlier : event ∈ (execute store first).2) :
    event ∈ (execute store (first++rest)).2 ∧ event.Valid := by
  constructor
  · rw [execute_append]; exact List.mem_append_left _ earlier
  · exact execute_valid store first event earlier

/-- A history originates in actual decoded requests in their chronological order.
Unrelated requests, retries, failures, resets and deletions may be skipped. -/
inductive Origin (width : Nat) : List Json → History width → Prop where
  | initial {past : List Json} {request : Json}
      (mode : request.getObjValAs? String "mode" = .ok "affine_init")
      (dimension : request.getObjValAs? Nat "width" = .ok width)
      (positive : 1 ≤ width) (capacity : width ≤ 128) :
      Origin width (past++[request]) .empty
  | append {past : List Json} {request : Json} {history : History width}
      (previous : Origin width past history) (rows : List (Row (width+width)))
      (mode : request.getObjValAs? String "mode" = .ok "affine_append")
      (equations : DecodedRows (width+width) request rows) :
      Origin width (past++[request]) (.append history rows)
  | keep {past : List Json} {request : Json} {history : History width}
      (previous : Origin width past history) : Origin width (past++[request]) history

def Sourced (requests : List Json) (store : Store) : Prop :=
  ∀ (name : String) (node : Node), store.nodes[name]? = some node → Origin node.width requests node.state.history

theorem empty_sourced (requests : List Json) : Sourced requests {} := by
  intro name node found
  simp at found

theorem sourced_keep (past : List Json) (request : Json) (store : Store)
    (sourced : Sourced past store) : Sourced (past++[request]) store :=
  fun name node found => .keep (sourced name node found)

theorem created_origin (past : List Json) (store : Store) (request : Json) (node : Node)
    (sourced : Sourced past store) (created : Created store request node) :
    Origin node.width (past++[request]) node.state.history := by
  rcases created with initial | appended
  · obtain ⟨width,mode,dimension,positive,capacity,rfl⟩ := initial
    rw [initialNode_history]
    exact .initial mode dimension positive capacity
  · obtain ⟨base,previous,rows,mode,field,found,decoded,used,rfl⟩ := appended
    rw [appendNode_history]
    exact .append (sourced base previous found) rows mode decoded

theorem definition_sourced (past : List Json) (store next : Store) (request reply : Json)
    (sourced : Sourced past store) (response : DefinitionResponse store next request reply) :
    Sourced (past++[request]) next := by
  obtain ⟨id,created,field,mapped,reported,retry|fresh⟩ := response
  · rw [retry.1]; exact sourced_keep past request store sourced
  · obtain ⟨absent,creation,changed⟩ := fresh
    intro name node found
    rw [changed] at found
    by_cases same : name = id
    · subst name
      have equal : node = created := by simpa only [Std.HashMap.getElem?_insert_self,Option.some.injEq] using found.symm
      subst node
      exact created_origin past store request created sourced creation
    · apply Origin.keep (sourced name node ?_)
      simpa [Std.HashMap.getElem?_insert,same,Ne.symm same] using found

theorem meaning_sourced (past : List Json) (store next : Store) (request reply : Json) (operation : Kind)
    (sourced : Sourced past store) (meaning : Meaning store next request operation reply) :
    Sourced (past++[request]) next := by
  cases operation with
  | define => exact definition_sourced past store next request reply sourced meaning
  | query => rw [meaning.1]; exact sourced_keep past request store sourced
  | stats => rw [meaning.1]; exact sourced_keep past request store sourced
  | reset =>
    intro name node found
    rw [meaning.1] at found
    simp [OracleMachines.Affine.reset] at found
  | config =>
    obtain ⟨slots,field,capacity,unchanged,cleared⟩ := meaning
    intro name node found
    exact .keep (sourced name node (unchanged ▸ found))
  | drop =>
    obtain ⟨names,field,capacity,rfl,reported⟩ := meaning
    intro name node found
    exact .keep (sourced name node (dropNames_submap store names.toList name node found))

theorem handle_sourced (past : List Json) (store : Store) (request : Json)
    (sourced : Sourced past store) : Sourced (past++[request]) (handle store request).1 := by
  have valid := handle_valid store request
  cases returned : (handle store request).2 with
  | error message =>
    rw [Event.Valid,returned] at valid
    have unchanged : (handle store request).1 = store := valid.1
    rw [unchanged]
    exact sourced_keep past request store sourced
  | ok reply =>
    rw [Event.Valid,returned] at valid
    obtain ⟨operation,decoded,executed,meaning⟩ := valid
    exact meaning_sourced past store _ request reply operation sourced meaning

theorem execute_sourced (past requests : List Json) (store : Store) (sourced : Sourced past store) :
    Sourced (past++requests) (execute store requests).1 := by
  induction requests generalizing store past with
  | nil => simpa [execute] using sourced
  | cons request rest ih =>
    have step := handle_sourced past store request sourced
    simpa [execute,List.append_assoc] using ih (past++[request]) (handle store request).1 step

theorem empty_execute_sourced (requests : List Json) : Sourced requests (execute {} requests).1 := by
  simpa using execute_sourced [] requests {} (empty_sourced [])

/-- A query after any finite trace from the empty store answers an original
system assembled from that trace's decoded input equations. Current root lookup
and historical input origin are both part of the contract. -/
theorem executed_query_semantics (requests : List Json) (request reply : Json)
    (accepted : OracleMachines.Affine.query (execute {} requests).1 request = .ok reply) :
    ∃ name node answer, request.getObjValAs? String "root" = .ok name ∧
      (execute {} requests).1.nodes[name]? = some node ∧
      Origin node.width requests node.state.history ∧
      reply.getObjValAs? Bool "answer" = .ok answer ∧
      (answer = true ↔ ∃ v, node.state.history.Holds v) ∧
      (answer = false ↔ ¬ ∃ v, node.state.history.Holds v) := by
  obtain ⟨name,node,summary,field,found,want,rfl⟩ := query_success _ request reply accepted
  obtain ⟨answer,reported,positive,negative⟩ := report_semantics node summary
  exact ⟨name,node,answer,field,found,empty_execute_sourced requests name node found,reported,positive,negative⟩

end OracleMachines.AffineHistory

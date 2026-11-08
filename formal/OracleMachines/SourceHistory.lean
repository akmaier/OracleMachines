import OracleMachines.SourceUpdates

/-! One executed dispatcher for native source requests, including rejected
operations. Its trace theorem composes the existing raw-initial, current-root
and exact-patch contracts over arbitrary finite interleavings. Meanings belong
to the store snapshot at that event; names may be reused after eviction/reset. -/
namespace OracleMachines.SourceHistory
open Lean OracleMachines.SourceNodes
open OracleMachines.Layered (sourceCNFEval)
open OracleMachines.SourceUpdates

inductive Kind where
  | setup | compile | define | drop | query | patch | bind
  deriving DecidableEq

def kind (request : Json) : Except String Kind := do
  let mode ← request.getObjValAs? String "mode"
  if mode == "source_init" then return .setup
  else if mode == "source_compile" then return .compile
  else if mode == "source_define" then return .define
  else if mode == "source_drop" then return .drop
  else if mode == "source_query" then return .query
  else if mode == "source_patch" then return .patch
  else if mode == "source_bind" then return .bind
  else throw "Unknown source operation"

/-- Full raw-CNF provenance or exact patch provenance, when the operation has
one, is retained in the specification. Administrative transitions use their
actual native functions and carry the typed store invariants. -/
def Meaning (store : Store) (request : Json) (operation : Kind) (result : Json) : Prop :=
  match operation with
  | .bind => ∃ context, store.context = some context ∧
      OracleMachines.SourceInitial.InitialResponse context.layout context.checked request result
  | .query => ∃ context, store.context = some context ∧
      OracleMachines.SourceVerdict.Response context.checked request result
  | .patch => ∃ context, store.context = some context ∧
      OracleMachines.SourceVerdict.PatchResponse context.checked context.layout.buckets.size request result
  | _ => True

def run (store : Store) (request : Json) : Kind → Except String (Store × Json)
  | .setup => initializeLayout store request
  | .compile => (compileEdges store request).map (fun reply => (store,reply))
  | .define => defineNodes store request
  | .drop => dropNodes store request
  | .query => (query store request).map (fun reply => (store,reply))
  | .patch => (patchQuery store request).map (fun reply => (store,reply))
  | .bind => (bindSource store request).map (fun reply => (store,reply))

theorem run_meaning (store next : Store) (request reply : Json) (operation : Kind)
    (success : run store request operation = .ok (next,reply)) : Meaning store request operation reply := by
  cases operation with
  | setup => trivial
  | compile => trivial
  | define => trivial
  | drop => trivial
  | query =>
    cases result : query store request with
    | error message => simp [run,result,Except.map] at success
    | ok returned =>
      have same : returned = reply := by simpa [run,result,Except.map] using congrArg (Except.map Prod.snd) success
      exact query_success store request reply (same ▸ result)
  | patch =>
    cases result : patchQuery store request with
    | error message => simp [run,result,Except.map] at success
    | ok returned =>
      have same : returned = reply := by simpa [run,result,Except.map] using congrArg (Except.map Prod.snd) success
      exact patchQuery_success store request reply (same ▸ result)
  | bind =>
    cases result : bindSource store request with
    | error message => simp [run,result,Except.map] at success
    | ok returned =>
      have same : returned = reply := by simpa [run,result,Except.map] using congrArg (Except.map Prod.snd) success
      exact bindSource_success store request reply (same ▸ result)

def dispatch (store : Store) (request : Json) : Except String (Store × Json) := do
  let operation ← kind request
  run store request operation

/-- This is executed by the JSON-lines worker: a rejected operation leaves its
predecessor store in place, including failures after partial local construction. -/
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
  | .ok reply => ∃ operation,
      kind event.request = .ok operation ∧
      run event.before event.request operation = .ok (event.after,reply) ∧
      Meaning event.before event.request operation reply

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

/-- Mathematical observation trace of the same handler. The running worker does
not accumulate this list or retain old stores just to execute erased proofs. -/
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

theorem execute_length (store : Store) (requests : List Json) :
    (execute store requests).2.length = requests.length := by
  induction requests generalizing store with
  | nil => rfl
  | cons request rest ih => simp [execute,ih]

theorem execute_append (store : Store) (first rest : List Json) :
    execute store (first++rest) =
      let front :=  execute store first
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

/-- Specialize to bind or patch to retain their complete decoded-source and
replacement certificates, rather than only the final Boolean answer. -/
theorem trace_meaning (store : Store) (requests : List Json) (event : Event)
    (member : event ∈ (execute store requests).2) (reply : Json)
    (accepted : event.reply = .ok reply) (operation : Kind)
    (selected : kind event.request = .ok operation) :
    Meaning event.before event.request operation reply := by
  have valid := execute_valid store requests event member
  rw [Event.Valid,accepted] at valid
  obtain ⟨found,decoded,_,meaning⟩ := valid
  have same : found = operation := Except.ok.inj (decoded.symm.trans selected)
  exact same ▸ meaning

/-- Every ordinary query in an arbitrary interleaved trace answers its complete
original CNF, with source identity taken from that event's actual store. -/
theorem trace_query_semantics (store : Store) (requests : List Json) (event : Event)
    (member : event ∈ (execute store requests).2) (reply : Json)
    (accepted : event.reply = .ok reply) (queryKind : kind event.request = .ok .query) :
    ∃ context name model answer,
      event.before.context = some context ∧
      event.request.getObjValAs? String "root" = .ok name ∧
      context.checked.models[name]? = some model ∧
      OracleMachines.SourceVerdict.Covers model ∧
      reply.getObjValAs? Bool "answer" = .ok answer ∧
      (answer = true ↔ ∃ valuation, sourceCNFEval model.source.clauses.toArray valuation = true) ∧
      (answer = false ↔ ¬ ∃ valuation, sourceCNFEval model.source.clauses.toArray valuation = true) := by
  have valid := execute_valid store requests event member
  rw [Event.Valid,accepted] at valid
  obtain ⟨operation,decoded,_,meaning⟩ := valid
  have same : operation = .query := Except.ok.inj (decoded.symm.trans queryKind)
  subst operation
  obtain ⟨context,present,response⟩ := meaning
  obtain ⟨name,model,answer,root,mapped,coverage,field,positive,negative⟩ :=
    OracleMachines.SourceVerdict.response_semantics response context.layout.mapping
  exact ⟨context,name,model,answer,present,root,mapped,coverage,field,positive,negative⟩

end OracleMachines.SourceHistory

import OracleMachines.SourceInitial

/-! Source-bearing nodes: provenance and relations use the same balanced tree.
The partition is fixed within a version family. Local edits replace the clauses
of one or more adjacent-block edges; an empty list deletes that edge's clauses.
Every cached decision carries a proof of its original-source meaning. Layout,
start and height index source nodes; joining preserves consecutive intervals.
Flat-source grouping, complete binding and named-map/metadata correspondence
carry proofs, as do serialized summaries, live child links and incoming counts.
Requested patches carry exact original-formula and returned-decision proofs.
Initial raw-CNF binding, serialized witness contents and persistence remain
separate integration obligations. -/
namespace OracleMachines.SourceUpdates
open Lean OracleMachines.Layered
open OracleMachines.SourceNodes
open OracleMachines.SourceStore
open OracleMachines.SourceLinks

structure Context where
  id : String
  signature : Json
  layout : CompiledSource
  checked : OracleMachines.SourceLifetime.Store id layout.layers layout.width := .empty id layout.layers layout.width

def Context.nodes (context : Context) : OracleMachines.Layered.Store := context.checked.relations

def Context.models (context : Context) : Std.HashMap String (CheckedNode context.layout.layers context.layout.width) :=
  context.checked.models

structure Store where
  context : Option Context := none

def initializeLayout (store : Store) (request : Json) : Except String (Store × Json) := do
  let id ← request.getObjValAs? String "id"
  let body := Json.mkObj [("width",← request.getObjVal? "width"),
    ("layers",← request.getObjVal? "layers"),("clauses",toJson (#[] : Array (Array Int)))]
  if let some old := store.context then
    if old.id == id && old.signature != body then throw "Source layout identity changed"
  let layout ← compileSource body
  return (⟨some ⟨id,body,layout,.empty id layout.layers layout.width⟩⟩,Json.mkObj [("valid",toJson true)])

def compileEdge (layout : CompiledSource) (edge : Nat) (clauses : Array (Array Int)) :
    Except String (CheckedCNF layout.layers layout.width edge clauses) := do
  if edge ≥ layout.buckets.size then throw "Source edit outside logical edges"
  if clauses.size > 200000 then throw "Local source clause cap exceeded"
  let mut literals := 0
  for clause in clauses do
    literals := literals + clause.size
    if literals > 2000000 then throw "Local source literal cap exceeded"
  translateCNF layout.positions edge clauses

def compileEdges (store : Store) (request : Json) : Except String Json := do
  let some context := store.context | throw "Source layout not initialized"
  let layout := context.layout
  let edits ← request.getObjValAs? (Array Json) "edits"
  if edits.size > 4096 then throw "Source edit batch exceeds capacity"
  let mut masks : Array Nat := #[]
  let mut tests := 0
  for edit in edits do
    let edge ← edit.getObjValAs? Nat "edge"
    let clauses ← edit.getObjValAs? (Array (Array Int)) "clauses"
    let checked ← compileEdge layout edge clauses
    masks := masks.push (relationMask (compileLocal layout.width checked.localCNF))
    tests := tests + 1 + clauses.size + (clauses.toList.map Array.size).sum
  return Json.mkObj [("masks",toJson masks),("source_cells",toJson (edits.size*(2^layout.width)^2)),
    ("literal_test_bound",toJson (tests*(2^layout.width)^2))]

def defineNodes (store : Store) (request : Json) : Except String (Store × Json) := do
  let some context := store.context | throw "Source layout not initialized"
  let layout := context.layout
  let nodes ← request.getObjValAs? (Array Json) "nodes"
  if nodes.size > 128 then throw "Source definition batch exceeds capacity"
  let mut out := context.checked
  let mut cells := 0
  let mut tests := 0
  let mut sourceNodes := 0
  let mut originalClauses := 0
  let mut originalLiterals := 0
  for body in nodes do
    let name ← readParsed String body "id"
    let id := name.value
    let before := out
    match present : before.relations.nodes[id]? with
    | some old =>
      if old.1 != body then throw "Source node identity changed"
    | none =>
      if before.relations.nodes.size ≥ 200000 then throw "Native source store capacity exceeded"
      let header ← readHeader context.id layout.width body name
      let start := header.start
      let height := header.height
      if height > 16 || start ≥ 65536 then throw "Source node range exceeds capacity"
      let parsedMask ← readParsed Nat body "mask"
      let mask := parsedMask.value
      if mask ≥ 2^((2^layout.width)^2) then throw "Source mask exceeds width"
      let checked : {node : CheckedNode layout.layers layout.width //
          BodyMatches context.id id body node ∧ (node.height = 0 ∨ JoinLinks before.models body node)} ← if zero : height = 0 then do
        let original ← readParsed (Array (Array Int)) body "clauses"
        let clauses := original.value
        if inside : start < layout.layers.size-1 then
          let translated ← compileEdge layout start clauses
          let localCNF := translated.localCNF
          cells := cells + (2^layout.width)^2
          tests := tests + (1 + clauses.size + (clauses.toList.map Array.size).sum)*(2^layout.width)^2
          originalClauses := originalClauses + clauses.size
          originalLiterals := originalLiterals + (clauses.toList.map Array.size).sum
          if same : relationEqual (maskRelation layout.width mask) (compileLocal layout.width localCNF) then
            let model := checkedLeaf start clauses inside translated (maskRelation layout.width mask)
              ((relationEqual_exact _ _).mp same)
            let bound := bindHeader header model rfl zero.symm ⟨mask,parsedMask.exact,rfl⟩ (by
              intro payload root
              have equal : clauses = payload := by simpa [model,checkedLeaf,OriginalTree.rootClauses] using root
              exact original.exact.trans (congrArg Except.ok equal))
            pure (OracleMachines.SourceLifetime.registration (models := before.models) bound (Or.inl rfl))
          else throw "Source leaf mask does not match clauses"
        else
          let empty ← expectEqual clauses #[] "Source padding must be empty"
          if same : relationEqual (maskRelation layout.width mask) identity then
            let model := checkedPad (layers := layout.layers) start (by omega) (maskRelation layout.width mask)
              ((relationEqual_exact _ _).mp same)
            let bound := bindHeader header model rfl zero.symm ⟨mask,parsedMask.exact,rfl⟩ (by
              intro payload root
              have equal : (#[] : Array (Array Int)) = payload := by simpa [model,checkedPad,OriginalTree.rootClauses] using root
              exact original.exact.trans (congrArg Except.ok (empty.down.trans equal)))
            pure (OracleMachines.SourceLifetime.registration (models := before.models) bound (Or.inl rfl))
          else throw "Source padding must be identity"
      else do
        let linked ← readJoin before.models body
        let joined := linked.val
        let location ← expectEqual joined.start start "Source children do not cover consecutive edges"
        let level ← expectEqual height joined.height "Unbalanced source node"
        if same : relationEqual (maskRelation layout.width mask) joined.tree.summary then
          let bound := bindHeader header joined location.down level.down.symm
            ⟨mask,parsedMask.exact,(relationEqual_exact _ _).mp same⟩ (by
              intro payload root
              rw [linked.property.rootClauses_none] at root
              cases root)
          pure (OracleMachines.SourceLifetime.registration bound (Or.inr linked.property))
        else throw "Incorrect source summary"
      out ← before.insert id body checked.val checked.property.1 checked.property.2 present
      sourceNodes := sourceNodes+1
  return (⟨some {context with checked := out}⟩,Json.mkObj [("valid",toJson true),
    ("source_cells",toJson cells),("literal_test_bound",toJson tests),
    ("original_source_nodes",toJson sourceNodes),("original_clause_entries",toJson originalClauses),
    ("original_literal_entries",toJson originalLiterals)])

def dropNodes (store : Store) (request : Json) : Except String (Store × Json) := do
  let some context := store.context | throw "Source layout not initialized"
  let ids ← request.getObjValAs? (Array String) "ids"
  if ids.size > 4096 then throw "Eviction batch exceeds capacity"
  let mut out := context.checked
  for id in ids do out ← out.erase id
  return (⟨some {context with checked := out}⟩,
    Json.mkObj [("valid",toJson true),("evicted",toJson ids.size)])

/-- Root coverage and the returned answer field are certified against the
current named source model. Warm decisions do not flatten original clauses. -/
def query (store : Store) (request : Json) : Except String Json := do
  let some context := store.context | throw "Source layout not initialized"
  let checked ← OracleMachines.SourceVerdict.query context.layout context.checked request
  return checked.val

/-- The nested returned verdict is certified for the complete original formula
obtained by applying the decoded request to the live predecessor. -/
def patchQuery (store : Store) (request : Json) : Except String Json := do
  let some context := store.context | throw "Source layout not initialized"
  let checked ← OracleMachines.SourceVerdict.patchQuery context.layout context.checked request
  return checked.val

/-- The exposed JSON-returning function inherits the certificate carried by
the constructor it actually executes. -/
theorem query_success (store : Store) (request result : Json)
    (accepted : query store request = .ok result) :
    ∃ context, store.context = some context ∧
      OracleMachines.SourceVerdict.Response context.checked request result := by
  cases present : store.context with
  | none => simp [query,present] at accepted
  | some context =>
    cases checked : OracleMachines.SourceVerdict.query context.layout context.checked request with
    | error message => simp [query,present,checked] at accepted
    | ok certified =>
      have same : certified.val = result := by simpa [query,present,checked] using accepted
      exact ⟨context,rfl,same ▸ certified.property⟩

theorem patchQuery_success (store : Store) (request result : Json)
    (accepted : patchQuery store request = .ok result) :
    ∃ context, store.context = some context ∧
      OracleMachines.SourceVerdict.PatchResponse context.checked context.layout.buckets.size request result := by
  cases present : store.context with
  | none => simp [patchQuery,present] at accepted
  | some context =>
    cases checked : OracleMachines.SourceVerdict.patchQuery context.layout context.checked request with
    | error message => simp [patchQuery,present,checked] at accepted
    | ok certified =>
      have same : certified.val = result := by simpa [patchQuery,present,checked] using accepted
      exact ⟨context,rfl,same ▸ certified.property⟩

/-- Initial binding certifies the parsed CNF, exact live original buckets,
complete root coverage and the returned decision. Its full scan is charged. -/
def bindSource (store : Store) (request : Json) : Except String Json := do
  let some context := store.context | throw "Source layout not initialized"
  let checked ← OracleMachines.SourceInitial.bindSource context.layout context.checked request
  return checked.val

theorem bindSource_success (store : Store) (request result : Json)
    (accepted : bindSource store request = .ok result) :
    ∃ context, store.context = some context ∧
      OracleMachines.SourceInitial.InitialResponse context.layout context.checked request result := by
  cases present : store.context with
  | none => simp [bindSource,present] at accepted
  | some context =>
    cases checked : OracleMachines.SourceInitial.bindSource context.layout context.checked request with
    | error message => simp [bindSource,present,checked] at accepted
    | ok certified =>
      have same : certified.val = result := by simpa [bindSource,present,checked] using accepted
      exact ⟨context,rfl,same ▸ certified.property⟩

end OracleMachines.SourceUpdates

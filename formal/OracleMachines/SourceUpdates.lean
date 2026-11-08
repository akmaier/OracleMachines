import OracleMachines.SourceStore

/-! Source-bearing nodes: provenance and relations use the same balanced tree.
The partition is fixed within a version family. Local edits replace the clauses
of one or more adjacent-block edges; an empty list deletes that edge's clauses.
Every cached decision carries a proof of its original-source meaning. Layout,
start and height index source nodes; joining preserves consecutive intervals.
Flat-source grouping, complete binding and named-map/metadata correspondence
carry proofs. Named child links, requested patches and persistence are separate. -/
namespace OracleMachines.SourceUpdates
open Lean OracleMachines.Layered
open OracleMachines.SourceNodes
open OracleMachines.SourceStore

structure Context where
  id : String
  signature : Json
  layout : CompiledSource
  checked : OracleMachines.SourceStore.Store id layout.layers layout.width := .empty id layout.layers layout.width

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
    if let some old := out.relations.nodes[id]? then
      if old.1 != body then throw "Source node identity changed"
    else
      if out.relations.nodes.size ≥ 200000 then throw "Native source store capacity exceeded"
      let header ← readHeader context.id layout.width body name
      let start := header.start
      let height := header.height
      if height > 16 || start ≥ 65536 then throw "Source node range exceeds capacity"
      let mask ← body.getObjValAs? Nat "mask"
      if mask ≥ 2^((2^layout.width)^2) then throw "Source mask exceeds width"
      let checked ← if zero : height = 0 then do
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
            pure (bindHeader header model rfl zero.symm (by
              intro payload root
              have equal : clauses = payload := by simpa [model,checkedLeaf,OriginalTree.rootClauses] using root
              exact original.exact.trans (congrArg Except.ok equal)))
          else throw "Source leaf mask does not match clauses"
        else
          let empty ← expectEqual clauses #[] "Source padding must be empty"
          if same : relationEqual (maskRelation layout.width mask) identity then
            let model := checkedPad (layers := layout.layers) start (by omega) (maskRelation layout.width mask)
              ((relationEqual_exact _ _).mp same)
            pure (bindHeader header model rfl zero.symm (by
              intro payload root
              have equal : (#[] : Array (Array Int)) = payload := by simpa [model,checkedPad,OriginalTree.rootClauses] using root
              exact original.exact.trans (congrArg Except.ok (empty.down.trans equal))))
          else throw "Source padding must be identity"
      else do
        let left ← body.getObjValAs? String "left"
        let right ← body.getObjValAs? String "right"
        let some ca := out.models[left]? | throw "Missing left source invariant"
        let some cb := out.models[right]? | throw "Missing right source invariant"
        let location ← expectEqual ca.start start "Source children do not cover consecutive edges"
        if h : cb.height = ca.height then
          if consecutive : cb.start = ca.start+2^ca.height then
            let joined := checkedJoin ca cb h consecutive
            let level ← expectEqual height joined.height "Unbalanced source node"
            if !relationEqual (maskRelation layout.width mask) joined.tree.summary then throw "Incorrect source summary"
            pure (bindHeader header joined location.down level.down.symm (by
              intro payload root
              simp [joined,checkedJoin,OriginalTree.rootClauses] at root))
          else throw "Source children do not cover consecutive edges"
        else throw "Unbalanced source children"
      out ← out.insert id body checked.val checked.property
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

def query (store : Store) (request : Json) : Except String Json := do
  let some context := store.context | throw "Source layout not initialized"
  let layout := context.layout
  let root ← request.getObjValAs? String "root"
  let some _ := context.nodes.nodes[root]? | throw "Unknown source root"
  let some model := context.models[root]? | throw "Missing source invariant"
  if model.start != 0 || 2^model.height < layout.buckets.size ||
      (model.height > 0 && 2^(model.height-1) ≥ layout.buckets.size) then
    throw "Source root does not cover the full partition"
  -- model.decide_exact layout.mapping proves the original-CNF meaning of this
  -- decision. Original clauses are retained, but not walked by a warm query.
  let answer := model.decide
  let want ← request.getObjValAs? Bool "witness"
  if !want then return Json.mkObj [("answer",toJson answer),("witness",Json.null),("height",toJson model.height)]
  let verdict ← OracleMachines.Layered.query context.nodes (Json.mkObj [("root",toJson root),
    ("size",toJson layout.buckets.size),("witness",toJson true),
    ("left",toJson (2^(2^layout.width)-1)),("right",toJson (2^(2^layout.width)-1))])
  if (← verdict.getObjValAs? Bool "answer") != answer then throw "Source witness decision disagrees"
  return verdict

def checkPatch : Nat → OracleMachines.Layered.Store → String → String → List (Nat × Json) → Except String Nat
  | 0, _, _, _, _ => .error "Source patch depth exhausted"
  | fuel+1, store, old, new, edits => do
    if edits.isEmpty then
      if old != new then throw "Source patch changed an unedited subtree"
      return 1
    let some (a,ta) := store.nodes[old]? | throw "Unknown source base node"
    let some (b,tb) := store.nodes[new]? | throw "Unknown source replacement node"
    let start ← a.getObjValAs? Nat "start"
    if ta.height != tb.height || start != (← b.getObjValAs? Nat "start") then
      throw "Source patch changed the partition"
    if ta.height == 0 then
      if edits.length != 1 then throw "Duplicate source edge edit"
      let some (edge,clauses) := edits.head? | throw "Missing source edit"
      if edge != start || (← b.getObjVal? "clauses") != clauses then throw "Source patch clauses differ"
      return 1
    let middle := start + 2^(ta.height-1)
    let left ← checkPatch fuel store (← a.getObjValAs? String "left") (← b.getObjValAs? String "left")
      (edits.filter (fun e => e.1 < middle))
    let right ← checkPatch fuel store (← a.getObjValAs? String "right") (← b.getObjValAs? String "right")
      (edits.filter (fun e => e.1 ≥ middle))
    return left+right+1

def patchQuery (store : Store) (request : Json) : Except String Json := do
  let some context := store.context | throw "Source layout not initialized"
  let layout := context.layout
  let base ← request.getObjValAs? String "base"
  let root ← request.getObjValAs? String "root"
  let edits ← request.getObjValAs? (Array Json) "edits"
  if edits.size > 4096 then throw "Source edit batch exceeds capacity"
  let mut seen : Std.HashSet Nat := {}
  let mut changes := []
  for edit in edits do
    let edge ← edit.getObjValAs? Nat "edge"
    if edge ≥ layout.buckets.size || seen.contains edge then throw "Invalid or duplicate source edit"
    seen := seen.insert edge
    changes := (edge,← edit.getObjVal? "clauses") :: changes
  let visits ← checkPatch 18 context.nodes base root changes
  let verdict ← query store request
  return Json.mkObj [("verdict",verdict),("patch_visits",toJson visits)]

/-- Initial flat CNF binding is intentionally linear. Later requests carry only
local clauses and use checkPatch; restart replays the source-bearing nodes. -/
def bindSource (store : Store) (request : Json) : Except String Json := do
  let some context := store.context | throw "Source layout not initialized"
  let layout := context.layout
  let compiled ← compileSource request
  if compiled.width != layout.width || compiled.layers != layout.layers then throw "Source partition differs"
  let root ← request.getObjValAs? String "root"
  let mut pending := [root]
  let mut visited := 0
  for _ in [:131072] do
    match pending with
    | [] => break
    | name::rest =>
      pending := rest
      visited := visited+1
      let some (body,t) := context.nodes.nodes[name]? | throw "Missing source binding node"
      if t.height == 0 then
        let edge ← body.getObjValAs? Nat "start"
        if edge < compiled.original.size then
          if (← body.getObjValAs? (Array (Array Int)) "clauses") != compiled.original[edge]! then
            throw "Original source clauses differ from checked leaves"
      else
        pending := (← body.getObjValAs? String "left") :: (← body.getObjValAs? String "right") :: pending
  if !pending.isEmpty then throw "Source binding traversal cap exceeded"
  let some (_,checked) := context.nodes.nodes[root]? | throw "Unknown source root"
  let bound ← bindCompilation compiled checked
  let answer := bound.decide
  let verdict ← query store request
  if (← verdict.getObjValAs? Bool "answer") != answer then throw "Source decision disagrees with binding proof"
  return (Json.mkObj [("verdict",verdict.setObjVal! "answer" (toJson answer)),
    ("binding_visits",toJson visited)]).mergeObj bound.metrics

end OracleMachines.SourceUpdates

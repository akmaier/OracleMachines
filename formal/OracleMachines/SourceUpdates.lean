import OracleMachines.SourceInvariant

/-! Source-bearing nodes: provenance and relations use the same balanced tree.
The partition is fixed within a version family. Local edits replace the clauses
of one or more adjacent-block edges; an empty list deletes that edge's clauses.
Every cached decision carries a proof of its current local-source meaning.
Variable positions and local CNF translation also carry original-source proofs.
JSON/global grouping and persistence refinement obligations remain separate. -/
namespace OracleMachines.SourceUpdates
open Lean OracleMachines.Layered
open OracleMachines.SourceInvariant

structure Store where
  layout : Option (String × Json × CompiledSource) := none
  nodes : OracleMachines.Layered.Store := {}
  models : Std.HashMap String CheckedSource := {}

def initializeLayout (store : Store) (request : Json) : Except String (Store × Json) := do
  let id ← request.getObjValAs? String "id"
  let body := Json.mkObj [("width",← request.getObjVal? "width"),
    ("layers",← request.getObjVal? "layers"),("clauses",toJson (#[] : Array (Array Int)))]
  if let some (old, signature, _) := store.layout then
    if old == id && signature != body then throw "Source layout identity changed"
  let layout ← compileSource body
  return (⟨some (id,body,layout),{},{}⟩,Json.mkObj [("valid",toJson true)])

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
  let some (_,_,layout) := store.layout | throw "Source layout not initialized"
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
  let some (layoutId,_,layout) := store.layout | throw "Source layout not initialized"
  let nodes ← request.getObjValAs? (Array Json) "nodes"
  if nodes.size > 128 then throw "Source definition batch exceeds capacity"
  let mut out := store.nodes
  let mut models := store.models
  let mut cells := 0
  let mut tests := 0
  for body in nodes do
    let id ← body.getObjValAs? String "id"
    if let some old := out.nodes[id]? then
      if old.1 != body then throw "Source node identity changed"
    else
      if out.nodes.size ≥ 200000 then throw "Native source store capacity exceeded"
      if (← body.getObjValAs? String "layout") != layoutId then throw "Source layout mismatch"
      if (← body.getObjValAs? Nat "width") != layout.width then throw "Source width mismatch"
      let start ← body.getObjValAs? Nat "start"
      let height ← body.getObjValAs? Nat "height"
      if height > 16 || start ≥ 65536 then throw "Source node range exceeds capacity"
      let mask ← body.getObjValAs? Nat "mask"
      if mask ≥ 2^((2^layout.width)^2) then throw "Source mask exceeds width"
      let checked ← if height == 0 then do
        let clauses ← body.getObjValAs? (Array (Array Int)) "clauses"
        if start < layout.buckets.size then
          let translated ← compileEdge layout start clauses
          let localCNF := translated.localCNF
          cells := cells + (2^layout.width)^2
          tests := tests + (1 + clauses.size + (clauses.toList.map Array.size).sum)*(2^layout.width)^2
          if same : relationEqual (maskRelation layout.width mask) (compileLocal layout.width localCNF) then
            pure (checkedLeaf layout.width (some localCNF) (maskRelation layout.width mask)
              ((relationEqual_exact _ _).mp same))
          else throw "Source leaf mask does not match clauses"
        else
          if !clauses.isEmpty then throw "Source padding must be empty"
          if same : relationEqual (maskRelation layout.width mask) identity then
            pure (checkedLeaf layout.width none (maskRelation layout.width mask)
              ((relationEqual_exact _ _).mp same))
          else throw "Source padding must be identity"
      else do
        let left ← body.getObjValAs? String "left"
        let right ← body.getObjValAs? String "right"
        let some (a,_) := out.nodes[left]? | throw "Missing source left child"
        let some (b,_) := out.nodes[right]? | throw "Missing source right child"
        if (← a.getObjValAs? Nat "start") != start ||
            (← b.getObjValAs? Nat "start") != start+2^(height-1) then
          throw "Source children do not cover consecutive edges"
        let some ca := models[left]? | throw "Missing left source invariant"
        let some cb := models[right]? | throw "Missing right source invariant"
        if w : ca.width = cb.width then
          if h : ca.height = cb.height then
            let joined := checkedJoin ca cb w h
            if height != joined.height || joined.width != layout.width then throw "Unbalanced source node"
            if !relationEqual (maskRelation joined.width mask) joined.tree.summary then throw "Incorrect source summary"
            pure joined
          else throw "Unbalanced source children"
        else throw "Source child width mismatch"
      out ← out.insert id (body,checked.checkedTree)
      models := models.insert id checked
  return ({store with nodes := out, models := models},Json.mkObj [("valid",toJson true),
    ("source_cells",toJson cells),("literal_test_bound",toJson tests)])

def dropNodes (store : Store) (request : Json) : Except String (Store × Json) := do
  let (nodes,response) ← OracleMachines.Layered.dropNodes store.nodes request
  let ids ← request.getObjValAs? (Array String) "ids"
  let models := ids.foldl (fun acc id => acc.erase id) store.models
  return ({store with nodes := nodes,models := models},response)

def query (store : Store) (request : Json) : Except String Json := do
  let some (_,_,layout) := store.layout | throw "Source layout not initialized"
  let root ← request.getObjValAs? String "root"
  let some (body,checked) := store.nodes.nodes[root]? | throw "Unknown source root"
  let some model := store.models[root]? | throw "Missing source invariant"
  if (← body.getObjValAs? Nat "start") != 0 || 2^checked.height < layout.buckets.size ||
      (checked.height > 0 && 2^(checked.height-1) ≥ layout.buckets.size) then
    throw "Source root does not cover the full partition"
  -- checked_decide_exact applies to this executable decision. Every padding
  -- leaf was checked at registration; decision-only queries need no source walk.
  let answer := model.decide
  let want ← request.getObjValAs? Bool "witness"
  if !want then return Json.mkObj [("answer",toJson answer),("witness",Json.null),("height",toJson model.height)]
  let verdict ← OracleMachines.Layered.query store.nodes (Json.mkObj [("root",toJson root),
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
  let some (_,_,layout) := store.layout | throw "Source layout not initialized"
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
  let visits ← checkPatch 18 store.nodes base root changes
  let verdict ← query store request
  return Json.mkObj [("verdict",verdict),("patch_visits",toJson visits)]

/-- Initial flat CNF binding is intentionally linear. Later requests carry only
local clauses and use checkPatch; restart replays the source-bearing nodes. -/
def bindSource (store : Store) (request : Json) : Except String Json := do
  let some (_,_,layout) := store.layout | throw "Source layout not initialized"
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
      let some (body,t) := store.nodes.nodes[name]? | throw "Missing source binding node"
      if t.height == 0 then
        let edge ← body.getObjValAs? Nat "start"
        if edge < compiled.original.size then
          if (← body.getObjValAs? (Array (Array Int)) "clauses") != compiled.original[edge]! then
            throw "Original source clauses differ from checked leaves"
      else
        pending := (← body.getObjValAs? String "left") :: (← body.getObjValAs? String "right") :: pending
  if !pending.isEmpty then throw "Source binding traversal cap exceeded"
  let verdict ← query store request
  return Json.mkObj [("verdict",verdict),("binding_visits",toJson visited)]

end OracleMachines.SourceUpdates

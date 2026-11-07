import OracleMachines.Layered
import Lean.Data.Json

namespace OracleMachines.Layered
open Lean

structure CheckedTree where
  width : Nat
  height : Nat
  tree : Tree (2^width) height
  valid : tree.Valid

abbrev Store := Std.HashMap String (Json × CheckedTree)

theorem cast_valid {q h k : Nat} (eq : h = k) (t : Tree q h) (valid : t.Valid) :
    (eq ▸ t).Valid := by subst k; exact valid

theorem cast_width_valid {w v h : Nat} (eq : w = v) (t : Tree (2^w) h) (valid : t.Valid) :
    (eq ▸ t).Valid := by subst v; exact valid

def maskRelation (width mask : Nat) : Relation (2^width) := fun x y =>
  mask.testBit (2^width*x.val+y.val)
def relationMask {q : Nat} (r : Relation q) : Nat :=
  ((List.finRange q).flatMap fun x => (List.finRange q).map fun y =>
    if r x y then 2^(q*x.val+y.val) else 0).sum

def defineNodes (store : Store) (request : Json) : Except String (Store × Json) := do
  let nodes ← request.getObjValAs? (Array Json) "nodes"
  if nodes.size > 128 then throw "Chain batch exceeds capacity"
  let mut out := store
  for node in nodes do
    let id ← node.getObjValAs? String "id"
    if let some old := out[id]? then
      if old.1 != node then throw "Chain identity collision"
    else
      if out.size ≥ 200000 then throw "Native chain store capacity exceeded"
      let width ← node.getObjValAs? Nat "width"
      if width == 0 || width > 4 then throw "Layer width must be 1 to 4"
      let height ← node.getObjValAs? Nat "height"
      if height > 16 then throw "Chain height exceeds capacity"
      let mask ← node.getObjValAs? Nat "mask"
      if mask ≥ 2^((2^width)^2) then throw "Invalid chain relation"
      let checked ← if height == 0 then
          pure (CheckedTree.mk width 0 (.leaf (maskRelation width mask)) True.intro)
        else do
          let left ← node.getObjValAs? String "left"
          let right ← node.getObjValAs? String "right"
          let some (_, a) := out[left]? | throw "Missing left chain child"
          let some (_, b) := out[right]? | throw "Missing right chain child"
          if w : a.width = b.width then
            if h : a.height = b.height then
              let bt : Tree (2^a.width) a.height := h.symm ▸ w.symm ▸ b.tree
              have hb : bt.Valid := cast_valid h.symm _ (cast_width_valid w.symm b.tree b.valid)
              let joined := join a.tree bt
              if width != a.width || height != a.height+1 || relationMask joined.summary != mask then
                throw "Incorrect layered summary, width or height"
              pure (CheckedTree.mk a.width (a.height+1) joined (join_valid _ _ a.valid hb))
            else throw "Unbalanced layered node"
          else throw "Layer width mismatch"

      out := out.insert id (node, checked)
  return (out, Json.mkObj [("valid", toJson true)])

/-- Prepend each left endpoint. Every accepted split has a middle state. -/
def witnessPrefix {q : Nat} : {h : Nat} → Tree q h → Fin q → Fin q → List Nat → List Nat
  | 0, .leaf _, x, _, tail => x.val :: tail
  | _+1, .branch _ l r, x, z, tail =>
    match (List.finRange q).find? (fun y => l.summary x y && r.summary y z) with
    | none => tail
    | some y => witnessPrefix l x y (witnessPrefix r y z tail)

def witness {q h : Nat} (tree : Tree q h) (x y : Fin q) : List Nat :=
  witnessPrefix tree x y [y.val]

def query (store : Store) (request : Json) : Except String Json := do
  let root ← request.getObjValAs? String "root"
  let some (_, checked) := store[root]? | throw "Unknown chain root"
  let size ← request.getObjValAs? Nat "size"
  if size > 2^checked.height then throw "Chain size exceeds capacity"
  let left ← request.getObjValAs? Nat "left"
  let right ← request.getObjValAs? Nat "right"
  if left ≥ 2^(2^checked.width) || right ≥ 2^(2^checked.width) then throw "Invalid endpoint mask"
  let want ← request.getObjValAs? Bool "witness"
  let pair := ((List.finRange (2^checked.width)).flatMap fun x => (List.finRange (2^checked.width)).map fun y => (x,y)).find? (fun (x,y) =>
    left.testBit x.val && right.testBit y.val && checked.tree.summary x y)
  return Json.mkObj [("answer", toJson pair.isSome),
    ("witness", if want then
        toJson (pair.map (fun (x,y) => (witness checked.tree x y).take (size+1)))
      else Json.null),
    ("height", toJson checked.height)]
end OracleMachines.Layered

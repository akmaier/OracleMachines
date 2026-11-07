import OracleMachines.BalancedChain
import Lean.Data.Json

namespace OracleMachines.Chain
open Lean

structure CheckedTree where
  height : Nat
  tree : Tree height
  valid : tree.Valid

abbrev Store := Std.HashMap String (Json × CheckedTree)

theorem cast_valid {h k : Nat} (eq : h = k) (t : Tree h) (valid : t.Valid) :
    (eq ▸ t).Valid := by subst k; exact valid

def maskRelation (mask : Nat) : Relation := fun x y => mask.testBit (2*x.toNat+y.toNat)
def relationMask (r : Relation) : Nat :=
  r false false |>.toNat |>.add (2*(r false true).toNat + 4*(r true false).toNat + 8*(r true true).toNat)

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
      let height ← node.getObjValAs? Nat "height"
      if height > 16 then throw "Chain height exceeds capacity"
      let mask ← node.getObjValAs? Nat "mask"
      if mask ≥ 16 then throw "Invalid chain relation"
      let checked ← if height == 0 then
          pure (CheckedTree.mk 0 (.leaf (maskRelation mask)) True.intro)
        else do
          let left ← node.getObjValAs? String "left"
          let right ← node.getObjValAs? String "right"
          let some (_, a) := out[left]? | throw "Missing left chain child"
          let some (_, b) := out[right]? | throw "Missing right chain child"
          if h : a.height = b.height then
            let bt : Tree a.height := h.symm ▸ b.tree
            have hb : bt.Valid := cast_valid h.symm b.tree b.valid
            let joined := join a.tree bt
            if height != a.height+1 || relationMask joined.summary != mask then
              throw "Incorrect chain summary or height"
            pure (CheckedTree.mk (a.height+1) joined (join_valid _ _ a.valid hb))
          else throw "Unbalanced chain node"
      out := out.insert id (node, checked)
  return (out, Json.mkObj [("valid", toJson true)])

/-- Prepend each edge's left endpoint, avoiding repeated list concatenation. -/
def witnessPrefix : {h : Nat} → Tree h → Bool → Bool → List Bool → List Bool
  | 0, .leaf _, x, _, tail => x :: tail
  | _+1, .branch _ l r, x, z, tail =>
    let y := !(l.summary x false && r.summary false z)
    witnessPrefix l x y (witnessPrefix r y z tail)

/-- Produce endpoints through each segment. Output work is linear in capacity. -/
def witness {h : Nat} (tree : Tree h) (x y : Bool) : List Bool :=
  witnessPrefix tree x y [y]

def query (store : Store) (request : Json) : Except String Json := do
  let root ← request.getObjValAs? String "root"
  let some (_, checked) := store[root]? | throw "Unknown chain root"
  let size ← request.getObjValAs? Nat "size"
  if size > 2^checked.height then throw "Chain size exceeds capacity"
  let left ← request.getObjValAs? Nat "left"
  let right ← request.getObjValAs? Nat "right"
  if left ≥ 4 || right ≥ 4 then throw "Invalid endpoint mask"
  let want ← request.getObjValAs? Bool "witness"
  let pair := [(false,false),(false,true),(true,false),(true,true)].find? (fun (x,y) =>
    left.testBit x.toNat && right.testBit y.toNat && checked.tree.summary x y)
  return Json.mkObj [("answer", toJson pair.isSome),
    ("witness", if want then
        toJson (pair.map (fun (x,y) => (witness checked.tree x y).take (size+1)))
      else Json.null),
    ("height", toJson checked.height)]
end OracleMachines.Chain

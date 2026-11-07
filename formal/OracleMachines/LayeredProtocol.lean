import OracleMachines.Layered
import Lean.Data.Json

namespace OracleMachines.Layered
open Lean

structure CheckedTree where
  width : Nat
  height : Nat
  tree : Tree (2^width) height
  valid : tree.Valid

structure Store where
  nodes : Std.HashMap String (Json × CheckedTree) := {}
  incoming : Std.HashMap String Nat := {}

def children (body : Json) : Except String (List String) := do
  if (← body.getObjValAs? Nat "height") == 0 then return []
  return [← body.getObjValAs? String "left", ← body.getObjValAs? String "right"]

def Store.insert (store : Store) (id : String) (node : Json × CheckedTree) : Except String Store := do
  let mut incoming := store.incoming
  for child in ← children node.1 do
    incoming := incoming.insert child (incoming[child]?.getD 0 + 1)
  return { nodes := store.nodes.insert id node, incoming := incoming }

/-- Delete only unreferenced identities, in parent-before-child order. A surviving
checked node therefore never loses a named dependency. No full-store scan. -/
def dropNodes (store : Store) (request : Json) : Except String (Store × Json) := do
  let ids ← request.getObjValAs? (Array String) "ids"
  if ids.size > 4096 then throw "Eviction batch exceeds capacity"
  let mut out := store
  for id in ids do
    let some node := out.nodes[id]? | throw "Unknown evicted node"
    if out.incoming[id]?.getD 0 != 0 then throw "Cannot evict a referenced node"
    for child in ← children node.1 do
      let count := out.incoming[child]?.getD 0
      if count == 0 then throw "Invalid native reference count"
      out := { out with incoming := out.incoming.insert child (count-1) }
    out := { out with nodes := out.nodes.erase id, incoming := out.incoming.erase id }
  return (out, Json.mkObj [("valid",toJson true),("evicted",toJson ids.size)])

/-- Retention changes availability, never the checked meaning of an identity.
The caller supplies a dependency-closed live set; trees retain their children. -/
def retain (store : Store) (request : Json) : Except String (Store × Json) := do
  let ids ← request.getObjValAs? (Array String) "ids"
  if ids.size > 200000 then throw "Retention set exceeds capacity"
  let mut out : Store := {}
  for id in ids do
    let some node := store.nodes[id]? | throw "Unknown retained node"
    out ← out.insert id node
  for id in ids do
    let some (body, tree) := out.nodes[id]? | throw "Missing retained node"
    if tree.height > 0 then
      let left ← body.getObjValAs? String "left"
      let right ← body.getObjValAs? String "right"
      if !out.nodes.contains left || !out.nodes.contains right then throw "Retention set is not dependency closed"
  return (out, Json.mkObj [("valid", toJson true), ("retained", toJson out.nodes.size)])

theorem cast_valid {q h k : Nat} (eq : h = k) (t : Tree q h) (valid : t.Valid) :
    (eq ▸ t).Valid := by subst k; exact valid

theorem cast_width_valid {w v h : Nat} (eq : w = v) (t : Tree (2^w) h) (valid : t.Valid) :
    (eq ▸ t).Valid := by subst v; exact valid

def maskRelation (width mask : Nat) : Relation (2^width) := fun x y =>
  mask.testBit (2^width*x.val+y.val)
def relationMask {q : Nat} (r : Relation q) : Nat :=
  ((List.finRange q).flatMap fun x => (List.finRange q).map fun y =>
    if r x y then 2^(q*x.val+y.val) else 0).sum

def relationEqual {q : Nat} (a b : Relation q) : Bool :=
  (List.finRange q).all fun x => (List.finRange q).all fun y => a x y == b x y

theorem relationEqual_exact {q : Nat} (a b : Relation q) :
    relationEqual a b = true ↔ a = b := by
  simp [relationEqual, List.all_eq_true, funext_iff]

def defineNodes (store : Store) (request : Json) : Except String (Store × Json) := do
  let nodes ← request.getObjValAs? (Array Json) "nodes"
  if nodes.size > 128 then throw "Chain batch exceeds capacity"
  let mut out := store
  for node in nodes do
    let id ← node.getObjValAs? String "id"
    if let some old := out.nodes[id]? then
      if old.1 != node then throw "Chain identity collision"
    else
      if out.nodes.size ≥ 200000 then throw "Native chain store capacity exceeded"
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
          let some (_, a) := out.nodes[left]? | throw "Missing left chain child"
          let some (_, b) := out.nodes[right]? | throw "Missing right chain child"
          if w : a.width = b.width then
            if h : a.height = b.height then
              let bt : Tree (2^a.width) a.height := h.symm ▸ w.symm ▸ b.tree
              have hb : bt.Valid := cast_valid h.symm _ (cast_width_valid w.symm b.tree b.valid)
              let joined := join a.tree bt
              if width != a.width || height != a.height+1 ||
                  !relationEqual (maskRelation a.width mask) joined.summary then
                throw "Incorrect layered summary, width or height"
              pure (CheckedTree.mk a.width (a.height+1) joined (join_valid _ _ a.valid hb))
            else throw "Unbalanced layered node"
          else throw "Layer width mismatch"

      out ← out.insert id (node, checked)
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

/-- A trace records each edge's left endpoint; the final endpoint is separate. -/
def Tree.Trace {q : Nat} : {h : Nat} → Tree q h → Fin q → Fin q → List Nat → Prop
  | _, .leaf r, x, y, xs => xs = [x.val] ∧ r x y = true
  | _, .branch _ l r, x, z, xs => ∃ y a b, l.Trace x y a ∧ r.Trace y z b ∧ xs = a ++ b

theorem witnessPrefix_sound {q h : Nat} (t : Tree q h) (valid : t.Valid)
    (x y : Fin q) (accepted : t.summary x y = true) (tail : List Nat) :
    ∃ xs, t.Trace x y xs ∧ witnessPrefix t x y tail = xs ++ tail := by
  induction t generalizing x y tail with
  | leaf r => exact ⟨[x.val],⟨rfl,accepted⟩,rfl⟩
  | branch r l t il ir =>
    rcases valid with ⟨hl,hr,eq⟩
    have existsMid : ∃ z, l.summary x z = true ∧ t.summary z y = true := by
      apply (compose_exact _ _ _ _).mp
      simpa only [Tree.summary,eq] using accepted
    cases found : (List.finRange q).find? (fun z => l.summary x z && t.summary z y) with
    | none =>
      obtain ⟨z,hz1,hz2⟩ := existsMid
      have no := List.find?_eq_none.mp found z (by simp)
      simp [hz1,hz2] at no
    | some z =>
      have hz := List.find?_some found
      simp only [Bool.and_eq_true] at hz
      obtain ⟨b,hb,eb⟩ := ir hr z y hz.2 tail
      obtain ⟨a,ha,ea⟩ := il hl x z hz.1 (witnessPrefix t z y tail)
      refine ⟨a++b,⟨z,a,b,ha,hb,rfl⟩,?_⟩
      simp only [witnessPrefix,found]
      rw [ea,eb,List.append_assoc]

theorem trace_length {q h : Nat} (t : Tree q h) (x y : Fin q) (xs : List Nat)
    (valid : t.Trace x y xs) : xs.length = 2^h := by
  induction t generalizing x y xs with
  | leaf r => rcases valid with ⟨rfl,_⟩; rfl
  | @branch h r l t il ir =>
    obtain ⟨z,a,b,ha,hb,rfl⟩ := valid
    simp only [List.length_append,il _ _ _ ha,ir _ _ _ hb,pow_succ]
    omega

theorem witness_length {q h : Nat} (t : Tree q h) (valid : t.Valid)
    (x y : Fin q) (accepted : t.summary x y = true) : (witness t x y).length = 2^h+1 := by
  obtain ⟨xs,trace,eq⟩ := witnessPrefix_sound t valid x y accepted [y.val]
  simp only [witness,eq,List.length_append,List.length_singleton,trace_length t x y xs trace]

/-- Split a checked relation into the logical prefix and padding suffix. Data
is materialized before the pair is returned, so repeated lookup does not replay
the recursive composition. -/
def splitSummary {q : Nat} : {h : Nat} → Tree q h → Nat → Relation q × Relation q
  | 0, .leaf r, n => if n = 0 then (identity,r) else (r,identity)
  | h+1, .branch _ l r, n =>
    if n ≤ 2^h then
      let parts := splitSummary l n
      let rows := materialize (compose parts.2 r.summary)
      (parts.1,fun x y => rows[x][y])
    else
      let parts := splitSummary r (n-2^h)
      let rows := materialize (compose l.summary parts.1)
      (fun x y => rows[x][y],parts.2)

theorem splitSummary_exact {q h : Nat} (t : Tree q h) (valid : t.Valid) (n : Nat) :
    compose (splitSummary t n).1 (splitSummary t n).2 = t.summary := by
  induction t generalizing n with
  | leaf r => simp only [splitSummary]; split <;> simp [Tree.summary,identity_compose,compose_identity]
  | branch value l r il ir =>
    rcases valid with ⟨hl,hr,eq⟩
    simp only [splitSummary]; split
    · change compose (splitSummary l n).1 (freeze (compose (splitSummary l n).2 r.summary)) = value
      rw [freeze_eq,← compose_assoc,il hl,← eq]
    · change compose (freeze (compose l.summary (splitSummary r _).1)) (splitSummary r _).2 = value
      rw [freeze_eq,compose_assoc,ir hr,← eq]

theorem identity_suffix_preserves_prefix {q h : Nat} (t : Tree q h) (valid : t.Valid) (n : Nat)
    (padding : (splitSummary t n).2 = identity) : (splitSummary t n).1 = t.summary := by
  have eq := splitSummary_exact t valid n
  simpa only [padding,compose_identity] using eq

def query (store : Store) (request : Json) : Except String Json := do
  let root ← request.getObjValAs? String "root"
  let some (_, checked) := store.nodes[root]? | throw "Unknown chain root"
  let size ← request.getObjValAs? Nat "size"
  if size > 2^checked.height then throw "Chain size exceeds capacity"
  if size < 2^checked.height && !relationEqual (splitSummary checked.tree size).2 identity then
    throw "Logical length requires identity suffix"
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

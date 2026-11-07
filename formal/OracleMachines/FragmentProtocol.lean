import OracleMachines.ProofFragments
import Lean.Data.Json

namespace OracleMachines.Fragments
open Lean Std.Sat

structure Session where
  base : Std.HashSet Clause := {}
  facts : Array (Option Clause) := #[]
  current : Option (String × OracleMachines.SAT.Formula × Clause) := none

def canonical (c : Clause) : Clause := c.mergeSort (fun a b =>
  if a.1 == b.1 then a.2.toNat ≤ b.2.toNat else a.1 ≤ b.1)

def prepare (old : Session) (bits : String) (f : OracleMachines.SAT.Formula) (cnf : CNF Nat) : Session :=
  let base := cnf.tail.foldl (fun set c => set.insert (canonical c)) ({} : Std.HashSet Clause)
  let retained := old.base.toList.all base.contains
  { base := base, facts := if retained then old.facts else #[],
    current := some (bits, f, cnf.head!) }

def parseClause (j : Json) : Except String Clause := do
  let integers ← fromJson? j (α := List Int)
  if integers.length > 65536 then throw "Proof clause exceeds capacity"
  integers.mapM fun i => do
    if i == 0 then throw "Zero is not a proof literal"
    return (i.natAbs-1, i > 0)

def extend (state : Session) (request : Json) : Except String (Session × Json) := do
  let start ← request.getObjValAs? Nat "start"
  if start != state.facts.size then throw "Proof fragment prefix mismatch"
  let steps ← request.getObjValAs? (Array Json) "steps"
  if steps.size > 128 || state.facts.size + steps.size > 100000 then throw "Proof fragment capacity exceeded"
  let mut facts := state.facts
  let mut accepted := 0
  for step in steps do
    let clause ← step.getObjVal? "clause" >>= parseClause
    let parents ← step.getObjValAs? (Array Json) "parents"
    if parents.size > 65536 then throw "Proof hints exceed capacity"
    let mut hints := []
    let mut ready := true
    for parent in parents do
      let ref ← parent.getArr?
      if ref.size != 2 then throw "Malformed proof dependency"
      let kind ← ref[0]!.getStr?
      if kind == "b" then
        let c ← parseClause ref[1]!
        if state.base.contains (canonical c) then hints := c :: hints
        else ready := false
      else if kind == "s" then
        let index ← ref[1]!.getNat?
        match (facts[index]?).join with
        | some c => hints := c :: hints
        | none => ready := false
      else throw "Unknown proof dependency"
    let valid := ready && check clause hints.reverse
    facts := facts.push (if valid then some clause else none)
    if valid then accepted := accepted + 1
  return ({state with facts := facts}, Json.mkObj [("accepted", toJson accepted),
    ("checked", toJson steps.size), ("size", toJson facts.size)])

def verify (state : Session) (request : Json) : Except String (OracleMachines.SAT.Formula × Json) := do
  let bits ← request.getObjValAs? String "bits"
  let some (prepared, f, root) := state.current | throw "No prepared proof context"
  if bits != prepared then throw "Proof query differs from current assumptions"
  let index ← request.getObjValAs? Nat "target"
  let valid := match (state.facts[index]?).join with
    | none => false
    | some c => check [] [root,c]
  return (f, Json.mkObj [("valid", toJson valid), ("parse_work", toJson (0 : Nat)),
    ("history_recompiled", toJson (0 : Nat)), ("checked_fragment_reuse", toJson valid)])
end OracleMachines.Fragments

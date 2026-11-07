import OracleMachines.Interfaces
import Lean.Data.Json

open Lean
namespace OracleMachines.SAT

/-! Native protocol for immutable checked factor DAGs. JSON/state management is
outside the kernel model; leaf exactness and each projection are proved in Lean.
Cached objects are scoped to this worker; replay rechecks them after restart. -/
structure CheckedFactor where
  factor : InterfaceFactor
  source : Option Formula
  parents : List String
  signature : String

abbrev FactorStore := Std.HashMap String CheckedFactor

def factorRows (f : InterfaceFactor) : Word :=
  (words f.scope.length).map (fun a => decide (a ∈ f.allowed))

def formulaIsConjunct (f g : Formula) : Bool :=
  if f == g then true else match f with
  | .conj l r => formulaIsConjunct l g || formulaIsConjunct r g
  | _ => false

theorem formulaIsConjunct_entails (f g : Formula) (v : Nat → Bool)
    (h : formulaIsConjunct f g = true) (sat : f.eval v = true) : g.eval v = true := by
  induction f with
  | falsum => simp [formulaIsConjunct] at h; subst g; exact sat
  | var i => simp [formulaIsConjunct] at h; subst g; exact sat
  | neg f => simp [formulaIsConjunct] at h; subst g; exact sat
  | conj l r ihl ihr =>
    by_cases he : Formula.conj l r = g
    · subst g; exact sat
    · simp [formulaIsConjunct, he] at h
      simp only [Formula.eval, Bool.and_eq_true] at sat
      rcases h with h | h
      · exact ihl h sat.1
      · exact ihr h sat.2

def loadFactors (db : FactorStore) (names : List String) : Except String (List InterfaceFactor) :=
  names.mapM fun name => do
    let some f := db[name]? | throw "Unknown factor dependency"
    return f.factor

def factorDefine (parse : String → Except String Formula) (bitsOut : Word → String)
    (db : FactorStore) (request : Json) : Except String (FactorStore × Json) := do
  let name ← request.getObjValAs? String "id"
  let body ← request.getObjVal? "definition"
  let signature := body.compress
  if let some old := db[name]? then
    if old.signature != signature then throw "Factor identity reused with a different definition"
    return (db, Json.mkObj [("cached", toJson true), ("scope", toJson old.factor.scope),
      ("rows", toJson (bitsOut (factorRows old.factor)))])
  if db.size ≥ 16384 then throw "Checked factor worker capacity exceeded"
  let kind ← body.getObjValAs? String "kind"
  let (factor, source, parents) ← if kind == "leaf" then do
      let f ← body.getObjValAs? String "bits" >>= parse
      let scope ← body.getObjValAs? (List Nat) "scope"
      if scope.length > 12 || scope.eraseDups != scope then throw "Invalid factor scope"
      if !(occurs f).all (scope.contains ·) then throw "Factor scope omits a variable"
      pure (formulaFactor f scope, some f, [])
    else if kind == "project" then do
      let parents ← body.getObjValAs? (List String) "parents"
      if parents.isEmpty || parents.length > 4096 then throw "Invalid factor parents"
      let x ← body.getObjValAs? Nat "variable"
      let inputs ← loadFactors db parents
      let scope := projectScope inputs x
      if scope.length > 11 then throw "Factor interface exceeds width limit"
      pure (projectFactor inputs x, none, parents)
    else throw "Unknown factor definition"
  let node : CheckedFactor := ⟨factor, source, parents, signature⟩
  return (db.insert name node, Json.mkObj [("cached", toJson false),
    ("scope", toJson factor.scope), ("rows", toJson (bitsOut (factorRows factor)))])

/-- Reachable source leaves. Backward-only construction prevents cycles; visited
nodes are shared and visited once even when the proof graph reconverges. -/
def factorLeaves (db : FactorStore) (root : String) : Except String (List String) := do
  let mut pending := [root]
  let mut visited : Std.HashSet String := {}
  let mut scheduled : Std.HashSet String := ({} : Std.HashSet String).insert root
  let mut leaves := []
  for _ in [:db.size + 1] do
    match pending with
    | [] => return leaves
    | name :: rest =>
      pending := rest
      if !visited.contains name then
        visited := visited.insert name
        let some node := db[name]? | throw "Missing factor evidence"
        if node.source.isSome then leaves := name :: leaves
        else
          for parent in node.parents do
            if !scheduled.contains parent then
              scheduled := scheduled.insert parent
              pending := parent :: pending
  -- Each identity is scheduled at most once.
  if pending.isEmpty then return leaves else throw "Factor traversal budget exhausted"

def factorNegative (db : FactorStore) (root : String) (active : List String) : Except String Bool := do
  let some node := db[root]? | throw "Unknown factor root"
  if !node.factor.allowed.isEmpty then return false
  let leaves ← factorLeaves db root
  return leaves.all (active.contains ·)

def factorPositive (db : FactorStore) (active : List String) (witness : Word) : Except String Bool := do
  for name in active do
    let some node := db[name]? | throw "Unknown active leaf"
    let some f := node.source | throw "An active constraint must be a leaf"
    if !(evalRun f witness).1 then return false
  return true

def factorQuery (db : FactorStore) (parseBits : String → Except String Word)
    (request : Json) : Except String Json := do
  let active ← request.getObjValAs? (List String) "active"
  if active.length > 16384 then throw "Too many active factors"
  -- Validate every active identity even if the negative core uses a subset.
  for name in active do
    let some node := db[name]? | throw "Unknown active factor"
    if node.source.isNone then throw "Active factor is not an original constraint"
  let answer ← request.getObjValAs? Bool "answer"
  let valid ← if answer then do
      let witness ← request.getObjValAs? String "witness" >>= parseBits
      factorPositive db active witness
    else do
      let root ← request.getObjValAs? String "root"
      factorNegative db root active
  return Json.mkObj [("valid", toJson valid), ("checked_factors", toJson db.size)]


def formulaConjuncts : Formula → List Formula
  | .conj f g => formulaConjuncts f ++ formulaConjuncts g
  | f => [f]

theorem formulaConjuncts_exact (f : Formula) (v : Nat → Bool) :
    ((formulaConjuncts f).all (fun g => g.eval v)) = f.eval v := by
  induction f <;> simp_all [formulaConjuncts, Formula.eval]

abbrev FactorBindings := Std.HashMap String (String × List String)

def factorBind (parse : String → Except String Formula) (db : FactorStore)
    (bindings : FactorBindings) (request : Json) : Except String (FactorBindings × Json) := do
  let name ← request.getObjValAs? String "id"
  let encoded ← request.getObjValAs? String "bits"
  let active ← request.getObjValAs? (List String) "active"
  let signature := (toJson (encoded, active)).compress
  if let some old := bindings[name]? then
    if old.1 != signature then throw "Constraint identity was changed"
    return (bindings, Json.mkObj [("valid", toJson true)])
  let f ← parse encoded
  let mut leaves : List Formula := []
  for name in active do
    let some node := db[name]? | throw "Missing decomposition leaf"
    let some leaf := node.source | throw "Expected original decomposition leaf"
    leaves := leaf :: leaves
  let terms := formulaConjuncts f
  let valid := terms.all (fun t => leaves.contains t) && leaves.all (fun t => terms.contains t)
  if !valid then return (bindings, Json.mkObj [("valid", toJson false)])
  return (bindings.insert name (signature, active), Json.mkObj [("valid", toJson true)])

def factorQueryBound (db : FactorStore) (bindings : FactorBindings)
    (parseBits : String → Except String Word) (request : Json) : Except String Json := do
  let constraints ← request.getObjValAs? (List String) "constraints"
  let mut active := []
  for name in constraints do
    let some binding := bindings[name]? | throw "Unknown original constraint binding"
    active := binding.2 ++ active
  let answer ← request.getObjValAs? Bool "answer"
  let valid ← if answer then do
      let witness ← request.getObjValAs? String "witness" >>= parseBits
      factorPositive db active witness
    else do
      let root ← request.getObjValAs? String "root"
      factorNegative db root active
  return Json.mkObj [("valid", toJson valid), ("checked_factors", toJson db.size)]

end OracleMachines.SAT

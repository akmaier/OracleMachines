import OracleMachines.Cache
import OracleMachines.Parsing
import OracleMachines.Knowledge
import Lean.Data.Json

open OracleMachines OracleMachines.SAT Lean

def parseBits (s : String) : Except String Word :=
  s.toList.mapM fun c =>
    if c == '0' then .ok false
    else if c == '1' then .ok true
    else .error "Bits must contain only 0 and 1"

def showBits (bits : Word) : String := String.mk (bits.map (fun b => if b then '1' else '0'))

def showProof : Refutation → Json
  | .conflict => toJson "conflict"
  | .split i l h => Json.arr #[toJson i, showProof l, showProof h]

/-- JSON handling is outside the abstract operation ledger. -/
def parseProof : Nat → Json → Except String Refutation
  | 0, _ => .error "Refutation exceeds the supported nesting depth"
  | fuel + 1, j => do
    if j == toJson "conflict" then return .conflict
    let a ← j.getArr?
    if a.size != 3 then throw "A refutation split needs an index and two children"
    let i ← a[0]!.getNat?
    let l ← parseProof fuel a[1]!
    let h ← parseProof fuel a[2]!
    return .split i l h

def respond (request : Json) : Except String Json := do
  let encoded ← request.getObjValAs? String "bits"
  let bits ← parseBits encoded
  let parsed := decodeRun bits
  let f ← match parsed.1 with
    | none => .error "Invalid formula encoding"
    | some f => .ok f
  let mode := (request.getObjValAs? String "mode").toOption.getD "hybrid"
  if mode == "exhaustive" then
    let result := solveRun f
    return Json.mkObj [("answer", toJson result.1.isSome),
      ("witness", toJson (result.1.map showBits)), ("certificate", Json.null),
      ("fast", toJson false), ("reuse_kind", toJson "none"), ("nodes", toJson (0 : Nat)),
      ("core_work", toJson (result.2 + 2)), ("parse_work", toJson parsed.2),
      ("counted_work", toJson (parsed.2 + result.2 + 2))]
  if mode != "hybrid" && mode != "baseline" then throw "Unknown solver mode"
  let candidates ← match request.getObjVal? "candidates" with
    | .ok j => do
      let a ← j.getArr?
      if a.size > 4 then throw "At most four witness candidates are supported"
      a.toList.mapM fun x => x.getStr? >>= parseBits
    | .error _ =>
      match (request.getObjValAs? (Option String) "candidate").toOption.getD none with
      | none => pure []
      | some s => (fun b => [b]) <$> parseBits s
  let proofs ← match request.getObjVal? "proofs" with
    | .ok j => do
      let a ← j.getArr?
      if a.size > 4 then throw "At most four refutation candidates are supported"
      a.toList.mapM (fun j => parseProof (j.compress.length + 1) j)
    | .error _ => pure []
  let result := if mode == "baseline" then solveSearch f else reuseSearch f candidates proofs
  let core := result.work + 1
  return Json.mkObj [
    ("answer", toJson result.witness.isSome), ("witness", toJson (result.witness.map showBits)),
    ("certificate", (result.certificate.map showProof).getD Json.null),
    ("fast", toJson (result.source != 0)),
    ("reuse_kind", toJson (if result.source == 1 then "witness" else if result.source == 2 then "refutation" else "none")),
    ("nodes", toJson result.nodes), ("core_work", toJson core), ("parse_work", toJson parsed.2),
    ("counted_work", toJson (parsed.2 + core))]

def main : IO Unit := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  repeat
    let line ← stdin.getLine
    if line.isEmpty then break
    let result := (Json.parse line).bind respond
    let response := match result with
      | .ok value => value
      | .error message => Json.mkObj [("error", toJson message)]
    stdout.putStrLn response.compress
    stdout.flush

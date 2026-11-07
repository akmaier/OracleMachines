import OracleMachines.Cache
import Lean.Data.Json

open OracleMachines OracleMachines.SAT Lean

def parseBits (s : String) : Except String Word :=
  s.toList.mapM fun c =>
    if c == '0' then .ok false
    else if c == '1' then .ok true
    else .error "Bits must contain only 0 and 1"

def showBits (bits : Word) : String := String.mk (bits.map (fun b => if b then '1' else '0'))

def respond (request : Json) : Except String Json := do
  let encoded ← request.getObjValAs? String "bits"
  let bits ← parseBits encoded
  let candidate ← match (request.getObjValAs? (Option String) "candidate").toOption.getD none with
    | none => pure none
    | some s => some <$> parseBits s
  let f ← match decode bits with
    | none => .error "Invalid formula encoding"
    | some f => .ok f
  let mode := (request.getObjValAs? String "mode").toOption.getD "hybrid"
  if mode == "baseline" then
    let result := solveRun f
    return Json.mkObj [("answer", toJson result.1.isSome),
      ("witness", toJson (result.1.map showBits)), ("fast", toJson false),
      ("core_work", toJson (result.2 + 2))]
  if mode != "hybrid" then throw "Unknown solver mode"
  let result := hybridRun candidate f
  let witness := if result.answer then result.state.map showBits else none
  return Json.mkObj [
    ("answer", toJson result.answer), ("witness", toJson witness),
    ("fast", toJson result.fast), ("core_work", toJson (result.work + 1))]

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

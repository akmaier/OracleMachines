import OracleMachines.FragmentProtocol
import OracleMachines.ChainProtocol
import OracleMachines.LayeredSource
import OracleMachines.SourceUpdates
import OracleMachines.Cache
import OracleMachines.Parsing
import OracleMachines.BoundedSearch
import OracleMachines.CompactExpansion
import OracleMachines.IncrementalProof
import OracleMachines.InterfaceProtocol
import Std.Sat.CNF.Dimacs
import Std.Tactic.BVDecide.LRAT.Parser
import Lean.Data.Json

open OracleMachines OracleMachines.SAT Lean

def parseBits (s : String) : Except String Word := do
  -- Accumulation avoids one native call frame per input bit.
  let reversed ← s.toList.foldlM (fun acc c =>
    if c == '0' then .ok (false :: acc)
    else if c == '1' then .ok (true :: acc)
    else .error "Bits must contain only 0 and 1") []
  return reversed.reverse

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


def baseCertificateValid (f : Formula) (certificate : Json) : Except String Bool := do
  match (certificate.getObjValAs? String "format").toOption with
  | some "aig_false" => return circuitFalse f
  | some "lrat" =>
    let proofText ← certificate.getObjValAs? String "text"
    let proof ← Std.Tactic.BVDecide.LRAT.parseLRATProof proofText.toUTF8
    return checkLRAT f proof
  | some _ => throw "Unknown certificate format"
  | none =>
    let tree ← parseProof (certificate.compress.length + 1) certificate
    return (checkRefutation f [] tree).1

def parseFormulaBits (s : String) : Except String Formula := do
  let bits ← parseBits s
  match (decodeRun bits).1 with
  | some f => return f
  | none => throw "Invalid formula encoding"

def factorCertificateValid (f : Formula) (certificate : Json) : Except String Bool := do
  let definitions ← certificate.getObjValAs? (Array Json) "definitions"
  if definitions.size > 16384 then throw "Factor certificate too large"
  let mut state : FactorStore := {}
  for definition in definitions do
    let lazyDefinition := Json.mkObj [("id", ← definition.getObjVal? "id"),
      ("definition", ← definition.getObjVal? "definition"), ("lazy", toJson true)]
    let result ← factorDefine parseFormulaBits showBits state lazyDefinition
    state := result.1
  let root ← certificate.getObjValAs? String "root"
  let leaves ← factorLeaves state root
  for name in leaves do
    let some node := state[name]? | throw "Missing certificate leaf"
    let some leaf := node.source | throw "Expected original leaf"
    if !formulaIsConjunct f leaf then return false
  return (← factorNegativeLazy state {} root leaves).2

def incrementalCertificateValid (f : Formula) (certificate : Json) : Except String Bool := do
  let history ← certificate.getObjValAs? (Array String) "history"
  if history.size > 512 then throw "Incremental certificate history too large"
  let mut graph : Std.Sat.AIG Nat := Std.Sat.AIG.empty
  for bits in history do
    let previous ← parseFormulaBits bits
    graph := (compileCircuit previous graph).entry.aig
    if graph.decls.size > 200000 then throw "Incremental certificate graph too large"
  let text ← certificate.getObjValAs? String "text"
  let proof ← Std.Tactic.BVDecide.LRAT.parseLRATProof text.toUTF8
  return checkIncrementalLRAT f graph proof

def incrementalPrepare (graph : Std.Sat.AIG Nat) (request : Json) :
    Except String (Std.Sat.AIG Nat × Formula × Std.Sat.CNF Nat × Json) := do
  let f ← request.getObjValAs? String "bits" >>= parseFormulaBits
  let entry := (compileCircuit f graph).entry
  if entry.aig.decls.size > 200000 then throw "Incremental graph capacity exceeded"
  let cnf := incrementalCNF entry
  return (entry.aig, f, cnf, Json.mkObj [("dimacs", toJson cnf.dimacs),
    ("width", toJson f.width), ("nodes", toJson entry.aig.decls.size)])

def certificateValid (f : Formula) (certificate : Json) : Except String Bool := do
  if (certificate.getObjValAs? String "format").toOption == some "conjunct" then
    let base ← certificate.getObjValAs? String "bits" >>= parseFormulaBits
    if !formulaIsConjunct f base then return false
    let proof ← certificate.getObjVal? "proof"
    -- One wrapper only. The stored proof remains independently replayable.
    if (proof.getObjValAs? String "format").toOption == some "incremental_lrat" then
      return ← incrementalCertificateValid base proof
    else return ← baseCertificateValid base proof
  if (certificate.getObjValAs? String "format").toOption == some "incremental_lrat" then
    return ← incrementalCertificateValid f certificate
  if (certificate.getObjValAs? String "format").toOption == some "factor_dag" then
    return ← factorCertificateValid f certificate
  if (certificate.getObjValAs? String "format").toOption != some "component" then
    return ← baseCertificateValid f certificate
  let encoded ← certificate.getObjValAs? String "bits"
  let bits ← parseBits encoded
  let base ← match (decodeRun bits).1 with
    | some base => pure base
    | none => throw "Invalid component formula"
  let paths ← certificate.getObjValAs? (Array String) "paths"
  if paths.size > 4096 then throw "Too many component conjunct paths"
  let parsedPaths ← paths.toList.mapM parseBits
  let ids ← certificate.getObjValAs? (Array Nat) "variables"
  if ids.size < base.width then throw "Incomplete component variable map"
  if !componentEmbedding f base parsedPaths ids.toList then return false
  let proof ← certificate.getObjVal? "proof"
  -- Only a base certificate is allowed: wrappers cannot recursively expand.
  return ← baseCertificateValid base proof

/-- A live graph is already reconstructed by incremental_prepare. Soundness of
checkIncrementalLRAT holds for every previous graph; no history string is trusted.
Only accepted refutations enter the native session's reusable negative store. -/
def verifyLiveIncremental (graph : Std.Sat.AIG Nat) (request : Json) : Except String (Formula × Json) := do
  let bits ← request.getObjValAs? String "bits" >>= parseBits
  let parsed := decodeRun bits
  let some f := parsed.1 | throw "Invalid formula encoding"
  let text ← request.getObjValAs? String "text"
  let proof ← Std.Tactic.BVDecide.LRAT.parseLRATProof text.toUTF8
  return (f, Json.mkObj [("valid", toJson (checkIncrementalLRAT f graph proof)),
    ("parse_work", toJson parsed.2), ("history_recompiled", toJson (0 : Nat))])

/-- Modern preprocessing and LRAT checking have no complete abstract cost ledger. -/
def fastRespond (f : Formula) (parseWork : Nat) (request : Json) : Except String Json := do
  let mode ← request.getObjValAs? String "mode"
  if mode == "verify_certificate" then
    let certificate ← request.getObjVal? "certificate"
    return Json.mkObj [("valid", toJson (← certificateValid f certificate)), ("parse_work", toJson parseWork)]
  if mode == "verify_witness" then
    let witness ← request.getObjValAs? String "witness" >>= parseBits
    return Json.mkObj [("valid", toJson (evalRun f witness).1), ("parse_work", toJson parseWork)]
  let fields := [("core_work", Json.null), ("parse_work", toJson parseWork),
    ("counted_work", Json.null), ("counted_complete", toJson false),
    ("nodes", Json.null)]
  let finish := fun (w : Option Word) (certificate : Json) (kind : String) => Json.mkObj
    (fields ++ [("answer", toJson w.isSome), ("witness", toJson (w.map showBits)),
      ("certificate", certificate), ("reuse_kind", toJson kind), ("fast", toJson (kind != "none"))])
  let candidates := (request.getObjValAs? (Array String) "candidates").toOption.getD #[]
  if candidates.size > 4 then throw "At most four witness candidates are supported"
  for candidate in candidates do
    let word ← parseBits candidate
    if (evalRun f word).1 then return finish (some word) Json.null "witness"
  let certificates := (request.getObjValAs? (Array Json) "proofs").toOption.getD #[]
  if certificates.size > 4 then throw "At most four refutation candidates are supported"
  for certificate in certificates do
    if ← certificateValid f certificate then return finish none certificate "refutation"
  if mode == "propose" then
    return Json.mkObj (fields ++ [("pending", toJson true)])
  let circuit := compiledCircuit f
  if circuit.aig.getConstant circuit.ref == some false then
    return finish none (Json.mkObj [("format", toJson "aig_false")]) "none"
  -- Cheap phase proposals avoid a subprocess for common all-positive/negative cases.
  for value in [false, true] do
    let word := List.replicate f.width value
    if (evalRun f word).1 then return finish (some word) Json.null "none"
  let budget := (request.getObjValAs? Nat "search_budget").toOption.getD 0
  if budget > 512 then throw "The preliminary search budget must be at most 512 nodes"
  if budget > 0 then
    let support :=  (distinctRun (occursRun f).1).1
    let attempt := boundedSearch f support [] budget
    if let some proposal := attempt.1 then
      if let some sparse := proposal.assignment then
        let word := (materialize sparse f.width).1
        if (evalRun f word).1 then return finish (some word) Json.null "none"
      else if (checkRefutation f [] proposal.proof).1 then
        return finish none (showProof proposal.proof) "none"
  let cnf := Std.Sat.AIG.toCNF circuit
  return Json.mkObj (fields ++ [("pending", toJson true), ("dimacs", toJson cnf.dimacs),
    ("width", toJson f.width), ("offset", toJson circuit.aig.decls.size),
    ("clauses", toJson cnf.length)])

def respond (request : Json) : Except String Json := do
  let encoded ← request.getObjValAs? String "bits"
  let bits ← parseBits encoded
  let parsed := decodeRun bits
  let f ← match parsed.1 with
    | none => .error "Invalid formula encoding"
    | some f => .ok f
  let mode := (request.getObjValAs? String "mode").toOption.getD "hybrid"
  if mode == "restricted" then
    let stage := (request.getObjValAs? Nat "stage").toOption.getD bits.length
    if stage > 1000000 then throw "Coverage state exceeds the service cell limit"
    let answer := compactAnswer (coverageState stage) bits
    return Json.mkObj [("answer", toJson answer), ("covered", toJson answer.isSome),
      ("coverage_cells", toJson stage), ("reference_query_bound", toJson (24 * (bits.length + 1) ^ 2)),
      ("counted_complete", toJson false)]
  if mode == "prepare" || mode == "propose" || mode == "verify_certificate" || mode == "verify_witness" then
    return ← fastRespond f parsed.2 request
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
  let mut factors : FactorStore := {}
  let mut factorClasses : FactorClasses := {}
  let mut bindings : FactorBindings := {}
  let mut rows : FactorRowStore := {}
  let mut graph : Std.Sat.AIG Nat := Std.Sat.AIG.empty
  let mut fragments : OracleMachines.Fragments.Session := {}
  let mut chains : OracleMachines.Chain.Store := {}
  let mut layers : OracleMachines.Layered.Store := {}
  let mut sourceLayers : OracleMachines.SourceUpdates.Store := {}
  let mut negatives : Std.HashMap String Formula := {}
  repeat
    let line ← stdin.getLine
    if line.isEmpty then break
    let parsed := Json.parse line
    let result ← match parsed with
      | .error e => pure (.error e)
      | .ok request =>
        let mode := (request.getObjValAs? String "mode").toOption.getD ""
        if mode == "source_init" then
          match OracleMachines.SourceUpdates.initializeLayout sourceLayers request with
          | .error e => pure (.error e)
          | .ok (state, response) => sourceLayers := state; pure (.ok response)
        else if mode == "source_compile" then
          pure (OracleMachines.SourceUpdates.compileEdges sourceLayers request)
        else if mode == "source_define" then
          match OracleMachines.SourceUpdates.defineNodes sourceLayers request with
          | .error e => pure (.error e)
          | .ok (state, response) => sourceLayers := state; pure (.ok response)
        else if mode == "source_drop" then
          match OracleMachines.SourceUpdates.dropNodes sourceLayers request with
          | .error e => pure (.error e)
          | .ok (state, response) => sourceLayers := state; pure (.ok response)
        else if mode == "source_query" then
          pure (OracleMachines.SourceUpdates.query sourceLayers request)
        else if mode == "source_patch" then
          pure (OracleMachines.SourceUpdates.patchQuery sourceLayers request)
        else if mode == "source_bind" then
          pure (OracleMachines.SourceUpdates.bindSource sourceLayers request)
        else if mode == "layered_compile" then
          pure (OracleMachines.Layered.compileRequest request)
        else if mode == "layered_source_query" then
          pure (OracleMachines.Layered.sourceQuery layers request)
        else if mode == "layered_define" then
          match OracleMachines.Layered.defineNodes layers request with
          | .error e => pure (.error e)
          | .ok (state, response) => layers := state; pure (.ok response)
        else if mode == "layered_retain" then
          match OracleMachines.Layered.retain layers request with
          | .error e => pure (.error e)
          | .ok (state, response) => layers := state; pure (.ok response)
        else if mode == "layered_drop" then
          match OracleMachines.Layered.dropNodes layers request with
          | .error e => pure (.error e)
          | .ok (state, response) => layers := state; pure (.ok response)
        else if mode == "layered_query" then
          pure (OracleMachines.Layered.query layers request)
        else if mode == "layered_reset" then
          layers := {}; pure (.ok (Json.mkObj [("valid", toJson true)]))
        else if mode == "chain_define" then
          match OracleMachines.Chain.defineNodes chains request with
          | .error e => pure (.error e)
          | .ok (state, response) => chains := state; pure (.ok response)
        else if mode == "chain_query" then
          pure (OracleMachines.Chain.query chains request)
        else if mode == "chain_reset" then
          chains := {}; pure (.ok (Json.mkObj [("valid", toJson true)]))
        else if mode == "negative_reuse" then
          pure do
            let name ← request.getObjValAs? String "id"
            let bits ← request.getObjValAs? String "bits" >>= parseBits
            let parsed := decodeRun bits
            let some f := parsed.1 | throw "Invalid formula encoding"
            let valid := (negatives[name]?).any (formulaIsConjunct f)
            return Json.mkObj [("valid", toJson valid), ("known", toJson (negatives.contains name)),
              ("parse_work", toJson parsed.2)]
        else if mode == "negative_register" then
          let checked := do
            let name ← request.getObjValAs? String "id"
            let f ← request.getObjValAs? String "bits" >>= parseFormulaBits
            let certificate ← request.getObjVal? "certificate"
            if let some old := negatives[name]? then
              if old != f then throw "Negative identity reused with different formula"
              return (name, f, true)
            return (name, f, ← certificateValid f certificate)
          match checked with
          | .error e => pure (.error e)
          | .ok (name, f, valid) =>
            if valid then
              if negatives.size ≥ 64 then negatives := {}
              negatives := negatives.insert name f
            pure (.ok (Json.mkObj [("valid", toJson valid)]))
        else if mode == "fragment_extend" then
          match OracleMachines.Fragments.extend fragments request with
          | .error e => pure (.error e)
          | .ok (state, response) => fragments := state; pure (.ok response)
        else if mode == "fragment_verify" then
          match OracleMachines.Fragments.verify fragments request with
          | .error e => pure (.error e)
          | .ok (f, response) =>
            if (response.getObjValAs? Bool "valid").toOption == some true then
              if let some name := (request.getObjValAs? String "id").toOption then
                if negatives.size ≥ 64 then negatives := {}
                negatives := negatives.insert name f
            pure (.ok response)
        else if mode == "incremental_verify" then
          match verifyLiveIncremental graph request with
          | .error e => pure (.error e)
          | .ok (f, response) =>
            if (response.getObjValAs? Bool "valid").toOption == some true then
              if let some name := (request.getObjValAs? String "id").toOption then
                if negatives.size ≥ 64 then negatives := {}
                negatives := negatives.insert name f
            pure (.ok response)
        else if mode == "incremental_prepare" then
          match incrementalPrepare graph request with
          | .error e => pure (.error e)
          | .ok (state, f, cnf, response) =>
            graph := state
            fragments := OracleMachines.Fragments.prepare fragments
              ((request.getObjValAs? String "bits").toOption.getD "") f cnf
            pure (.ok response)
        else if mode == "incremental_reset" then
          graph := Std.Sat.AIG.empty; fragments := {}; pure (.ok (Json.mkObj [("valid", toJson true)]))
        else if mode == "factor_define_many" then
          let checked := do
            let definitions ← request.getObjValAs? (Array Json) "definitions"
            if definitions.size > 128 then throw "Too many definitions in one batch"
            let mut state := factors
            let mut responses : Array Json := #[]
            for definition in definitions do
              let (next, response) ← factorDefine parseFormulaBits showBits state definition
              state := next
              responses := responses.push response
            return (state, Json.mkObj [("results", toJson responses)])
          match checked with
          | .error e => pure (.error e)
          | .ok (state, response) => factors := state; pure (.ok response)
        else if mode == "factor_define" then
          match factorDefine parseFormulaBits showBits factors request with
          | .error e => pure (.error e)
          | .ok (state, response) => factors := state; pure (.ok response)
        else if mode == "factor_bind" then
          match factorBind parseFormulaBits factors bindings request with
          | .error e => pure (.error e)
          | .ok (state, response) => bindings := state; pure (.ok response)
        else if mode == "factor_equate" || mode == "factor_rebind" then
          match factorEquate factors rows factorClasses request with
          | .error e => pure (.error e)
          | .ok (state, classes, response) => rows := state; factorClasses := classes; pure (.ok response)
        else if mode == "factor_row" then
          match factorRowRequest factors rows parseBits request with
          | .error e => pure (.error e)
          | .ok (state, response) => rows := state; pure (.ok response)
        else if mode == "factor_query_bound" || mode == "factor_query" then
          match factorQueryLazy factors bindings rows parseBits request with
          | .error e => pure (.error e)
          | .ok (state, response) => rows := state; pure (.ok response)
        else if mode == "factor_reset" then
          factors := {}; bindings := {}; rows := {}; factorClasses := {}; pure (.ok (Json.mkObj [("valid", toJson true)]))
        else pure (respond request)
    let response := match result with
      | .ok value => value
      | .error message => Json.mkObj [("error", toJson message)]
    stdout.putStrLn response.compress
    stdout.flush

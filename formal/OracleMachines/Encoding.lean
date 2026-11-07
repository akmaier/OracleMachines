import OracleMachines.SAT

/-!
# Binary SAT instances and concrete finite expansion

Postfix opcodes are 00 (false), 01 followed by a unary variable index, 10
(negation), and 11 (conjunction). An index i is i ones followed by zero. Unary
indices make their storage and traversal explicit. Decoding rejects incomplete
instructions, stack underflow, and final stacks other than a single formula.
-/

namespace OracleMachines.SAT

inductive Instruction where
  | falsum
  | load (index : Nat)
  | neg
  | conj
  deriving DecidableEq, Repr

def compile : Formula → List Instruction
  | .falsum => [.falsum]
  | .var i => [.load i]
  | .neg f => compile f ++ [.neg]
  | .conj f g => compile f ++ compile g ++ [.conj]

def assemble : List Instruction → List Formula → Option (List Formula)
  | [], stack => some stack
  | .falsum :: rest, stack => assemble rest (.falsum :: stack)
  | .load i :: rest, stack => assemble rest (.var i :: stack)
  | .neg :: rest, f :: stack => assemble rest (.neg f :: stack)
  | .conj :: rest, g :: f :: stack => assemble rest (.conj f g :: stack)
  | _, _ => none

theorem assemble_compile (f : Formula) (rest : List Instruction) (stack : List Formula) :
    assemble (compile f ++ rest) stack = assemble rest (f :: stack) := by
  induction f generalizing rest stack with
  | falsum => rfl
  | var i => rfl
  | neg f ih => simp only [compile, List.append_assoc, ih, List.cons_append, List.nil_append, assemble]
  | conj f g ihf ihg =>
    simp only [compile, List.append_assoc, ihf, ihg, List.cons_append, List.nil_append, assemble]

def putNat (n : Nat) : Word := List.replicate n true ++ [false]

def readNat : Word → Option (Nat × Word)
  | [] => none
  | false :: rest => some (0, rest)
  | true :: rest => do
    let (n, tail) ← readNat rest
    some (n + 1, tail)

theorem readNat_putNat (n : Nat) (tail : Word) :
    readNat (putNat n ++ tail) = some (n, tail) := by
  induction n with
  | zero => simp [putNat, readNat]
  | succ n ih =>
    have h := congrArg (fun result => result.bind (fun (i, rest) => some (i + 1, rest))) ih
    simpa [putNat, List.replicate_succ, readNat] using h

def encodeInstruction : Instruction → Word
  | .falsum => [false, false]
  | .load i => [false, true] ++ putNat i
  | .neg => [true, false]
  | .conj => [true, true]

def encodeProgram (p : List Instruction) : Word := p.flatMap encodeInstruction

def parseProgram : Nat → Word → Option (List Instruction)
  | 0, _ => none
  | _ + 1, [] => some []
  | fuel + 1, false :: false :: rest => do
    let tail ← parseProgram fuel rest
    some (.falsum :: tail)
  | fuel + 1, false :: true :: rest => do
    let (i, tail) ← readNat rest
    let code ← parseProgram fuel tail
    some (.load i :: code)
  | fuel + 1, true :: false :: rest => do
    let tail ← parseProgram fuel rest
    some (.neg :: tail)
  | fuel + 1, true :: true :: rest => do
    let tail ← parseProgram fuel rest
    some (.conj :: tail)
  | _, _ => none

theorem encodeProgram_length (p : List Instruction) : p.length ≤ (encodeProgram p).length := by
  induction p with
  | nil => simp [encodeProgram]
  | cons i rest ih =>
    cases i <;> simp [encodeProgram, encodeInstruction, putNat] at * <;> omega

theorem parseProgram_encode (p : List Instruction) (fuel : Nat) (hf : p.length < fuel) :
    parseProgram fuel (encodeProgram p) = some p := by
  induction p generalizing fuel with
  | nil => cases fuel <;> simp_all [encodeProgram, parseProgram]
  | cons i rest ih =>
    cases fuel with
    | zero => omega
    | succ fuel =>
      have hr : rest.length < fuel := by simpa using hf
      have hr' : parseProgram fuel (rest.flatMap encodeInstruction) = some rest := ih fuel hr
      cases i <;>
        simp [encodeProgram, encodeInstruction, parseProgram, readNat_putNat, hr']

def decode (bits : Word) : Option Formula := do
  let instructions ← parseProgram (bits.length + 1) bits
  let stack ← assemble instructions []
  match stack with
  | [f] => some f
  | _ => none

def encode (f : Formula) : Word := encodeProgram (compile f)

theorem decode_encode (f : Formula) : decode (encode f) = some f := by
  have hp : parseProgram ((encode f).length + 1) (encode f) = some (compile f) :=
    parseProgram_encode (compile f) ((encode f).length + 1)
      (Nat.lt_succ_of_le (encodeProgram_length (compile f)))
  have ha := assemble_compile f [] []
  simp only [List.append_nil, assemble] at ha
  simp [decode, hp, ha]

theorem encode_injective : Function.Injective encode := by
  intro f g h
  have := congrArg decode h
  simpa only [decode_encode, Option.some.injEq] using this

def EncodedSAT (bits : Word) : Prop :=
  ∃ f, decode bits = some f ∧ Satisfiable f

def solveEncoded (bits : Word) : Bool :=
  match decode bits with
  | none => false
  | some f => solve f

theorem solveEncoded_correct (bits : Word) : solveEncoded bits = true ↔ EncodedSAT bits := by
  cases hd : decode bits with
  | none => simp [solveEncoded, EncodedSAT, hd]
  | some f => simp [solveEncoded, EncodedSAT, hd, solve_correct]

theorem encode_satisfiable (f : Formula) : EncodedSAT (encode f) ↔ Satisfiable f := by
  simp [EncodedSAT, decode_encode]

def satTable (n : Nat) : Table := table solveEncoded n

theorem satTable_correct (n : Nat) (bits : Word) (h : bits.length ≤ n) :
    lookup bits (satTable n) = some true ↔ EncodedSAT bits :=
  exact_on_domain EncodedSAT solveEncoded solveEncoded_correct n bits h

theorem satTable_preserves (n : Nat) (bits : Word) (h : bits.length ≤ n) :
    lookup bits (satTable (n + 1)) = lookup bits (satTable n) :=
  preserves_answers solveEncoded n bits h

/-- A stateful expansion operation: retain the old table and solve the new block. -/
def expandSAT (n : Nat) (old : Table) : Table :=
  old ++ (words (n + 1)).map (fun bits => (bits, solveEncoded bits))

theorem expandSAT_eq (n : Nat) : expandSAT n (satTable n) = satTable (n + 1) := by
  exact (table_append solveEncoded n).symm

end OracleMachines.SAT

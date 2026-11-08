import OracleMachines.LayeredProtocol
import Std.Data.DHashMap
import Init.Data.BitVec.Lemmas

/-! Global variable names and local source semantics. Positions contain the
original array lookup proof, not only an unchecked pair of natural numbers.
The translation builders below carry evaluation equalities for the supplied
source. Array accumulation is bound back to that source by an equality check.
Global bucket grouping is treated in SourceGrouping. JSON parsing and
persistent-store refinement remain separate obligations. -/
namespace OracleMachines.Layered

structure LocalLiteral where
  right : Bool
  slot : Nat
  positive : Bool

def LocalLiteral.eval (lit : LocalLiteral) (x y : Nat) : Bool :=
  (if lit.right then y else x).testBit lit.slot == lit.positive

abbrev LocalCNF := Array (Array LocalLiteral)

def localEval (cnf : LocalCNF) (x y : Nat) : Bool :=
  cnf.toList.all fun clause => clause.toList.any fun lit => lit.eval x y

def compileLocal (width : Nat) (cnf : LocalCNF) : Relation (2^width) :=
  fun x y => localEval cnf x.val y.val

theorem compileLocal_exact (width : Nat) (cnf : LocalCNF) (x y : Fin (2^width)) :
    compileLocal width cnf x y = true ↔
      ∀ clause ∈ cnf.toList, ∃ lit ∈ clause.toList, lit.eval x.val y.val = true := by
  simp only [compileLocal,localEval,List.all_eq_true,List.any_eq_true]

structure SourcePosition (layers : Array (Array Nat)) (width varId : Nat) where
  layer : Fin layers.size
  slot : Fin layers[layer].size
  within : slot.val < width
  original : layers[layer][slot] = varId

abbrev SourcePositions (layers : Array (Array Nat)) (width : Nat) :=
  Std.DHashMap Nat (SourcePosition layers width)

def sourceLiteralEval (lit : Int) (valuation : Nat → Bool) : Bool :=
  valuation lit.natAbs == decide (lit > 0)

def sourceClauseEval (clause : Array Int) (valuation : Nat → Bool) : Bool :=
  clause.toList.any (sourceLiteralEval · valuation)

def sourceCNFEval (clauses : Array (Array Int)) (valuation : Nat → Bool) : Bool :=
  clauses.toList.all (sourceClauseEval · valuation)

/-- Agreement refers to original array entries, independent of the lookup map. -/
def SourceAgrees (layers : Array (Array Nat)) (valuation : Nat → Bool)
    (words : Nat → Nat) : Prop :=
  ∀ (i : Fin layers.size) (j : Fin layers[i].size),
    (words i.val).testBit j.val = valuation layers[i][j]

theorem SourcePosition.agrees {layers : Array (Array Nat)} {width varId : Nat}
    (position : SourcePosition layers width varId) (valuation : Nat → Bool)
    (words : Nat → Nat) (agreement : SourceAgrees layers valuation words) :
    (words position.layer.val).testBit position.slot.val = valuation varId := by
  exact (agreement position.layer position.slot).trans (congrArg valuation position.original)

def positionMatches {layers : Array (Array Nat)} {width : Nat}
    (positions : SourcePositions layers width) (i : Fin layers.size) (j : Fin layers[i].size) : Bool :=
  let key : Nat := layers[i][j]
  let found : Option (SourcePosition layers width key) := positions.get? key
  found.any fun position => position.layer.val == i.val && position.slot.val == j.val

def alignmentCheck {layers : Array (Array Nat)} {width : Nat}
    (positions : SourcePositions layers width) : Bool :=
  (List.finRange layers.size).all fun i =>
    (List.finRange layers[i].size).all fun j => positionMatches positions i j

theorem alignmentCheck_exact {layers : Array (Array Nat)} {width : Nat}
    (positions : SourcePositions layers width) :
    alignmentCheck positions = true ↔ ∀ i j, positionMatches positions i j = true := by
  simp [alignmentCheck,List.all_eq_true]

structure CheckedLayout (layers : Array (Array Nat)) (width : Nat) where
  positions : SourcePositions layers width
  complete : ∀ i j, positionMatches positions i j = true

def buildSourcePositions (layers : Array (Array Nat)) (width : Nat) :
    Except String (CheckedLayout layers width) := do
  let mut positions : SourcePositions layers width := {}
  for hi : i in [:layers.size] do
    let block := layers[i]
    if bound : block.size ≤ width then
      for hj : j in [:block.size] do
        let varId := block[j]
        if varId == 0 || positions.contains varId then throw "Variable blocks must be disjoint positive IDs"
        let layer : Fin layers.size := ⟨i,by get_elem_tactic⟩
        let slot : Fin layers[layer].size := ⟨j,by get_elem_tactic⟩
        let position : SourcePosition layers width varId :=
          ⟨layer,slot,Nat.lt_of_lt_of_le (by get_elem_tactic) bound,rfl⟩
        positions := positions.insert varId position
    else throw "Variable block exceeds supplied width"
  if checked : alignmentCheck positions = true then
    return ⟨positions,(alignmentCheck_exact positions).mp checked⟩
  else throw "Source variable index does not match original blocks"

theorem CheckedLayout.locate {layers : Array (Array Nat)} {width : Nat}
    (layout : CheckedLayout layers width) (i : Fin layers.size) (j : Fin layers[i].size) :
    ∃ position : SourcePosition layers width (layers[i][j]), layout.positions.get? (layers[i][j]) = some position ∧
      position.layer.val = i.val ∧ position.slot.val = j.val := by
  have present := layout.complete i j
  change (layout.positions.get? (layers[i][j])).any
    (fun position => position.layer.val == i.val && position.slot.val == j.val) = true at present
  cases found : layout.positions.get? (layers[i][j]) with
  | none => simp only [found,Option.any_none,Bool.false_eq_true] at present
  | some position =>
    refine ⟨position,rfl,?_⟩
    simpa only [found,Option.any_some,Bool.and_eq_true,beq_iff_eq] using present

theorem CheckedLayout.blockWidth {layers : Array (Array Nat)} {width : Nat}
    (layout : CheckedLayout layers width) (i : Fin layers.size) : layers[i].size ≤ width := by
  by_contra tooWide
  have within : width < layers[i].size := by omega
  obtain ⟨position,_,_,same⟩ := layout.locate i ⟨width,within⟩
  have bound := position.within
  simp only at same
  omega

def sourceValuation {layers : Array (Array Nat)} {width : Nat}
    (positions : SourcePositions layers width) (words : Nat → Nat) (varId : Nat) : Bool :=
  match positions.get? varId with
  | none => false
  | some position => (words position.layer.val).testBit position.slot.val

theorem CheckedLayout.sourceValuation_agrees {layers : Array (Array Nat)} {width : Nat}
    (layout : CheckedLayout layers width) (words : Nat → Nat) :
    SourceAgrees layers (sourceValuation layout.positions words) words := by
  intro i j
  obtain ⟨position,found,layer,slot⟩ := layout.locate i j
  unfold sourceValuation
  rw [found]
  change (words i.val).testBit j.val = (words position.layer.val).testBit position.slot.val
  rw [layer,slot]

def blockWord (block : Array Nat) (valuation : Nat → Bool) : Nat :=
  (BitVec.ofBoolListLE (block.toList.map valuation)).toNat

theorem blockWord_bit (block : Array Nat) (valuation : Nat → Bool) (j : Fin block.size) :
    (blockWord block valuation).testBit j.val = valuation block[j] := by
  change (BitVec.ofBoolListLE (block.toList.map valuation)).getLsbD j.val = _
  rw [BitVec.getLsbD_ofBoolListLE]
  simp [List.getD_eq_getElem?_getD,j.isLt]

theorem blockWord_bound (block : Array Nat) (valuation : Nat → Bool) (width : Nat)
    (bound : block.size ≤ width) : blockWord block valuation < 2^width := by
  have small := (BitVec.ofBoolListLE (block.toList.map valuation)).isLt
  simp only [List.length_map,Array.length_toList] at small
  exact Nat.lt_of_lt_of_le small (Nat.pow_le_pow_right (by decide) bound)

def sourceWords (layers : Array (Array Nat)) (valuation : Nat → Bool) (i : Nat) : Nat :=
  if inside : i < layers.size then blockWord layers[i] valuation else 0

theorem sourceWords_agree (layers : Array (Array Nat)) (valuation : Nat → Bool) :
    SourceAgrees layers valuation (sourceWords layers valuation) := by
  intro i j
  simpa [sourceWords,i.isLt] using blockWord_bit layers[i] valuation j

theorem CheckedLayout.sourceWords_bound {layers : Array (Array Nat)} {width : Nat}
    (layout : CheckedLayout layers width) (valuation : Nat → Bool) (i : Nat) :
    sourceWords layers valuation i < 2^width := by
  unfold sourceWords
  split
  · exact blockWord_bound _ _ _ (layout.blockWidth ⟨i,by assumption⟩)
  · exact Nat.two_pow_pos _

structure CheckedLiteral (layers : Array (Array Nat)) (width edge : Nat) (literal : Int) where
  localLiteral : LocalLiteral
  nonzero : literal ≠ 0
  within : localLiteral.slot < width
  exact : ∀ valuation words, SourceAgrees layers valuation words →
    localLiteral.eval (words edge) (words (edge+1)) = sourceLiteralEval literal valuation

def translateLiteral {layers : Array (Array Nat)} {width : Nat}
    (positions : SourcePositions layers width) (edge : Nat) (literal : Int) :
    Except String (CheckedLiteral layers width edge literal) := do
  if zero : literal = 0 then throw "Zero is not a literal" else
    let some position := positions.get? literal.natAbs | throw "Source variable missing from blocks"
    if adjacent : position.layer.val = edge ∨ position.layer.val = edge+1 then
      let localLiteral := LocalLiteral.mk (decide (position.layer.val = edge+1)) position.slot.val (decide (literal > 0))
      return ⟨localLiteral,zero,position.within,by
        intro valuation words agreement
        have same := position.agrees valuation words agreement
        rcases adjacent with left | right
        · have different : position.layer.val ≠ edge+1 := by omega
          simpa [localLiteral,LocalLiteral.eval,sourceLiteralEval,left,different] using
            congrArg (fun b => b == decide (literal > 0)) same
        · simpa [localLiteral,LocalLiteral.eval,sourceLiteralEval,right] using
            congrArg (fun b => b == decide (literal > 0)) same⟩
    else throw "Clause lies outside edited edge"

structure ClauseBuilder (layers : Array (Array Nat)) (width edge : Nat) where
  original : Array Int
  localClause : Array LocalLiteral
  exact : ∀ valuation words, SourceAgrees layers valuation words →
    localClause.toList.any (fun lit => lit.eval (words edge) (words (edge+1))) =
      sourceClauseEval original valuation

def ClauseBuilder.empty (layers : Array (Array Nat)) (width edge : Nat) : ClauseBuilder layers width edge :=
  ⟨#[],#[],by intros; rfl⟩

def ClauseBuilder.push {layers : Array (Array Nat)} {width edge : Nat}
    (builder : ClauseBuilder layers width edge) (literal : Int)
    (checked : CheckedLiteral layers width edge literal) : ClauseBuilder layers width edge :=
  ⟨builder.original.push literal,builder.localClause.push checked.localLiteral,by
    intro valuation words agreement
    simp only [Array.toList_push,List.any_append,List.any_cons,List.any_nil,Bool.or_false,
      sourceClauseEval]
    rw [builder.exact valuation words agreement,checked.exact valuation words agreement]
    rfl⟩

structure CheckedClause (layers : Array (Array Nat)) (width edge : Nat) (source : Array Int) where
  localClause : Array LocalLiteral
  exact : ∀ valuation words, SourceAgrees layers valuation words →
    localClause.toList.any (fun lit => lit.eval (words edge) (words (edge+1))) =
      sourceClauseEval source valuation

def translateClause {layers : Array (Array Nat)} {width : Nat}
    (positions : SourcePositions layers width) (edge : Nat) (clause : Array Int) :
    Except String (CheckedClause layers width edge clause) := do
  let mut builder := ClauseBuilder.empty layers width edge
  for literal in clause do
    let checked ← translateLiteral positions edge literal
    builder := builder.push literal checked
  if same : builder.original = clause then
    return ⟨builder.localClause,by simpa only [same] using builder.exact⟩
  else throw "Translated clause differs from source"

structure CNFBuilder (layers : Array (Array Nat)) (width edge : Nat) where
  original : Array (Array Int)
  localCNF : LocalCNF
  exact : ∀ valuation words, SourceAgrees layers valuation words →
    localEval localCNF (words edge) (words (edge+1)) = sourceCNFEval original valuation

def CNFBuilder.empty (layers : Array (Array Nat)) (width edge : Nat) : CNFBuilder layers width edge :=
  ⟨#[],#[],by intros; rfl⟩

def CNFBuilder.push {layers : Array (Array Nat)} {width edge : Nat}
    (builder : CNFBuilder layers width edge) (clause : Array Int)
    (checked : CheckedClause layers width edge clause) : CNFBuilder layers width edge :=
  ⟨builder.original.push clause,builder.localCNF.push checked.localClause,by
    intro valuation words agreement
    have old := builder.exact valuation words agreement
    have current := checked.exact valuation words agreement
    simpa [localEval,sourceCNFEval,sourceClauseEval,Array.toList_push] using congrArg₂ Bool.and old current⟩

structure CheckedCNF (layers : Array (Array Nat)) (width edge : Nat) (source : Array (Array Int)) where
  localCNF : LocalCNF
  exact : ∀ valuation words, SourceAgrees layers valuation words →
    localEval localCNF (words edge) (words (edge+1)) = sourceCNFEval source valuation

def translateCNF {layers : Array (Array Nat)} {width : Nat}
    (positions : SourcePositions layers width) (edge : Nat) (clauses : Array (Array Int)) :
    Except String (CheckedCNF layers width edge clauses) := do
  let mut builder := CNFBuilder.empty layers width edge
  for clause in clauses do
    let checked ← translateClause positions edge clause
    builder := builder.push clause checked
  if same : builder.original = clauses then
    return ⟨builder.localCNF,by simpa only [same] using builder.exact⟩
  else throw "Translated CNF differs from source"

/-- The agreement premise is realizable in both directions: global assignments
encode into bounded states, and boundary states extend to a global assignment.
This theorem concerns one checked source bucket, not global bucket grouping. -/
theorem CheckedCNF.satisfiable_exact {layers : Array (Array Nat)} {width edge : Nat}
    {source : Array (Array Int)} (layout : CheckedLayout layers width)
    (checked : CheckedCNF layers width edge source) :
    (∃ valuation, sourceCNFEval source valuation = true) ↔
      ∃ x y : Fin (2^width), compileLocal width checked.localCNF x y = true := by
  constructor
  · rintro ⟨valuation,satisfies⟩
    refine ⟨⟨sourceWords layers valuation edge,layout.sourceWords_bound valuation edge⟩,
      ⟨sourceWords layers valuation (edge+1),layout.sourceWords_bound valuation (edge+1)⟩,?_⟩
    change localEval checked.localCNF _ _ = true
    rw [checked.exact valuation (sourceWords layers valuation) (sourceWords_agree layers valuation)]
    exact satisfies
  · rintro ⟨x,y,possible⟩
    let words := fun i => if i = edge then x.val else if i = edge+1 then y.val else 0
    refine ⟨sourceValuation layout.positions words,?_⟩
    rw [← checked.exact _ words (layout.sourceValuation_agrees words)]
    simpa [words,compileLocal] using possible

theorem CheckedCNF.unsatisfiable_exact {layers : Array (Array Nat)} {width edge : Nat}
    {source : Array (Array Int)} (layout : CheckedLayout layers width)
    (checked : CheckedCNF layers width edge source) :
    (¬ ∃ x y : Fin (2^width), compileLocal width checked.localCNF x y = true) ↔
      ¬ ∃ valuation, sourceCNFEval source valuation = true :=
  not_congr (checked.satisfiable_exact layout).symm

end OracleMachines.Layered

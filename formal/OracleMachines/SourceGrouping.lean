import OracleMachines.SourceMapping

/-! Proof-carrying grouping of an original flat CNF into adjacent-block buckets.
The permutation invariant preserves every clause occurrence, including repeats
and empty clauses. Per-edge equality connects the grouped source to its actual
local translations. JSON parsing and native tree/store binding are separate. -/
namespace OracleMachines.Layered

theorem flatMap_modify_push {α : Type} (groups : List (Array α)) (index : Nat)
    (item : α) (inside : index < groups.length) :
    ((groups.modify index (·.push item)).flatMap Array.toList).Perm
      (groups.flatMap Array.toList ++ [item]) := by
  induction groups generalizing index with
  | nil => simp at inside
  | cons head tail ih =>
    cases index with
    | zero =>
      simpa only [List.modify_zero_cons,List.flatMap_cons,Array.toList_push,List.append_assoc] using
        (List.perm_append_comm (l₁ := [item]) (l₂ := tail.flatMap Array.toList)).append_left head.toList
    | succ index =>
      have smaller : index < tail.length := by simpa using inside
      simpa only [List.modify_succ_cons,List.flatMap_cons,List.append_assoc] using
        (ih index smaller).append_left head.toList

structure GroupedCNF (layers : Array (Array Nat)) (width edges : Nat)
    (source : Array (Array Int)) where
  buckets : Array LocalCNF
  original : Array (Array (Array Int))
  bucket_count : buckets.size = edges
  original_count : original.size = edges
  partition : (original.toList.flatMap Array.toList).Perm source.toList
  exact : ∀ (edge : Nat) (inside : edge < edges) valuation words,
    SourceAgrees layers valuation words →
      localEval (buckets[edge]'(by omega)) (words edge) (words (edge+1)) =
        sourceCNFEval (original[edge]'(by omega)) valuation

def GroupedCNF.empty (layers : Array (Array Nat)) (width edges : Nat) :
    GroupedCNF layers width edges #[] :=
  ⟨Array.replicate edges #[],Array.replicate edges #[],by simp,by simp,
    by simp,by intros; simp [localEval,sourceCNFEval]⟩

def GroupedCNF.push {layers : Array (Array Nat)} {width edges : Nat}
    {source : Array (Array Int)} (grouped : GroupedCNF layers width edges source)
    (edge : Fin edges) (clause : Array Int)
    (checked : CheckedClause layers width edge.val clause) :
    GroupedCNF layers width edges (source.push clause) :=
  ⟨grouped.buckets.modify edge.val (·.push checked.localClause),
    grouped.original.modify edge.val (·.push clause),
    by simpa using grouped.bucket_count,by simpa using grouped.original_count,by
      simp only [Array.toList_modify,Array.toList_push]
      exact (flatMap_modify_push grouped.original.toList edge.val clause
        (by rw [Array.length_toList,grouped.original_count]; exact edge.isLt)).trans
        (grouped.partition.append_right [clause]),by
      intro other inside valuation words agreement
      simp only [Array.getElem_modify]
      by_cases same : edge.val = other
      · subst other
        simp only [ite_true,localEval,sourceCNFEval,Array.toList_push,List.all_append,List.all_cons,
          List.all_nil,Bool.and_true]
        exact congrArg₂ Bool.and (grouped.exact edge.val edge.isLt valuation words agreement)
          (checked.exact valuation words agreement)
      · simpa only [same,ite_false] using grouped.exact other inside valuation words agreement⟩

structure GroupingBuilder (layers : Array (Array Nat)) (width edges : Nat) where
  source : Array (Array Int)
  grouped : GroupedCNF layers width edges source

def GroupingBuilder.empty (layers : Array (Array Nat)) (width edges : Nat) :
    GroupingBuilder layers width edges := ⟨#[],GroupedCNF.empty layers width edges⟩

def GroupingBuilder.push {layers : Array (Array Nat)} {width edges : Nat}
    (builder : GroupingBuilder layers width edges) (edge : Fin edges) (clause : Array Int)
    (checked : CheckedClause layers width edge.val clause) : GroupingBuilder layers width edges :=
  ⟨builder.source.push clause,builder.grouped.push edge clause checked⟩

def groupClauses {layers : Array (Array Nat)} {width : Nat}
    (mapping : CheckedLayout layers width) (clauses : Array (Array Int)) :
    Except String (GroupedCNF layers width (layers.size-1) clauses) := do
  if clauses.size > 200000 then throw "Source clause cap exceeded"
  let mut builder := GroupingBuilder.empty layers width (layers.size-1)
  let mut literals := 0
  for clause in clauses do
    literals := literals+clause.size
    if literals > 2000000 then throw "Source literal cap exceeded"
    let mut lo := layers.size
    let mut hi := 0
    for lit in clause do
      if lit == 0 then throw "Zero is not a literal"
      let some position := mapping.positions.get? lit.natAbs | throw "Source variable missing from blocks"
      lo := min lo position.layer.val
      hi := max hi position.layer.val
    if !clause.isEmpty && hi > lo+1 then throw "Clause crosses nonadjacent blocks"
    let edge := if clause.isEmpty then 0 else min lo (layers.size-2)
    if inside : edge < layers.size-1 then
      let checked ← translateClause mapping.positions edge clause
      builder := builder.push ⟨edge,inside⟩ clause checked
    else throw "Source clause has no logical edge"
  if same : builder.source = clauses then
    return same ▸ builder.grouped
  else throw "Grouped clauses differ from original source"

theorem list_all_perm {α : Type} {a b : List α} (permutation : a.Perm b) (p : α → Bool) :
    a.all p = b.all p := by
  apply Bool.eq_iff_iff.mpr
  simp only [List.all_eq_true]
  constructor
  · intro all x inside; exact all x (permutation.mem_iff.mpr inside)
  · intro all x inside; exact all x (permutation.mem_iff.mp inside)

theorem GroupedCNF.original_exact {layers : Array (Array Nat)} {width edges : Nat}
    {source : Array (Array Int)} (grouped : GroupedCNF layers width edges source)
    (valuation : Nat → Bool) :
    sourceCNFEval source valuation = true ↔
      ∀ (edge : Nat) (inside : edge < edges),
        sourceCNFEval (grouped.original[edge]'(by rw [grouped.original_count]; exact inside)) valuation = true := by
  have same := list_all_perm grouped.partition (sourceClauseEval · valuation)
  change source.toList.all (sourceClauseEval · valuation) = true ↔ _
  rw [← same,List.all_flatMap]
  change grouped.original.toList.all (fun clauses => sourceCNFEval clauses valuation) = true ↔ _
  simp only [List.all_eq_true,Array.mem_toList_iff,← Array.forall_getElem]
  simp only [grouped.original_count]

theorem GroupedCNF.clause_occurrences {layers : Array (Array Nat)} {width edges : Nat}
    {source : Array (Array Int)} (grouped : GroupedCNF layers width edges source) (clause : Array Int) :
    (grouped.original.toList.flatMap Array.toList).count clause = source.toList.count clause :=
  grouped.partition.count_eq clause

def GroupedCNF.Accepts {layers : Array (Array Nat)} {width edges : Nat}
    {source : Array (Array Int)} (grouped : GroupedCNF layers width edges source)
    (states : Nat → Fin (2^width)) : Prop :=
  ∀ (edge : Nat) (inside : edge < edges),
    compileLocal width (grouped.buckets[edge]'(by rw [grouped.bucket_count]; exact inside))
      (states edge) (states (edge+1)) = true

/-- All buckets must share one state at each block; independent nonemptiness
of the buckets is not enough. This statement uses the original complete CNF. -/
theorem GroupedCNF.satisfiable_exact {layers : Array (Array Nat)} {width edges : Nat}
    {source : Array (Array Int)} (layout : CheckedLayout layers width)
    (grouped : GroupedCNF layers width edges source) :
    (∃ valuation, sourceCNFEval source valuation = true) ↔ ∃ states, grouped.Accepts states := by
  constructor
  · rintro ⟨valuation,satisfies⟩
    refine ⟨fun i => ⟨sourceWords layers valuation i,layout.sourceWords_bound valuation i⟩,?_⟩
    intro edge inside
    change localEval _ _ _ = true
    rw [grouped.exact edge inside valuation _ (sourceWords_agree layers valuation)]
    exact (grouped.original_exact valuation).mp satisfies edge inside
  · rintro ⟨states,accepts⟩
    let words := fun i => (states i).val
    let valuation := sourceValuation layout.positions words
    refine ⟨valuation,(grouped.original_exact valuation).mpr ?_⟩
    intro edge inside
    rw [← grouped.exact edge inside valuation words (layout.sourceValuation_agrees words)]
    exact accepts edge inside

theorem GroupedCNF.unsatisfiable_exact {layers : Array (Array Nat)} {width edges : Nat}
    {source : Array (Array Int)} (layout : CheckedLayout layers width)
    (grouped : GroupedCNF layers width edges source) :
    (¬ ∃ states, grouped.Accepts states) ↔ ¬ ∃ valuation, sourceCNFEval source valuation = true :=
  not_congr (grouped.satisfiable_exact layout).symm

end OracleMachines.Layered

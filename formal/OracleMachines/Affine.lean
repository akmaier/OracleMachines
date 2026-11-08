import Mathlib.Algebra.Field.ZMod
import Mathlib.Data.Vector.Basic
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Data.Fin.Tuple.Basic
import Mathlib.Tactic

/-! Exact affine summaries over GF(2). Elimination operates on coefficient
vectors, never on assignment tables. Parsing, persistence and compiled execution
are separate from the mathematical and row-operation contracts. -/
namespace OracleMachines.Affine
abbrev F := ZMod 2

structure Row (n : Nat) where
  coeff : Vector F n
  rhs : F
  deriving DecidableEq

variable {n : Nat}
def Row.eval (r : Row n) (v : Fin n → F) : F := ∑ i, r.coeff[i] * v i
def Row.Holds (r : Row n) (v : Fin n → F) : Prop := r.eval v = r.rhs
def Holds (rows : List (Row n)) (v : Fin n → F) : Prop := ∀ r ∈ rows, r.Holds v

def Row.reduce (p r : Row n) (i : Fin n) : Row n :=
  let factor := r.coeff[i] / p.coeff[i]
  ⟨Vector.ofFn (fun j => r.coeff[j] - factor * p.coeff[j]),r.rhs - factor * p.rhs⟩

theorem Row.reduce_eval (p r : Row n) (i : Fin n) (v : Fin n → F) :
    (p.reduce r i).eval v = r.eval v - (r.coeff[i] / p.coeff[i]) * p.eval v := by
  simp [Row.reduce,Row.eval,sub_mul,mul_assoc,Finset.sum_sub_distrib,Finset.mul_sum]

theorem Row.reduce_zero (p r : Row n) (i : Fin n) (nonzero : p.coeff[i] ≠ 0) :
    (p.reduce r i).coeff[i] = 0 := by
  simp only [Row.reduce,Fin.getElem_fin,Vector.getElem_ofFn]
  change r.coeff[i] - r.coeff[i] / p.coeff[i] * p.coeff[i] = 0
  rw [div_mul_cancel₀ _ nonzero,sub_self]

theorem Row.reduce_holds (p r : Row n) (i : Fin n) (v : Fin n → F) (pivot : p.Holds v) :
    (p.reduce r i).Holds v ↔ r.Holds v := by
  unfold Row.Holds at *
  rw [Row.reduce_eval,pivot]
  simp [Row.reduce]

inductive Pivot (rows : List (Row n)) (i : Fin n) where
  | absent (zero : ∀ r ∈ rows, r.coeff[i] = 0)
  | found (row : Row n) (member : row ∈ rows) (nonzero : row.coeff[i] ≠ 0)

def choose : (rows : List (Row n)) → (i : Fin n) → Pivot rows i
  | [], _ => .absent (by simp)
  | r::rs, i =>
    if h : r.coeff[i] = 0 then
      match choose rs i with
      | .absent zero => .absent (by intro row member; simp only [List.mem_cons] at member; rcases member with rfl|member; exact h; exact zero row member)
      | .found row member nonzero => .found row (List.mem_cons_of_mem _ member) nonzero
    else .found r (by simp) h

theorem reduce_system (rows : List (Row n)) (p : Row n) (member : p ∈ rows)
    (i : Fin n) (v : Fin n → F) :
    Holds rows v ↔ p.Holds v ∧ Holds (rows.map (fun r => p.reduce r i)) v := by
  constructor
  · intro all
    refine ⟨all p member,?_⟩
    intro r hr
    obtain ⟨s,hs,rfl⟩ := List.mem_map.mp hr
    exact (p.reduce_holds s i v (all p member)).mpr (all s hs)
  · rintro ⟨pivot,rest⟩ r hr
    exact (p.reduce_holds r i v pivot).mp (rest _ (List.mem_map.mpr ⟨r,hr,rfl⟩))

theorem Row.eval_update (r : Row n) (v : Fin n → F) (i : Fin n) (a : F) :
    r.eval (Function.update v i a) = r.eval v + r.coeff[i] * (a-v i) := by
  unfold Row.eval
  rw [Fintype.sum_eq_add_sum_compl i (fun j => r.coeff[j] * Function.update v i a j),
    Fintype.sum_eq_add_sum_compl i (fun j => r.coeff[j] * v j)]
  have tail : (∑ j ∈ ({i}ᶜ : Finset (Fin n)), r.coeff[j] * Function.update v i a j) =
      ∑ j ∈ ({i}ᶜ : Finset (Fin n)), r.coeff[j] * v j := by
    apply Finset.sum_congr rfl
    intro j hj
    simp only [Finset.mem_compl,Finset.mem_singleton] at hj
    simp [Function.update_of_ne hj]
  rw [tail,Function.update_self]
  ring

theorem Row.holds_update_zero (r : Row n) (v : Fin n → F) (i : Fin n) (a : F)
    (zero : r.coeff[i] = 0) : r.Holds (Function.update v i a) ↔ r.Holds v := by
  simp [Row.Holds,r.eval_update,zero]

/-- Eliminate one coordinate. All rows remain as coefficient vectors; the
later normalization removes redundancy without enumerating valuations. -/
def eliminate (rows : List (Row n)) (i : Fin n) : List (Row n) :=
  match choose rows i with
  | .absent _ => rows
  | .found p _ _ => rows.map (fun r => p.reduce r i)

theorem eliminate_zero (rows : List (Row n)) (i : Fin n) :
    ∀ r ∈ eliminate rows i, r.coeff[i] = 0 := by
  unfold eliminate
  cases choose rows i with
  | absent zero => exact zero
  | found p member nonzero =>
    intro r hr
    obtain ⟨s,hs,rfl⟩ := List.mem_map.mp hr
    exact p.reduce_zero s i nonzero

theorem eliminate_exact (rows : List (Row n)) (i : Fin n) (v : Fin n → F) :
    Holds (eliminate rows i) v ↔ ∃ a, Holds rows (Function.update v i a) := by
  unfold eliminate
  cases choose rows i with
  | absent zero =>
    constructor
    · intro all; exact ⟨v i,by simpa using all⟩
    · rintro ⟨a,all⟩ r hr
      exact (r.holds_update_zero v i a (zero r hr)).mp (all r hr)
  | found p member nonzero =>
    constructor
    · intro rest
      let a := v i + (p.rhs-p.eval v)/p.coeff[i]
      have pivot : p.Holds (Function.update v i a) := by
        unfold Row.Holds
        rw [p.eval_update]
        change p.eval v + p.coeff[i] * (v i + (p.rhs-p.eval v)/p.coeff[i] - v i) = p.rhs
        calc
          _ = p.eval v + ((p.rhs-p.eval v)/p.coeff[i])*p.coeff[i] := by ring
          _ = p.rhs := by rw [div_mul_cancel₀ _ nonzero]; ring
      refine ⟨a,(reduce_system rows p member i _).mpr ⟨pivot,?_⟩⟩
      intro r hr
      obtain ⟨s,hs,rfl⟩ := List.mem_map.mp hr
      exact (Row.holds_update_zero _ v i a (p.reduce_zero s i nonzero)).mpr
        (rest _ (List.mem_map.mpr ⟨s,hs,rfl⟩))
    · rintro ⟨a,all⟩ r hr
      obtain ⟨s,hs,rfl⟩ := List.mem_map.mp hr
      have reduced := (reduce_system rows p member i _).mp all
      exact (Row.holds_update_zero _ v i a (p.reduce_zero s i nonzero)).mp
        (reduced.2 _ (List.mem_map.mpr ⟨s,hs,rfl⟩))

def Supported (rows : List (Row n)) (todo : List (Fin n)) : Prop :=
  ∀ r ∈ rows, ∀ i, i ∉ todo → r.coeff[i] = 0

def contradiction (n : Nat) : Row n := ⟨Vector.replicate n 0,1⟩

def constants (rows : List (Row n)) : List (Row n) :=
  if rows.all (fun r => r.rhs == 0) then [] else [contradiction n]

theorem constants_exact (rows : List (Row n)) (supported : Supported rows []) (v : Fin n → F) :
    Holds (constants rows) v ↔ Holds rows v := by
  have evalZero : ∀ r ∈ rows, r.eval v = 0 := by
    intro r hr
    apply Finset.sum_eq_zero
    intro i _
    rw [supported r hr i (by simp),zero_mul]
  have exactRows : Holds rows v ↔ ∀ r ∈ rows, r.rhs = 0 := by
    constructor
    · intro all r hr; exact (all r hr).symm.trans (evalZero r hr)
    · intro all r hr; exact (evalZero r hr).trans (all r hr).symm
  rw [exactRows]
  unfold constants
  split
  · simpa [Holds] using (List.all_eq_true.mp (by assumption : rows.all (fun r => r.rhs == 0) = true))
  · have bad : ¬ ∀ r ∈ rows, r.rhs = 0 := by
      simpa only [List.all_eq_true,beq_iff_eq] using (by assumption : ¬rows.all (fun r => r.rhs == 0) = true)
    simp [Holds,Row.Holds,Row.eval,contradiction,bad]

/-- Each chosen pivot contributes one output row. Zero rows contribute none;
inconsistency is represented by one constant row. -/
def basisAux : List (Fin n) → List (Row n) → List (Row n)
  | [], rows => constants rows
  | i::todo, rows =>
    match choose rows i with
    | .absent _ => basisAux todo rows
    | .found p _ _ => p :: basisAux todo (rows.map (fun r => p.reduce r i))

theorem basisAux_size (todo : List (Fin n)) (rows : List (Row n)) :
    (basisAux todo rows).length ≤ todo.length+1 := by
  induction todo generalizing rows with
  | nil => simp only [basisAux,constants]; split <;> simp
  | cons i todo ih =>
    simp only [basisAux]
    cases choose rows i with
    | absent => have := ih rows; simp only [List.length_cons]; omega
    | found p member nonzero =>
      have := ih (rows.map (fun r => p.reduce r i))
      simp only [List.length_cons]; omega

theorem supported_absent (rows : List (Row n)) (i : Fin n) (todo : List (Fin n))
    (supported : Supported rows (i::todo)) (zero : ∀ r ∈ rows, r.coeff[i] = 0) :
    Supported rows todo := by
  intro r hr j hj
  by_cases same : j = i
  · subst j; exact zero r hr
  · exact supported r hr j (by simp [same,hj])

theorem supported_reduce (rows : List (Row n)) (i : Fin n) (todo : List (Fin n))
    (supported : Supported rows (i::todo)) (p : Row n) (member : p ∈ rows)
    (nonzero : p.coeff[i] ≠ 0) : Supported (rows.map (fun r => p.reduce r i)) todo := by
  intro r hr j hj
  obtain ⟨s,hs,rfl⟩ := List.mem_map.mp hr
  by_cases same : j = i
  · subst j; exact p.reduce_zero s i nonzero
  · have notIn : j ∉ i::todo := by simp [same,hj]
    simp only [Row.reduce,Fin.getElem_fin,Vector.getElem_ofFn]
    change s.coeff[j] - (s.coeff[i]/p.coeff[i])*p.coeff[j] = 0
    rw [supported s hs j notIn,supported p member j notIn]
    simp

theorem basisAux_exact (todo : List (Fin n)) (rows : List (Row n))
    (supported : Supported rows todo) (v : Fin n → F) :
    Holds (basisAux todo rows) v ↔ Holds rows v := by
  induction todo generalizing rows with
  | nil => exact constants_exact rows supported v
  | cons i todo ih =>
    simp only [basisAux]
    cases choose rows i with
    | absent zero => exact ih rows (supported_absent rows i todo supported zero)
    | found p member nonzero =>
      have tail := ih (rows.map (fun r => p.reduce r i)) (supported_reduce rows i todo supported p member nonzero)
      change Holds (p :: basisAux todo (rows.map (fun r => p.reduce r i))) v ↔ Holds rows v
      have cons : ∀ rs : List (Row n), Holds (p::rs) v ↔ p.Holds v ∧ Holds rs v := by
        intro rs; simp [Holds]
      rw [cons,tail]
      exact (reduce_system rows p member i v).symm

def basis (rows : List (Row n)) : List (Row n) := basisAux (List.finRange n) rows

theorem basis_size (rows : List (Row n)) : (basis rows).length ≤ n+1 := by
  simpa [basis] using basisAux_size (List.finRange n) rows

theorem basis_exact (rows : List (Row n)) (v : Fin n → F) : Holds (basis rows) v ↔ Holds rows v :=
  basisAux_exact _ rows (by intro r hr i hi; simp at hi) v

def project : List (Fin n) → List (Row n) → List (Row n)
  | [], rows => rows
  | i::todo, rows => project todo (eliminate rows i)

def AgreesOutside (hidden : List (Fin n)) (v w : Fin n → F) : Prop :=
  ∀ i, i ∉ hidden → w i = v i

theorem project_exact (hidden : List (Fin n)) (rows : List (Row n)) (v : Fin n → F) :
    Holds (project hidden rows) v ↔ ∃ w, AgreesOutside hidden v w ∧ Holds rows w := by
  induction hidden generalizing rows v with
  | nil =>
    constructor
    · intro all; exact ⟨v,by intro i _; rfl,all⟩
    · rintro ⟨w,agree,all⟩
      have same : w = v := funext (fun i => agree i (by simp))
      simpa [same,project] using all
  | cons i todo ih =>
    simp only [project,ih,eliminate_exact]
    constructor
    · rintro ⟨w,agree,a,all⟩
      refine ⟨Function.update w i a,?_,all⟩
      intro j hj
      simp only [List.mem_cons,not_or] at hj
      rw [Function.update_of_ne hj.1]
      exact agree j hj.2
    · rintro ⟨w,agree,all⟩
      refine ⟨Function.update w i (v i),?_,w i,?_⟩
      · intro j hj
        by_cases same : j = i
        · subst j; simp
        · rw [Function.update_of_ne same]
          exact agree j (by simp [same,hj])
      · simpa using all

theorem eliminate_preserves_zero (rows : List (Row n)) (i j : Fin n)
    (zero : ∀ r ∈ rows, r.coeff[j] = 0) : ∀ r ∈ eliminate rows i, r.coeff[j] = 0 := by
  unfold eliminate
  cases choose rows i with
  | absent => exact zero
  | found p member nonzero =>
    intro r hr
    obtain ⟨s,hs,rfl⟩ := List.mem_map.mp hr
    simp only [Row.reduce,Fin.getElem_fin,Vector.getElem_ofFn]
    change s.coeff[j] - (s.coeff[i]/p.coeff[i])*p.coeff[j] = 0
    rw [zero s hs,zero p member]; simp

theorem project_preserves_zero (hidden : List (Fin n)) (rows : List (Row n)) (j : Fin n)
    (zero : ∀ r ∈ rows, r.coeff[j] = 0) : ∀ r ∈ project hidden rows, r.coeff[j] = 0 := by
  induction hidden generalizing rows with
  | nil => exact zero
  | cons i todo ih => exact ih _ (eliminate_preserves_zero rows i j zero)

theorem project_zero (hidden : List (Fin n)) (rows : List (Row n)) (j : Fin n) (member : j ∈ hidden) :
    ∀ r ∈ project hidden rows, r.coeff[j] = 0 := by
  induction hidden generalizing rows with
  | nil => simp at member
  | cons i todo ih =>
    simp only [List.mem_cons] at member
    rcases member with rfl|member
    · exact project_preserves_zero todo _ j (eliminate_zero rows j)
    · exact ih _ member

theorem project_length (hidden : List (Fin n)) (rows : List (Row n)) :
    (project hidden rows).length = rows.length := by
  induction hidden generalizing rows with
  | nil => rfl
  | cons i todo ih =>
    simp only [project,ih,eliminate]
    cases choose rows i <;> simp

def decide (rows : List (Row n)) : Bool :=
  (project (List.finRange n) rows).all (fun r => r.rhs == 0)

theorem holds_zero (rows : List (Row n)) : Holds rows (fun _ => 0) ↔ ∀ r ∈ rows, r.rhs = 0 := by
  simp [Holds,Row.Holds,Row.eval,eq_comm]

theorem decide_exact (rows : List (Row n)) : decide rows = true ↔ ∃ v, Holds rows v := by
  simp only [decide,List.all_eq_true,beq_iff_eq,← holds_zero,project_exact]
  simp [AgreesOutside]

theorem decide_false (rows : List (Row n)) : decide rows = false ↔ ¬ ∃ v, Holds rows v := by
  rw [← decide_exact]
  cases decide rows <;> decide

def Row.liftLeft {b : Nat} (r : Row b) : Row (b+b) :=
  ⟨Vector.ofFn (Fin.append (fun i => r.coeff[i]) (fun _ => 0)),r.rhs⟩

def Row.dropLeft {b : Nat} (r : Row (b+b)) : Row b :=
  ⟨Vector.ofFn (fun i => r.coeff[Fin.natAdd b i]),r.rhs⟩

theorem Row.liftLeft_exact {b : Nat} (r : Row b) (u v : Fin b → F) :
    r.liftLeft.Holds (Fin.append u v) ↔ r.Holds u := by
  simp only [Row.Holds,Row.eval,Row.liftLeft,Fin.getElem_fin,Vector.getElem_ofFn,Fin.eta,Fin.sum_univ_add,Fin.append_left,Fin.append_right,Fin.eta,zero_mul,Finset.sum_const_zero,add_zero]

theorem Row.dropLeft_exact {b : Nat} (r : Row (b+b)) (u v : Fin b → F)
    (zero : ∀ i : Fin b, r.coeff[i.castAdd b] = 0) :
    r.dropLeft.Holds v ↔ r.Holds (Fin.append u v) := by
  simp only [Row.Holds,Row.eval,Row.dropLeft,Fin.getElem_fin,Vector.getElem_ofFn,Fin.eta,Fin.sum_univ_add,Fin.append_left,Fin.append_right]
  change (∑ i : Fin b, r.coeff[Fin.natAdd b i] * v i) = r.rhs ↔
    (∑ i : Fin b, r.coeff[i.castAdd b] * u i) + (∑ i : Fin b, r.coeff[Fin.natAdd b i] * v i) = r.rhs
  have leftZero : (∑ i : Fin b, r.coeff[i.castAdd b] * u i) = 0 := by
    apply Finset.sum_eq_zero
    intro i _; rw [zero i,zero_mul]
  rw [leftZero,zero_add]

def leftIndices (b : Nat) : List (Fin (b+b)) := (List.finRange b).map (Fin.castAdd b)

theorem leftIndices_member {b : Nat} (i : Fin (b+b)) : i ∈ leftIndices b ↔ i.val < b := by
  simp only [leftIndices,List.mem_map,List.mem_finRange,true_and]
  constructor
  · rintro ⟨j,rfl⟩; exact j.isLt
  · intro inside; exact ⟨⟨i.val,inside⟩,by ext; rfl⟩

theorem project_left_exact {b : Nat} (rows : List (Row (b+b))) (v : Fin b → F) :
    Holds ((project (leftIndices b) rows).map Row.dropLeft) v ↔
      ∃ u, Holds rows (Fin.append u v) := by
  have drop : Holds ((project (leftIndices b) rows).map Row.dropLeft) v ↔
      Holds (project (leftIndices b) rows) (Fin.append (fun _ => 0) v) := by
    constructor
    · intro all r hr
      exact (r.dropLeft_exact (fun _ => 0) v (fun i => project_zero _ rows _
        (leftIndices_member _ |>.mpr i.isLt) r hr)).mp (all _ (List.mem_map.mpr ⟨r,hr,rfl⟩))
    · intro all r hr
      obtain ⟨s,hs,rfl⟩ := List.mem_map.mp hr
      exact (s.dropLeft_exact (fun _ => 0) v (fun i => project_zero _ rows _
        (leftIndices_member _ |>.mpr i.isLt) s hs)).mpr (all s hs)
  rw [drop,project_exact]
  constructor
  · rintro ⟨w,agree,all⟩
    let u := fun i : Fin b => w (i.castAdd b)
    have same : w = Fin.append u v := by
      funext i
      refine Fin.addCases (fun j => ?_) (fun j => ?_) i
      · simp [u]
      · rw [Fin.append_right]
        have h := agree (Fin.natAdd b j) (by rw [leftIndices_member]; simp)
        simpa only [Fin.append_right] using h
    exact ⟨u,same ▸ all⟩
  · rintro ⟨u,all⟩
    refine ⟨Fin.append u v,?_,all⟩
    intro i
    refine Fin.addCases (fun j hi => ?_) (fun j _ => ?_) i
    · exact False.elim (hi ((leftIndices_member _).mpr j.isLt))
    · simp only [Fin.append_right]

/-- Append a fresh block. The old prefix is exposed only through its current
boundary. Raw new equations may mention the old and the fresh boundary. -/
def extend {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) : List (Row b) :=
  basis ((project (leftIndices b) (previous.map Row.liftLeft ++ equations)).map Row.dropLeft)

theorem extend_size {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) :
    (extend previous equations).length ≤ b+1 := basis_size _

theorem extend_exact {b : Nat} (previous : List (Row b)) (equations : List (Row (b+b))) (v : Fin b → F) :
    Holds (extend previous equations) v ↔ ∃ u, Holds previous u ∧ Holds equations (Fin.append u v) := by
  rw [extend,basis_exact,project_left_exact]
  apply exists_congr
  intro u
  have append : ∀ a c : List (Row (b+b)), Holds (a++c) (Fin.append u v) ↔
      Holds a (Fin.append u v) ∧ Holds c (Fin.append u v) := by
    intro a c; simp only [Holds,List.mem_append,or_imp,forall_and]
  rw [append]
  apply and_congr_left
  intro _
  simp only [Holds,List.forall_mem_map,Row.liftLeft_exact]

end OracleMachines.Affine

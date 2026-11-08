import OracleMachines.AffineResident
import Std.Data.HashSet.Lemmas

/-! Exact duplicate removal preserves every boundary assignment. Hash collisions
are resolved by structural row equality, not trusted as an equivalence test. -/
namespace OracleMachines.Affine

def rowHash {n : Nat} (seed : UInt64) (row : Row n) : UInt64 :=
  mixHash (row.coeff.toArray.foldl (fun acc value => mixHash acc (hash value.val)) seed) (hash row.rhs.val)

instance {n : Nat} : Hashable (Row n) := ⟨rowHash (hash n)⟩

def uniqueRowsAux {n : Nat} (seen : Std.HashSet (Row n)) : List (Row n) → List (Row n)
  | [] => []
  | row::rest =>
    if row ∈ seen then uniqueRowsAux seen rest
    else row::uniqueRowsAux (seen.insert row) rest

theorem uniqueRowsAux_mem {n : Nat} (seen : Std.HashSet (Row n)) (rows : List (Row n)) (row : Row n) :
    row ∈ uniqueRowsAux seen rows ↔ row ∈ rows ∧ row ∉ seen := by
  induction rows generalizing seen with
  | nil => simp [uniqueRowsAux]
  | cons head rest ih =>
    simp only [uniqueRowsAux]
    split_ifs with found
    · rw [ih]; simp only [List.mem_cons]; constructor
      · exact fun h => ⟨Or.inr h.1,h.2⟩
      · rintro ⟨same|member,absent⟩
        · subst row; exact False.elim (absent found)
        · exact ⟨member,absent⟩
    · rw [List.mem_cons,ih]
      simp only [Std.HashSet.mem_insert,beq_iff_eq,List.mem_cons]
      clear ih
      by_cases same : row = head <;> simp_all [eq_comm]

theorem uniqueRowsAux_length {n : Nat} (seen : Std.HashSet (Row n)) (rows : List (Row n)) :
    (uniqueRowsAux seen rows).length ≤ rows.length := by
  induction rows generalizing seen with
  | nil => simp [uniqueRowsAux]
  | cons row rest ih =>
    simp only [uniqueRowsAux]
    split_ifs
    · have := ih seen; simp only [List.length_cons]; omega
    · simpa only [List.length_cons,Nat.add_le_add_iff_right] using ih (seen.insert row)

theorem uniqueRowsAux_nodup {n : Nat} (seen : Std.HashSet (Row n)) (rows : List (Row n)) :
    (uniqueRowsAux seen rows).Nodup := by
  induction rows generalizing seen with
  | nil => simp [uniqueRowsAux]
  | cons row rest ih =>
    simp only [uniqueRowsAux]
    split_ifs
    · exact ih seen
    · apply List.nodup_cons.mpr
      refine ⟨?_,ih (seen.insert row)⟩
      intro member
      exact (uniqueRowsAux_mem (seen.insert row) rest row).mp member |>.2 (Std.HashSet.mem_insert_self)

def uniqueRows {n : Nat} (rows : List (Row n)) : List (Row n) := uniqueRowsAux {} rows

theorem uniqueRows_mem {n : Nat} (rows : List (Row n)) (row : Row n) :
    row ∈ uniqueRows rows ↔ row ∈ rows := by simp [uniqueRows,uniqueRowsAux_mem]

theorem uniqueRows_length {n : Nat} (rows : List (Row n)) :
    (uniqueRows rows).length ≤ rows.length := uniqueRowsAux_length {} rows

theorem uniqueRows_exact {n : Nat} (rows : List (Row n)) (v : Fin n → F) :
    Holds (uniqueRows rows) v ↔ Holds rows v := by simp only [Holds,uniqueRows_mem]

structure PreparedRows {n : Nat} (original : List (Row n)) where
  rows : List (Row n)
  exact : ∀ v, Holds rows v ↔ Holds original v
  bound : rows.length ≤ original.length

def prepareRows {n : Nat} (rows : List (Row n)) : PreparedRows rows :=
  ⟨uniqueRows rows,uniqueRows_exact rows,uniqueRows_length rows⟩

structure PreparedEntry where
  width : Nat
  original : List (Row width)
  result : PreparedRows original

def PreparedEntry.matchInput {n : Nat} (entry : PreparedEntry) (original : List (Row n)) :
    Option (PreparedRows original) :=
  if width : entry.width = n then by
    cases width
    exact if same : entry.original = original then some (same ▸ entry.result) else none
  else none

end OracleMachines.Affine

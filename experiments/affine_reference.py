"""Independent integer-bitset elimination of the complete original history.

No compiled boundary summary is read by this oracle. Intended for validation,
not for proving the native solver correct or comparing optimized SAT solvers.
"""
def flattened_sat(width,batches):
    variables=width*(len(batches)+1)
    rows=[]
    for step,batch in enumerate(batches):
        for equation in batch:
            lhs=sum(int(value)<<(step*width+i) for i,value in enumerate(equation['coefficients']))
            rows.append(lhs | (int(equation['rhs'])<<variables))
    pivots={}
    mask=(1<<variables)-1
    for row in rows:
        while row & mask:
            pivot=(row & mask).bit_length()-1
            if pivot in pivots:row^=pivots[pivot]
            else:
                pivots[pivot]=row
                break
        else:
            if row>>variables:return False
    return True


def equation(width,indices=(),rhs=False):
    return dict(coefficients=[i in indices for i in range(2*width)],rhs=rhs)

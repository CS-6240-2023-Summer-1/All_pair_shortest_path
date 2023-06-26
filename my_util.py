from pyspark.rdd import portable_hash as pyspark_portable_hash
from scipy.sparse.csgraph import floyd_warshall as apsp_fw

import numpy as np
import numba as nb

# Compute block dim q
# and num blocks N
def block_vars(n, b):
    q = int((n-1) / b) + 1
    N = (q * (q+1)) / 2
    return q, N

def verify_partitioner(F, q):
    assert F == 'md' or F == 'ph', \
        'Error: Unrecognized partitioner \'' + F + '\'. Use \'md\' or \'ph\'.'

    if F == 'md':
        def multi_diag(x):
            (k1, k2) = x
            return int(k1 - (0.5) * (k1 - k2) * (k1 - k2 + 2 * q  + 1))
        return multi_diag
    return pyspark_portable_hash # otherwise use default.

def scipy_floyd(ADJ_MAT):
    return apsp_fw(ADJ_MAT, directed=False, unweighted=False, overwrite=True)

'''
 Min-plus matrix multiplication of matrices
 A and B. Compiled for better performance using numba.
'''
@nb.jit(nopython=True)
def mpmatmul(A, B):
    assert A.shape[1] == B.shape[0], 'Matrix dimension mismatch in mpmatmul().'

    C = np.zeros((A.shape[0], B.shape[1]))
    for i in range(A.shape[0]):
        for j in range(B.shape[1]):
            somesum = np.inf
            for k in range(A.shape[1]):
                somesum = min(somesum, A[i, k] + B[k, j])
            C[i, j] = somesum
    return C

'''
 Min-plus matrix multiplication of matrices
 A*B = C. D_ returned is elementwise min of C and input D_.
 Compiled for better performance using numba.
 Input matrices A, B stored C, Fortran contiguous, respectively, for best performance.
'''
def minmpmatmul(A, B, D_):
    return _minmpmatmul(np.ascontiguousarray(A), np.asfortranarray(B), D_)
@nb.jit(nopython=True)
def _minmpmatmul(A, B, D_):
    assert A.shape[1] == B.shape[0], 'Matrix dimension mismatch in minmpmatmul().'

    for i in range(A.shape[0]):
        for j in range(B.shape[1]):
            somesum = np.inf
            for k in range(A.shape[1]):
                somesum = min(somesum, A[i, k] + B[k, j])
            D_[i, j] = min(D_[i, j], somesum)
    return D_

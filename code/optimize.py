import numpy as np
import numpy.linalg as la
import traceback
import sys
import scipy
from scipy import optimize as scopt


def norm_dif(x, *args):
    """
    Return || b - Ax || (Frobenius norm).
    """
    A, b = args
    return la.norm(b - np.dot(A, x))

# use as baseline to test conjugate gradient
def gradient_descent(X, g, f = None, numIter = 500):
    """
    Standard gradient descent for SYMMETRIC,
    POSITIVE-DEFINITE matrices.
    Needs thorough testing.

    Args:
        numpy.ndarray X:    n x n transformation matrix.
        numpy.ndarray g:    n x 1 "target values".
        numpy.ndarray f:    n x 1 initial guess (optional).
        int     numIter:    Number of passes over data.

    Returns:
        argmin(f) [Xf - g].
    """
    n = len(X)
    # Ensure sound inputs
    assert len(X.T) == n
    assert len(g) == n
    # Working with (n, ) vectors, not (n, 1)
    if len(g.shape) == 2: g = g.reshape(n, )
    if f is None:
        f = np.random.randn(n, )
    else:
        assert len(f) == n
        if len(f.shape) == 2: f = f.reshape(n, ) # (n, ) over (n, 1)

    # Start descent
    for _ in range(numIter):
        #print('Iter %d' % _)

        # calculate residual (direction of steepest descent)
        r = g - np.dot(X, f)
        if la.norm(r) < 0.000000000001: break

        # calculate step size (via line search)
        a = np.inner(r.T, r) / float(np.inner(r.T, np.inner(X, r)))

        # update x
        f += a * r

    return f

def conjugate_gs(u, A):
    """
    Conjugate Gram-Schmidt process.
    https://www.cs.cmu.edu/~quake-papers/painless-conjugate-gradient.pdf

    Args:
        (numpy.ndarray) u: array of n linearly independent column vectors.
        (numpy.ndarray) A: matrix for vectors to be mutually conjugate to.

    Returns:
        (numpy.ndarray) d: array of n mutually A-conjugate column vectors.
    """
    n = len(u)
    d = np.copy(u)

    for i in range(1, n):
        for j in range(0,i):

            Adj = np.dot(A, d[:, j])


            Bij = -np.inner(u[:, i].T, Adj)
            Bij /= np.inner(d[:, j].T, Adj) # (37)

            d[:, i] += np.dot(Bij, d[:, j]) # (36)

    return d

def conjugate_gs_alt(U, A):
    """
    Conjugate Gram-Schmidt process.
    https://www.cs.cmu.edu/~quake-papers/painless-conjugate-gradient.pdf

    Args:
        (numpy.ndarray) U: array of n linearly independent column vectors.
        (numpy.ndarray) A: matrix for vectors to be mutually conjugate to.

    Returns:
        (numpy.ndarray) D: array of n mutually A-conjugate column vectors.
    """
    n = len(U)
    D = np.copy(U)
    beta = np.zeros([n,n])

    D[:, 0] = U[:, 0]
    for i in range(1, n):
        for j in range(0,i-1):

            Adj = np.dot(A, D[:, j])

            beta[i, j] = -np.dot(U[:, i].T, Adj)
            beta[i, j] /= np.dot(D[:, j].T, Adj) # (37)

            D[:, i] = U[:, i] + np.dot(beta[i, j], D[:, j]) # (36)

    ## checks
    for i in range(0, n-1):
        for j in range(i+1,n):
            # print( np.dot(U[:, i],np.dot(A,D[:, j])) + beta[i, j]*np.dot(D[:, j].T,np.dot(A,D[:, j])) )
            print( np.dot(D[:,i], np.dot(A, D[:,j])) )

    return D

# REFERENCE IMPLEMENTATION
def conjugate_gradient_ideal(X, g, f = None, numIter = 500):
    """
    For SYMMETRIC, POSITIVE-DEFINITE matrices.
    """
    pass

def conjugate_gradient(X, g, f = None, numIter = 500):
    """
    placeholder
    """
    pass

def jacobi(A,b,tol=0.001,maxiter=1000,x0=None):
    '''
    Solves Ax = b with Jacobi splitting method
        A \in R^[n x n]
        b,x \in R^n

    ONLY WORKS for matrices A such that spectral_radius(B) < 1, where
        B = D-1 E,
        D = diagonal elements of A (zero elsewhere),
        E = non-diagonal elements of A (zero on diagonal)

    '''

    n = A.shape[0]

    ## start
    if x0 == None:
        x0 = np.random.randn(n)

    ## construct matrix components
    D = np.zeros([n,n])
    for i in range(n):
        for j in range(n):
            D[i][i] = A[i][i]
    E = A-D
    Dinv = la.inv(D)
    B = np.dot(-Dinv,E)
    z = np.dot(Dinv,b)

    spec_rad = max(la.svd(B)[1])**2
    if spec_rad >= 1:
        print('Spectral radius of B (%f) >= 1. Method won\'t converge.' % spec_rad)
        print('Returning None.')
    else: print('Spectral radius of B: %f' % spec_rad)

    ## iterations
    x = x0
    for i in range(maxiter):
        x = np.dot(B,x) + z
        #print(la.norm(np.dot(A,x)-b))
        if la.norm(np.dot(A,x)-b) <= tol:
            break

    return x

def iter_refinement(A, b, tol=0.001, maxIter=500, x0=None, debug=False):
    """
    Iterative refinement method.
    Use as a sort of postprocessing to fix round-off error?

    https://en.wikipedia.org/wiki/Iterative_refinement

    Works, but needs more testing on various sizes, condition numbers + initial
    error in Ax=b.
    """
    # tol *= la.norm(A)

    m = len(A)
    n = len(A.T)
    if x0 is None:
        x0 = np.random.randn(n)

    x = x0

    for _ in range(maxIter):
        if debug: print('Iter %d' % _)
        # Compute the residual r
        r = b - np.dot(A, x)

        # Solve the system (Ad = r) for d
        result = scopt.minimize(fun=norm_dif, x0=np.random.randn(m), args=(A, r), method='CG')
        d, success, msg = result.x, result.success, result.message
        if debug: print(success, msg)
        # TODO: find out which method is best/quickest to solve this

        x += d

        if norm_dif(x, A, b) < tol:
            break

    return x

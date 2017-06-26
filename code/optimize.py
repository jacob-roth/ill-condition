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

# baseline
def gradient_descent(A, b, tol=0.001, x = None, numIter = 500, full_output=False):
    """
    Standard gradient descent for SYMMETRIC,
    POSITIVE-DEFINITE matrices.
    Needs thorough testing.

    Re-calculates residual EVERY iteration (so slow but a bit more accurate).

    Args:
        numpy.ndarray A:    n x n transformation matrix.
        numpy.ndarray b:    n x 1 "target values".
        numpy.ndarray x:    n x 1 initial guess (optional).
        int     numIter:    Number of passes over data.

    Returns:
        argmin(x) ||Ab - x||.
    """
    n = len(A)
    if x is None:
        x = np.zeros(n)

    if full_output:
        resids = []

    # Start descent
    for i in range(numIter):
        #print('Iter %d' % i)
        if full_output:
            resids.append(norm_dif(x, A, b))

        # calculate residual (direction of steepest descent)
        r = b - np.dot(A, x)

        # calculate step size (via line search)
        a = np.inner(r.T, r) / float(np.inner(r.T, np.inner(A, r)))

        # update x
        x += a * r

        if la.norm(b - np.dot(A, x)) < tol:
            print('GD: Close enough at iter %d' % i)
            if full_output:
                return x, i, True, resids
            else:
                return x

    print('GD: Max iteration reached (%d)' % numIter)
    if full_output:
        return x, numIter, False, resids
    else:
        return x

# modification: 1 matrix-vector multiplication per iteration
def gradient_descent_alt(A, b, x0=None, x_tru=None, numIter=500, recalc=499):
    """
    Implementation of gradient descent for PSD matrices.
    
    Notes:
        Needs thorough testing.
        Re-calculate residual EVERY iteration (so slow but a bit more accurate).
        Only 1 matrix-vector computation is performed per iteration (vs 2).
        Slow history tracking.

    Args:
        (numpy.ndarray)     A:    n x n transformation matrix.
        (numpy.ndarray)     b:    n x 1 "target values".
        (numpy.ndarray)    x0:    n x 1 initial guess (optional).
        (numpy.ndarray) x_tru:    n x 1 true x (optional).
        (int)         numIter:    Number of passes over data.

    Returns:
        argmin(x) ||Ax - b||_2.
    """
    
    n = len(A)
    
    # Ensure sound inputs
    assert len(A.T) == n
    assert len(b) == n
    
    # Working with (n, ) vectors, not (n, 1)
    if len(b.shape) == 2: b = b.reshape(n, )
    if x0 is None:
        x0 = np.random.randn(n, )
    else:
        assert len(x0) == n
        if len(x0.shape) == 2: x0 = x0.reshape(n, ) # (n, ) over (n, 1)

    # diagnostics
    x_hist = []
    if x_tru != None:
        err_hist = []

    # first descent step
    x = x0
    r_curr = b - np.dot(A, x)
    Ar_curr = np.dot(A,r_curr)
    a = np.inner(r_curr.T, r_curr) / float(np.inner(r_curr.T, Ar_curr))
    r_new = r_curr - a*Ar_curr
    x += a * r_curr
    x_hist += x
    err = la.norm(x-xtru)
    err_hist += err

    # remaining descent steps
    for _ in range(1,numIter):
        if _%recalc == 0:
            r = b - np.dot(A, x)
            if la.norm(r) < 10**-11: break
            a = np.inner(r.T, r) / float(np.inner(r.T, np.inner(A, r)))
            x += a * r
        else:
            #print('Iter %d' % _)

            # calculate residual (direction of steepest descent)
            r_curr = r_new
            if la.norm(r_curr) < 10**-11: break

            # calculate step size (via analytic line search)
            Ar_curr = np.inner(A, r_curr)
            a = np.inner(r_curr.T, r_curr) / float(np.inner(r_curr.T, Ar_curr))
            r_new = r_curr - a*Ar_curr

            # updates
            x += a * r_curr
            x_hist += x
            err = la.norm(x-xtru)
            err_hist += err

    return x

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
def conjugate_gradient_ideal(A, b, \
                            tol=0.001, x = None, \
                            numIter = 500, full_output=False \
                            ):
    """
    For SYMMETRIC, POSITIVE-DEFINITE matrices.
    https://www.cs.cmu.edu/~quake-papers/painless-conjugate-gradient.pdf (p. 32)

    Tested on a handful of small (~50x50 - 500x500 matrices) w/ various
    condition numbers. Behaviour is as expected - systems with higher
    condition numbers take longer to solve accurately.

    Returns:
        If not full_output: just the optimal x.
        If full_output: optimal x, num iterations taken, success, residuals plot.
    """
    #tol *= la.norm(A)

    m, n = len(A), len(A.T)

    if x is None:
        x = np.zeros(n)

    # d: first search direction (same as initial residual)
    d = b - np.dot(A, x) # d(0) = r(0) = b - Ax(0)
    r = d                # from eq. (45)

    if full_output:
        resids = []

    for i in range(numIter):
        if full_output:
            resids.append(norm_dif(x, A, b))

        # if 0:
        #     print(('r(%d): ' + str(r)) % i)
        #     recalc_r = b - np.dot(A, x)
        #     print('recalc: ' + str(recalc_r))
        #     print('resid dif: %f' % la.norm(r - recalc_r))


        a = np.dot(r.T, r) / np.dot(d.T, np.dot(A, d)) # eq. (46)

        x += a * d

        new_r = r - (a * np.dot(A, d)) # calculate new residual (A-orthogonal to
                                       # previous except d)      (eq. 47)

        beta = np.dot(new_r.T, new_r) / np.dot(r.T, r) # eq. (48)

        d = new_r + beta * d
        r = new_r

        if la.norm(b - np.dot(A, x)) < tol:
            print('CG: Close enough at iter %d' % i)
            if full_output:
                return x, i, True, resids
            else:
                return x

    print('CG: Max iteration reached (%d)' % numIter)
    if full_output:
        return x, numIter, False, resids
    else:
        return x


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
        return None
    else:
        print('Spectral radius of B: %f' % spec_rad)

    ## iterations
    x = x0
    for i in range(maxiter):
        x = np.dot(B,x) + z
        #print(la.norm(np.dot(A,x)-b))
        if la.norm(np.dot(A,x)-b) <= tol:
            break

    return x

def iter_refinement(A, b, tol=0.001, numIter=500, x=None, full_output=False):
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
    if x is None:
        x = np.zeros(n)

    if full_output:
        resids = []

    for i in range(numIter):
        #print('Iter %d' % i)
        if full_output:
            resids.append(norm_dif(x, A, b))

        # Compute the residual r
        r = b - np.dot(A, x)

        # Solve the system (Ad = r) for d
        result = scopt.minimize(fun=norm_dif, x0=np.random.randn(m), \
                                args=(A, r), method='CG')
        d, success, msg = result.x, result.success, result.message
        # TODO: find out which method is best/quickest to solve this

        x += d


        if la.norm(b - np.dot(A, x)) < tol:
            print('IR: Close enough at iter %d' % i)
            if full_output:
                return x, i, True, resids
            else:
                return x

    print('IR: Max iteration reached (%d)' % numIter)
    if full_output:
        return x, numIter, False, resids
    else:
        return x

def continuation():
    pass

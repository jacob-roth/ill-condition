import numpy as np
import numpy.linalg as la
import scipy
import scipy.sparse as sps
import scipy.sparse.linalg as spsla
import matplotlib.pyplot as plt
import optimize, time



def f_eval(A,b,x):
    """
    Objective function f(x) = (1/2)(x.T A x) - (b.T x)
    """
    f = 0.5*x.dot(A.dot(x)) - b.dot(x)
    return f

def btls(A, b, x, p, g, alpha=1, rho=0.1, c=0.9):
    """
    Backtracking line-search. Takes small/conservative
        steps.
    Does NOT guarantee the sufficient decrease condition
        (3.6a from Nocedal+Wright) is satisfied.

    Args:
        alpha: initial trial step size
        rho: decrement factor
        c: additional decrease factor
    """
    f_curr = f_eval(A,b,x)
    diff = 1.0
    i = 0
    while diff > 0:
        x_proposed = x + alpha*np.copy(p)
        x_proposed = x_proposed.reshape(len(x), )
        f_proposed = f_eval(A=A,b=b,x=x_proposed)
        f_compare = np.copy(f_curr) + c*alpha*g.dot(p)
        diff = f_proposed - f_compare
        i += 1
        alpha *= rho
        if alpha < 10**-16:
            print("alpha: machine precision reached")
            break
    return alpha

def wolfe(a, c1, c2, A, b, x, x_new, p, gr, gr_new):
    """
    Determines whether step size 'a' satisfies Wolfe conditions (not strong).

    Args:
             a:     Step size.
        c1, c2:     Constants from (0,1).
          A, b:     From Ax=b.
             x:     Current estimate of optimal x.
         x_new:     Next (prospective) x.
             p:     Current search direction.
            gr:     Current gradient (Ax - b).
        gr_new:     Gradient at (prospective) next x.
    """
    # condition 1
    lhs = la.norm( b - A.dot(x_new) )
    rhs = la.norm(b - A.dot(x)) + c1*a*np.inner(p.T, gr)

    if lhs > rhs: return False

    # condition 2
    lhs = -np.inner(p.T, gr_new)
    rhs = -c2*np.inner(p.T, gr)

    return lhs <= rhs

def bfgs(A, b, H=None, B=1.0, tol=10**-5, max_iter=500, x_true=None):
    """
    Page 140/Algorithm 6.1 in Nocedal and Wright.
    Also see the Implementation section on pages 142-143.

    Algorithm currently makes all elements of x NEGATIVE, even though
        the elements of x_true are all positive/zeros.
    """
    # =======================================================
    n = A.shape[0]          # A is symmetric (n x n)
    if sps.issparse(A):
        iden = sps.eye
    else:
        iden = np.identity

    # Initialize H as BI
    if H is None:
        H = B * iden(n)     # inverse Hessian approximation H0

    # =======================================================

    k = 0
    x = np.zeros(n)
    exes = [x]
    if x_true is not None:
        x_difs = [la.norm(x_true - x)]

    start_time = time.time()

    gr = A.dot(x) - b           # gradient
    gr_norm = la.norm(gr)
    residuals = [(gr_norm, time.time() - start_time)] # residual = -gradient
    # OPTIMIZED
    p = np.array(-H.dot(gr)).reshape(n, )

    while gr_norm > tol:
        # NON-OPTIMIZED
        # p = np.array(-H.dot(gr)).reshape(n, )   # search direction (6.18)

        # ===================================================
        # TODO: Best way to det. step size
        # TODO: DAMPED BFGS (for when curvature doesn't change much)
        Ap = A.dot(p)
        a = (np.inner(b, p) - np.inner(x, Ap)) / (np.inner(p, Ap))
        print('step size at %d: %f' % (k, a))

        # ===================================================
        # Then update x, calculate new gradient
        x_new = x + a*p
        gr_new = A.dot(x_new) - b
        gr_norm = la.norm(gr_new)

        residuals.append((gr_norm, time.time() - start_time))
        if x_true is not None:
            x_difs.append(la.norm(x_true - x_new))

        # ===================================================
        # Calculate x-step, gradient-change
        s = x_new - x
        y = gr_new - gr
        # ===================================================
        # Update your inverse Hessian approximation
        # COMPUTE Hk+1 BY MEANS OF (6.17)
        rho = 1.0 / np.inner(y.T, s)    # <== (6.14)

        # NON-OPTIMIZED
        # H = ( iden(n) -rho*np.outer(s, y.T) ).dot( H.dot( iden(n) - rho*np.outer(y, s.T) ) )
        # H += rho * np.outer(s, s.T)

        # OPTIMIZED
        Hy = H.dot(y)
        #print(Hy.shape, type(Hy))
        Hy = np.array(Hy).reshape(n,)
        yHy = y.dot(Hy)
        HysT = np.outer(Hy,s)
        rssT = rho*np.outer(s,s)

        H = H - rho*HysT - rho*HysT.T + rho*yHy*rssT + rssT

        # ===================================================
        # Then calculate your new search direction
        p = -H.dot(gr_new)
        p = np.array(p).reshape(n,)






        # ===================================================
        k += 1
        x, gr = x_new, gr_new
        exes.append(x)
        if k >= max_iter:
            break

    if x_true is None:
        return x, k, residuals, exes
    else:
        return x, k, residuals, exes, x_difs

class BFGSSolver(optimize.Solver):
    """
    Unfinished
    """

    def __str__(self):
        l1 = 'BFGS Solver\n'
        if self.A is None:
            l2 = 'A: None; '
        else:
            l2 = 'A: %d x %d; ' % (self.A.shape[0], self.A.shape[1])
        if self.b is None:
            l2 += 'b: None\n'
        else:
            l2 += 'b: %d x %d\n' % (len(self.b), len(self.b.T))
        if self.full_output:
            l3 = 'full_output: True'
        else:
            l3 = 'full_output: False'
        return l1+l2+l3

    def _check_ready(self):
        """
        Ensure A is square, dimensions line up w/ b.

        """

        assert self.A.shape[0] == self.A.shape[1]
        assert b.shape == (A.shape[0], )


    def _full(self, tol, x, max_iter, x_true, **kwargs):
        n = self.A.shape[0]          # A is symmetric (n x n)
        if sps.issparse(self.A):
            iden = sps.eye
        else:
            iden = np.identity

        if 'H' not in kwargs:
            if 'B' not in kwargs:
                B = 1.0

            H = B * iden(n) # inverse Hessian approximation

        k = 0



if __name__ == "__main__":

    X = sps.random(m=100, n=100, density=0.02)
    X = X.T.dot(X)
    f_true = np.array([50 if 40<=i and i<60 else 0 for i in range(100)])
    g = X.dot(f_true)

    print('Init resid err: %f' % la.norm(g - X.dot(np.zeros(100))))
    fopt, n_iter, residuals, exes = bfgs(A=X, b=g, B=2.0)
    print('Final resid err: %f' % la.norm(g - X.dot(fopt)))
    print('Took %d iter' % n_iter)

    plt.plot([t for n,t in residuals], [n for n,t in residuals], marker='o')
    plt.title('RESIDUALS')
    plt.yscale('log')
    plt.show()

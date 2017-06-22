import numpy as np
import numpy.linalg as la
import matplotlib.pyplot as plt
import optimize, visual

def mat_from_cond(cond_num, m=50, n=50, min_sing=None):
    """
    Generates an (m x n) matrix with the specified condition number. Use this
    to get a matrix with large (by most standards), decaying singular values.

    Args:
        (int)   cond_num:   Desired condition number.
        (int)          m:   Desired number of rows.
        (int)          n:   Desired number of columns.
        (float) min_sing:   Desired minimum singular value. Max singular value
                                will equal (cond_num * min_sing).

    Returns:
        Singular values of returned matrix will usually be large (depending
        on the supplied cond_num and min_sing, but usually the max >> 1).
        If you leave min_sing==None, it returns a positive-definite matrix.
        If min_sing < 0, it returns a negative-definite matrix.
    """
    if cond_num < 1:
        raise la.linAlgError('Condition number must be greater than or equal to 1')

    if min_sing == None:
        min_sing = abs(np.random.randn())

    max_sing = min_sing * float(cond_num)
    s = np.array(sorted([np.random.uniform(low=min_sing, high=max_sing) for _ in range(min(m,n)-2)] + [min_sing, max_sing], reverse=True))

    A = np.random.randn(m, n)
    u,_,v = la.svd(A, full_matrices=False)

    # Sparse? instead of np.diag(s)
    return np.dot(u, np.dot(np.diag(s), v))

def small_sing_vals(cond_num, m=50, n=50, max_sing=0.8):
    """
    Use to generate a matrix whose singular values all have magnitude less than
    one.

    NEED TO TEST THOROUGHLY.
    """
    if abs(max_sing) >= 1:
        print('Spectral radius of this matrix will have magnitude >= 1. Are you sure?')

    min_sing = max_sing / float(cond_num)
    s = np.array(sorted([np.random.uniform(low=min_sing, high=max_sing) for _ in range(min(m,n)-2)] + [min_sing, max_sing], reverse=True))

    A = np.random.randn(m, n)
    u,_,v = la.svd(A, full_matrices=False)

    # Sparse? instead of np.diag(s)
    return np.dot(u, np.dot(np.diag(s), v))

def psd_with_cond(cond_num, n=50, min_sing=None):
    """
    Generates a square matrix with specified condition number. Use this
    to get a matrix with large (by most standards), decaying singular values.

    Args:
        (int)   cond_num:   Desired condition number.
        (int)          n:   Desired number of columns and columns.
        (float) min_sing:   Desired minimum singular value. Max singular value
                                will equal (cond_num * min_sing).

    Returns:
        Singular values of returned matrix will usually be large (depending
        on the supplied cond_num and min_sing, but usually the max >> 1).
        If you leave min_sing==None, it returns a positive-definite matrix.
        If min_sing < 0, it returns a negative-definite matrix.
    """
    if min_sing == None:
        min_sing = abs(np.random.randn())

    max_sing = min_sing * float(np.sqrt(cond_num))
    s = np.array(sorted([np.random.uniform(low=min_sing, high=max_sing) for _ in range(n-2)] + [min_sing, max_sing], reverse=True))

    A = np.random.randn(n, n)
    u,_,v = la.svd(A, full_matrices=False)

    B = np.dot(u, np.dot(np.diag(s), v))
    return np.dot(B.T,B)

def ghetto_command_line():
    """
    Unfinished
    """
    num_mem = 100 # number of past commands to remember
    past_commands = []
    while True:
        try:
            sys.stdout.write('>>> ')
            inp = raw_input()
            if inp=='continue':
                break
            else:
                past_commands.append(inp)
                exec(inp)
        except KeyboardInterrupt:
            print('')
            break
        except BaseException:
            traceback.print_exc()

def scratch():
    """
    Visual GD.
    """
    A = psd_with_cond(cond_num=1000,n=2)
    x_true = np.random.randn(2)
    b = np.dot(A,x_true)
    evals,evecs = la.eig(A)
    #print('eigenvalues are: %s' % evals)

    x_opt = optimize.gradient_descent(A,b, x=np.array([2.0,2.0]))
    path = visual.gd_path(A, b, x=np.array([2.0,2.0]))
    #print(path[0])
    span = np.sqrt((path[0][0] - x_opt[0])**2 + (path[0][1] - x_opt[1])**2)
    # print(la.norm(x_true-x_opt))

    num = 100
    # x1 = x2 = np.linspace(-evals[1], evals[0], num)
    x1 = x2 = np.linspace(-span, span, num)
    x1v, x2v = np.meshgrid(x1, x2, indexing='ij', sparse=False)
    hv = np.zeros([num,num])

    for i in range(len(x1)):
        for j in range(len(x2)):
            # hv[i,j] = la.norm(np.dot(A,[x1v[i,j],x2v[i,j]])-b)
            xx = np.array([x1v[i,j],x2v[i,j]])
            hv[i,j] = np.dot(xx.T,np.dot(A,xx))-np.dot(b.T,xx)

    #print(hv)
    fig = plt.figure(1)
    ax = fig.gca()
    # ax.contour(x1v, x2v, hv,50)
    ll = np.linspace(0.0000000001,4,20)
    ll = 10**ll
    cs = ax.contour(x1v, x2v, hv,levels=ll)
    plt.clabel(cs)
    plt.axis('equal')
    plt.plot([p[0] for p in path], [p[1] for p in path], marker='o')
    plt.plot(x_true[0], x_true[1], marker='D', markersize=25) # TRUE POINT
    plt.plot(path[0][0], path[0][1], marker='x', markersize=25) # STARTING POINT
    print('num iter: %d' % len(path))
    plt.show()

# X68000 MicroPython + ulab: capability limits check (stage 2)
# ASCII only. No large allocations. Use after ulab_capability_check.py.
# PASS = expected result confirmed
# LIMIT = optional feature unavailable or rejects this case
# FAIL = wrong result, or unexpected error in a required test
# INFO = observation (view/copy) only, not a compatibility guarantee

from ulab import numpy as np

TOL = 0.0001
count_pass = 0
count_limit = 0
count_fail = 0
count_info = 0


def nearly(a, b):
    return abs(a - b) <= TOL


def values(a):
    shape = a.shape
    if len(shape) == 1:
        return [a[i] for i in range(shape[0])]
    if len(shape) == 2:
        return [a[i, j] for i in range(shape[0]) for j in range(shape[1])]
    raise ValueError("Only 1D and 2D are handled by this checker")


def expect(a, expected, shape=None):
    if shape is not None and a.shape != shape:
        raise AssertionError("shape: got %s, expected %s" % (a.shape, shape))
    got = values(a)
    if len(got) != len(expected):
        raise AssertionError("length: got %d, expected %d" % (len(got), len(expected)))
    for i in range(len(expected)):
        if not nearly(got[i], expected[i]):
            raise AssertionError("item %d: got %s, expected %s" % (i, got[i], expected[i]))
    return "shape=%s values=%s" % (a.shape, got)


def run(name, func, optional=False, info=False):
    global count_pass, count_limit, count_fail, count_info
    print("\n---", name, "---")
    try:
        note = func()
        if info:
            count_info += 1
            print("INFO:", note)
        else:
            count_pass += 1
            print("PASS:", note)
    except AssertionError as e:
        count_fail += 1
        print("FAIL (wrong value):", e)
    except Exception as e:
        if optional:
            count_limit += 1
            print("LIMIT/UNSUPPORTED:", type(e).__name__, e)
        else:
            count_fail += 1
            print("FAIL (unexpected error):", type(e).__name__, e)


def real2():
    return np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float)


def check_reshape_view():
    a = real2()
    b = a.reshape((3, 2))
    b[0, 0] = 91.0
    return "source[0,0]=%s ; %s" % (a[0, 0], "VIEW" if nearly(a[0, 0], 91) else "COPY")


def check_transpose_view():
    a = real2()
    b = a.T
    b[0, 1] = 92.0
    return "source[1,0]=%s ; %s" % (a[1, 0], "VIEW" if nearly(a[1, 0], 92) else "COPY")


def check_slice_view():
    a = real2()
    b = a[:, 1]
    b[0] = 93.0
    return "source[0,1]=%s ; %s" % (a[0, 1], "VIEW" if nearly(a[0, 1], 93) else "COPY")


def check_flatten_copy():
    a = real2()
    b = a.flatten()
    b[0] = 94.0
    if not nearly(a[0, 0], 1.0):
        raise AssertionError("flatten changed source: %s" % a[0, 0])
    return "source unchanged, copy[0]=%s" % b[0]


def check_flatten_transpose():
    base = real2()
    a = base.T
    c = a.flatten(order='C')
    f = a.flatten(order='F')
    return "C: %s ; F: %s" % (expect(c, [1, 4, 2, 5, 3, 6], (6,)),
                                  expect(f, [1, 2, 3, 4, 5, 6], (6,)))


def check_flatten_slice():
    base = real2()
    a = base[:, 1:]
    return expect(a.flatten(), [2, 3, 5, 6], (4,))


def check_reshape_noncontiguous():
    base = real2()
    a = base.T
    b = a.reshape((6,))
    return expect(b, [1, 4, 2, 5, 3, 6], (6,))


def check_bad_reshape():
    a = real2()
    try:
        a.reshape((4, 2))
    except Exception as e:
        return "correctly rejected: %s" % type(e).__name__
    raise AssertionError("reshape allowed 6 elements -> 8 elements")


def check_3d_array():
    a = np.zeros((2, 2, 2))
    return "3D array accepted: shape=%s" % (a.shape,)


def check_1d_matmul():
    a = np.array([1.0, 2.0], dtype=np.float)
    b = np.array([[3.0, 4.0], [5.0, 6.0]], dtype=np.float)
    result = a @ b
    return expect(result, [13.0, 16.0], (2,))


def check_matmul_wrong_shape():
    a = real2()
    b = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float)
    try:
        _ = a @ b
    except Exception as e:
        return "correctly rejected: %s" % type(e).__name__
    raise AssertionError("matmul allowed (2,3) @ (2,2)")


def check_matmul_int16():
    a = np.array([[1, 2], [3, 4]], dtype=np.int16)
    b = np.array([[5, 6], [7, 8]], dtype=np.int16)
    return expect(a @ b, [19, 22, 43, 50], (2, 2))


def check_repeat_axis():
    a = real2()
    b = a.repeat(2, axis=0)
    return expect(b, [1, 2, 3, 1, 2, 3, 4, 5, 6, 4, 5, 6], (4, 3))


def check_complex_arithmetic():
    a = np.array([1+2j, 3+4j], dtype=np.complex)
    b = np.array([2-1j, 1+1j], dtype=np.complex)
    add = a + b
    mul = a * b
    return "add: %s ; multiply: %s" % (expect(add, [3+1j, 4+5j], (2,)),
                                           expect(mul, [4+3j, -1+7j], (2,)))


def check_complex_flatten():
    a = np.array([[1+2j, 3+4j], [5+6j, 7+8j]], dtype=np.complex)
    b = a.flatten()
    return expect(b, [1+2j, 3+4j, 5+6j, 7+8j], (4,))


def check_linalg_det():
    a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float)
    got = np.linalg.det(a)
    if not nearly(got, -2.0):
        raise AssertionError("det = %s (expected -2)" % got)
    return "det = %s" % got


def check_linalg_inv():
    a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float)
    return expect(np.linalg.inv(a), [-2.0, 1.0, 1.5, -0.5], (2, 2))


def check_linalg_norm():
    a = np.array([3.0, 4.0], dtype=np.float)
    got = np.linalg.norm(a)
    if not nearly(got, 5.0):
        raise AssertionError("norm = %s (expected 5)" % got)
    return "norm = %s" % got


def check_convolve():
    a = np.array([1.0, 2.0, 3.0], dtype=np.float)
    b = np.array([1.0, 1.0], dtype=np.float)
    return expect(np.convolve(a, b), [1.0, 3.0, 5.0, 3.0], (4,))


def check_arange():
    return expect(np.arange(5, dtype=np.int16), [0, 1, 2, 3, 4], (5,))


def check_linspace():
    return expect(np.linspace(0.0, 1.0, 5, dtype=np.float),
                  [0.0, 0.25, 0.5, 0.75, 1.0], (5,))


def check_random_module():
    return "np.random available=%s; functions=%s" % (hasattr(np, 'random'),
                                                        dir(np.random))


print("=== X68000 ulab limits check (stage 2) ===")
try:
    import ulab
    print("ulab version:", ulab.__version__)
except Exception:
    print("ulab version: unknown")

run("reshape: view or copy", check_reshape_view, info=True)
run("transpose: view or copy", check_transpose_view, info=True)
run("slice: view or copy", check_slice_view, info=True)
run("flatten returns independent copy", check_flatten_copy)
run("flatten of transpose, C and F order", check_flatten_transpose)
run("flatten of sliced array", check_flatten_slice)
run("reshape noncontiguous transpose", check_reshape_noncontiguous, optional=True)
run("reject reshape with wrong element count", check_bad_reshape)
run("3D array support", check_3d_array, optional=True)
run("1D @ 2D support", check_1d_matmul, optional=True)
run("reject incompatible matmul shapes", check_matmul_wrong_shape)
run("int16 @ int16 support", check_matmul_int16, optional=True)
run("repeat(axis=0) support", check_repeat_axis, optional=True)
run("complex elementwise arithmetic", check_complex_arithmetic, optional=True)
run("complex flatten", check_complex_flatten, optional=True)
run("linalg.det", check_linalg_det, optional=True)
run("linalg.inv", check_linalg_inv, optional=True)
run("linalg.norm", check_linalg_norm, optional=True)
run("np.convolve", check_convolve, optional=True)
run("np.arange explicit dtype", check_arange, optional=True)
run("np.linspace explicit dtype", check_linspace, optional=True)
run("np.random API listing", check_random_module, optional=True, info=True)

print("\n=== Summary ===")
print("PASS:", count_pass, "LIMIT:", count_limit,
      "FAIL:", count_fail, "INFO:", count_info)
print("LIMIT does not mean a bug. FAIL needs investigation.")
print("A passing sample does not guarantee general compatibility.")

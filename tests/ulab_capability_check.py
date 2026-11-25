# X68000 MicroPython + ulab capability check
# ASCII-only source for easier use on Human68k.
# Each test runs independently; failures do not stop later tests.
# Outputs should be checked for numerical correctness too.

import ulab
from ulab import numpy as np

print("=== X68000 ulab capability check ===")
try:
    print("ulab version:", ulab.__version__)
except Exception as e:
    print("ulab version: unknown", e)

ok_count = 0
fail_count = 0

def check(name, func):
    global ok_count, fail_count
    print("\n---", name, "---")
    try:
        func()
        print("RESULT: executed (verify values above)")
        ok_count += 1
    except Exception as e:
        print("RESULT: unavailable/error:", type(e), e)
        fail_count += 1


def real_array():
    return np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float)


def test_basic():
    a = real_array()
    print("array:", a)
    print("shape:", a.shape, "ndim:", a.ndim, "size:", a.size)
    print("strides:", a.strides)


def test_math():
    a = np.array([1.0, 2.0, 3.0], dtype=np.float)
    print("a + 10:", a + 10)
    print("a * 2 - 1:", a * 2 - 1)
    print("sum/mean/min/max:", np.sum(a), np.mean(a), np.min(a), np.max(a))


def test_slice_broadcast():
    a = real_array()
    print("column 1:", a[:, 1])
    print("broadcast:", a + np.array([10.0, 20.0, 30.0], dtype=np.float))


def test_transpose():
    a = real_array()
    print("a.T:", a.T)
    print("a.T shape/strides:", a.T.shape, a.T.strides)


def test_reshape():
    a = real_array()
    b = a.reshape((3, 2))
    print("reshape (3,2):", b)
    print("shape:", b.shape)


def test_reshape_infer():
    a = real_array()
    print("reshape (-1,2):", a.reshape((-1, 2)))


def test_flatten_c():
    a = real_array()
    f = a.flatten()
    print("flatten C:", f)
    print("shape:", f.shape)


def test_flatten_f():
    a = real_array()
    f = a.flatten(order='F')
    print("flatten F (expect 1,4,2,5,3,6):", f)


def test_repeat_scalar():
    a = np.array([1.0, 2.0, 3.0], dtype=np.float)
    print("repeat(2):", a.repeat(2))


def test_repeat_vector():
    a = np.array([1.0, 2.0, 3.0], dtype=np.float)
    print("repeat([1,3,2]):", a.repeat([1, 3, 2]))


def matrices():
    a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float)
    b = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float)
    return a, b


def test_matmul():
    a, b = matrices()
    print("A @ B (expect [[19,22],[43,50]]):", a @ b)


def test_dot():
    a, b = matrices()
    print("dot(A,B) (expect [[19,22],[43,50]]):", np.dot(a, b))


def test_fft():
    from ulab import fft
    x = np.array([1.0, 0.0, -1.0, 0.0], dtype=np.float)
    print("fft([1,0,-1,0]) (expect 0,2,0,2):", fft.fft(x))


def test_complex_explicit():
    a = np.array([1+2j, 3+4j], dtype=np.complex)
    print("complex array:", a)
    print("real:", a.real, "imag:", a.imag)


def test_complex_auto():
    a = np.array([1+2j, 3+4j])
    print("complex inferred dtype:", a)


def test_complex_abs():
    a = np.array([1+2j, 3+4j], dtype=np.complex)
    print("abs complex (expect sqrt(5),5):", np.abs(a))


def test_optional_modules():
    print("numpy.linalg present:", hasattr(np, 'linalg'))
    print("numpy.random present:", hasattr(np, 'random'))
    print("numpy.convolve present:", hasattr(np, 'convolve'))
    print("numpy.arange present:", hasattr(np, 'arange'))
    print("numpy.linspace present:", hasattr(np, 'linspace'))


check("basic ndarray", test_basic)
check("element-wise and reductions", test_math)
check("slice and broadcasting", test_slice_broadcast)
check("transpose", test_transpose)
check("reshape", test_reshape)
check("reshape -1", test_reshape_infer)
check("flatten C-order", test_flatten_c)
check("flatten F-order", test_flatten_f)
check("repeat scalar", test_repeat_scalar)
check("repeat per element", test_repeat_vector)
check("matmul @", test_matmul)
check("numpy.dot", test_dot)
check("FFT", test_fft)
check("complex explicit", test_complex_explicit)
check("complex auto inference", test_complex_auto)
check("complex abs", test_complex_abs)
check("module presence only", test_optional_modules)
print("\n=== Summary ===")
print("Executed:", ok_count, "Error:", fail_count)
print("Execution alone is not proof of correct numerical values.")

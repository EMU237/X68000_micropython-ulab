[日本語](README.md)
# micropython-x68k-ulab: Custom `ulab` Port & Math Art Benchmarks for X68000 (060turbo)

A custom build of MicroPython for Sharp X68000 (`micropython-x68k`) with `ulab` (a fast NumPy / FFT-compatible numerical computing library) integrated via custom patches, along with mathematical art demos and CPU/FPU benchmark records.

---

## 1. Overview & Features

* **Target Platform**: Sharp X68000 / X68030 + 060turbo (MC68060, Cache ON)
  * **XM6 TypeG**: 50 MHz (actual hardware speed) and 200 MHz (50 MHz × 4x overclock)
  * **XEiJ**: MC68060 mode
* **OS / Runtime**: Human68k + `micropython-x68k` (requires 4 MB+ RAM)
* **Integrated Module**: `ulab` (`ulab.numpy`, `ulab.fft`)

---

## 2. Applying the Patch & Building

### Applying `ulab_patch.diff`
Clone the base `micropython-x68k` repository and apply `ulab_patch.diff`:

```bash
git clone https://github.com/yunkya2/micropython-x68k.git
cd micropython-x68k
patch -p1 < /path/to/ulab_patch.diff
```

### Enabling Hardware FPU (`-m68060` Optimization)
By default, building for `-m68000` uses software floating-point emulation (soft-float) for compatibility across all X68000 models. However, since `micropython-x68k` requires at least 4 MB of RAM, targeting environments equipped with an FPU / accelerator (`-m68060`) unlocks the MC68060's built-in hardware FPU and dramatically boosts performance.

Edit `ports/x68k/Makefile`:

```makefile
M68K_CPU ?= 68060
CFLAGS += -m$(M68K_CPU)
LDFLAGS += -m$(M68K_CPU)
```

Then build as usual (`make -C ports/x68k`).

---

## 3. Supported Features & Memory Limits (`test_ulab_env.py`)

Verified capabilities and constraints from the comprehensive environment test script (`test_ulab_env.py`):

* **Supported Operations**:
  * Basic `ndarray` creation (`array`, `zeros`, `ones`, `arange`, `linspace`)
  * `reshape`, transpose (`.T`), slicing (`a[2:8]`, `a[::2]`)
  * Element-wise math & trigonometry (`sin`, `cos`, `sqrt`, arithmetic operators)
  * Reductions (`sum`, `min`, `max`, `mean`)
  * Matrix multiplication (`np.dot`)
  * Fast Fourier Transform (`ulab.fft.fft`)
  * Array methods: `a.repeat()`, `a.flatten()`
* **Implementation Notes**:
  * `np.flatten(a)` (module-level function) is not implemented; use the method form `a.flatten()` instead.
* **2D Array Memory Limit**:
  * `np.zeros((256, 256))` (`float32`, 256 KB) succeeds.
  * `np.zeros((512, 512))` (`float32`, 1 MB) triggers `MemoryError`.
  * *Tip*: When rendering 512×512 graphics (such as the Mandelbrot set), compute row-by-row using 1D arrays of length 512 to stay well within heap limits.

---

## 4. Benchmark Results

Execution times for 512×512 graphics rendering (16-color GVRAM mode) across different emulator settings and compiler flags (in `ms`):

| Demo Program | XEiJ (`-m68000`) | XM6 200MHz (`-m68000`) | XM6 200MHz (`-m68060` FPU) | XM6 50MHz (`-m68060` FPU) | Workload Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Gilbreath's Conjecture Fractal** | `18,820 ms` | `2,470 ms` | **`1,710 ms`** | **`6,860 ms`** | Difference pyramid of 250 primes (`ulab` slice subtraction) |
| **2. Sacks Spiral** | `28,240 ms` | `2,540 ms` | **`990 ms`** | **`3,960 ms`** | Primes up to 22,000 (vectorized `sqrt`, `sin`, `cos`) |
| **3. Gilbreath Waveform FFT** | `3,980 ms` | `480 ms`<br>*(FFT: 60 ms)* | **`330 ms`**<br>*(FFT: 30 ms)* | **`1,280 ms`**<br>*(FFT: 120 ms)* | 256-point difference waveform + `ulab.fft` spectrum plot |
| **4. Mandelbrot Set (512×512)** | `2,295,970 ms`<br>*(~38m 16s)* | `152,900 ms`<br>*(~2m 33s)* | **`44,610 ms`**<br>*(~44.6s)* | **`179,480 ms`**<br>*(~2m 59s)* | 512×512 pixels, max 32 iterations (row-by-row vector math) |
| **5. 3D Wireframe Rotation** | — | — | **~`5.6–6.1 FPS`** | — | Torus (384 vertices, 768 edges), `np.dot` 3D rotation + double buffering |

### Key Findings
* **Hardware FPU Acceleration**: Switching from `-m68000` to `-m68060` achieved a **3.4x speedup** on the Mandelbrot set and a **2.6x speedup** on the Sacks spiral, bringing Sacks spiral rendering under 1 second at 200 MHz.
* **Linear Clock Scaling**: Comparing 50 MHz (real 060turbo speed) and 200 MHz (4x speed) shows near-perfect 4.0x scaling across all benchmarks (`3,960 ms` vs `990 ms` = 4.00x; `179,480 ms` vs `44,610 ms` = 4.02x), demonstrating that CPU/FPU execution and cache utilization are free of I/O bottlenecks.

---

## 5. Demo Scripts (`examples/`)

### 5.1 `gilbreath_fractal.py` — Gilbreath's Conjecture Fractal Triangle
Computes successive absolute differences of prime numbers using `ulab` slice operations (`row[1:] - row[:-1]`), revealing self-similar triangular zero-regions alongside the unbroken leftmost diagonal of `1`s.

```python
import x68k
import time
from ulab import numpy as np

x68k.crtmod(4, True)
g = x68k.GVRam(0)
x68k.vpage(1)
g.fill(0, 0, 511, 511, 0)

def get_primes_array(n):
    primes = []
    num = 2
    while len(primes) < n:
        is_p = True
        for p in primes:
            if p * p > num:
                break
            if num % p == 0:
                is_p = False
                break
        if is_p:
            primes.append(num)
        num += 1
    return np.array(primes, dtype=np.int16)

t0 = time.ticks_ms()

n_primes = 250
row = get_primes_array(n_primes)

for r_idx in range(n_primes):
    y = 10 + r_idx
    length = len(row)

    for c_idx in range(length):
        val = int(row[c_idx])
        if val == 0 and r_idx > 0:
            continue

        x = 6 + r_idx + c_idx * 2
        if r_idx == 0:
            col = 15
        elif c_idx == 0:
            col = 6
        else:
            col = ((val // 2) % 6) + 9
        g.pset(x, y, col)

    if length <= 1:
        break
    diff = row[1:] - row[:-1]
    row = np.sqrt(diff * diff)

t1 = time.ticks_ms()
print("GILBREATH_TIME:", time.ticks_diff(t1, t0), "ms")
```

---

### 5.2 `sacks_spiral.py` — Sacks Spiral (Vectorized)
Plots prime numbers along an Archimedean spiral ($r = \sqrt{n}$, $	heta = 2\pi\sqrt{n}$) using batch `ulab` vector operations (`np.sqrt`, `np.cos`, `np.sin`).

```python
import x68k
import math
import time
from ulab import numpy as np

x68k.crtmod(4, True)
g = x68k.GVRam(0)
x68k.vpage(1)
g.fill(0, 0, 511, 511, 0)

t0 = time.ticks_ms()

limit = 22000
sieve = bytearray(limit + 1)
primes = []
for i in range(2, limit + 1):
    if sieve[i] == 0:
        primes.append(i)
        for j in range(i * i, limit + 1, i):
            sieve[j] = 1

p_arr = np.array(primes, dtype=np.float)
r = np.sqrt(p_arr)
theta = (2.0 * math.pi) * r

scale = 1.6
xs = 256.0 + (r * scale) * np.cos(theta)
ys = 256.0 - (r * scale) * np.sin(theta)

for i in range(len(xs)):
    x = int(xs[i])
    y = int(ys[i])
    if 0 <= x < 512 and 0 <= y < 512:
        col = int(r[i] / 35.0) % 7 + 9
        g.pset(x, y, col)

t1 = time.ticks_ms()
print("SACKS_TIME:", time.ticks_diff(t1, t0), "ms")
```

---

### 5.3 `gilbreath_fft.py` — Frequency Analysis via `ulab.fft`
Treats the 1st and 16th difference rows of Gilbreath's triangle as 256-point signals and compares their frequency spectra using `ulab.fft.fft`.

```python
import x68k
import math
import time
from ulab import numpy as np
from ulab import fft

x68k.crtmod(4, True)
g = x68k.GVRam(0)
x68k.vpage(1)
g.fill(0, 0, 511, 511, 0)

t_total_start = time.ticks_ms()

N = 256
def get_primes_array(count):
    primes = []
    num = 2
    while len(primes) < count:
        is_p = True
        for p in primes:
            if p * p > num:
                break
            if num % p == 0:
                is_p = False
                break
        if is_p:
            primes.append(num)
        num += 1
    return np.array(primes, dtype=np.float)

row = get_primes_array(N + 1)
diff = row[1:] - row[:-1]
wave_row1 = np.sqrt(diff * diff)

row_deep = get_primes_array(N + 16)
for _ in range(16):
    d = row_deep[1:] - row_deep[:-1]
    row_deep = np.sqrt(d * d)
wave_row16 = row_deep

def compute_spectrum(signal):
    mean_val = float(np.sum(signal)) / len(signal)
    centered = signal - mean_val
    fft_res = fft.fft(centered)
    half = len(signal) // 2
    mag = np.zeros(half)
    for i in range(half):
        c = fft_res[i]
        mag[i] = math.sqrt(c.real * c.real + c.imag * c.imag) / len(signal)
    return mag

t_fft_start = time.ticks_ms()
spec_row1 = compute_spectrum(wave_row1)
spec_row16 = compute_spectrum(wave_row16)
t_fft_end = time.ticks_ms()

def draw_graph(signal, x_offset, width, y_offset, height, color):
    smin = float(np.min(signal))
    smax = float(np.max(signal))
    span = max(abs(smax - smin), 1e-6)

    ratio = (len(signal) - 1) / (width - 1)
    prev_x = x_offset
    prev_y = int(y_offset + height - ((signal[0] - smin) / span) * height)

    for dx in range(1, width):
        pos = dx * ratio
        i = int(pos)
        frac = pos - i
        if i >= len(signal) - 1:
            val = signal[len(signal) - 1]
        else:
            val = signal[i] * (1.0 - frac) + signal[i + 1] * frac

        x = x_offset + dx
        y = int(y_offset + height - ((val - smin) / span) * height)
        g.line(prev_x, prev_y, x, y, color)
        prev_x = x
        prev_y = y

g.line(0, 165, 511, 165, 8)
g.line(0, 330, 511, 330, 8)
g.line(256, 330, 256, 511, 8)

draw_graph(wave_row1, 10, 492, 15, 135, 14)
draw_graph(wave_row16, 10, 492, 180, 135, 12)
draw_graph(spec_row1, 10, 236, 345, 150, 11)
draw_graph(spec_row16, 266, 236, 345, 150, 6)

t_total_end = time.ticks_ms()

print("FFT_TIME:", time.ticks_diff(t_fft_end, t_fft_start), "ms")
print("TOTAL_TIME:", time.ticks_diff(t_total_end, t_total_start), "ms")
```

---

### 5.4 `mandelbrot_ulab.py` — 512×512 Mandelbrot Set
Computes the Mandelbrot set row-by-row using 1D `ulab` arrays (`width = 512`) and early-exit escape masks (`np.sum(mask) == 0`).

```python
import x68k
import time
from ulab import numpy as np

x68k.crtmod(4, True)
g = x68k.GVRam(0)
x68k.vpage(1)
g.fill(0, 0, 511, 511, 0)

t_start = time.ticks_ms()

WIDTH = 512
HEIGHT = 512
MAX_ITER = 32

X_MIN, X_MAX = -2.1, 0.7
Y_MIN, Y_MAX = -1.4, 1.4

cr = np.linspace(X_MIN, X_MAX, WIDTH)
ys = np.linspace(Y_MIN, Y_MAX, HEIGHT)

for y in range(HEIGHT):
    ci = float(ys[y])
    zr = np.zeros(WIDTH)
    zi = np.zeros(WIDTH)
    iters = np.zeros(WIDTH, dtype=np.int16)

    for i in range(MAX_ITER):
        zr2 = zr * zr
        zi2 = zi * zi
        mag2 = zr2 + zi2

        mask = (mag2 <= 4.0)
        if np.sum(mask) == 0:
            break

        iters = iters + mask
        new_zr = zr2 - zi2 + cr
        new_zi = 2.0 * zr * zi + ci
        zr = new_zr * mask
        zi = new_zi * mask

    for x in range(WIDTH):
        it = int(iters[x])
        if it < MAX_ITER:
            col = (it % 14) + 1
            g.pset(x, y, col)

t_end = time.ticks_ms()
print("MANDELBROT_TIME:", time.ticks_diff(t_end, t_start), "ms")
```

---

### 5.5 `wireframe_3d.py` — Real-Time 3D Wireframe Torus
Rotates a 384-vertex, 768-edge torus in real time using `np.dot` matrix multiplication and double-buffered GVRAM pages (`x68k.vpage`). Press any key (`x68k.iocs.b_keysns()`) to exit cleanly.

```python
import x68k
import math
import time
from ulab import numpy as np

x68k.crtmod(4, True)
g0 = x68k.GVRam(0)
g1 = x68k.GVRam(1)
g0.fill(0, 0, 511, 511, 0)
g1.fill(0, 0, 511, 511, 0)

R_MAJOR = 110.0
R_MINOR = 45.0
SEG_U = 24
SEG_V = 16

verts = []
edges = []

for i in range(SEG_U):
    u = 2.0 * math.pi * i / SEG_U
    cu, su = math.cos(u), math.sin(u)
    for j in range(SEG_V):
        v = 2.0 * math.pi * j / SEG_V
        cv, sv = math.cos(v), math.sin(v)

        x = (R_MAJOR + R_MINOR * cv) * cu
        y = (R_MAJOR + R_MINOR * cv) * su
        z = R_MINOR * sv
        verts.append([x, y, z])

        curr = i * SEG_V + j
        next_v = i * SEG_V + ((j + 1) % SEG_V)
        next_u = ((i + 1) % SEG_U) * SEG_V + j
        edges.append((curr, next_v))
        edges.append((curr, next_u))

V = np.array(verts, dtype=np.float)

def make_rotation_matrix(ax, ay, az):
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)

    r00 = cy * cz
    r01 = sx * sy * cz - cx * sz
    r02 = cx * sy * cz + sx * sz

    r10 = cy * sz
    r11 = sx * sy * sz + cx * cz
    r12 = cx * sy * sz - sx * cz

    r20 = -sy
    r21 = sx * cy
    r22 = cx * cy

    return np.array([
        [r00, r10, r20],
        [r01, r11, r21],
        [r02, r12, r22]
    ], dtype=np.float)

ax, ay, az = 0.0, 0.0, 0.0
FOV = 360.0
CAM_DIST = 340.0

page = 0
frame_count = 0
t_fps = time.ticks_ms()

print("3D Wireframe running... Press any key to stop.")

while True:
    if page == 0:
        g = g1
        show_vpage = 2
    else:
        g = g0
        show_vpage = 1

    g.fill(60, 60, 451, 451, 0)

    rot_mat = make_rotation_matrix(ax, ay, az)
    V_rot = np.dot(V, rot_mat)

    xs = V_rot[:, 0]
    ys = V_rot[:, 1]
    zs = V_rot[:, 2] + CAM_DIST

    scale = FOV / zs
    px = 256.0 + xs * scale
    py = 256.0 - ys * scale

    for idx1, idx2 in edges:
        z_val = float(zs[idx1])
        if z_val < CAM_DIST - 20.0:
            col = 15
        elif z_val < CAM_DIST + 20.0:
            col = 11
        else:
            col = 9

        g.line(int(px[idx1]), int(py[idx1]), int(px[idx2]), int(py[idx2]), col)

    x68k.vpage(show_vpage)
    page = 1 - page

    ax += 0.05
    ay += 0.07
    az += 0.03

    frame_count += 1
    if frame_count % 30 == 0:
        now = time.ticks_ms()
        dt = time.ticks_diff(now, t_fps)
        if dt > 0:
            print("FPS:", round(30000.0 / dt, 1))
        t_fps = now

    if x68k.iocs.b_keysns() != 0:
        x68k.iocs.b_keyinp()
        break

x68k.vpage(1)
print("Stopped.")
```

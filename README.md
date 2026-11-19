
# X68000 (060turbo) + MicroPython + カスタム `ulab` 数学アート＆ベンチマーク検証記録

X68000用 MicroPython（`micropython-x68k`）に自作パッチ（`ulab_patch.diff`）で `ulab`（NumPy / FFT 互換の高速数値計算ライブラリ）を組み込んだカスタムビルド環境において、各種数学アートの描画と MC68060 CPU / FPU ベンチマークを実施した記録です。

---

## 1. 検証環境

* **ターゲットマシン / エミュレータ**: X68030 + 060turbo（MC68060 / キャッシュON）
  * **XM6 TypeG**: 50MHz（実機等倍速）および 200MHz（50MHz × 4倍速）
  * **XEiJ**: MC68060 動作モード
* **ソフトウェア環境**: Human68k + `micropython-x68k`（`ulab` 導入カスタムビルド）
* **ビルド設定の比較**:
  * **汎用ビルド (`-m68000`)**: 全機種互換・ソフトウェア浮動小数点演算（soft-float）
  * **060最適化ビルド (`-m68060`)**: ハードウェア FPU 命令有効化

---

## 2. パッチ適用およびビルド手順

`micropython-x68k` のソースツリーに対して `ulab_patch.diff` を適用し、X68030 / 060turbo（RAM 4MB以上必須）向けに FPU を有効化してビルドする手順です。

```bash
# 1. パッチの適用
cd micropython-x68k
patch -p1 < ulab_patch.diff

# 2. Makefile の CPU 指定を 68060 に変更（ハードウェア FPU 有効化）
# ports/x68k/Makefile 内の該当箇所を以下のように設定:
#   M68K_CPU ?= 68060
#   CFLAGS += -m$(M68K_CPU)
#   LDFLAGS += -m$(M68K_CPU)

# 3. ビルド実行
cd ports/x68k
make clean
make
```

---

## 3. 動作確認済み `ulab` 機能とメモリ制限仕様

`test_ulab_env.py` による総合テストで判明した実装仕様と制限事項です。

* **サポートされている主な機能**:
  * 基本配列生成・操作: `np.array`, `np.zeros`, `np.ones`, `np.arange`, `np.linspace`, スライス (`a[2:8]`, `a[::2]`)
  * 形状変換: `reshape`, 転置 (`.T`), メソッド形式の `a.flatten()`, `a.repeat()`
  * 要素演算・数学関数: 四則演算, `np.sin`, `np.cos`, `np.sqrt`
  * リダクション・行列積: `np.sum`, `np.min`, `np.max`, `np.mean`, `np.dot`
  * 高速フーリエ変換: `from ulab import fft` / `fft.fft()`
* **制限事項・注意点**:
  * モジュール関数版の `np.flatten(a)` は未実装のため、メソッド形式の `a.flatten()` を使用します。
  * **2次元配列のメモリ上限**: `float32` 型の2次元配列は **`256 × 256`（256 KB）まで確保可能**、`512 × 512`（1 MB）で `MemoryError` となります。512×512 ドットの全画面計算を行う場合は、横1行（長さ 512）ずつのベクトル演算に分割します。

---

## 4. ベンチマーク結果一覧

それぞれのプログラムを 512×512 ドット（16色グラフィックVRAMモード）で計算・描画した際の処理時間（単位: `ms`）。

| プログラム名 | XEiJ (`-m68000`) | XM6 200MHz (`-m68000`) | XM6 200MHz (`-m68060` FPU) | XM6 50MHz (`-m68060` FPU) | 備考・計算内容 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. ギルブレス予想（三角形）** | `18,820 ms` | `2,470 ms` | **`1,710 ms`** | **`6,860 ms`** | 素数250個の差分ピラミッド（スライス演算） |
| **2. サックスの螺旋** | `28,240 ms` | `2,540 ms` | **`990 ms`** | **`3,960 ms`** | 22,000以下の素数（`sqrt`, `sin`, `cos` 一括計算） |
| **3. ギルブレス波形 FFT 解析** | `3,980 ms` | `480 ms`<br>*(FFT: 60 ms)* | **`330 ms`**<br>*(FFT: 30 ms)* | **`1,280 ms`**<br>*(FFT: 120 ms)* | 256点差分波形の生成 ＋ `ulab.fft` 解析・4画面描画 |
| **4. マンデルブロ集合** | `2,295,970 ms`<br>*(約38分16秒)* | `152,900 ms`<br>*(約2分33秒)* | **`44,610 ms`**<br>*(約44.6秒)* | **`179,480 ms`**<br>*(約2分59秒)* | 512×512ピクセル、最大反復回数 32 回 |
| **5. 3D ワイヤーフレーム回転** | — | — | **約 `5.6〜6.1 FPS`** | — | トーラス（384頂点・768辺）の `np.dot` 回転＋ダブルバッファ描画 |

### 考察

1. **ハードウェア FPU 有効化（`-m68060`）の劇的な効果**:
   `micropython-x68k` は実行に RAM 4MB 以上を要するため、増設メモリや上位機種の環境を前提として `-m68060` に振り切ることで MC68060 内蔵 FPU 命令が有効になり、**マンデルブロ集合で約 3.4 倍**、**サックスの螺旋で約 2.6 倍** の高速化を達成しました。
2. **動作クロックに対する理想的なスケーリング**:
   50MHz（実機等倍速）と 200MHz（4倍速）を比較すると、サックスの螺旋が **4.00 倍**、マンデルブロ集合が **4.02 倍**、ギルブレス予想が **4.01 倍** となり、クロック倍率にほぼ完全に比例しています。I/O ボトルネックが少なく、MC68060 の CPU / FPU とキャッシュ性能が `ulab` の配列演算によって最大限に引き出されています。

---

## 5. デモスクリプト一覧（`examples/`）

### 5.1 ギルブレス予想のフラクタル三角形（`gilbreath_fractal.py`）

素数の数列から隣り合う要素の差の絶対値を `row[1:] - row[:-1]` のスライス演算で反復計算し、内部に現れる「0の空白（逆三角形）」と網目模様、そして左端の斜めラインが常に「1」を保ち続ける様子を描画します。

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
<img width="826" height="651" alt="スクリーンショット 2026-11-19 200702" src="https://github.com/user-attachments/assets/bebb3790-58a8-4013-98a8-bdfb13c7bae5" />


---

### 5.2 サックスの螺旋（`sacks_spiral.py`）

アルキメデスの螺旋（$r = \sqrt{n}$, $	heta = 2\pi\sqrt{n}$）上に素数を配置し、二次多項式が描く放物線状の腕（アーム）を `ulab` のベクトル一括計算で描画します。

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
<img width="826" height="651" alt="スクリーンショット 2026-11-19 200728" src="https://github.com/user-attachments/assets/ebfef166-8611-4f77-8e77-5c96f040cb4c" />


---

### 5.3 ギルブレス波形の `ulab.fft` 周波数解析（`gilbreath_fft.py`）

1行目の差分波形（素数の間隔）と16行目の差分波形を `ulab.fft` で解析し、波形と周波数スペクトルを4画面に並べて描画します。

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

<img width="826" height="651" alt="スクリーンショット 2026-11-19 200801" src="https://github.com/user-attachments/assets/55f20656-b55f-458f-ad92-93dffe3a0f20" />

---

### 5.4 マンデルブロ集合（`mandelbrot_ulab.py`）

メモリ上限を考慮し、横1行（512ピクセル）単位の `ulab` ベクトル演算と早期発散マスクによって 512×512 ドットのマンデルブロ集合を描画します。

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
<img width="826" height="651" alt="スクリーンショット 2026-11-19 200801" src="https://github.com/user-attachments/assets/e9f9fdd8-a0e5-45bb-bf6b-a0c5dee4c825" />

---

### 5.5 3D ワイヤーフレーム リアルタイム回転（`wireframe_3d.py`）

384頂点・768辺のトーラスモデルに対し、3軸回転行列との積（`np.dot`）および透視投影をベクトル一括計算し、ダブルバッファリングでリアルタイム回転させます。任意のキー押下（`x68k.iocs.b_keysns()`）で安全に終了します。

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
            fps = 30000.0 / dt
            print("FPS:", round(fps, 1))
        t_fps = now

    if x68k.iocs.b_keysns() != 0:
        x68k.iocs.b_keyinp()
        break

x68k.vpage(1)
print("Stopped.")
<img width="826" height="651" alt="スクリーンショット 2026-11-19 201539" src="https://github.com/user-attachments/assets/23bf570f-4bc4-4973-9cd6-768e17ab87e5" />

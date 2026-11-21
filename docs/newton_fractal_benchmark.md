# X68000 MicroPython + ulab
## ニュートンフラクタル描画・性能検証記録

**実施日：2026年11月20日〜21日**

### 1. 検証目的

X68000向けMicroPythonに移植した `ulab` を使用し、ニュートンフラクタルの描画を通じて、浮動小数点演算と配列演算の動作および実行性能を確認する。

特に、FPUを備えた高速CPU環境と、FPUを持たないMC68000環境での動作を比較する。

また、長時間実行におけるMicroPythonの時間計測機能についても検証する。

### 2. 実行環境

| 項目 | 内容 |
|---|---|
| 対象機種 | X68000 |
| エミュレータ | XM6 |
| 言語処理系 | X68000向けMicroPython |
| 数値演算ライブラリ | ulab（移植パッチ適用） |
| 描画API | `x68k.GVRam` |
| 描画解像度 | 512 × 512 |
| 色数 | 16色 |
| 高速環境 | MC68060 / 200MHz、FPUあり |
| 低速環境 | MC68000 / 10MHz、FPUなし |
| 高速化機能 | XM6 TURBO（ノーウェイト実行） |

関連リポジトリ：

https://github.com/EMU237/X68000_micropython-ulab

### 3. 描画プログラム

ニュートン法によって複素平面上の各点を反復計算し、収束先と反復回数に応じて色分けする。

対象関数：

\[
f(z)=z^3-1
\]

ニュートン法の反復式：

\[
z_{n+1}=z_n-\frac{z_n^3-1}{3z_n^2}
\]

3つの収束先は以下の通り。

- \(1\)
- \(-\frac12+\frac{\sqrt3}{2}i\)
- \(-\frac12-\frac{\sqrt3}{2}i\)

描画条件：

| 項目 | 設定 |
|---|---|
| 描画範囲 | 実部・虚部ともに -2.0〜2.0 |
| 画像サイズ | 512 × 512ピクセル |
| 最大反復回数 | 32回 |
| 収束判定 | 距離の二乗が \(10^{-6}\) 未満 |
| 配列演算 | `ulab.numpy` |
| 描画方法 | 1ラインずつ計算、`GVRam.pset()` で描画 |

各ラインの計算にはulabの配列演算を使用し、最終的なピクセル描画は個別に実行する。

### 4. 実行結果

#### 4.1 MC68060 / 200MHz

計測値：

**189,400ms（3分9.4秒）**

512 × 512ピクセルの描画を完了した。

#### 4.2 MC68000 / 10MHz

FPUを持たない環境で実行したところ、通常速度では描画に非常に長い時間を要した。

そこでXM6のTURBOモードを使用し、CPUの実行待ちを取り除いた状態で処理を継続した。

TURBO実行時のエミュレータ表示は、おおむね通常の3500〜4800%程度で変動した。

初回の完走時に得られた計測値：

**85,508,610ms（23時間45分8.61秒）**

ただし、この数値はエミュレータ内で計測された時間であり、実際の経過時間とは異なる。

#### 4.3 再実行と計測値の異常

再実行では、最終計測値として891,440msが表示されるケースがあった。

処理内容や描画結果から考えると、この数値をそのまま実行時間と解釈することには疑問が残った。

そこで、時間計測機能を個別に検証した。

### 5. タイマーの動作確認

#### 5.1 sleepによる検証

```python
import time

start = time.ticks_ms()
time.sleep_ms(10000)
elapsed = time.ticks_diff(time.ticks_ms(), start)

print("elapsed:", elapsed, "ms")
```

通常速度・TURBOモードのいずれでも、計測結果は約10,000msだった。

#### 5.2 浮動小数点演算による検証

```python
import time

start = time.ticks_ms()

a = 0.0
for i in range(10000):
    a = a * 1.000001 + 0.000001

elapsed = time.ticks_diff(time.ticks_ms(), start)

print("result:", a)
print("elapsed:", elapsed, "ms")
```

両モードで以下の結果を得た。

- 演算結果：`0.01004748`
- 計測時間：`20900ms`

通常速度では実際に約21秒かかった一方、TURBOモードでは実時間約1〜2秒で終了した。

このことから、少なくともこの環境での `ticks_ms()` は、ホストPCの実時間ではなく、エミュレータ内の仮想的な経過時間を反映していると考えられる。

### 6. 長時間描画中の計測記録

描画中に32ラインごとの経過時間を表示するよう変更し、再度実行した。

| ライン | 表示値（ms） |
|---:|---:|
| 0 | 18,900 |
| 32 | 6,222,060 |
| 64 | 11,675,120 |
| 96 | -69,266,800 |
| 128 | -64,073,330 |
| 160 | -59,274,100 |
| 192 | -54,057,300 |
| 224 | -49,362,380 |
| 256 | -43,420,250 |
| 288 | -37,418,640 |
| 320 | -32,859,250 |
| 352 | -27,486,880 |
| 384 | -22,730,160 |
| 416 | -17,428,240 |
| 448 | -12,175,660 |
| 480 | -6,762,020 |
| 完了 | **-926,150** |

※一部の数値はエミュレータ画面の文字が読み取りづらく、転記誤差の可能性がある。

#### 6.1 観察された現象

line 64までは正の計測値が増加していたが、line 96で突然、大きな負の値となった。

その後は負の値のまま、描画の進行に伴っておおむね一定のペースで増加した。

この挙動は、計算処理の停止や逆行ではなく、時間計測値の不連続を示唆している。

### 7. 24時間周期の補正仮説

不連続後の表示値に、24時間に相当する86,400,000msを加算すると、前後の描画ペースと整合する。

例えばline 96では、

\[
-69,266,800+86,400,000
=17,133,200\ \mathrm{ms}
\]

となる。

line 64の11,675,120msとの差は5,458,080msであり、他の32ライン区間と同程度である。

最終計測値についても、

\[
-926,150+86,400,000
=85,473,850\ \mathrm{ms}
\]

と補正できる。

すなわち、**23時間44分33.85秒**である。

ただし、86,400,000msの補正が数値的に整合することと、タイマー自体が24時間周期で折り返すことは同義ではない。

実装上の原因は未確認である。

### 8. 再現性の確認

| 実行 | 計測時間 |
|---|---:|
| 初回完走 | 85,508,610ms |
| 再実行（24時間補正仮説） | 85,473,850ms |
| 差 | 34,760ms |
| 相対差 | 約0.041% |

両者は非常によく一致している。

少なくとも今回の描画処理については、初回と再実行でほぼ同等の計算時間が得られたと考えられる。

### 9. CPU環境による性能比較

| CPU環境 | 計測時間 |
|---|---:|
| MC68060 / 200MHz、FPUあり | 189,400ms |
| MC68000 / 10MHz、FPUなし | 85,473,850ms（補正推定） |

比率：

\[
\frac{85,473,850}{189,400}\approx451.3
\]

今回の条件では、MC68000環境の実行時間はMC68060環境の約451倍となった。

ただし、この差はCPUクロックのみを比較したものではない。

FPUの有無、浮動小数点演算方式、配列演算処理、MicroPython実装、エミュレータの設定など、複数の要因が影響していると考えられる。

### 10. 今後の検証課題

1. X68000版MicroPythonの `mp_hal_ticks_ms()` 相当の実装を確認する。
2. `time.ticks_ms()` および `time.ticks_diff()` の折り返し条件を調べる。
3. 長時間計測時には短い区間ごとの計測値を記録・積算する。
4. 可能であれば実時間とエミュレータ内時間を並行して測定する。
5. ulabの配列演算と通常のPythonループによる演算速度を比較する。
6. FPUあり・なしでの浮動小数点演算性能を個別に評価する。

### 11. まとめ

X68000向けMicroPythonに移植したulabを使用し、512 × 512ピクセルのニュートンフラクタル描画を、MC68060およびMC68000の両環境で完了できた。

特にFPUを持たないMC68000環境でも、複素数に相当する浮動小数点配列演算を含む処理が最後まで動作したことは、移植版ulabの実用的な動作確認となった。

性能面では、MC68060環境とMC68000環境で約451倍の実行時間差が観測された。

また、長時間実行によって `ticks_diff()` の計測値に大きな不連続が発生する現象を確認した。

24時間相当の補正を行うと、初回と再実行の計測時間が約0.041%の差で一致したが、その原因については引き続き調査が必要である。

今回の実験は、ulabの移植動作確認に加え、X68000版MicroPythonの時間計測機能を検証するための有用な記録となった。

---

**検証状況：描画完了／性能比較実施／タイマー不連続の原因は未解明**

```python

# Newton Fractal for X68000
# MicroPython + custom ulab
# f(z) = z^3 - 1
# 512x512 / 16 colors

import x68k
import time
from ulab import numpy as np

# ----------------------------------------
# Graphics initialization
# ----------------------------------------

x68k.crtmod(4, True)

g = x68k.GVRam(0)
x68k.vpage(1)
g.fill(0, 0, 511, 511, 0)

# ----------------------------------------
# Parameters
# ----------------------------------------

WIDTH = 512
HEIGHT = 512

MAX_ITER = 32

X_MIN = -2.0
X_MAX = 2.0
Y_MIN = -2.0
Y_MAX = 2.0

# Squared convergence tolerance
EPS2 = 0.000001

# Avoid division by zero
TINY = 0.0000000001

# Roots of z^3 - 1
ROOT3 = 0.866025403784

# ----------------------------------------
# Coordinate arrays
# ----------------------------------------

xs = np.linspace(X_MIN, X_MAX, WIDTH)
ys = np.linspace(Y_MIN, Y_MAX, HEIGHT)

t_start = time.ticks_ms()

# ----------------------------------------
# Main drawing loop
# ----------------------------------------

for py in range(HEIGHT):

    # Initial values for this scanline
    zr = xs * 1.0
    zi = np.full(WIDTH, float(ys[py]))

    # Iteration count and active mask
    iters = np.zeros(WIDTH, dtype=np.int16)
    active = np.ones(WIDTH, dtype=np.int16)

    for n in range(MAX_ITER):

        # z^2
        zr2 = zr * zr
        zi2 = zi * zi

        # f(z) = z^3 - 1
        fr = zr * (zr2 - 3.0 * zi2) - 1.0
        fi = zi * (3.0 * zr2 - zi2)

        # f'(z) = 3z^2
        dr = 3.0 * (zr2 - zi2)
        di = 6.0 * zr * zi

        # Complex division
        denom = dr * dr + di * di + TINY

        qr = (fr * dr + fi * di) / denom
        qi = (fi * dr - fr * di) / denom

        # Newton step
        new_zr = zr - qr
        new_zi = zi - qi

        # Update only active pixels
        zr = new_zr * active + zr * (1 - active)
        zi = new_zi * active + zi * (1 - active)

        iters = iters + active

        # --------------------------------
        # Convergence tests
        # --------------------------------

        # Root 1: (1, 0)
        d0 = (zr - 1.0) * (zr - 1.0) + zi * zi

        # Root 2: (-0.5, +sqrt(3)/2)
        d1 = (zr + 0.5) * (zr + 0.5)
        d1 = d1 + (zi - ROOT3) * (zi - ROOT3)

        # Root 3: (-0.5, -sqrt(3)/2)
        d2 = (zr + 0.5) * (zr + 0.5)
        d2 = d2 + (zi + ROOT3) * (zi + ROOT3)

        # A pixel has converged if near any root
        hit0 = d0 < EPS2
        hit1 = d1 < EPS2
        hit2 = d2 < EPS2

        hit = (hit0 + hit1 + hit2) > 0

        # Stop updating converged pixels
        active = active * (1 - hit)

        if np.sum(active) == 0:
            break

    # ------------------------------------
    # Color mapping and drawing
    # ------------------------------------

    for px in range(WIDTH):

        x = float(zr[px])
        y = float(zi[px])
        it = int(iters[px])

        root_id = -1

        # Root 1
        dx = x - 1.0
        dy = y

        if dx * dx + dy * dy < EPS2:
            root_id = 0

        # Root 2
        if root_id < 0:
            dx = x + 0.5
            dy = y - ROOT3

            if dx * dx + dy * dy < EPS2:
                root_id = 1

        # Root 3
        if root_id < 0:
            dx = x + 0.5
            dy = y + ROOT3

            if dx * dx + dy * dy < EPS2:
                root_id = 2

        if root_id >= 0:

            # Five color levels per root
            shade = (it - 1) % 5

            if root_id == 0:
                col = 1 + shade
            elif root_id == 1:
                col = 6 + shade
            else:
                col = 11 + shade

            g.pset(px, py, col)

    if py % 32 == 0:
        elapsed = time.ticks_diff(
            time.ticks_ms(), t_start
        )
        print("line", py, "time", elapsed)

# ----------------------------------------
# Benchmark
# ----------------------------------------

t_end = time.ticks_ms()

print("NEWTON_TIME:",
      time.ticks_diff(t_end, t_start),
      "ms")

print("done")

```

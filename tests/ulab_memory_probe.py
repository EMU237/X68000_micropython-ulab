# X68000 MicroPython + ulab: optional memory capacity probe
# ASCII only. Run separately from ulab_limits_check.py.
# Start with small arrays. Set TRY_512=True only if you wish to probe 512x512.

import gc
from ulab import numpy as np

TRY_512 = False
sizes = [32, 64, 128, 256]
if TRY_512:
    sizes.append(512)

print('=== X68000 ulab memory probe ===')
for n in sizes:
    gc.collect()
    print('\nsize: %d x %d, data bytes (float32): %d' % (n, n, 4*n*n))
    if hasattr(gc, 'mem_free'):
        print('free before:', gc.mem_free())
    a = None
    try:
        a = np.zeros((n, n), dtype=np.float)
        a[0, 0] = 123.0
        a[n - 1, n - 1] = 456.0
        if a.shape == (n, n) and a[0, 0] == 123.0 and a[n - 1, n - 1] == 456.0:
            print('PASS: allocation and boundary access')
        else:
            print('FAIL: unexpected shape or values')
        if hasattr(gc, 'mem_free'):
            print('free with array:', gc.mem_free())
    except MemoryError as e:
        print('LIMIT: MemoryError', e)
        a = None
        gc.collect()
        break
    except Exception as e:
        print('FAIL/UNSUPPORTED:', type(e).__name__, e)
        a = None
        gc.collect()
        break
    a = None
    gc.collect()
    if hasattr(gc, 'mem_free'):
        print('free after release:', gc.mem_free())
print('\n=== done ===')

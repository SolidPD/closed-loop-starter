#!/usr/bin/env python3
"""Extract phase B (D13 blink) current and timing from a ppk2-capture-v3 CSV.

Usage: r2-analyze.py <capture.csv> [--rate 100000] [--dump a b]
Time base: sample_index / rate (PPK2 nominal 100 kS/s).
Phase C is found as the drop to the sleep floor (50 ms mean < 32 mA); phase B is the 5.6 s before it.
LED edges are found on a centred 9 ms moving average of the 1 ms means, with a threshold midway
between the LED-off and LED-on levels (hysteresis 30 % of the step). The 10 LED-on periods are the last 10 rising edges before the
drop; phase B window = [first LED rising edge, +5.000 s).
"""
import csv, sys, statistics
path = sys.argv[1]
rate = float(sys.argv[sys.argv.index('--rate') + 1]) if '--rate' in sys.argv else 100000.0
BIN = 100  # 1 ms
ms, raw, acc, cnt = [], [], 0.0, 0
with open(path, newline='') as f:
    rd = csv.reader(f); next(rd)
    for row in rd:
        v = float(row[2]) / 1000.0  # mA
        raw.append(v); acc += v; cnt += 1
        if cnt == BIN: ms.append(acc / BIN); acc = 0.0; cnt = 0
n = len(raw)
T = lambda i: i * BIN / rate
print(f"{path}: samples {n}  duration {n/rate:.3f} s  1 ms bins {len(ms)}")

if '--dump' in sys.argv:
    a = float(sys.argv[sys.argv.index('--dump') + 1]); b = float(sys.argv[sys.argv.index('--dump') + 2])
    for i in range(int(a * 1000), int(b * 1000), 10):
        c = ms[i:i+10]; print(f"{i/1000:8.3f} s  {statistics.fmean(c):7.3f} mA")
    sys.exit()

# phase C starts: 50 ms mean drops below 32 mA after being above 38 mA
drops, above = [], False
for j in range(0, len(ms) - 50):
    m = statistics.fmean(ms[j:j+50])
    if m > 38: above = True
    elif m < 32 and above: drops.append(j); above = False
print(f"phase C drops at: {' '.join(f'{T(d):.3f}' for d in drops)} s")
fmt = lambda xs: ' '.join(f"{x:.0f}" for x in xs)
results = []
for k, c_start in enumerate(drops):
    lo, hi = max(0, c_start - 5600), c_start
    # centred 9 ms moving average for edge detection (1 ms bins carry ~+/-1.5 mA ripple)
    seg = [statistics.fmean(ms[max(0, i-4):i+5]) for i in range(lo, hi)]
    srt = sorted(seg[len(seg)-5100:len(seg)-50])  # levels from the blink region only (excludes phase A tail)
    off_lvl = statistics.median(srt[:len(srt)//3]); on_lvl = statistics.median(srt[-len(srt)//3:])
    thr = (off_lvl + on_lvl) / 2; hyst = (on_lvl - off_lvl) * 0.30
    print(f"\n=== cycle {k}: drop to floor at {T(c_start):.3f} s; search [{T(lo):.3f}, {T(hi):.3f}) ===")
    print(f"LED-off level ~{off_lvl:.3f} mA, LED-on level ~{on_lvl:.3f} mA, step {on_lvl-off_lvl:.3f} mA, thr {thr:.3f}")
    state = seg[0] > thr; edges = []  # (index, +1 rise / -1 fall)
    for j, v in enumerate(seg):
        if not state and v > thr + hyst: state = True; edges.append((lo + j, +1))
        elif state and v < thr - hyst: state = False; edges.append((lo + j, -1))
    print("edges: " + ' '.join(f"{'R' if s>0 else 'F'}{T(i):.3f}" for i, s in edges))
    rises = [i for i, s in edges if s > 0]; falls = [i for i, s in edges if s < 0]
    if len(rises) == 9 and edges[0][1] < 0:
        # the first LED-on period follows the phase A clear frame within ~3 ms, so its rise merges
        # with the pixel tail; take the rise as the ms after the pixel current (> on level + 1.5 mA) ends
        f1 = falls[0] - lo
        pix = [j for j in range(0, f1) if seg[j] > on_lvl + 1.5]  # coarse: smoothed series
        if pix:
            js = pix[-1]; r1 = js + 1
            for j in range(max(0, js - 8), min(f1, js + 8)):  # refine on raw 1 ms bins (no smoothing lag)
                if all(ms[lo + j + q] < on_lvl + 1.5 for q in range(3)): r1 = j; break
            rises.insert(0, lo + r1)
            print(f"first rise inferred from pixel-off transition at {T(rises[0]):.3f} s")
    if len(rises) < 10: print("FAIL: fewer than 10 rising edges"); continue
    r10 = rises[-10:]
    f10 = [next((f for f in falls if f > r), None) for r in r10]
    if None in f10: print("FAIL: unpaired rise"); continue
    b0, b1 = r10[0], r10[0] + 5000
    win = raw[b0 * BIN: b1 * BIN]
    mean_b = statistics.fmean(win)
    on_d = [f - r for r, f in zip(r10, f10)]
    off_d = [r10[i+1] - f10[i] for i in range(9)]
    per = [r10[i+1] - r10[i] for i in range(9)]
    extra = [i for i in rises if b0 < i <= b1 and i not in r10]
    print(f"phase B window [{T(b0):.3f}, {T(b1):.3f}) s: MEAN {mean_b:.3f} mA  (min {min(win):.3f} max {max(win):.3f}, {len(win)} samples)")
    print(f"LED on  durations (ms): {fmt(on_d)}  -> mean {statistics.fmean(on_d):.1f} min {min(on_d)} max {max(on_d)}")
    print(f"LED off durations (ms): {fmt(off_d)}  -> mean {statistics.fmean(off_d):.1f} min {min(off_d)} max {max(off_d)}")
    print(f"rise-to-rise period (ms): {fmt(per)}  -> mean {statistics.fmean(per):.1f} min {min(per)} max {max(per)}")
    print(f"blinks 10, span rise1->fall10 {f10[-1]-r10[0]} ms (nominal 4750); extra rises inside window: {len(extra)}")
    on_mean = statistics.fmean([v for r, f in zip(r10, f10) for v in ms[r+5:f-5]])
    off_mean = statistics.fmean([v for i in range(9) for v in ms[f10[i]+5:r10[i+1]-5]])
    print(f"plateau means: LED-on {on_mean:.3f} mA, LED-off {off_mean:.3f} mA; LED-on last fall -> floor drop {T(c_start)-T(f10[-1]):.3f} s")
    print(f"phase C floor (2 s after drop+0.1 s): {statistics.fmean(ms[c_start+100:c_start+2100]):.3f} mA")
    results.append((T(b0), mean_b, statistics.fmean(on_d), statistics.fmean(off_d), statistics.fmean(per)))
print("\nSUMMARY (window start s, phase B mean mA, on ms, off ms, period ms):")
for r in results: print("  " + '  '.join(f"{x:.3f}" for x in r))

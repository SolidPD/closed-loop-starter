#!/usr/bin/env python3
"""ws2812-decode-v1: decode WS2812 frames on channel 0 of a Logic 2 raw digital CSV export (4 MS/s).

Usage: ws2812-decode-v1.py <digital.csv> [--expect-interval 0.5 --tol 0.005]
Rows in the CSV are transitions: time, ch0..ch7.  A high pulse of ~0.25-0.5 us is a 0,
~0.75-1.0 us is a 1; 24 bits per frame, GRB MSB first; a gap > 50 us ends a frame.
"""
import csv, sys

print("ws2812-decode-v1", file=sys.stderr)

path = sys.argv[1]
expect = tol = None
if '--expect-interval' in sys.argv:
    expect = float(sys.argv[sys.argv.index('--expect-interval') + 1])
if '--tol' in sys.argv:
    tol = float(sys.argv[sys.argv.index('--tol') + 1])

pulses = []  # (rise_time, width)
prev = None
rise = None
with open(path, newline='') as f:
    rd = csv.reader(f)
    header = next(rd)
    for row in rd:
        t = float(row[0]); v = int(float(row[1]))
        if prev is None:
            prev = v; continue
        if v == 1 and prev == 0:
            rise = t
        elif v == 0 and prev == 1 and rise is not None:
            pulses.append((rise, t - rise))
        prev = v

frames = []  # list of (start_time, [widths])
cur = []
last_end = None
for rise, w in pulses:
    if last_end is not None and rise - last_end > 50e-6:
        frames.append(cur); cur = []
    cur.append((rise, w))
    last_end = rise + w
if cur:
    frames.append(cur)

def decode(fr):
    bits = [1 if w > 0.625e-6 else 0 for _, w in fr]
    if len(bits) != 24:
        return None, bits
    val = 0
    for b in bits:
        val = (val << 1) | b
    return ((val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF), bits

print(f"pulses={len(pulses)} frames={len(frames)}")
starts = []
for i, fr in enumerate(frames):
    grb, bits = decode(fr)
    t0 = fr[0][0]
    starts.append(t0)
    dt = (t0 - starts[i-1]) if i else 0.0
    ws = [w for _, w in fr]
    label = 'G%02X R%02X B%02X' % grb if grb else f'BAD({len(bits)} bits)'
    print(f"frame {i:2d}  t={t0:10.6f} s  dt={dt*1000:9.3f} ms  {label}  "
          f"pulse min/max {min(ws)*1e6:.2f}/{max(ws)*1e6:.2f} us")
if expect is not None:
    bad = [(i, (starts[i]-starts[i-1])) for i in range(2, len(starts))
           if abs((starts[i]-starts[i-1]) - expect) > tol]
    print(f"interval check {expect*1000:.0f} ms +/- {tol*1000:.0f} ms on frames 2..{len(starts)-1}: "
          + ("OK" if not bad else "FAIL " + str([(i, round(d*1000,3)) for i, d in bad])))

#!/usr/bin/env python3
"""logic-edges-v1: timing summary of every channel in a Saleae Logic 2 raw digital CSV export.

    python logic-edges-v1.py <digital.csv> [channel ...]

Logic 2's export (the export_raw_data_csv MCP tool, or File > Export Data) writes one row per transition:
Time [s], Channel 0, Channel 1, ... For each channel the script prints the number of edges, the high and low
pulse widths (min / median / max), and the period and frequency between rising edges. Use it to check a
pass test such as "the LED toggles at 2 Hz +/- 2 %" or "the SPI clock is 1 MHz".
"""
import csv
import statistics
import sys

VERSION = "logic-edges-v1"


def fmt(v):
    for unit, scale in (("s", 1), ("ms", 1e-3), ("us", 1e-6), ("ns", 1e-9)):
        if abs(v) >= scale * 0.9995:
            return f"{v / scale:.4g} {unit}"
    return f"{v:.3g} s"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    with open(sys.argv[1], newline="") as f:
        r = csv.reader(f)
        head = next(r)
        rows = [(float(x[0]), [int(v) for v in x[1:]]) for x in r if x]
    want = [int(c) for c in sys.argv[2:]] or range(len(head) - 1)
    print(f"{VERSION}: {sys.argv[1]}, {len(rows)} rows, span {fmt(rows[-1][0] - rows[0][0])}")
    for c in want:
        edges, prev = [], None
        for t, vals in rows:
            v = vals[c]
            if prev is not None and v != prev:
                edges.append((t, v))
            prev = v
        if len(edges) < 2:
            print(f"  {head[c + 1]}: {len(edges)} edges (static at {rows[-1][1][c]})")
            continue
        hi = [edges[i + 1][0] - edges[i][0] for i in range(len(edges) - 1) if edges[i][1] == 1]
        lo = [edges[i + 1][0] - edges[i][0] for i in range(len(edges) - 1) if edges[i][1] == 0]
        rises = [t for t, v in edges if v == 1]
        per = [rises[i + 1] - rises[i] for i in range(len(rises) - 1)]
        line = f"  {head[c + 1]}: {len(edges)} edges"
        for name, xs in (("high", hi), ("low", lo), ("period", per)):
            if xs:
                line += f" | {name} {fmt(min(xs))} / {fmt(statistics.median(xs))} / {fmt(max(xs))}"
        if per:
            line += f" | {1 / statistics.median(per):.4g} Hz"
        print(line)


if __name__ == "__main__":
    main()

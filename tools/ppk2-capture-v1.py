#!/usr/bin/env python3
"""ppk2-capture-v1: power (or meter) your board with a Nordic PPK2 for N seconds and save the current to CSV.

    python ppk2-capture-v1.py <mV> <seconds> <out.csv> [abort_mA] [--ampere]

Source mode (default): the PPK2 supplies <mV> (800 to 5000). Ampere mode (--ampere): the board keeps its
own supply and the PPK2 meters it in series; <mV> is ignored. The output is switched off in `finally`,
even on an error or Ctrl-C, and the run aborts if a 50 ms mean exceeds abort_mA (default 150).

The CSV has one row per sample (100 kS/s): chunk_t_s, sample_index, current_uA. The script prints the mean,
percentiles, and a per-second table, which is usually enough to read the phases of your firmware.

Tested: Windows (called from WSL2 as python.exe), source mode, ppk2-api 0.9.2. Not yet tested: --ampere.
"""
import csv
import statistics
import sys
import time

VERSION = "ppk2-capture-v1"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ampere = "--ampere" in sys.argv
    if len(args) < 3:
        sys.exit(__doc__)
    mv, secs, out = int(args[0]), float(args[1]), args[2]
    abort_ma = float(args[3]) if len(args) > 3 else 150.0
    from ppk2_api.ppk2_api import PPK2_API  # pip install ppk2-api==0.9.2
    ports = PPK2_API.list_devices()
    if not ports:
        sys.exit(f"{VERSION}: no PPK2 found")
    p = PPK2_API(ports[0], timeout=1, write_timeout=1, exclusive=True)
    p.stop_measuring()  # drain a stream left running by an interrupted run
    quiet = time.time()
    while time.time() - quiet < 0.5:
        if p.ser.in_waiting:
            p.ser.read(p.ser.in_waiting)
            quiet = time.time()
        time.sleep(0.05)
    p.get_modifiers()
    if ampere:
        p.use_ampere_meter()
    else:
        if not 800 <= mv <= 5000:
            sys.exit(f"{VERSION}: the PPK2 sources 800 to 5000 mV")
        p.use_source_meter()
        p.set_source_voltage(mv)
    rows, aborted = [], None
    try:
        p.toggle_DUT_power("ON")
        p.start_measuring()
        t0 = time.time()
        while time.time() - t0 < secs:
            d = p.get_data()
            if d:
                s, _ = p.get_samples(d)  # 0.9.2 returns (samples in uA, digital bits)
                rows.append((time.time() - t0, s))
                if len(s) > 500 and statistics.fmean(s[-5000:]) / 1000 > abort_ma:
                    aborted = f"mean {statistics.fmean(s[-5000:]) / 1000:.1f} mA > {abort_ma} mA"
                    break
            time.sleep(0.01)
    finally:
        try:
            p.stop_measuring()
        finally:
            p.toggle_DUT_power("OFF")
            p.ser.close()
    allv = [x for _, s in rows for x in s]
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chunk_t_s", "sample_index", "current_uA"])
        i = 0
        for t, s in rows:
            for x in s:
                w.writerow([f"{t:.3f}", i, f"{x:.2f}"])
                i += 1
    mode = "ampere" if ampere else f"{mv} mV"
    print(f"{VERSION}: {mode}, {secs} s, port {ports[0]}, {len(allv)} samples -> {out}, output OFF")
    if aborted:
        print("ABORTED:", aborted)
    if allv:
        srt = sorted(allv)
        n = len(srt)
        print(f"mean {statistics.fmean(allv) / 1000:.3f} mA  median {srt[n // 2] / 1000:.3f}  "
              f"p99 {srt[n * 99 // 100] / 1000:.3f}  max {srt[-1] / 1000:.3f} mA")
        for k in range(0, n, 100000):
            c = allv[k:k + 100000]
            print(f"  s{k // 100000:<3d} mean {statistics.fmean(c) / 1000:8.3f} mA  max {max(c) / 1000:8.3f} mA")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""ppk2-power-v1: keep a Nordic PPK2 powering your board while you flash and capture, then switch it off.

    python ppk2-power-v1.py on [mV] [--ampere]   start a holder process that keeps the PPK2 port open with
                                                 the output on, and logs the live mean current to
                                                 ppk2-hold.status beside this script
    python ppk2-power-v1.py status               print the holder's last status line
    python ppk2-power-v1.py off                  ask the holder to switch the output off, and wait for it

Why a holder: the PPK2 switches its output off when its serial port closes, so a script that turns power
on and exits leaves the board dark. The holder switches off by itself after 15 minutes.

Source mode (default, 800 to 5000 mV): the PPK2 supplies the board.
Ampere mode (--ampere): the board keeps its own supply and the PPK2 sits in series as a meter
(the nRF7002 DK's P22 header, a Nucleo's IDD jumper).

On Windows the holder is started through WMI (Win32_Process.Create), so it survives a WSL shell that
calls python.exe and then exits. Tested: Windows (called from WSL2), source mode, with ppk2-api 0.9.2.
Not yet tested: Linux and macOS (a detached child process), and --ampere.
"""
import os
import statistics
import subprocess
import sys
import time

VERSION = "ppk2-power-v1"
HERE = os.path.dirname(os.path.abspath(__file__))
STOP, STATUS = os.path.join(HERE, "ppk2-hold.stop"), os.path.join(HERE, "ppk2-hold.status")
MAX_S = 15 * 60


def open_ppk2():
    from ppk2_api.ppk2_api import PPK2_API  # pip install ppk2-api==0.9.2
    ports = PPK2_API.list_devices()
    if not ports:
        sys.exit(f"{VERSION}: no PPK2 found")
    p = PPK2_API(ports[0], timeout=1, write_timeout=1, exclusive=True)
    p.stop_measuring()  # a killed run can leave the stream on; drain until 0.5 s of silence
    quiet = time.time()
    while time.time() - quiet < 0.5:
        if p.ser.in_waiting:
            p.ser.read(p.ser.in_waiting)
            quiet = time.time()
        time.sleep(0.05)
    p.get_modifiers()
    return p


def hold(mv, ampere):
    p = open_ppk2()
    if ampere:
        p.use_ampere_meter()
    else:
        p.use_source_meter()
        p.set_source_voltage(mv)
    t0, buf, reason = time.time(), [], "off requested"
    try:
        p.toggle_DUT_power("ON")
        p.start_measuring()
        last = 0.0
        while not os.path.exists(STOP):
            if time.time() - t0 > MAX_S:
                reason = "15 min limit"
                break
            d = p.get_data()
            if d:
                s, _ = p.get_samples(d)
                buf = (buf + s)[-100000:]
            if buf and time.time() - last > 0.5:
                last = time.time()
                mode = "ampere" if ampere else f"{mv} mV"
                with open(STATUS, "w") as f:
                    f.write(f"ON {mode}, {time.time() - t0:.0f} s, last-1s mean {statistics.fmean(buf) / 1000:.2f} mA\n")
            time.sleep(0.02)
    finally:
        try:
            p.stop_measuring()
        finally:
            p.toggle_DUT_power("OFF")
            p.ser.close()
            with open(STATUS, "w") as f:
                f.write(f"OFF ({reason})\n")
            if os.path.exists(STOP):
                os.remove(STOP)


def start_holder(args):
    me = os.path.abspath(__file__)
    if os.name == "nt":
        line = f'"{sys.executable}" "{me}" _hold {" ".join(args)}'.replace("'", "''")
        ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments "
              f"@{{CommandLine='{line}'; CurrentDirectory='{HERE}'}}; exit $r.ReturnValue")
        rc = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], stdin=subprocess.DEVNULL,
                            capture_output=True, text=True).returncode
        if rc != 0:
            sys.exit(f"{VERSION}: Win32_Process.Create returned {rc}")
    else:
        subprocess.Popen([sys.executable, me, "_hold", *args], start_new_session=True, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def live_status():
    if not os.path.exists(STATUS):
        return None
    return open(STATUS).read().strip(), time.time() - os.path.getmtime(STATUS)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "_hold":
        hold(int(sys.argv[2]), "--ampere" in sys.argv)
    elif cmd == "on":
        ampere = "--ampere" in sys.argv
        nums = [a for a in sys.argv[2:] if a.isdigit()]
        mv = int(nums[0]) if nums else 3300
        if not ampere and not 800 <= mv <= 5000:
            sys.exit(f"{VERSION}: the PPK2 sources 800 to 5000 mV")
        st = live_status()
        if st and st[1] < 3 and st[0].startswith("ON"):
            sys.exit(f"{VERSION}: already on: {st[0]}")
        if os.path.exists(STOP):
            os.remove(STOP)
        open(STATUS, "w").write("STARTING\n")
        start_holder([str(mv)] + (["--ampere"] if ampere else []))
        for _ in range(40):
            time.sleep(0.25)
            st = live_status()
            if st and st[0].startswith("ON"):
                print(f"{VERSION}: {st[0]}")
                return
        sys.exit(f"{VERSION}: the holder did not report ON within 10 s: {live_status()}")
    elif cmd == "off":
        open(STOP, "w").write("stop\n")
        for _ in range(40):
            time.sleep(0.25)
            st = live_status()
            if st and st[0].startswith("OFF"):
                break
        print(f"{VERSION}: {live_status()[0] if live_status() else 'no holder'}")
    else:
        st = live_status()
        if not st:
            print(f"{VERSION}: no holder has run")
        elif st[0].startswith("ON") and st[1] >= 3:
            print(f"{VERSION}: STALE ({st[1]:.0f} s old, the holder is gone): {st[0]}")
        else:
            print(f"{VERSION}: {st[0]}")


if __name__ == "__main__":
    main()

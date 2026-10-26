# Closed-loop bench: instructions for the coding agent

You are driving a real board on a real bench. Work this loop for every change:

**write the pass test first → change the firmware → build → flash → measure → prove or revert → commit.**

Fill in the `<...>` fields below for your bench before your first session, and keep `BENCH.md` current.

## Hardware

- Board: `<board, e.g. XIAO BLE Sense (nRF52840)>`
- Build: `<command, e.g. west build -b xiao_ble/nrf52840/sense app>`
- Flash: `<command, e.g. nrfutil device program --firmware build/zephyr/zephyr.hex>`
- Serial console: `<port and baud, or "none">`
- Power: a Nordic PPK2 in `<source mode at N mV | ampere mode>`. The board is unpowered unless the PPK2 output is on.
- Logic analyzer: a Saleae with Logic 2's MCP server (`logic2`). Channels: `<ch0 = signal, ch1 = signal, ...>`. Sample rate: `<e.g. 4 MS/s; older hardware times out at higher rates>`.

## Tools (in `tools/`)

- Power on and keep it on: `python tools/ppk2-power-v1.py on <mV>` (or `on --ampere`); check with `status`; finish with `off`. **Always switch power off when you finish, even on failure.**
- Current capture to CSV (powers on, measures, powers off): `python tools/ppk2-capture-v1.py <mV> <seconds> captures/<name>.csv`
- Saleae: the `logic2` MCP tools. `start_capture` with a `timedCaptureMode`, `wait_capture`, then `export_raw_data_csv` into `captures/<name>/`. Arm the capture before you power the board if you need its boot.
- Timing from a Saleae export: `python tools/logic-edges-v1.py captures/<name>/digital.csv [channels]`
- An example protocol decoder: `tools/ws2812-decode-v1.py` (WS2812 pixel data). Write your own decoder the same way, or add a Logic 2 analyzer through the MCP server.

## Rules

- One change per cycle. Write the pass test as numbers with a tolerance, in `<name>-pass-test.md`, **before** editing code.
- For a low-power change, measure the "before" on the current firmware first, under the same conditions you will use after.
- Save every capture as a file and cite it in your report.
- Commit when the test passes, with the measured numbers in the message. If it fails, say why and revert.
- Read the SDK and libraries installed in this workspace (headers, samples, source) instead of recalling APIs from memory: they change every release.
- If a tool's output disagrees with what you expect, check the tool before you blame the hardware.
- Powering the board on needs a person's OK unless `BENCH.md` says otherwise.

## Windows (WSL2) notes

- Logic 2, the PPK2's Python, and the flash tools run on Windows. From WSL, call them as `.exe` (for example `/mnt/c/Users/<you>/ppk2-venv/Scripts/python.exe`).
- Run Windows programs with stdin closed (`</dev/null`) and in the foreground.
- Logic 2 writes exports to Windows paths: `C:\tmp\cap` is `/mnt/c/tmp/cap` in WSL.

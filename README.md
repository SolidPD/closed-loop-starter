# closed-loop-starter

Let a coding agent close the hardware loop on your bench: **write the pass test, change the firmware, flash,
measure with a Saleae and a Nordic PPK2, then prove or revert**. Made for the teams in Penn's ESE 5180 (IoT
Venture), and useful on any bench with those two instruments.

This repository is the kit we ran on 2026-10-26: Claude Code in WSL2 on a Windows laptop met both
closed-loop requirements on a real board, one prompt each (see
[`examples/fabbit-2026-10-26/`](examples/fabbit-2026-10-26/)).

## What's in it

| Path | What it is |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | The instructions your agent follows: the loop, the tools, the rules. Fill in the `<...>` fields for your board. Codex reads it directly; [`CLAUDE.md`](CLAUDE.md) and [`GEMINI.md`](GEMINI.md) import it |
| [`BENCH.md`](BENCH.md) | One row per instrument: how the agent reaches it, its hardware check, its limits, the last check |
| [`prompts/`](prompts/) | Two prompts to paste, with the requirement left blank: a feature validated with the Saleae, and a low-power change with PPK2 numbers before and after |
| [`tools/ppk2-power-v1.py`](tools/ppk2-power-v1.py) | Keeps the PPK2 powering (or metering) your board while you flash and capture; `on`, `status`, `off` |
| [`tools/ppk2-capture-v1.py`](tools/ppk2-capture-v1.py) | Powers or meters the board for N seconds and saves the current to CSV, with a per-second summary |
| [`tools/logic-edges-v1.py`](tools/logic-edges-v1.py) | Edge counts, pulse widths, and frequency for every channel of a Logic 2 CSV export |
| [`tools/ws2812-decode-v1.py`](tools/ws2812-decode-v1.py) | An example protocol decoder for a Logic 2 export (WS2812 pixel data) |
| [`docs/wsl2-and-boards-guide-v1.pdf`](docs/wsl2-and-boards-guide-v1.pdf) | Two pages: running Hapimatic on Windows with WSL2, and putting the PPK2 on the nRF7002 DK, the XIAO BLE Sense, and the Nucleo LoRa board |

## Start

1. **Saleae:** install Logic 2 (2.4.48 or newer), then Settings › Automation › turn on **MCP Server**. Add it to your agent:
   ```bash
   claude mcp add --transport http -s user logic2 http://127.0.0.1:10530
   ```
   For Codex or Gemini CLI, add the same URL as an HTTP MCP server in its settings.
2. **PPK2:** `pip install ppk2-api==0.9.2` (on Windows, in the Windows Python you'll call from WSL).
3. **This repository:** clone it next to your firmware (or copy `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `BENCH.md`, and `tools/` into your project), and fill in the `<...>` fields.
4. **First check:** ask your agent to list the Saleae devices, and run `python tools/ppk2-power-v1.py on 3300` then `status` with a 1 kΩ resistor as the load (about 3.3 mA), then `off`.
5. **First loop:** paste [`prompts/feature-v1.md`](prompts/feature-v1.md) with one requirement that has a number in it.

### Where to run the agent

- **[Hapimatic](https://hapimatic.com)** (open-source core, Linux; on Windows via WSL2 with the guide in `docs/`): runs Claude Code, Codex, and Gemini CLI sessions you can watch and steer from a browser or phone.
- **Directly** in a terminal with Claude Code, Codex, or Gemini CLI. On a Mac, Logic 2's MCP server and ppk2-api both run, so the agent drives them directly.

## What has been tested

| | Tested | Not yet tested |
| --- | --- | --- |
| Agent | Claude Code (in WSL2 on Windows 11) | Codex, Gemini CLI |
| PPK2 | source mode, Windows Python called from WSL2 | `--ampere`, Linux and macOS hosts |
| Saleae | an original Saleae Logic through Logic 2.4.48's MCP server | Logic 8, Pro 8, Pro 16 |
| Boards | an ATmega328P test board (Arduino CLI) | the nRF7002 DK, the XIAO BLE Sense, the Nucleo LoRa board |

## Traps we hit

- The PPK2 turns its output off when its serial port closes. Keep `ppk2-power-v1.py on` running while you flash.
- A killed PPK2 run leaves the stream on, and the next script fails with `UnicodeDecodeError`; the tools here drain it first.
- On Windows, programs called from WSL read the rest of a piped script from stdin: run them with `</dev/null`.
- A USB cable or a debugger on the board adds its own current. Measure low power with both removed, or say they were there.

MIT licensed. From Matt Starfield, the Senior Electrical Engineer at Solid Product Design.

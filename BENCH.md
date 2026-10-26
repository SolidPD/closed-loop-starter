# BENCH.md: what the agent can reach, and what it may do

One row per instrument. Update the "last check" column every time a hardware check passes, so the next
session knows what to trust.

| Instrument | How the agent reaches it | Hardware check (a known answer) | Limits | Last check |
| --- | --- | --- | --- | --- |
| Saleae Logic | Logic 2's MCP server, `http://127.0.0.1:10530` (`logic2`) | a known UART string at a known baud rate, or a pin you toggle at a known rate | `<sample rate limit, channel count>` | `<date: result>` |
| Nordic PPK2 | `tools/ppk2-power-v1.py`, `tools/ppk2-capture-v1.py` (ppk2-api 0.9.2) | a 1 kΩ resistor at 3.3 V reads about 3.3 mA | source mode 800 to 5000 mV; output drops when its port closes | `<date: result>` |
| Board | `<build and flash commands>` | `<e.g. a blink you can see, or a serial banner>` | `<e.g. measure with the debugger and USB unplugged>` | `<date: result>` |

## Rules

- Capture, decode, build, and flash freely.
- Powering the board: `<who says yes, e.g. a teammate's OK each session>`.
- Before trusting a low-power number: USB and the debugger are off the board, or noted in the result.

# Worked example: two requirements on a FabBit test board (2026-10-26)

Setup: Claude Code in Ubuntu on WSL2 on a Windows 11 laptop; an original Saleae Logic through Logic 2's
MCP server (channel 0 on the pixel data line, 4 MS/s); a Nordic PPK2 in source mode at 5.0 V on the
board's 5 V rail; an ATmega328P board (Arduino Uno bootloader) with one WS2812 pixel and an LED. The
agent got one prompt per requirement and ran the loop on its own.

| Requirement | Pass test (written first) | Measured | Time |
| --- | --- | --- | --- |
| Feature: add a magenta step after white; step every 500 ms instead of 1250 ms | 10 frames, the GRB bytes in order, every gap 500 ± 5 ms (`r1-pass-test.md`) | 10 frames in order, every gap 500.458 to 500.462 ms (`r1-saleae-decoded.txt`, frames 6 to 15) | 3.5 min |
| Low power: cut the blink phase by at least 5 mA; keep 10 blinks at 2 Hz | before measured first: 43.3 mA in two cycles; after ≤ 38.3 mA; on and off 250 ± 5 ms (`r2-pass-test.md`) | 34.0 mA (9.3 mA saved); on 249 to 254 ms, off 247 to 253 ms (`r2-after-analysis.txt`) | 13 min |

The low-power change: the processor idles between Timer0 ticks instead of spinning in `delay()`.

What went wrong first: the agent reported the board's USB chip unplugged. It wasn't: the power script
switched the PPK2 on and exited, and the PPK2 turns its output off when its port closes. That is why
`tools/ppk2-power-v1.py` keeps a holder process running. Check the tool before you trust a conclusion
built on it.

Files: the two pass tests, the decoded Saleae frames, the PPK2 analyses before and after, and the
agent's own analysis script for the low-power run (`r2-analyze.py`).

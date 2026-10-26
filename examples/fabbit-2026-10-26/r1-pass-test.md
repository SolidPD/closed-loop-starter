# R1 pass test (written 2026-10-26 before editing firmware)

Requirement: phase A adds magenta (R64 G0 B64) after white; step interval 1250 ms -> 500 ms; two rounds = 10 colour frames.

Capture: Saleae Logic ch0 = D4, 4 MS/s, timed capture started before PPK2 power-on so the boot clear frame and all of phase A land in the window.

- Frame count: exactly 10 colour frames between the boot clear frame (00 00 00) and the phase-end clear frame (00 00 00).
- Frame order, GRB bytes hex:
  1 red     00 40 00
  2 green   40 00 00
  3 blue    00 00 40
  4 white   30 30 30
  5 magenta 00 40 40
  6-10      repeat 1-5
  then clear 00 00 00
- Spacing: all 9 colour-frame start-to-start gaps = 500 ms +/- 5 ms; clear frame 500 ms +/- 5 ms after frame 10.
- Each frame: 24 bits (0 = 0.25-0.5 us high, 1 = 0.75-1.0 us high), frames separated by > 50 us gaps.

Pass = every line above holds. Fail = any deviation; then revert the firmware.

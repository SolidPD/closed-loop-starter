# R2 pass test (written 2026-10-26 before editing firmware)

Requirement: cut phase B's average board current by >= 5 mA without changing what phase B does
(10 blinks, D13 high 250 ms then low 250 ms, 2 Hz). Phases A and C unchanged.

## Conditions (same before and after)
PPK2 source meter 5.000 V, `ppk2-capture-v3.py 5000 45 <csv> 150` from a cold power-on (the capture
script powers the board on, samples 45 s at 100 kS/s, powers off). Analysis: `r2-analyze.py <csv>`.
Phase B window = [first D13 rise, +5.000 s); the first rise is the pixel-off transition at the end of
phase A (the LED goes high ~3 ms later, after the serial marker). D13 edges come from the LED's current
step on a centred 9 ms moving average of 1 ms means, threshold midway between the LED-off and LED-on
levels. Edge timing resolution is about +/-3 ms. Two phase B windows land in each 45 s capture
(cycle 0 at ~11 s, cycle 1 at ~37.6 s); both must pass.

## Before (measured now, firmware at commit 4eddc3c, capture r2-before-45s.csv, analysis r2-before-analysis.txt)
| cycle | window (s)        | phase B mean | LED-on plateau | LED-off plateau | LED step |
|-------|-------------------|--------------|----------------|-----------------|----------|
| 0     | 10.915 .. 15.915  | 43.303 mA    | 45.02 mA       | 41.61 mA        | 3.79 mA  |
| 1     | 37.569 .. 42.569  | 43.275 mA    | 44.98 mA       | 41.54 mA        | 3.82 mA  |
Phase C floor: 27.38 / 27.34 mA. Blink timing before: on 249-253 ms (blink 1: 255/258 ms, includes
the ~3 ms serial marker), off 247-252 ms, rise-to-rise period 500-502 ms (blinks 2..10),
span first rise -> tenth fall 4758 / 4760 ms, LED-on tail to sleep-floor drop 233 ms.

## Required after
1. Current: phase B mean <= 38.3 mA (43.3 - 5.0) in BOTH phase B windows of one 45 s capture.
   Report the saving as 43.30 - after (cycle 0) and 43.28 - after (cycle 1); each must be >= 5.0 mA.
2. Blink timing, from the PPK2 trace, every blink:
   - D13 high (on duration) 250 +/- 5 ms for blinks 2..10; blink 1 (measured from pixel-off, includes
     the serial marker) 253 +/- 6 ms;
   - D13 low (off duration) 250 +/- 5 ms for all 9 off periods;
   - rise-to-rise period 500 +/- 5 ms for blinks 2..10 (i.e. 2.00 Hz +/- 1 %);
   - exactly 10 LED-on periods, no extra edges in the window; span first rise -> tenth fall 4750 +/- 20 ms.
3. The LED still lights: LED-on plateau minus LED-off plateau = 3.8 +/- 0.6 mA.
4. Phase A unchanged: Saleae ch0 (D4) 4 MS/s, 30 s capture armed before power-on, decoded with
   ws2812-decode.py: 10 colour frames in the R1 order (00 40 00, 40 00 00, 00 00 40, 30 30 30, 00 40 40, x2)
   then clear, start-to-start 500 +/- 5 ms (same test as r1-pass-test.md).
5. Phase C unchanged: sleep floor 27.4 +/- 0.3 mA for >= 15 s after phase B.

Pass = all five hold. Fail = any deviation; revert the firmware and say why. If the 2 Hz timing does
not hold with the chosen method, report the measured numbers and choose another method.

## Method (one change)
Phase B replaces the busy `delay(250)` with an idle-sleep wait: unused peripherals (ADC, SPI, TWI,
Timer1, Timer2) are clock-gated for the phase and the CPU enters SLEEP_MODE_IDLE between Timer0
overflow interrupts (every 1.024 ms) until millis() shows the 250 ms elapsed. Timer0 keeps running from
the 16 MHz clock, so timing stays crystal-derived as with delay(). Peripherals are re-enabled at the
end of phase B. Fallback if < 5 mA: also gate USART0 between markers; then watchdog power-down with
run-time calibration (timing risk, to be measured).

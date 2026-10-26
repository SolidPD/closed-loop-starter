# Low-power prompt (validated with the PPK2, before and after)

```text
Requirement: <cut the current of a named phase or mode by at least N mA (or to below N uA)>,
without changing what it does: <the behaviour that must hold, with a tolerance>.

Work the loop in AGENTS.md. Before you edit anything, write <name>-pass-test.md: measure the "before"
now with tools/ppk2-capture-v1.py on the current firmware, under the same conditions you will use
after, and write the required "after" and the behaviour checks as numbers. Then change the firmware,
build, flash, measure again, and check the behaviour (from the PPK2 trace, the Saleae, or both).
Power the board off at the end. Commit on a pass with the before and after numbers in the message.
If your method breaks the behaviour, say so with the measured numbers and try another method.
```

Example requirement (the one that passed on 2026-10-26): "Cut phase B's average current by at least
5 mA without changing it: 10 blinks, D13 high 250 ms then low 250 ms (2 Hz)."

For a battery product, measure with USB and the debugger off the board: on the test board, a connected
USB cable alone raised the sleep current from 3.9 mA to 27.3 mA.

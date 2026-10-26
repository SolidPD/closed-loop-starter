# Feature prompt (validated with the Saleae)

Paste into your agent from this repository's folder, with the requirement filled in.

```text
Requirement: <one sentence, with a number and a tolerance>.

Work the loop in AGENTS.md. Before you edit anything, write <name>-pass-test.md with the pass test as
numbers with a tolerance. Then change the firmware, build, power the board, flash it, capture the
relevant channels with the logic2 MCP server (arm the capture before you power or reset the board if
you need its start), analyse the exported CSV, and decide pass or fail against your test. Power the
board off at the end. Commit on a pass; on a fail, revert and say why. Finish with a short report:
the test, the measured numbers, the files you saved, and the commit.
```

Example requirement (the one that passed on 2026-10-26, see `examples/fabbit-2026-10-26/`):
"In phase A, add a magenta step after white, and change the step interval from 1250 ms to 500 ms."

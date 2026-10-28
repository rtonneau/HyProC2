# Ticket 02: physics-takes-reaction-config

**Status:** ✅ Done

## Local Test Result

`ruff check && pytest && grep <module constants>` → All checks passed!; 19 passed; grep prints nothing (exit 1).

## Review Notes

Implemented by a subagent (Opus, low effort); reviewed the diff and re-ran the verification here with no changes. Physics functions take `reaction` after positional args; app passes `self.reaction` (experiment default) to every call, so behaviour is unchanged; unused M1/M2/A2/energy_res removed; two new tests (E_R shift, cH_make Z2 selection); conftest comment and CLAUDE.md gotcha updated. App not run manually.

## Blockers / Challenges

None.

## Commits

- 326c94b refactor: pass ReactionConfig explicitly to physics modules (ticket 02)

## Time Spent

2m (ticket-start.js to ticket-complete.js)

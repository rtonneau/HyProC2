# Ticket 04: reactions-in-simulation-file

**Status:** ✅ Done

## Local Test Result

`.venv/Scripts/ruff check && .venv/Scripts/python -m pytest` → All checks passed!; 23 passed.

## Review Notes

Implemented by a subagent (Sonnet, high effort); reviewed the diff and re-ran the verification here with no changes. Save writes `reactions` {standard, experiment}; load parses with the pure `reactions_from_sim` inside the existing try (ValueError → existing error dialog) and assigns only after validation; missing block/keys fall back to defaults. Three new tests. GUI save/load not exercised manually.

## Blockers / Challenges

None.

## Commits

- caafacd feat: save reaction configs in simulation files (ticket 04)

## Time Spent

1m (ticket-start.js to ticket-complete.js)

# Ticket 01: reaction-config-and-settings

**Status:** ✅ Done

## Local Test Result

`.venv/Scripts/ruff check && .venv/Scripts/python -m pytest` → All checks passed!; 17 passed.

## Review Notes

Implemented by a subagent (Sonnet, high effort); reviewed the diff and re-ran the verification here with no changes. All criteria hold: ReactionConfig with casting/defaults, new `reactions` block, one-time migration in load_settings, default_reactions/save_default_reactions, tests. Outside the listed files: physics modules now read default_reactions()[1] (per Notes) and app.load_Z2 reads the new shape, needed to keep the app working.

## Blockers / Challenges

None.

## Commits

- 92dce4e feat: add ReactionConfig and per-side reaction defaults (ticket 01)

## Time Spent

2m (ticket-start.js to ticket-complete.js)

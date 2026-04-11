# Resume From Handoff

Create a fresh child session from the current session's `handoff.md` artifacts.

```bash
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" resume-from-handoff "fresh context resume"
```

This keeps the parent session paused and selects the new child session as current.

Preconditions:

- The source session must already be `status=paused` and `phase=handoff`.
- Run `prepare-reset` first if the session has not produced a reset handoff yet.

# Harness Design Kit Doctor

Run an environment and session health check for the current workspace.

```bash
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" doctor
```

If the current session pointer is missing or stale, target a specific session directly:

```bash
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" --session <session-id> doctor
```

Useful follow-ups:

```bash
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" list-sessions
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" select-session <session-id>
```

# Dev Kit

Local Codex plugin for disciplined development workflows.

## Included Skills

### Workflow

- `clarify-requirements`: narrow vague requests into a saved context brief with complexity routing
- `craft-plan`: write executable implementation plans with explicit verification
- `execute-plan`: execute plans through worker-validator loops
- `verify-implementation`: independently verify implementation against the plan
- `decompose-milestones`: break large projects into milestone DAGs with parallel review
- `orchestrate-execution`: orchestrate multi-milestone execution with checkpoints and recovery

### Guardrails And Cleanup

- `write-surgically`: implementation discipline for scoped, verified code changes
- `remove-slop`: post-generation cleanup for AI-shaped code smells
- `simplify-changes`: diff-based quality, reuse, and efficiency review with direct fixes

### Debugging And Performance

- `debug-systematically`: reproduce-first, root-cause-first debugging workflow
- `measure-performance`: measurement-first optimization guardrails

## Structure

- `.codex-plugin/plugin.json`: plugin manifest
- `skills/`: bundled workflow and discipline skills
- `hooks/hooks.json`: hook definitions
- `scripts/`: local helper scripts
- `assets/`: icons, logos, screenshots
- `.app.json`: app or connector mappings
- `.mcp.json`: MCP server mappings

## Notes

- Planning artifacts default to `docs/dev-kit/`
- `systematic-debugging/` includes supporting reference material and helper scripts
- `milestone-planning` and `long-run` extend the core plan/execute/review pipeline for larger work

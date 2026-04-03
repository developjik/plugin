# Dev Kit

Local Codex plugin for disciplined development workflows.

## Included Skills

### Workflow

- `clarify`: narrow vague requests into a saved context brief with complexity routing
- `plan-crafting`: write executable implementation plans with explicit verification
- `run-plan`: execute plans through worker-validator loops
- `review-work`: independently verify implementation against the plan
- `milestone-planning`: break large projects into milestone DAGs with parallel review
- `long-run`: orchestrate multi-milestone execution with checkpoints and recovery

### Guardrails And Cleanup

- `karpathy`: implementation discipline for scoped, verified code changes
- `clean-ai-slop`: post-generation cleanup for AI-shaped code smells
- `simplify`: diff-based quality, reuse, and efficiency review with direct fixes

### Debugging And Performance

- `systematic-debugging`: reproduce-first, root-cause-first debugging workflow
- `rob-pike`: measurement-first optimization guardrails

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

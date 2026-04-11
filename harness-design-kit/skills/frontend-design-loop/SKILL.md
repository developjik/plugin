---
name: frontend-design-loop
description: Run a generator-evaluator loop for frontend work using explicit grading on design quality, originality, craft, and functionality.
---

# Frontend Design Loop

Use this skill for landing pages, product surfaces, or other UI work where "technically correct" is not enough and the output must be visually strong.

## Hard Rules

1. Grade the design on explicit criteria instead of vague taste.
2. Weight design quality and originality more heavily than craft and functionality.
3. Prefer evaluating a live page over judging static screenshots or code alone.
4. After each round, explicitly choose to refine the current direction or pivot to a new one.
5. Keep the best candidate, not automatically the last one.

## Session Setup

If there is no active session, initialize one in frontend mode:

```bash
python3 "${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-.}}/scripts/harness_state.py" init "<goal>" frontend
```

Use:

- `design-brief.md` for the visual brief
- `evaluation.md` for per-round critique
- `progress.md` for the direction chosen after each round
- `python3 .../scripts/harness_state.py start-round [candidate-id]` to open a tracked iteration
- `python3 .../scripts/harness_state.py finish-round <refine|pivot|accept> [candidate-id]` to record the result

## Scoring Criteria

- `design quality`
  - coherence of typography, layout, color, imagery, and mood
- `originality`
  - evidence of deliberate creative choices instead of stock defaults or generic AI patterns
- `craft`
  - spacing, contrast, hierarchy, and execution fundamentals
- `functionality`
  - task clarity, navigability, and usability independent of visual taste

## Recommended Loop

Default to 3-5 rounds. Stretch to 5-15 only when the user explicitly wants a more expensive exploration loop.

For each round:

1. the generator produces or revises the frontend
2. the `design-evaluator` scores the live page
   - when a live URL exists, capture evidence with `python3 .../scripts/live_eval.py run --url <app-url>`
3. write the critique to `evaluation.md`
4. choose one:
   - refine the current direction
   - pivot to a different aesthetic
5. record the chosen direction in `progress.md`
6. if one direction clearly wins, mark it with `python3 .../scripts/harness_state.py mark-best-candidate <candidate-id>`

## Design Biases To Enforce

- penalize generic white-card plus purple-gradient outputs
- look for a distinct visual identity
- prefer intentional typography and composition over component-library defaults
- push for museum-quality ambition without breaking usability

## Output

By the end of the loop, leave:

- the best implementation in code
- the latest critique in `evaluation.md`
- a short note in `progress.md` explaining why the chosen direction won

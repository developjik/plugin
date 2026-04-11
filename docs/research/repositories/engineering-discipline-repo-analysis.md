# Engineering Discipline Repository Analysis

- Repository: `https://github.com/tmdgusya/engineering-discipline`
- Analysis date: `2026-04-09`
- Analysis basis: remote clone inspected locally, including full git history and repository files

## 1. Executive Summary

`engineering-discipline` is not a traditional software product repository. It is a documentation-first skill/plugin repository that packages prompt-based engineering workflows for AI coding agents.

The repository has three primary identities at once:

1. Skill source repository
2. Static documentation site for GitHub Pages
3. Multi-platform distribution package for Claude Code, Codex, Cursor, Gemini CLI, and OpenCode

The center of gravity is `skills/*/SKILL.md`. Everything else exists to expose, install, document, or present those skill definitions.

The repository is structurally strong in workflow design, information isolation, and process rigor. Its main weaknesses are metadata drift, incomplete platform parity, and the absence of executable automated validation for most of the repository's behavior.

## 2. High-Level Identity

### What this repo is

- A reusable skill library for AI coding agents
- A process framework for moving from ambiguous requests to verified implementation
- A prompt-engineering system encoded as Markdown skill specs
- A static showcase/documentation site

### What this repo is not

- An application backend
- A library with executable runtime logic
- A test-heavy codebase with functional coverage
- A compiled product with release artifacts

## 3. Repository Shape

Snapshot metrics from the inspected clone:

- Tracked files: `54`
- Canonical skill specs: `11`
- Skill HTML pages: `22`
- Markdown docs under `docs/`: `8`
- Largest files by line count:
  - `css/style.css`: `639`
  - `skills/milestone-planning/SKILL.md`: `618`
  - `skills/long-run/SKILL.md`: `394`
  - `skills/plan-crafting/SKILL.md`: `336`

### Top-Level Breakdown

| Path | Role |
| --- | --- |
| `skills/` | Canonical skill specs plus rendered HTML pages |
| `docs/engineering-discipline/` | Internal planning and review artifacts |
| `.claude-plugin/` | Claude marketplace/distribution metadata |
| `.cursor-plugin/` | Cursor plugin metadata |
| `.codex/` | Codex install guidance |
| `.github/workflows/` | GitHub Pages deployment |
| `index.html`, `index-en.html`, `css/`, `assets/` | Static website |
| `README*.md` | Multi-language entry docs |
| `GEMINI.md` | Gemini-oriented skill exposure file |

### Structural Diagram

```text
engineering-discipline/
|
+-- skills/
|   |
|   +-- <skill>/SKILL.md            <- canonical behavior spec
|   +-- *.html                      <- published skill detail pages
|   +-- en/*.html                   <- English mirror pages
|   +-- systematic-debugging/*.md   <- supporting reference guides
|
+-- docs/engineering-discipline/
|   |
|   +-- plans/                      <- internal implementation plans
|   +-- reviews/                    <- internal verification records
|
+-- .claude-plugin/                 <- marketplace metadata
+-- .cursor-plugin/                 <- cursor metadata
+-- .codex/INSTALL.md               <- codex install guide
+-- .github/workflows/deploy.yml    <- pages deployment
+-- index.html / index-en.html      <- docs landing pages
+-- css/style.css                   <- site design system
+-- README.md / README.ko.md / README.cn.md
```

## 4. Core Product Model

This repository's real "product" is a chained workflow of skills.

### Workflow Graph

```text
User request
    |
    v
clarification
    |
    +-- complexity scoring
          |
          +-- simple  -> plan-crafting -> run-plan -> review-work
          |
          +-- complex -> milestone-planning -> long-run
                                                |
                                                +-- milestone N:
                                                    plan-crafting
                                                       -> run-plan
                                                       -> review-work

Independent overlays:
- karpathy
- clean-ai-slop
- simplify
- systematic-debugging
- rob-pike
```

### Architectural Reading

The skill chain is built around one governing idea: separate planning, implementation, and verification so that the verifying side does not inherit the builder's bias.

That principle appears repeatedly:

- `run-plan` enforces worker/validator separation
- `review-work` forbids execution context and returns only `PASS` or `FAIL`
- `milestone-planning` requires independent reviewer perspectives before synthesis
- `long-run` persists state to disk to avoid conversational memory becoming state

This is the most important design pattern in the repo.

## 5. Skill Taxonomy

The 11 canonical skills split into three groups.

### A. Primary Workflow Skills

| Skill | Purpose |
| --- | --- |
| `clarification` | Resolve ambiguity and produce a Context Brief |
| `plan-crafting` | Turn a clear scope into an executable implementation plan |
| `run-plan` | Execute tasks through worker/validator loops |
| `review-work` | Independently verify implementation against the plan |

### B. Long-Running Orchestration

| Skill | Purpose |
| --- | --- |
| `milestone-planning` | Create milestone DAGs using 5 isolated reviewer perspectives |
| `long-run` | Execute multi-milestone work with checkpoints and recovery |

### C. Standalone Discipline Skills

| Skill | Purpose |
| --- | --- |
| `karpathy` | Guardrails before/during coding |
| `clean-ai-slop` | Post-generation cleanup discipline |
| `simplify` | Parallel review of changed code |
| `systematic-debugging` | Reproduce-first debugging workflow |
| `rob-pike` | Measurement-first performance discipline |

## 6. How the Repo Is Organized Operationally

This repository has an authoring pipeline rather than a software runtime pipeline.

```text
Author edits SKILL.md
      |
      +--> README summaries updated
      |
      +--> HTML showcase pages updated
      |
      +--> plugin metadata consumed by hosts
      |
      +--> GitHub Pages publishes repository root
```

This means the main consistency risk is not broken runtime code. It is drift across surfaces:

- canonical skill docs
- README summaries
- HTML showcase pages
- plugin metadata
- installation docs

## 7. Frontend / Site Layer

The site is a pure static site:

- `index.html`: Korean landing page
- `index-en.html`: English landing page
- `css/style.css`: single shared design system
- skill detail pages in Korean and English
- GitHub Pages deployment via `.github/workflows/deploy.yml`

### Observations

- The website is intentionally simple and low-friction: no build step, no bundler, no JS app shell.
- Deployment uploads the repository root as the Pages artifact.
- The design language is explicitly Neo-Brutalist.
- The site is secondary to the skills, but it is polished enough to act as a discovery layer.

## 8. Distribution / Platform Strategy

The repo claims support for:

- Claude Code
- Gemini CLI
- Cursor
- Codex
- OpenCode

### Platform Packaging Model

```text
Canonical source: skills/*/SKILL.md
        |
        +-- Claude: .claude-plugin/*
        +-- Cursor: .cursor-plugin/*
        +-- Codex: .codex/INSTALL.md
        +-- Gemini: GEMINI.md
        +-- OpenCode: README install instructions
```

This is a reasonable strategy: one canonical skill corpus, many host-specific adapters.

## 9. Maturity Signals

The repository shows unusually strong process maturity for a prompt-skill repo.

### Positive signals

- The repo dogfoods its own methods.
  - Evidence: `docs/engineering-discipline/plans/*` and `reviews/*`
- Skills use hard gates, anti-patterns, stop conditions, and transitions consistently.
- Long-running execution is treated as a state machine, not as a loose chat workflow.
- The authors iterated quickly:
  - bootstrap on `2026-03-31`
  - workflow chain expansion on `2026-04-01`
  - hardening review and fixes on `2026-04-01`
  - UI/site expansion on `2026-04-05`

### Commit Evolution Diagram

```text
2026-03-31
  bootstrap
    -> clarification
    -> plan-crafting + run-plan
    -> install/marketplace cleanup

2026-04-01
  review-work
    -> simplify
    -> validator hardening
    -> complexity gate
    -> milestone-planning
    -> long-run
    -> governance hardening
    -> multilingual README

2026-04-02
  karpathy + clean-ai-slop
    -> experimental Team Agent Mode
    -> Team Agent Mode reverted

2026-04-05
  GitHub Pages site
    -> all skill detail pages
    -> standardization pass
    -> English site/versioning
```

## 10. Strengths

### 1. Strong conceptual center

The repository has a clear thesis: AI coding should be guided by explicit engineering discipline, not by ad hoc prompting.

### 2. Information isolation is treated seriously

This is the strongest differentiator in the repo. The authors repeatedly defend against prompt contamination and confirmation bias.

### 3. Long-run thinking is better than average

Most skill repos stop at "generate code" or "make a plan." This repo goes further into:

- recovery
- retry budgets
- checkpointing
- DAG validation
- user gate control
- context window management

### 4. Documentation quality is high

The skill docs are not shallow slogans. They contain:

- hard gates
- anti-patterns
- explicit output contracts
- stop conditions
- transition rules

### 5. Dogfooding loop exists

Internal plans and reviews suggest the maintainers use the framework on itself, which is a good sign for refinement quality.

## 11. Weaknesses and Verified Issues

The following are concrete issues verified from the inspected files.

### 1. Repository URL drift in plugin manifests

Verified in:

- `.claude-plugin/plugin.json`
- `.cursor-plugin/plugin.json`

Both point to:

```text
https://github.com/tmdgusya/engineering-disciplines
```

But the actual repository is `engineering-discipline` singular.

Impact:

- broken or misleading metadata
- marketplace/install confusion
- trust erosion across host integrations

### 2. README links to a missing OpenCode install guide

Verified in all three READMEs:

- `README.md`
- `README.ko.md`
- `README.cn.md`

They link to:

```text
.opencode/INSTALL.md
```

That path does not exist in the repository.

Impact:

- install path for one advertised platform is incomplete
- documentation quality appears lower than the rest of the repo

### 3. Gemini support appears narrower than the README implies

`GEMINI.md` references only:

- `skills/rob-pike/SKILL.md`
- `skills/systematic-debugging/SKILL.md`

But the README markets the repository as a broader multi-skill system across platforms.

Interpretation:

- either Gemini integration is intentionally partial
- or Gemini packaging has not kept up with the full skill set

Either way, platform parity looks incomplete.

### 4. No executable automated test suite for the core asset

This repository's primary asset is skill behavior encoded in Markdown. That behavior is hard to test automatically, and the repo currently relies mostly on:

- human review
- grep/build-only checks
- internal plan/review process

Impact:

- excellent process documentation, but weak mechanical enforcement
- drift and regression are still possible across docs, metadata, and host adapters

### 5. Publishing the repository root to GitHub Pages broadens exposure

`deploy.yml` uploads `path: .`

This is operationally simple, but it means the public artifact surface includes more than the minimal website payload.

Impact:

- good transparency
- weaker separation between public site assets and internal project files

## 12. Internal Governance Quality

A notable strength is that the repo records its own self-critique.

The review document `docs/engineering-discipline/reviews/2026-04-01-long-running-harness-review.md` documents 12 governance gaps and marks the work `FAIL` before hardening. That is a strong signal that the maintainers are not only producing process docs, but also auditing them adversarially.

This is unusually mature for a prompt-driven repository.

## 13. Detailed Interpretation by Layer

### Layer 1: Canonical knowledge layer

`skills/*/SKILL.md`

This is the true source of behavior. If anything conflicts with these files, these files should be treated as authoritative.

### Layer 2: Presentation layer

`README*.md`, `index*.html`, `skills/*.html`, `skills/en/*.html`

This layer improves discoverability and adoption, but it is derivative. It is also the layer most likely to drift.

### Layer 3: Distribution layer

`.claude-plugin/`, `.cursor-plugin/`, `.codex/`, `GEMINI.md`

This layer determines actual platform reach. It is currently useful, but not fully uniform.

### Layer 4: Operational memory layer

`docs/engineering-discipline/plans/` and `reviews/`

This layer proves the maintainers are applying the framework to the framework itself.

## 14. Practical Recommendations

### High priority

1. Fix repository URL drift in plugin manifests.
2. Add the missing `.opencode/INSTALL.md` or remove the README links.
3. Decide whether `GEMINI.md` should expose the full skill chain or explicitly document partial support.

### Medium priority

4. Separate publishable site files from repository-internal files before Pages deployment.
5. Add consistency checks for:
   - repository URL
   - install guide path existence
   - skill count parity across README/site/platform adapters
6. Add a generated manifest from canonical `SKILL.md` sources to reduce drift.

### Nice to have

7. Generate HTML skill pages from `SKILL.md` automatically.
8. Add repository health checks in CI for broken internal links and missing files.

## 15. Final Assessment

`engineering-discipline` is a high-signal prompt-systems repository with a clearer architecture than most AI-agent skill collections. Its strongest quality is not breadth, but discipline: it encodes adversarial verification, stateful orchestration, and anti-bias guardrails into the workflow itself.

The repository is best understood as an engineering operating model for AI coding agents, wrapped in a multi-platform plugin/docs package.

If maintained carefully, it can become a strong reference implementation for process-oriented agent skills. If left without consistency automation, its main risk is not algorithmic failure but documentation and packaging drift.

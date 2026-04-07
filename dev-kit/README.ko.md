# Dev Kit

[English](./README.md) | 한국어

Claude Code와 Codex를 위한 구조화된 개발 워크플로우 플러그인입니다.

## 개요

Dev Kit은 하나의 공식 개발 흐름만 제공합니다.

`clarify -> planning -> execute -> review-execute`

모든 작업은 이 네 phase를 모두 거칩니다. 복잡도는 여전히 중요하지만, 이제는 사용자에게 보이는 라우팅이 아니라 각 phase의 깊이만 바꿉니다. 요청이 이미 충분히 명확하면 `clarify`는 direct mode로 짧게 끝날 수 있고, trivial work라면 `planning`은 minimal approved plan만 freeze할 수 있지만, 두 phase 자체를 생략하지는 않습니다. 내부적으로 `planning`은 `planner`, `critic`, `readiness-checker`를 사용하지만 사용자에게는 여전히 하나의 phase로 보입니다. 그 뒤 `execute`는 순수 실행 단계로 동작하고, `review-execute`는 승인된 plan 기준으로 최종 결과를 검증합니다.

세션 복구는 공용 상태 헬퍼를 통해 각 phase skill 안에 통합되어 있습니다. 더 이상 별도의 visible skill이 아닙니다.
재개 대상은 `in_progress`와 `paused`입니다. `completed`는 복구 후보에서 제외됩니다.

플러그인은 워크스페이스 루트의 `.dev-kit/` 아래에 상태를 저장합니다.

- `.dev-kit/current.json`은 재개 가능한 세션이 있을 때 우선 포인터 역할을 합니다.
- `.dev-kit/sessions/<session-id>/state.json`은 machine-readable source of truth입니다.
- `brief.md`, `plan.md`, `plan-review.md`, `review.md`는 사람이 읽는 문서로 같은 세션 디렉터리에 저장됩니다.
- `checkpoints/`는 phase 실행 중 생성되는 checkpoint JSON을 저장합니다.

이 저장 방식은 호환성이 깨지는 변경입니다. 기존 Markdown 기반 세션 레이아웃은 더 이상 사용하지 않으며, 자동 마이그레이션도 하지 않습니다.

## 워크플로우

```text
clarify -> planning -> execute -> review-execute

clarify
  - 모든 새 작업의 필수 진입 phase다
  - 모호함을 줄이거나 모호함이 거의 없음을 확인한다
  - 요청 명확도에 따라 interactive mode 또는 direct mode로 동작한다
  - brief.md를 작성한다
  - state.json과 current.json을 초기화한다
  - 다음 visible step을 planning으로 남긴다

planning
  - execute 직전의 필수 phase다
  - minimal plan 또는 full approved plan.md를 작성한다
  - planner 초안 작성 뒤 critic와 readiness-checker의 독립 검토를 수행한다
  - 집계된 승인 결과를 plan-review.md에 기록한다
  - 승인 전에 execute readiness를 검증한다
  - 승인된 plan을 freeze한 뒤 execute로 넘긴다

execute
  - 승인된 plan을 읽는다
  - worker-validator 실행과 checkpointing을 수행한다
  - 구현이 끝나면 바로 review-execute로 진행한다

review-execute
  - 승인된 plan 기준으로 최종 독립 검증을 수행한다
  - 항상 review.md를 작성한다
  - implementation drift만 execute로 되돌린다
```

품질 및 디버깅 스킬은 독립적으로 유지되며, 사용자가 명시적으로 호출하는 방식입니다.

## Active Session Hooks

Dev Kit은 두 개의 read-only hook을 제공합니다.

- `SessionStart`
- `UserPromptSubmit`

두 hook 모두 워크스페이스 루트를 해석하고, 공용 session-recovery helper를 사용합니다. 우선 `.dev-kit/current.json`을 보고, 필요하면 `.dev-kit/sessions/*/state.json`을 스캔한 뒤 짧은 요약을 출력합니다.

- `session_id`
- `current_phase`
- `status`
- `next_action`
- `execution_profile`
- `plan_status`
- `plan_version`

재개 가능한 세션을 선택할 수 없으면 상태를 바꾸지 않고 한 줄 경고만 출력합니다.

## Skills

### Core Pipeline

| Skill | Trigger | Description |
|---|---|---|
| **clarify** | Dev Kit 흐름에 들어오는 모든 새 작업, 특히 모호하거나 불완전한 요청 | 필수 진입 phase입니다. Context Brief를 만들고, 복잡도를 평가하며, `.dev-kit/` 세션 상태를 초기화합니다. 이미 명확한 작업은 긴 Q&A 대신 direct clarify로 짧게 처리할 수 있습니다. |
| **planning** | clarify 완료 후, 또는 필수 pre-execute planning phase를 재개할 때 | 필수 pre-execute phase입니다. minimal plan 또는 full approved `plan.md`를 쓰고, 내부적으로 `planner -> critic + readiness-checker` 검토 번들을 수행하고, 집계된 결과를 `plan-review.md`에 기록하고, execute readiness를 증명한 뒤 active session state를 실행 상태로 업데이트합니다. |
| **execute** | "run the plan", "execute the plan", "let's start implementing" | 승인된 plan만 실행하는 통합 실행 오케스트레이터입니다. worker-validator loop를 돌리고, phased run용 checkpoint JSON을 쓰고, 완료된 작업을 review-execute로 넘깁니다. |
| **review-execute** | "review the work", "verify the implementation", "check if the plan was executed correctly" | 승인된 plan에 대한 최종 독립 검증입니다. |

### Debugging

| Skill | Trigger | Description |
|---|---|---|
| **systematic-debugging** | 버그, 테스트 실패, 예상 밖 동작 | Define -> Reproduce -> Evidence -> Isolate -> Lock -> Fix -> Verify의 7단계 디버깅 워크플로우입니다. |

### Code Quality

| Skill | Trigger | Description |
|---|---|---|
| **karpathy** | 구현 전 코드 읽기 없이 수정하려고 할 때, 또는 "implement..."류 요청 | read before write, 좁은 범위 유지, 가정 검증, 성공 기준 정의를 강제하는 구현 규율입니다. |
| **rob-pike** | "optimize", "slow", "performance", "speed up" | 측정 기반 최적화 규율입니다. |
| **clean-ai-slop** | "clean up", "deslop", "clean AI code" | AI가 만든 코드에서 자주 나오는 냄새를 순차 패스로 제거합니다. `.dev-kit/**` 메타데이터는 제외합니다. |
| **simplify-code** | "simplify", "clean up the code", "review the changes" | reuse, quality, efficiency 관점에서 diff를 병렬 리뷰합니다. `.dev-kit/**` 메타데이터는 검토 범위에서 제외합니다. |

## 상태 모델

### Workspace Root Resolution

Dev Kit은 canonical workspace root를 다음 순서로 결정합니다.

1. `DEV_KIT_STATE_ROOT`
2. git top-level
3. 현재 작업 디렉터리

JSON에 저장되는 모든 상태 경로는 이 루트를 기준으로 한 상대 경로입니다.

### `.dev-kit/current.json`

```json
{
  "schema_version": 1,
  "session_id": "2026-04-06T16-30-auth-refactor",
  "session_path": ".dev-kit/sessions/2026-04-06T16-30-auth-refactor",
  "updated_at": "2026-04-06T16:45:00+09:00"
}
```

### `.dev-kit/sessions/<session-id>/state.json`

필수 필드는 다음과 같습니다.

- `schema_version`
- `session_id`
- `title`
- `feature_slug`
- `status`
- `current_phase`
- `execution_profile`
- `plan_status`
- `plan_version`
- `next_action`
- `artifacts`
- `phase_status`
- `created_at`
- `updated_at`

선택 필드:

- `failure_reason`

번들된 스키마는 `schema/state.schema.json`에 있습니다.

### Status Semantics

- `in_progress` — 세션이 `clarify`, `planning`, `execute`, `review-execute` 중 하나 안에서 진행 중인 상태
- `completed` — `review-execute`가 통과한 뒤의 최종 성공 상태
- `failed` — 실행 드리프트, 검증 반복 실패, 워크플로에서 회복 불가한 실패가 기록된 상태
- `paused` — 외부 의존성 또는 사용자 결정 대기 등으로 재개가 필요한 중단 상태

`failure_reason`은 `status`가 `failed` 또는 `paused`가 아니면 `null`이어야 하며, 해당 상태에서는 설명 문자열이 필수입니다.

승인된 plan이 실제로는 실행 불가능한 것으로 드러나더라도, 그 상황은 정상 상태 그래프 밖에서 해결해야 하는 planning contract violation으로 취급합니다.

### Plan Status Semantics

- `not_started` — planning에 들어갈 만큼 clarify는 끝났지만 아직 초안 plan이 없음
- `drafting` — planning이 `plan.md`를 작성 중인 상태
- `in_review` — `critic`와 `readiness-checker`가 현재 draft plan을 검토 중인 상태
- `revising` — critique 또는 readiness 결과를 반영해 draft를 수정 중인 상태
- `approved` — plan이 freeze되었고 `execute`로 넘어갈 수 있는 상태

### Phase Status Semantics

- `pending` — 계획된 phase가 아직 시작되지 않음
- `executing` — phase가 현재 실행 중
- `completed` — phase가 성공적으로 끝남

### 사람이 읽는 산출물

각 세션 디렉터리에는 다음 파일이 있을 수 있습니다.

- `brief.md`
- `plan.md`
- `plan-review.md` — 원시 reviewer 로그가 아니라 planning 승인 근거를 모은 집계 문서
- `review.md`
- `progress.md` — append-only 실행 진행 로그, `state.json`에 추적하지 않음
- `handoff.md` — context reset mode용 통합 재개 스냅샷, `state.json`에 추적하지 않음
- `checkpoints/*.json`

이 문서들은 사람을 위한 것이고, machine-readable source of truth는 항상 `state.json`입니다.

## 핵심 설계 원칙

**One Visible Flow** — 모든 작업은 `clarify -> planning -> execute -> review-execute`를 통과하며, 복잡도는 사용자에게 보이는 라우팅이 아니라 phase 깊이에만 영향을 줍니다.

**Planning Owns Plan Quality** — `planning`은 `execute` 전에 plan을 draft, critique, readiness-check, revise, freeze까지 마쳐야 합니다.

**Planning Closes Execute Readiness** — 환경, 검증, 의존성, worktree 가정은 `planning`에서 증명해야 하며 `execute`로 미루지 않습니다.

**Planning Uses Internal Role Isolation** — `planner`, `critic`, `readiness-checker`는 서로 독립적으로 동작하고, orchestrator만 `.dev-kit` 상태와 산출물을 기록합니다.

**Pure Execute Stage** — `execute`는 승인된 plan을 소비해 구현과 검증을 수행하며, planning을 다시 열거나 새 workflow state를 만들지 않습니다.

**Clarify And Planning Always Exist** — 이미 명확한 작업은 direct clarify를 사용하고, trivial work는 minimal approved plan을 사용하지만, execute는 두 상위 phase가 materialize되기 전에는 시작하지 않습니다.

**Review-Execute Verifies Results Only** — `review-execute`는 최종 코드베이스를 승인된 plan과 비교하고, implementation drift가 있을 때만 `execute`로 돌려보냅니다.

**JSON Source Of Truth** — `state.json`이 canonical source이고, Markdown 문서는 사람이 읽는 파생물입니다.

**Shared Session Recovery** — planning, execute, review-execute는 별도 `resume` skill 대신 공용 `.dev-kit/current.json` 포인터와 session scan helper를 사용합니다.

**Worker-Validator Isolation** — task validator는 worker output과 분리되고, final review도 execution context와 분리됩니다.

**Single Writer State** — 특히 phased execution이나 worktree 기반 실행에서는 orchestrator만 session JSON을 갱신합니다.

**Checkpointed Recovery** — phased execution은 integration gate 통과 후 checkpoint JSON을 기록해서, 별도 recovery stage 없이도 안전하게 재시작할 수 있게 합니다.

## Quick Start

```text
"Clarify this task, create a plan, execute it, and run review-execute on the result."
"Debug this failing test with systematic root-cause analysis."
"Review and simplify the changed code for quality issues."
```

## 프로젝트 구조

```text
dev-kit/
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
├── .mcp.json
├── .app.json
├── hooks/
│   ├── hooks.json
│   ├── session-start.sh
│   └── user-prompt-submit.sh
├── schema/
│   └── state.schema.json
├── scripts/
│   └── dev_kit_state.py
├── tests/
│   └── test_dev_kit_state.py
├── README.md
├── README.ko.md
├── assets/
│   ├── icon.png
│   └── logo.png
└── skills/
    ├── clarify/SKILL.md
    ├── planning/SKILL.md
    ├── execute/SKILL.md
    ├── review-execute/SKILL.md
    ├── systematic-debugging/
    ├── karpathy/SKILL.md
    ├── rob-pike/SKILL.md
    ├── clean-ai-slop/SKILL.md
    └── simplify-code/SKILL.md
```

## License

MIT

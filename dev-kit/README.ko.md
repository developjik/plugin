# Dev Kit

[English](./README.md) | 한국어

Dev Kit은 Claude Code와 Codex를 위한 구조화된 개발 워크플로우 플러그인입니다. 일반 구현 작업에 하나의 공식 흐름을 적용하고, 세션 상태를 `.dev-kit/` 아래에 남기며, 디버깅과 코드 품질 검토는 별도의 명시적 스킬로 유지합니다.

## 언제 쓰는가

다음처럼 추적 가능한 구현 워크플로우가 필요할 때 메인 Dev Kit 흐름을 사용합니다.

- 기능 개발이나 리팩터링을 `brief.md`, `plan.md`, `review.md` 같은 산출물과 함께 관리하고 싶을 때
- `.dev-kit/current.json` 또는 재개 가능한 세션을 기준으로 작업을 이어가고 싶을 때
- 계획, 실행, 최종 검증을 명시적으로 분리하고 싶을 때

다음처럼 일반적인 기능 구현이 아닌 작업은 독립 스킬을 사용합니다.

- 버그, 플래키 테스트, 예상 밖 동작은 `systematic-debugging`
- 변경 후 정리와 품질 검토는 `simplify-code` 또는 `clean-ai-slop`
- 성능 작업은 `rob-pike`
- `.dev-kit/learnings/` 지식 저장소 관리는 `compound`

## 설치

이 README만 직접 열었다면 먼저 플러그인을 설치해야 합니다.

- Codex: [../docs/guides/install/codex-local-plugin-install.ko.md](../docs/guides/install/codex-local-plugin-install.ko.md)
- Claude Code: [../docs/guides/install/claude-code-local-plugin-install.ko.md](../docs/guides/install/claude-code-local-plugin-install.ko.md)

## 워크플로우 한눈에 보기

Dev Kit의 공식 구현 흐름은 다음과 같습니다.

`clarify -> planning -> execute -> review-execute`

이 흐름이 보장하는 것은 다음과 같습니다.

- 일반 실행을 시작하기 전에 `clarify`와 `planning` 산출물이 준비됩니다.
- 훅은 읽기 전용이며 단계를 자동 시작하거나 자동 재개하지 않습니다.
- `planning`이 계획 품질과 실행 준비 상태를 책임집니다.
- `execute`는 승인된 계획을 따르며, 실행 중에 새 계획을 다시 만들지 않습니다.
- `review-execute`는 실행 컨텍스트와 분리된 상태에서 최종 검증을 수행합니다.

## 빠른 시작

### 일반 기능 작업

1. 워크플로우를 명시적으로 시작합니다.

   ```text
   이 작업에 Dev Kit을 사용해줘. 주문 페이지에 CSV 내보내기를 추가하는 작업을 clarify부터 시작해줘.
   ```

2. `clarify` 이후에는 다음 파일이 생깁니다.
   - `.dev-kit/current.json`
   - `.dev-kit/sessions/<session-id>/state.json`
   - `.dev-kit/sessions/<session-id>/brief.md`

3. 다음 단계로 계획을 진행합니다.

   ```text
   현재 활성 Dev Kit 세션에 대해 planning을 실행해줘.
   ```

4. `planning` 이후에는 다음 파일을 기대할 수 있습니다.
   - `.dev-kit/sessions/<session-id>/plan.md`
   - `.dev-kit/sessions/<session-id>/plan-review.md`

5. 승인된 계획을 실행합니다.

   ```text
   승인된 Dev Kit 계획을 execute해줘.
   ```

6. `execute` 이후에는 코드 변경과 함께 다음 실행 산출물이 추가될 수 있습니다.
   - `.dev-kit/sessions/<session-id>/progress.md`
   - 단계 분할 실행일 때 `.dev-kit/sessions/<session-id>/checkpoints/*.json`
   - 컨텍스트 리셋 모드를 쓸 때 `.dev-kit/sessions/<session-id>/handoff.md`

7. 마지막으로 최종 검증을 실행합니다.

   ```text
   현재 활성 Dev Kit 세션에 대해 review-execute를 실행해줘.
   ```

8. `review-execute` 이후에는 다음 파일을 기대할 수 있습니다.
   - `.dev-kit/sessions/<session-id>/review.md`
   - 재사용 가능한 학습을 추출한 경우 `.dev-kit/sessions/<session-id>/compound.md`

### 독립 진입점

```text
이 실패하는 테스트를 systematic-debugging으로 디버깅해줘.
변경된 코드를 simplify-code로 검토해줘.
Dev Kit 학습 저장소를 compound refresh로 정리해줘.
```

## 작업은 어떻게 시작되는가

새 작업의 기본 진입점은 `clarify`입니다. 요청이 모호하면 짧은 탐색 루프를 돌고, 이미 충분히 구체적이면 direct clarify로 빠르게 정리합니다.

`planning`도 여전히 필수 실행 전 단계이지만, 다음 조건을 모두 만족하면 direct-clarify 산출물을 직접 만들면서 시작할 수 있습니다.

- 재개 가능한 세션이 없고
- 요청이 바로 계획을 만들 만큼 충분히 구체적이며
- 짧은 `brief.md`를 즉시 만들 수 있을 때

즉, 기본 규칙은 "먼저 `clarify`"이고, 예외적으로 이미 명확한 작업은 `planning`이 바로 진입하는 빠른 경로를 가질 수 있습니다.

## 핵심 단계

| 단계 | 역할 | 주요 산출물 |
|---|---|---|
| `clarify` | 범위, 성공 기준, 제약, 기술 컨텍스트를 잠그고 복잡도를 평가하며 세션 상태를 초기화합니다. | `current.json`, `state.json`, `brief.md` |
| `planning` | 실행 가능한 계획을 만들고, 내부 `planner -> critic + readiness-checker` 검토를 거쳐 승인된 계획을 고정합니다. | `plan.md`, `plan-review.md` |
| `execute` | 승인된 계획을 worker-validator 루프, 체크포인트, 재개 가능한 상태 갱신으로 수행합니다. | 코드 변경, `progress.md`, 선택적 `checkpoints/*.json`, 선택적 `handoff.md` |
| `review-execute` | 승인된 계획을 기준으로 분리된 최종 검증을 수행합니다. | `review.md`, 선택적 `compound.md` |

### `review-execute`의 격리 모델

`review-execute`는 단순한 마지막 체크리스트가 아닙니다. 오케스트레이터가 세션 탐색과 사전 점검을 수행한 뒤, 독립된 리뷰어 에이전트를 실행합니다. 이 리뷰어는 `plan.md`, `plan-review.md`, `state.json`, 그리고 실제 코드베이스만 읽고 검증하며, 실행 로그나 워커 출력은 읽지 않습니다.

## 훅

Dev Kit은 두 개의 읽기 전용 훅을 제공합니다.

- `SessionStart`
- `UserPromptSubmit`

이 훅들이 하는 일:

- 워크스페이스 루트를 해석합니다.
- 먼저 `.dev-kit/current.json`을 보고, 필요하면 `.dev-kit/sessions/*/state.json`을 스캔해 우선 세션을 찾습니다.
- 현재 활성 세션 또는 재개 가능한 세션의 수동 컨텍스트를 보여줍니다.

이 훅들이 하지 않는 일:

- `clarify`, `planning`, `execute`, `review-execute`를 자동 시작하지 않습니다.
- 세션 상태를 변경하지 않습니다.
- 다음 단계를 임의로 선택하지 않습니다.

`SessionStart`는 수동 `additionalContext`를 추가합니다. 산출물 상태에 따라 다음 정보가 포함될 수 있습니다.

- 세션 요약
- 최근 진행 상황
- 핸드오프 재개 지점
- Compound Learning 요약

`UserPromptSubmit`는 현재 세션에 대한 간단한 한 줄 요약을 출력합니다. 예를 들면 다음과 같습니다.

```text
Dev Kit: 2026-04-06T16-30-auth-refactor | phase=planning | status=in_progress | next=Run planning. Read .dev-kit/sessions/2026-04-06T16-30-auth-refactor/brief.md. | profile=medium | plan=not_started/v0 | compound=none
```

이 줄이 보인다는 뜻은 훅이 세션 상태를 찾았다는 의미입니다. 단계가 자동으로 시작됐다는 뜻은 아닙니다.

## 재개는 어떻게 동작하는가

세션 복구는 단계 스킬과 훅이 공용으로 사용합니다.

- 우선 포인터: `.dev-kit/current.json`
- 대체 탐색: `.dev-kit/sessions/*/state.json`
- 재개 가능한 상태: `in_progress`, `paused`
- 재개 대상이 아닌 상태: `completed`

재개 가능한 세션이 여러 개 있는데 유효한 `current.json`이 없으면, Dev Kit은 임의로 고르지 않고 경고를 반환하며 명시적 포인터를 요구합니다.

## 세션 파일

모든 세션 상태는 워크스페이스 루트의 `.dev-kit/` 아래에 저장됩니다.

| 경로 | 용도 |
|---|---|
| `.dev-kit/current.json` | 현재 활성 세션 또는 우선 재개 세션을 가리키는 포인터 |
| `.dev-kit/sessions/<session-id>/state.json` | 기계가 참조하는 기준 세션 상태 파일 |
| `.dev-kit/sessions/<session-id>/brief.md` | 범위, 제약, 성공 기준, 복잡도 평가를 담는 clarify 산출물 |
| `.dev-kit/sessions/<session-id>/plan.md` | 승인된 실행 계획의 기준 문서 |
| `.dev-kit/sessions/<session-id>/plan-review.md` | critic와 readiness checking의 집계된 planning 판정 기록 |
| `.dev-kit/sessions/<session-id>/review.md` | `review-execute`의 최종 검증 결과 |
| `.dev-kit/sessions/<session-id>/progress.md` | 오케스트레이터가 기록하는 추가 전용 실행 로그 |
| `.dev-kit/sessions/<session-id>/handoff.md` | 컨텍스트 리셋 모드에서 사용하는 재개 스냅샷 |
| `.dev-kit/sessions/<session-id>/checkpoints/*.json` | 단계 분할 실행을 위한 체크포인트 |
| `.dev-kit/sessions/<session-id>/compound.md` | 이번 작업에서 추출한 세션 로컬 학습 |
| `.dev-kit/learnings/index.json` | 전역 학습 인덱스 |
| `.dev-kit/learnings/<id>.md` | 이후 세션에서 재사용되는 개별 학습 문서 |

## 상태 헬퍼 CLI

`scripts/dev_kit_state.py`는 훅과 단계 스킬이 함께 사용하는 공용 계약입니다.

자주 쓰는 명령은 다음과 같습니다.

- `summary`: 우선 재개 세션 요약 출력
- `resolve-workspace-root`: 현재 호출 기준의 워크스페이스 루트 해석
- `write-json`: `.dev-kit` JSON 파일을 안전하게 갱신
- `learnings-summary`: 관련 Compound Learning 요약 출력
- `bump-learning`: 실제로 참조한 학습의 카운터 갱신
- `clear-current`: 대상 세션을 가리킬 때만 `current.json` 제거

## 워크스페이스 루트 해석

Dev Kit은 워크스페이스 루트를 다음 순서로 결정합니다.

1. `DEV_KIT_STATE_ROOT`
2. 가장 가까운 기존 `.dev-kit` 루트
3. git top-level
4. 현재 작업 디렉터리

JSON에 저장되는 모든 경로는 이 루트를 기준으로 한 상대 경로여야 합니다.

## 지원 스킬

### 워크플로우 지원

| 스킬 | 역할 |
|---|---|
| `compound` | `.dev-kit/learnings/` 아래의 재사용 가능한 학습을 추출, 갱신, 조회합니다. 사용자가 원하면 완료된 작업뿐 아니라 진행 중인 작업에서도 학습을 추출할 수 있습니다. |

### 디버깅

| 스킬 | 역할 |
|---|---|
| `systematic-debugging` | Define -> Reproduce -> Evidence -> Isolate -> Lock -> Fix -> Verify의 7단계 디버깅 워크플로우 |

### 코드 품질

| 스킬 | 역할 |
|---|---|
| `karpathy` | read-before-write 구현 규율 |
| `rob-pike` | 측정 기반 성능 개선 규율 |
| `clean-ai-slop` | AI 생성 코드에서 자주 보이는 냄새 제거 |
| `simplify-code` | 변경된 코드의 재사용성, 품질, 효율성 검토 |

## 기여자 참고 자료

핵심 구현과 참조 문서:

- [skills/clarify/SKILL.md](./skills/clarify/SKILL.md)
- [skills/planning/SKILL.md](./skills/planning/SKILL.md)
- [skills/execute/SKILL.md](./skills/execute/SKILL.md)
- [skills/review-execute/SKILL.md](./skills/review-execute/SKILL.md)
- [skills/compound/SKILL.md](./skills/compound/SKILL.md)
- [scripts/dev_kit_state.py](./scripts/dev_kit_state.py)
- [hooks/hooks.json](./hooks/hooks.json)
- [schema/state.schema.json](./schema/state.schema.json)
- [schema/learnings-index.schema.json](./schema/learnings-index.schema.json)
- [tests/test_dev_kit_state.py](./tests/test_dev_kit_state.py)

## 프로젝트 구조

```text
dev-kit/
├── .claude-plugin/
├── .codex-plugin/
├── .mcp.json
├── .app.json
├── assets/
├── hooks/
├── schema/
├── scripts/
├── skills/
├── tests/
├── README.md
└── README.ko.md
```

## 라이선스

MIT

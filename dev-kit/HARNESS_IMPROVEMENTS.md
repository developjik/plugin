# Dev Kit 개선 분석: Anthropic Harness 설계 원칙 기반

## 참고 문서
- [Harness Design for Long-Running Application Development](https://www.anthropic.com/engineering/harness-design-long-running-apps) (2025-11-26)
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (2026-03-24)

### 중요한 맥락
두 글 사이의 시간차(약 2.5개월)는 중요합니다. 초기 글에서 강조하던 sprint scaffolding, multi-session handoff, feature list tracking은 **모델 성능 향상에 따라 최신 글에서는 단순화되는 방향**으로 변합니다. 따라서 Dev Kit에 필요한 것은 "필수 구조"가 아니라 **profile-gated optional mode**입니다.

---

## 1. 현재 dev-kit이 이미 잘 하고 있는 부분

| Anthropic 권장사항 | dev-kit 현장 상태 |
|---|---|
| JSON source of truth | `state.json` + schema validation ✓ |
| Generator-Evaluator 분리 | worker-validator isolation, review-execute 독립 ✓ |
| Planning → Execute 분리 | clarify → planning → execute → review-execute ✓ |
| 독립적 critique | critic + readiness-checker 병렬 검토 ✓ |
| 파일 기반 에이전트 간 통신 | brief.md, plan.md, plan-review.md, review.md ✓ |
| Checkpoint/Recovery | phased execution + checkpoint JSON ✓ |
| 강한 행동 제약 | Hard Gates로 각 phase 경계 엄격히 유지 ✓ |
| Pure Execution | execute는 planning을 다시 열지 않음 ✓ |
| Review Isolation | review-execute는 plan.md + 코드만 봄 ✓ |

---

## 2. Context Reset: Profile-Gated Optional Mode

### 배경
- 2025-11 글: Context anxiety 해결을 위해 context reset (clean slate + handoff artifact) 강력 권장
- 2026-03 글: "더 강한 모델"에서는 context reset 불필요 → sprint scaffolding 제거
- **결론**: 필수가 아닌 선택적 최적화

### Profile별 필요도
| Profile | 필요도 | 근거 |
|---|---|---|
| Low | ✗ 불필요 | 한 세션 내 완료 예상 |
| Medium | △ Optional | 2-3시간 이상 실행 시 검토 |
| High | ○ 권장 | 장시간 multi-phase 실행, context anxiety 위험 |

### 구현 전략 (Optional)
**활성화 조건**: Medium/High profile에서만 기능 제공

1. planning 단계에서 "context reset enabled" 옵션 표시
2. execute에서 checkpoint JSON을 더 풍부한 handoff artifact로 확장
3. Context reset 필요 시 깨끗한 context로 새 session 시작 (기존 session 종료)
4. Checkpoint에서 진행 상태 복구

**호환성**: 옵션이므로 disable 가능, 현재 continuous session 방식 유지 가능

### 구현 위치
- `skills/planning/SKILL.md` — Execution Strategy 섹션에 "Context Reset Mode" 옵션 기술
- `skills/execute/SKILL.md` — Recovery 섹션 확장 (context reset from checkpoint)

---

## 3. Progress Log (Resume Artifact) — Schema 비확장

### 문제
세션이 중단되면 checkpoint JSON만으로는 "무엇을 했고, 어디서 멈췄고, 다음 단계"를 사람이 빠르게 파악하기 어려움

### 개선안: Artifact로 추가 (schema 변경 없음)

**핵심**: `.dev-kit/sessions/<session-id>/progress.md` 추가
- **state.json과 분리** — artifacts 필드 없이 순수 산출물로만 존재
- execute가 task 완료 시마다 append (파일 기반)
- Markdown 형식 → hook과 에이전트가 즉시 읽을 수 있음
- **기존 `state.json` schema 무수정**

### 파일 포맷 예시
```markdown
# Execution Progress Log

**Session:** 2026-04-06T16-30-auth-refactor
**Plan Version:** 1
**Status:** In Progress (Phase P1, Task 3/5)

## Completed Tasks

- Task 1: Update auth middleware ✓ (18m) [3a7b8c9]
- Task 2: Add JWT generation ✓ (22m) [5f2e1d4]

## Current Task

Task 3: Session persistence (IN PROGRESS)
- Started: 2026-04-06T17:15:00+09:00
- Working on: src/db/sessions.ts

## Remaining

- Task 4: Add logout endpoint
- Task 5: Update API auth checks
```

### 구현 위치
- `skills/execute/SKILL.md` — Step 2-2 Worker Implementation 후 progress.md에 append
- `hooks/render-session-summary.sh` — 확장하여 progress.md의 마지막 N줄도 출력

---

## 4. Session-Start Context 강화 (Hook 확장)

### 문제
현재 session-start hook은 한 줄 요약만 출력. 에이전트가 세션 복구 시 "무엇을 읽어야 하는가"를 명시적으로 받지 않음

### 개선안
`session-start.sh` hook 확장: progress.md 마지막 N줄, 최근 git log, 다음 action 함께 출력 (기존 한 줄 요약 + 맥락)

### 출력 예시
```
=== Dev Kit Session Resume ===

Session: 2026-04-06T16-30-auth-refactor
Phase: execute | Status: in_progress | Next: Continue Task 3

Recent Progress (last 3 tasks):
  ✓ Task 1: Update auth middleware (3a7b8c9)
  ✓ Task 2: Add JWT generation (5f2e1d4)
  → Task 3: Session persistence (IN PROGRESS)

Latest git log (last 3):
  5f2e1d4 Task 2: Add JWT token generation
  3a7b8c9 Task 1: Update authentication middleware

Action: Continue executing Task 3. Run `cat progress.md` for full log.
```

### 구현 위치
- `hooks/render-session-summary.sh` — 리팩토링하여 progress.md, git log 함께 출력

---

## 5. Planning의 E2E 검증 도구 탐지

### 문제
Discover Verification 단계에서 "어떤 검증을 할 수 있을까"를 자동으로 탐지하지 않음. 브라우저 E2E 테스팅 도구(Playwright, Puppeteer) 가용성을 고려하지 않음

### 개선안
planning의 **Step 1: Discover Verification**을 확장하여 탐지:
- 웹 앱: init.sh 제공, localhost:port 검증 가능한가?
- API: Postman collection, curl test 검증 가능한가?
- CLI: 간단한 smoke test 스크립트 검증 가능한가?

가용성에 따라 Verification Strategy 조정

### 구현 위치
- `skills/planning/SKILL.md` — Step 1 "Discover Verification" 섹션 상세화
- 기존 readiness-checker의 environment verification과 통합

---

## 6. Evaluator 보정 자산 분리 (Review-Execute 가이드라인)

### 문제
Validator/Evaluator가 너무 관대하거나 너무 엄격할 수 있음. Few-shot calibration이 스킬 문서에 명시되지 않음

### 개선안: 스킬 가이드라인 강화 (state 변경 없음)

`skills/review-execute/SKILL.md`에 **Evaluator Calibration** 섹션 추가:
- "PASS해야 하는 경우" vs "FAIL해야 하는 경우" 명시적 예시
- plan.md의 acceptance criteria vs review 판정의 관계 명확화
- 한 세션 내 판정 일관성 유지 가이드

### 예시 구조
```markdown
## Evaluator Calibration

### ✓ PASS 기준
- [Feature A] 기능이 계획된 대로 동작하는가?
- [Feature B] 사용자 시나리오를 모두 완료할 수 있는가?
- [Performance] 명시된 성능 목표를 달성하는가?

### ✗ FAIL 기준 (판정하지 않기)
- "UI가 깔끔하지 않다" (plan에 없음)
- "코드가 더 효율적일 수 있다" (acceptance criteria에 없음)
- "주변 모듈도 업그레이드해야 한다" (scope 밖)

### ✗ FAIL 기준 (판정하기)
- [Acceptance Criterion 1] 불만족 + 관찰 근거
- [Acceptance Criterion 2] 불만족 + 파일/line number 포함
```

### 구현 위치
- `skills/review-execute/SKILL.md` — Step 4: Reach Verdict 전에 추가

---

## 7. Low-Profile Fast Path (산출물 밀도 조절, phase 생략 아님)

### 문제
Low profile 작업에서도 모든 phase가 같은 양의 산출물을 요구. Trivial 작업에 과도한 ceremony

### 개선안: Phase 생략 아니라 **산출물 밀도 감소**

```
Low Profile (trivial 작업):
  clarify (direct mode, 문장 3줄 brief) 
  → planning (minimal approved plan, 필수 요소만)
  → execute (single-phase, light validation)
  → review-execute (PASS/FAIL 판정만, 상세 분석 없음)

High Profile (복잡한 작업):
  clarify (interactive discovery, 상세 brief)
  → planning (full plan, parallel groups, worktree 평가)
  → execute (multi-phase, 각 phase마다 checkpoint)
  → review-execute (상세 검증, acceptance criteria 항목별 평가)
```

**핵심**: phase 자체는 모두 통과하되, 내용/출력/깊이를 profile로 조절

### 구현 위치
- 각 스킬의 "When To Use" 섹션에 profile-specific guidance 추가
- `README.md`에 "Profile-Based Ceremony" 섹션 추가

---

## 8. ~~Sprint Contract~~ → Planning의 Acceptance Criteria 강화

### 제거된 제안
- **원래 제안**: execute에서 worker-validator간 "contract 협상" 추가
- **문제**: execute는 planning을 다시 열면 안 됨 (Pure Execute Stage 원칙 위반)
  - 근거: execute/SKILL.md line 10, README.md line 186
  
### 올바른 방향
**Planning 단계에서 acceptance criteria를 더 구체적으로 작성**
- Task-level criterion을 "검증 가능한" 형태로 명확화
- Planning의 readiness-checker가 "이 기준으로 PASS/FAIL 판정 가능한가?"를 검증

### 구현 위치
- `skills/planning/SKILL.md` — Canonical Plan Structure의 Task 정의 가이드 강화

---

## 9. ~~Task-level State Tracking in state.json~~ → Schema 보존

### 제거된 제안
- **원래 제안**: `state.json`에 tasks 배열 추가하여 진행 상태 추적
- **문제 1**: schema의 `additionalProperties: false` + `required` 필드 모두 변경 필요 = **breaking change**
- **문제 2**: review-execute가 task-level validator 결과를 입력으로 받으면 **review isolation 약화** (review-execute/SKILL.md line 12)

### 올바른 방향
**`state.json` schema 변경 없음**
- Task 상태는 **checkpoint JSON** + **progress.md**에만 기록
- review-execute는 여전히 plan.md + 코드만 보기 (isolation 유지)

---

## 10. Git Commit 정책 (선택적 가이드)

### 권장사항 (강제 아님)
- execute에서 각 task validator PASS 후 git commit 권장
- Commit message format: `[session-id] Task <id>: <name>`
- 실패 시 `git reset` 또는 checkpoint에서 복구 경로 제시

### 구현 위치
- `skills/execute/SKILL.md` — Step 2-3 Validator Review 후 가이드라인 추가 (SHOULD, MUST 아님)

---

## 우선순위별 구현 계획

### 우선 시작 (Low Friction, High Impact)

| 항목 | 구현 내용 | 난이도 | 작업량 |
|---|---|---|---|
| **Progress Log** | progress.md artifact 추가, execute에서 append | 낮음 | 2h |
| **Session-Start Hook 강화** | hook 출력 확장 (progress.md, git log) | 낮음 | 1h |
| **Evaluator Calibration** | review-execute에 가이드라인 섹션 추가 | 낮음 | 1h |

### 다음 단계 (Medium Friction, Foundational)

| 항목 | 구현 내용 | 난이도 | 작업량 |
|---|---|---|---|
| **Planning의 E2E 도구 탐지** | Step 1 확장하여 verify 도구 자동 탐지 | 중 | 3h |
| **Low-Profile Fast Path** | 각 스킬의 profile-specific guides | 중 | 3h |
| **Git Commit 정책** | execute 가이드라인 추가 | 낮음 | 1h |

### 선택적 (High Friction, Future)

| 항목 | 구현 내용 | 조건 | 난이도 | 작업량 |
|---|---|---|---|---|
| **Context Reset Mode** | checkpoint 기반 session reset | Medium/High profile만 | 높음 | 8h |

---

## 변경 사항 요약

### 제거된 제안 (구조와 충돌)
- ~~Sprint Contract in execute~~ → planning의 acceptance criteria 강화로 대체
- ~~Task-level state in state.json~~ → checkpoint JSON + progress.md로 대체 (schema 무수정)
- ~~Validator history in state~~ → review isolation 유지하므로 불필요
- ~~tasks.json as review input~~ → plan.md + 코드만 review (경계 유지)

### 수정된 제안 (Profile-Gated)
- **Context Reset**: "필수"에서 "Medium/High profile optional mode" 변경
- **Feature List tracking**: 불필요 (modern model, progress.md로 충분)
- **Multi-session handoff**: optional (checkpoint JSON 확장으로 커버)

### 유지된 제안 (즉시 가능)
- **Progress log** (artifact, state 무관)
- **Session-start summary** (hook 확장)
- **E2E capability detection** (planning 단계)
- **Evaluator calibration** (guidelines, state 무관)
- **Low-profile fast path** (density 조절, phase 생략 아님)

---

## 결론

Dev Kit은 이미 Anthropic의 "Pure Harness" 원칙을 잘 따르고 있습니다. 개선의 방향:

1. **구조 변경 아닌 강화**: 기존 경계(Pure Execute, Review Isolation, Schema)와 원칙을 유지하면서 가시성/복구성 개선
2. **Profile-Aware Design**: Low/Medium/High 작업의 필요도 다름을 인정하고 profile에 따른 차별화
3. **선택적 최적화**: Context reset, multi-session handoff 같은 것들은 옵션이지 필수가 아님

**가장 빠르게 진행할 수 있는 3개 항목**부터 시작하면, 이후 더 큰 개선사항의 기초가 됩니다:
1. Progress log (2h)
2. Session-start hook (1h)  
3. Evaluator calibration (1h)

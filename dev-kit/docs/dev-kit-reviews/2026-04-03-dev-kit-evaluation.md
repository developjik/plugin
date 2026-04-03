# dev-kit 종합 평가 보고서

**날짜:** 2026-04-03
**평가 대상:** dev-kit plugin v1.2.0 (skills 11개)
**평가 방법:** 4개 독립 에이전트 병렬 평가 (Architecture / Workflow Completeness / Naming & DX / Coherence & Anti-patterns)

---

## 1. 평가 에이전트별 총평

| 에이전트 | 평가 | 핵심 발견 |
|----------|------|-----------|
| **Architecture** | GOOD | 정보 격리 패턴이 최고 수준. `measure-performance`만 구조적으로 취약 |
| **Workflow Completeness** | GOOD | 파이프라인 자체는 강건. 리팩토링, 마이그레이션, 코드리뷰 커버리지 갭 존재 |
| **Naming & DX** | ADEQUATE~GOOD | README가 구 이름 그대로. 내부 제목 불일치. 트리거 단어 중복 |
| **Coherence** | GOOD | `remove-slop` vs `defense-in-depth` 모순이 최대 위험. 스킬 3계층 분류 불명확 |

---

## 2. 종합 평점

| 영역 | 등급 | 비고 |
|------|------|------|
| 정보 흐름 설계 | **EXCELLENT** | Worker-Validator 격리, 고정 템플릿, 파일 기반 핸드오프 |
| 에러 복구 | **GOOD** | 체크포인트/복구 시스템, 재시도 정책 일관성 |
| 패턴 일관성 | **GOOD** | 파이프라인 스킬은 템플릿 엄격. `measure-performance`만 이탈 |
| 워크플로우 커버리지 | **GOOD** | 신규 기능/버그픽스 강력. 리팩토링·마이그레이션·코드리뷰 공백 |
| 스킬 간 일관성 | **GOOD** | 모순 4건(1건 HIGH), 중복 3건(1건 MODERATE) |
| 명명 & DX | **ADEQUATE** | README/내부 제목 미갱신이 최대 걸림돌 |
| 플러그인 설정 | **GOOD** | `defaultPrompt` 3/11만 커버, 키워드 확장 필요 |
| 확장성 | **ADEQUATE** | 소규모 작업에 과도한 오버헤드, 중간 복잡도에 경량화 부재 |

---

## 3. 발견된 문제 (심각도순)

### HIGH (즉시 수정 권장)

| # | 문제 | 출처 | 상세 |
|---|------|------|------|
| H1 | README.md가 구 이름 11개를 그대로 사용 중 | Naming & DX | 이름 변경 작업이 README에 반영되지 않아 사용자에게 혼란 발생. `karpathy`, `rob-pike`, `clean-ai-slop` 등 구 이름이 그대로 노출됨 |
| H2 | SKILL.md 내부 `# 제목` 6개가 구 이름 사용 | Naming & DX | `craft-plan/` → "# Plan Crafting", `execute-plan/` → "# Run Plan", `verify-implementation/` → "# Review Work", `decompose-milestones/` → "# Milestone Planning (Ultraplan)", `orchestrate-execution/` → "# Long Run Harness", `simplify-changes/` → "# Simplify" |
| H3 | `remove-slop`가 `defense-in-depth`가 추가한 다층 검증을 제거 가능 | Coherence | remove-slop Pass 4(Defensive Paranoia)가 "Null checks on values guaranteed non-null"을 제거 대상으로 지정하지만, defense-in-depth가 의도적으로 추가한 다중 계층 검증과 구분 불가. 방어 가드 없음 |
| H4 | `plugin.json`의 `defaultPrompt`가 3/11 스킬만 커버 | Naming & DX | clarify+plan, execute, debug만 포함. verify, milestones, orchestration, simplify, remove-slop, write-surgically, measure-performance 누락 |

### MODERATE (개선 권장)

| # | 문제 | 출처 | 상세 |
|---|------|------|------|
| M1 | `simplify-changes` vs `remove-slop` 역할 중복 | Coherence, Naming | 양쪽 모두 "clean up" 트리거 매칭. 코멘트 정리, 추상화 제거 작업이 겹침. 사용자가 어느 스킬을 쓸지 판단 어려움 |
| M2 | 리팩토링, 코드리뷰, 마이그레이션 스킬 부재 | Completeness | 신규 기능/버그픽스만 커버. 기존 코드 구조 변경, PR 리뷰, DB 마이그레이션, 프레임워크 업그레이드 등에 대응 스킬 없음 |
| M3 | 소규모 작업(1~2파일)에 파이프라인 오버헤드 과대 | Completeness | 10분 작업에 clarify→craft-plan→execute-plan→verify-implementation 전체 파이프라인이 30~40분 소모 가능. 경량 경로 없음 |
| M4 | 스킬 3계층이 명시적으로 분류되지 않음 | Coherence | Thinking Discipline(write-surgically, measure-performance) / Corrective(remove-slop, simplify-changes, debug-systematically) / Workflow(clarify→execute→verify) 구분이 암묵적 |
| M5 | `craft-plan` 산출물과 `execute-plan` 검증자 템플릿 간 포맷 불일치 | Architecture | execute-plan validator가 "Acceptance Criteria" 필드를 기대하지만, craft-plan의 task 포맷에는 해당 필드가 명시적으로 없음. main agent가 추론해야 함 |
| M6 | `write-surgically` "defensive check 금지" vs `defense-in-depth` "모든 계층에 검증" | Coherence | write-surgically Rule 5: "null guard 하지 마라". defense-in-depth: "모든 계층에 검증 추가하라". 적용 시점(구현 vs 버그수정 후)은 다르지만 명시적 조율 없음 |
| M7 | `decompose-milestones` 트리거 "ultraplan"이 문서화되지 않은 전문 용어 | Naming & DX | description에 "ultraplan"이 트리거로 포함되어 있으나, 사용자가 이 단어를 자연스럽게 말할 리 없음 |

### LOW (참고사항)

| # | 문제 | 출처 | 상세 |
|---|------|------|------|
| L1 | `measure-performance`가 68줄로 다른 스킬의 ~1/9, 섹션 5개 누락 | Architecture | When NOT To Use, Anti-Patterns 테이블, Minimal Checklist, Transition, Completion Standard 없음. 참조 카드 수준 |
| L2 | `verify-implementation`이 execute-plan의 per-task 검증을 재수행 | Coherence | 의도적 독립 감사이지만 명시되지 않아 "중복 작업"으로 오인 가능 |
| L3 | 체크리스트 항목("No placeholders/TODO")이 4개 스킬에서 중복 | Coherence | execute-plan, verify-implementation, remove-slop, craft-plan 모두 동일 항목 포함 |
| L4 | 상태 파일 포맷에 버전 필드 없음 | Architecture | state.md, checkpoint 파일에 버전 정보가 없어 스킬 정의 변경 시 마이그레이션 경로 불명확 |
| L5 | "reviewer agents" vs "worker subagents" 용어 불일치 | Coherence | 동일한 Agent tool 메커니즘이지만 decompose-milestones은 "reviewer agents", execute-plan은 "worker subagents"로 표기 |
| L6 | `orchestrate-execution`이 milestone에서 "Scope" 참조하지만 milestone 포맷엔 "Files Affected"만 존재 | Coherence | 암묵적 매핑(Scope ← Files Affected)이 명시되지 않아 혼란 가능 |

---

## 4. Architecture Reviewer 상세 평가

### 4.1 패턴 일관성: GOOD

파이프라인 스킬(clarify-requirements, craft-plan, execute-plan, verify-implementation, decompose-milestones, orchestrate-execution)은 Hard Gates → When To Use → Process → Anti-Patterns → Checklist → Transition 구조를 엄격히 따름.

규율 스킬(write-surgically, remove-slop, simplify-changes, debug-systematically, measure-performance)은 각자의 도메인에 맞는 구조를 사용. `measure-performance`만 5개 섹션이 누락된 이탈.

스킬별 문서 길이 편차:
| 스킬 | 줄 수 |
|------|-------|
| decompose-milestones | 619 |
| orchestrate-execution | 395 |
| craft-plan | 344 |
| clarify-requirements | 278 |
| execute-plan | 276 |
| debug-systematically | 271 |
| write-surgically | 193 |
| simplify-changes | 181 |
| remove-slop | 185 |
| verify-implementation | 217 |
| measure-performance | 68 |

### 4.2 정보 흐름 설계: EXCELLENT

Worker-Validator 분리가 가장 강력한 설계 특징:

- **execute-plan**: Validator가 Task Goal, Acceptance Criteria, File List, Test Commands만 수신. Worker의 diff/log/접근방식은 완전 차단
- **verify-implementation**: plan 파일 경로만 입력. 실행 컨텍스트 완전 격리
- **decompose-milestones**: 5개 리뷰어가 서로의 결과를 보지 않음. Main agent의 verbatim copy 규칙으로 합성 에이전트에 편향 방지

파일 기반 핸드오프 계약:
| From | To | 산출물 | 위치 |
|------|----|--------|------|
| clarify-requirements | craft-plan / decompose-milestones | Context Brief | `docs/dev-kit/context/YYYY-MM-DD-<topic>-brief.md` |
| craft-plan | execute-plan | Plan Document | `docs/dev-kit/plans/YYYY-MM-DD-<feature-name>.md` |
| execute-plan | verify-implementation | Plan file path (동일 산출물) | 동일 |
| decompose-milestones | orchestrate-execution | Milestone DAG + state.md | `docs/dev-kit/harness/<session-slug>/` |

### 4.3 에러 복구: GOOD

재시도/에스컬레이션 정책이 파이프라인 전반에 일관성 있게 적용됨:

| 수준 | 최대 재시도 | 에스컬레이션 |
|------|------------|-------------|
| Task (execute-plan) | 3 validator 실패 | 사용자 개입 |
| E2E gate (execute-plan) | 2 fix 시도 | 사용자 결정: debug / re-plan / accept |
| Milestone (orchestrate-execution) | 3 attempts | 정지 및 보고 |
| Cross-milestone integration | 2 fix 시도 | 사용자 결정 |
| Reviewer (decompose-milestones) | 1 re-dispatch, 최소 3/5 | 3 미만이면 중지 |
| Debugging (debug-systematically) | 3 fix 시도 | 구조 재검토 |

약점: `measure-performance`는 실패 처리가 전혀 없음. `remove-slop`은 "revert and investigate"라고만 하고 재시도 정책이 명확하지 않음.

### 4.4 구조적 약점: ADEQUATE

1. **Subagent dispatch 신뢰성** (MEDIUM-HIGH): 전체 아키텍처가 Agent tool 기반 subagent에 의존하지만, dispatch 실패/타임아웃/빈 응답에 대한 처리가 execute-plan에 없음
2. **Fixed template 경직성** (MEDIUM): execute-plan validator가 "Acceptance Criteria"를 기대하지만 craft-plan에 명시적 필드가 없음
3. **Context window 압력** (MEDIUM): orchestrate-execution이 395줄이며 milestone마다 craft-plan → execute-plan → verify-implementation을 inline으로 호출할지 subagent로 dispatch할지 불명확
4. **버전 관리 부재** (LOW-MEDIUM): state.md, checkpoint, milestone 파일에 버전 필드가 없어 스킬 정의 변경 시 호환성 문제 가능

---

## 5. Workflow Completeness Reviewer 상세 평가

### 5.1 커버리지 갭

**커버리지 없는 개발 시나리오:**

| 시나리오 | 현재 상태 | 권장 |
|----------|----------|------|
| 코드리뷰 (plan 없는) | verify-implementation은 plan 문서 필요 | `review-code` 스킬 추가 |
| 리팩토링 | write-surgically가 적극 차단 ("not your task") | `refactor-safely` 스킬 추가 |
| 마이그레이션 (DB, 프레임워크, 언어) | 신규 코드 생성만 가정 | craft-plan에 migration 템플릿 추가 |
| 테스트 전략 | "테스트 추가"는 각 task에 포함되지만 인프라 수준 결정은 없음 | `strengthen-tests` 스킬 또는 Verification Discovery 확장 |
| API/인터페이스 설계 | clarify와 plan 사이의 갭 | craft-plan에 interface design phase 추가 |
| 긴급 핫픽스 | 파이프라인 최소 경로가 너무 많은 의식 | debug-systematically에 "fast path" 추가 |
| 탐색/스파이크 | clarify는 범위 축소용, open-ended exploration 아님 | `spike` 스킬 추가 |
| 문서 작성 | remove-slop는 AI 코멘트 정리만 | `write-docs` 스킬 (우선순위 낮음) |

### 5.2 엣지케이스 처리

| 케이스 | 상태 | 비고 |
|--------|------|------|
| Borderline score (8-9) | Well handled | 양쪽 옵션 제시 + 추천 |
| Plan에 task 1개 | Partially addressed | "execute-plan 쓰지 마라"는 있지만 대안이 명확하지 않음 |
| 순환 종속성 | Well handled | DAG 검증이 2계층(decompose + orchestrate)에서 수행 |
| 병렬 milestone이 같은 파일 수정 | Well handled | worktree 격리 + merge protocol + conflict check |
| Context Brief에 미해결 질문 | Partially addressed | craft-plan이 "assumptions로 반영"하나 사용자 확인 강제 메커니즘 없음 |

### 5.3 실제 마찰 지점

1. **소규모 작업 오버헤드**: 10분 코딩에 30~40분 파이프라인. write-surgically만으로 충분한 "quick mode" 정의 필요
2. **Hard Gate 과도한 엄격성**: remove-slop의 "한 pass에 한 냄새 카테고리" → 6회 테스트 실행. 작은 파일에 과도
3. **무한 루프 위험**: simplify-changes가 "재실행 권장"하지만 수렴 판정 기준 없음
4. **파일 구조 가정**: `docs/dev-kit/` 구조가 첫 사용 시 설명 없이 생성됨
5. **`write-surgically` 분류 문제**: "supporting"으로 분류되었으나 실제로는 가장 중요한 교차 스킬. 모든 코딩 작업에 적용되어야 함

---

## 6. Naming & DX Reviewer 상세 평가

### 6.1 이름 품질: GOOD

**장점:**
- 동사+명사 형태가 CLI 관례와 일치 (git push, npm install 등)
- `clarify-requirements`, `execute-plan`, `verify-implementation`, `remove-slop`은 즉시 이해 가능
- `measure-performance`는 기술적으로 가장 정확

**개선 검토:**

| 현재 이름 | 평가 | 대안 | 근거 |
|-----------|------|------|------|
| `simplify-changes` | remove-slop와 혼란 | `review-changes` 또는 `improve-changes` | 3-agent 분석 패스임을 명확히 |
| `orchestrate-execution` | execute-plan과 "execution" 충돌 | 현행 유지 또는 `run-milestones` | 단축 가능하지만 정확성 감소 |
| `write-surgically` | 동사+부사(스타일 이탈) | 현행 유지 | 기억에 남고 의미가 명확 |

### 6.2 트리거 단어 & 발견성: GOOD

**겹치는 트리거:**
- `simplify-changes`와 `remove-slop` 모두 "clean up" 매칭
- `write-surgically`는 사용자가 자연스럽게 말할 trigger phrase가 아닌 상황 기반 발동

**누락된 트리거 동의어:**
- `craft-plan`: "create a plan", "write a plan", "plan this out" 누락
- `verify-implementation`: "QA", "check the implementation", "does it work?" 누락
- `orchestrate-execution`: "run all milestones"가 description에 없음

### 6.3 문서 명확성: ADEQUATE

**README.md 문제:**
- 구 이름 11개가 그대로 사용 중 (이름 변경이 반영되지 않음)
- 전체 워크플로우 파이프라인 설명 없음
- 스킬 간 관계(transition)가 README에 노출되지 않음
- "when to use which skill" 의사결정 트리 없음

**SKILL.md 품질:** 개별 스킬 문서는 우수. 구조 일관성이 높고 anti-patterns 테이블이 실제 실패 모드를 잘 예측.

### 6.4 플러그인 설정: GOOD

**plugin.json 개선점:**
- `longDescription`이 실제 스킬 이름을 사용하지 않음
- `defaultPrompt` 3개로 11개 스킬의 27%만 대표
- `keywords`에 "milestones", "review", "refactoring", "testing" 누락

**추가 defaultPrompt 후보:**
```
"Review the implementation against the plan and give me a PASS/FAIL verdict."
"Clean up the AI-generated code smells without changing behavior."
"Find out where this code is actually slow before optimizing."
```

---

## 7. Coherence & Anti-patterns Reviewer 상세 평가

### 7.1 스킬 간 모순

#### C1. `write-surgically` vs `defense-in-depth` (MODERATE)
- write-surgically Rule 5: "null guard 하지 마라, 현재 코드에서 가능하지 않다면"
- defense-in-depth: "모든 계층에 검증을 추가하라"
- **적용 시점이 다름** (구현 vs 버그수정 후 경화) but 명시적 조정 없음

#### C2. `write-surgically` "read first" vs `execute-plan` "follow steps exactly" (LOW)
- 실제로는 plan이 write-surgically 원칙을 이미 내포해야 하므로 실질적 충돌은 없음
- 단, plan이 수정하라고 지시한 파일을 worker가 읽지 않은 경우에 대한 명시적 처리 없음

#### C3. `remove-slop` vs `defense-in-depth` (HIGH)
- remove-slop Pass 4: "Null checks on values guaranteed non-null"을 제거 대상
- defense-in-depth: "Entry → Business → Environment → Debug 4계층 방어"를 권장
- **직접적 철학 충돌**. remove-slop가 의도적으로 추가된 방어 코드를 제거할 위험

#### C4. `simplify-changes` vs `remove-slop` 엄격도 차이 (MODERATE)
- simplify-changes: "Fix issues directly" (행동 변화 가능)
- remove-slop: "Preserve behavior exactly" (행동 보존 절대)
- 겹치는 작업(코멘트 정리, 추상화 제거)에 서로 다른 엄격도 적용

### 7.2 중복

#### R1. `simplify-changes` ↔ `remove-slop` (MODERATE)
- 코멘트 정리: 양쪽 모두 동일 예시로 동일 작업
- 추상화 제거: 양쪽 모두 불필요한 추상화 타겟
- **역할 구분 필요**: simplify-changes는 diff 기반 3-agent 병렬 품질 리뷰, remove-slop는 file 기반 6-pass 순차 AI 냄새 제거

#### R2. `verify-implementation` ↔ execute-plan validator (LOW, 의도적)
- execute-plan의 per-task validator가 각 task를 검증
- verify-implementation이 전체 plan을 독립적으로 재검증
- **의도적 독립 감사**이나 명시되지 않아 "중복"으로 오인 가능

#### R3. 체크리스트 항목 중복 (LOW)
- "No placeholders/TODO" → execute-plan, verify-implementation, remove-slop, craft-plan
- "Run tests" → execute-plan, verify-implementation, remove-slop, simplify-changes
- "No changes outside scope" → write-surgically, remove-slop, simplify-changes, verify-implementation
- 건강한 독립 검증이나 4개 스킬이 동일 항목을 검사함

### 7.3 개념 드리프트

#### T1. "task" vs "step" vs "milestone" vs "phase" vs "cycle"
- Milestone > Task > Step: 명확한 계층. 일관성 있게 사용됨
- Phase: 스킬 내부 프로세스 단계. milestone과 혼동 없음
- Cycle: clarify-requirements의 반복 루프. 적절
- **용어는 실제로 일관성 있음**

#### T2. "reviewer agents" vs "worker subagents"
- 동일한 Agent tool 메커니즘이지만 용어가 다름
- cosmetic하지만 subagent 모델을 이해하려는 사용자에게 혼란 가능

#### T3. 3계층 추상화 수준이 명시되지 않음
1. **Thinking Discipline** (항상 활성 가드레일): write-surgically, measure-performance
2. **Corrective** (구현 후 실행): remove-slop, simplify-changes, debug-systematically
3. **Workflow** (다단계 산출물 기반 프로세스): clarify-requirements, craft-plan, execute-plan, verify-implementation, decompose-milestones, orchestrate-execution

이 구분이 어디에도 명시되지 않아 사용자가 "write-surgically를 써야 할 때인지 craft-plan을 써야 할 때인지" 헷갈릴 수 있음.

---

## 8. 우선순위별 액션 아이템

### Phase 1: 즉시 수정 (HIGH)

| # | 액션 | 근거 | 난이도 |
|---|------|------|--------|
| 1 | README.md 갱신 — 구 이름→새 이름, 워크플로우 다이어그램 추가 | H1 | 낮음 |
| 2 | SKILL.md 내부 `# 제목` 6개 갱신 | H2 | 낮음 |
| 3 | `remove-slop` Pass 4에 가드 추가 — defense-in-depth 의도로 추가된 검증 보존 | H3 | 낮음 |
| 4 | `plugin.json` defaultPrompt 확장 (3→7개) | H4 | 낮음 |

### Phase 2: 개선 (MODERATE)

| # | 액션 | 근거 | 난이도 |
|---|------|------|--------|
| 5 | `simplify-changes` ↔ `remove-slop` "When to use this vs. the other" 섹션 추가 | M1 | 낮음 |
| 6 | `write-surgically`에 "quick mode" 최소 게이트 세트 추가 | M3 | 중간 |
| 7 | README/plugin.json에 3계층 택소노미 추가 | M4 | 낮음 |
| 8 | `craft-plan` task 포맷에 명시적 "Acceptance Criteria" 필드 추가 | M5 | 중간 |
| 9 | `write-surgically`와 `defense-in-depth`에 적용 시점 명시 | M6 | 낮음 |
| 10 | `decompose-milestones` description에서 "ultraplan" 제거 또는 정의 | M7 | 낮음 |

### Phase 3: 고도화 (장기)

| # | 액션 | 근거 | 난이도 |
|---|------|------|--------|
| 11 | `refactor-safely` 스킬 추가 | M2 | 높음 |
| 12 | `review-code` 스킬 추가 (plan 없는 코드 리뷰) | M2 | 높음 |
| 13 | `measure-performance` 보강 — 누락 5개 섹션 추가 | L1 | 중간 |
| 14 | 상태 파일 포맷에 버전 필드 추가 | L4 | 중간 |
| 15 | `verify-implementation`에 독립 감사 의도 명시 | L2 | 낮음 |

---

## 9. 평가 대상 파일 목록

```
dev-kit/
├── .codex-plugin/plugin.json
├── README.md
├── skills/
│   ├── clarify-requirements/SKILL.md
│   ├── craft-plan/SKILL.md
│   ├── execute-plan/SKILL.md
│   ├── verify-implementation/SKILL.md
│   ├── decompose-milestones/SKILL.md
│   ├── orchestrate-execution/SKILL.md
│   ├── write-surgically/SKILL.md
│   ├── remove-slop/SKILL.md
│   ├── simplify-changes/SKILL.md
│   ├── debug-systematically/SKILL.md
│   ├── debug-systematically/condition-based-waiting.md
│   ├── debug-systematically/defense-in-depth.md
│   ├── debug-systematically/root-cause-tracing.md
│   └── measure-performance/SKILL.md
```

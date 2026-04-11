# Dev Kit에 복리 학습(Compound Learning) 적용 방안

> **관련 분석**: [Compound Engineering Plugin 분석](./research-compound-engineering-plugin.ko.md)
> **작성일**: 2026-04-08
> **상태**: 제안 (Proposal)

---

## 1. 배경

### 1.1 현재 Dev Kit의 한계

Dev Kit의 4-phase 사이클은 **1회성**이다:

```
clarify → planning → execute → review-execute → [completed]
```

review-execute가 끝나면 세션이 `completed`로 전환되고, 그 안에서 발견한 인사이트는 다음 세션으로 전달되지 않는다. 이것은 Compound Engineering Plugin이 지적하는 "전통적 개발의 기술 부채 누적"과 같은 구조적 한계다.

### 1.2 Compound Engineering의 참고 모델

Compound Engineering Plugin은 `/ce:compound` 스킬로 작업 완료 후 학습을 추출하고, `/ce:compound-refresh`로 기존 학습을 갱신하며, 이후 `/ce:brainstorm`과 `/ce:plan`에서 과거 학습을 자동 참조한다.

이 패턴을 Dev Kit의 철학과 아키텍처에 맞게 재설계한다.

---

## 2. 설계 원칙

### 2.1 Dev Kit 철학과의 정합성

| Dev Kit 원칙 | 복리 학습 적용 시 함의 |
|---|---|
| **One Visible Flow** | 코어 4-phase는 유지. compound는 review-execute의 연장선이지 독립 5th phase가 아님 |
| **JSON Source of Truth** | 학습 메타데이터도 JSON으로 관리. Markdown은 human-readable derivative |
| **Planning Owns Plan Quality** | 과거 학습이 planning의 입력으로 들어와야 함 |
| **Pure Execute Stage** | execute는 학습을 직접 소비하지 않음. planning이 필터링하여 전달 |
| **Single Writer State** | 학습 쓰기도 오케스트레이터가 담당 |

### 2.2 핵심 설계 결정

**독립 phase가 아닌 review-execute의 부산물로 설계**

```
clarify → planning → execute → review-execute
                                    │
                                    └─ [+compound] 완료 시 학습 추출
                                        │
                                        ▼
                                 .dev-kit/learnings/
                                        │
                           session-start hook ← 여기서 소비
```

이유:
- 코어 4-phase를 그대로 유지하여 예측 가능성 보존
- 모든 작업이 5번째 단계를 강제받지 않음 (오버헤드 최소)
- 학습 추출은 review-execute 완료 조건에 자연스럽게 통합

---

## 3. 데이터 모델

### 3.1 학습 저장소 구조

```
.dev-kit/
├── current.json                     # 기존 (변경 없음)
├── learnings/
│   ├── index.json                   # 학습 인덱스 (machine-readable)
│   └── <slug>.md                    # 개별 학습 문서 (human-readable)
└── sessions/                        # 기존 (변경 없음)
    └── <session-id>/
        ├── state.json
        ├── brief.md
        ├── ...
        └── compound.md              # 신규: 세션에서 추출한 학습 원본
```

### 3.2 학습 인덱스 (`learnings/index.json`)

```json
{
  "schema_version": 1,
  "learnings": [
    {
      "id": "async-error-pattern",
      "title": "Promise.all 실패 시 개별 에러 복구 패턴",
      "source_session": "2026-04-08T14-30-api-refactor",
      "tags": ["async", "error-handling", "typescript"],
      "context_types": ["nodejs", "api"],
      "file": "async-error-pattern.md",
      "created_at": "2026-04-08T16:00:00+09:00",
      "last_referenced_at": "2026-04-10T09:30:00+09:00",
      "reference_count": 3,
      "status": "active"
    }
  ]
}
```

### 3.3 개별 학습 문서 (`learnings/<slug>.md`)

```markdown
# async-error-pattern

> 출처: 2026-04-08T14-30-api-refactor 세션

## 상황
Node.js 서비스에서 Promise.all을 사용할 때, 하나의 promise가 실패하면
전체 작업이 실패하는 문제가 발생.

## 결정
Promise.allSettle + 결과 필터 패턴을 사용.
실패한 항목만 로깅하고 성공한 항목은 정상 처리.

## 근거
- 부분 실패가 예상되는 외부 API 호출에서 all-or-nothing 정책이 부적합
- 에러 타입별 복구 전략을 분리하여 테스트 용이성 향상

## 적용 조건
- 여러 독립 비동기 작업을 병렬 실행할 때
- 개별 실패가 전체 프로세스를 중단시키면 안 될 때
```

### 3.4 state.json 확장

```json
{
  "artifacts": {
    "brief": "...",
    "plan": "...",
    "plan_review": "...",
    "review": "...",
    "compound": null                    # 신규: 학습 추출 여부
  },
  "compound_status": null               # 신규: not_started | extracted | skipped
}
```

`compound_status` 값:
- `null` — 아직 review-execute를 통과하지 않음
- `not_started` — review-execute 통과, 학습 추출 대기
- `extracted` — 학습이 추출되어 learnings/에 저장됨
- `skipped` — 사용자가 학습 추출을 건너뜀 (단순 작업 등)

---

## 4. 워크플로우 상세

### 4.1 추출 (Extract)

**트리거**: review-execute가 PASS 판정을 내린 후, `completed` 전환 전

**프로세스**:

1. review-execute가 PASS 판정
2. 오케스트레이터가 세션의 brief.md, plan.md, review.md를 분석
3. 재사용 가능한 패턴/결정/인사이트가 있는지 판단
4. 사용자에게 한 줄 질문:
   > "이번 작업에서 재사용 가능한 패턴을 발견했나요? (추출할 학습이 있다면 설명해주세요, 없으면 '건너뛰기')"
5. 응답에 따라:
   - **학습 있음**: `compound.md` 작성 → `learnings/index.json` 업데이트 → `state.json.compound_status = "extracted"`
   - **건너뛰기**: `state.json.compound_status = "skipped"` → 바로 `completed`

**자동 감지 기준** (오케스트레이터가 판단):

| 감지 신호 | 예시 |
|---|---|
| 반복 패턴 해결 | "이 에러 패턴은 이전에도 발생했다" |
| 아키텍처 결정 | "이 구조를 선택한 이유는..." |
| 성능 최적화 | "N+1 쿼리를 batch로 변경하여 응답시간 80% 감소" |
| 디버깅 인사이트 | "원인은 X의 초기화 순서였다" |
| 테스트 전략 | "이런 유형은 통합 테스트가 단위 테스트보다 효과적" |

### 4.2 소비 (Consume)

**트리거**: `session-start.sh` hook 실행 시 passive context 갱신

**확장된 hook 동작**:

```bash
session-start.sh
  ├─ 기존: 세션 상태 요약 출력
  └─ 추가: 관련 learnings 검색 → passive additionalContext 반영
       │
       ├─ .dev-kit/learnings/index.json 로드
       ├─ 현재 워크스페이스의 태그/컨텍스트와 매칭
       ├─ 관련도 순으로 상위 N개 선택
       └─ 세션 요약에 관련 학습 요약 추가 출력
```

**소비 지점**:

이 학습은 workflow를 자동 시작하지 않으며, 관련 phase가 명시적으로 호출될 때만 활용됩니다.

| Phase | 학습 사용 방식 |
|---|---|
| clarify | 관련 과거 경험을 참고하여 질문의 질 향상 |
| planning | 과거 결정의 근거를 plan.md에 반영 |
| execute | (직접 소비하지 않음. planning이 필터링하여 전달) |
| review-execute | 과거 학습과 일치하는 패턴인지 확인 |

### 4.3 갱신 (Refresh)

**트리거**: 사용자가 명시적으로 요청 (독립 스킬 또는 수동)

**프로세스**:

1. `learnings/index.json`의 모든 학습을 순회
2. 각 학습의 상태를 분류:
   - **keep**: 최근에 참조되었고 여전히 유효
   - **update**: 참조되었지만 내용이 구식
   - **replace**: 더 나은 패턴을 발견하여 대체 필요
   - **archive**: 더 이상 관련 없음
3. 분류 결과를 사용자에게 제시
4. 승인 후 `index.json` 업데이트

**평가 기준**:

| 기준 | keep | update/replace | archive |
|---|---|---|---|
| 마지막 참조 | 최근 30일 이내 | 30-90일 | 90일+ |
| 코드베이스 반영 | 여전히 유효 | 부분 변경 | 완전 변경 |
| 참조 횟수 | 3회+ | 1-2회 | 0회 |

---

## 5. Dev Kit 아키텍처 통합

### 5.1 디렉토리 구조 (확장)

```
dev-kit/
├── .claude-plugin/plugin.json
├── hooks/
│   ├── hooks.json
│   ├── session-start.sh              # 확장: learnings 검색 추가
│   └── user-prompt-submit.sh
├── schema/
│   ├── state.schema.json             # 확장: compound_status 필드
│   └── learnings-index.schema.json   # 신규: 학습 인덱스 스키마
├── scripts/
│   └── dev_kit_state.py              # 확장: 학습 CRUD 헬퍼
├── skills/
│   ├── clarify/SKILL.md              # 확장: 관련 학습 자동 참조
│   ├── planning/SKILL.md             # 확장: 관련 학습 자동 참조
│   ├── execute/SKILL.md
│   ├── review-execute/SKILL.md       # 확장: 완료 시 학습 추출 단계
│   └── ...
└── README.md
```

### 5.2 Hooks 변경

**session-start.sh 확장**:

```bash
# 기존: 세션 상태 요약
# 추가: 관련 학습 요약
if [ -f ".dev-kit/learnings/index.json" ]; then
  echo "---"
  echo "📚 Relevant Learnings:"
  # 관련도 높은 학습 최대 5개 출력
  python3 "${PLUGIN_ROOT}/scripts/dev_kit_state.py" learnings-summary
fi
```

### 5.3 state.json 확장

```json
{
  "$schema": "../schema/state.schema.json",
  "schema_version": 1,
  "session_id": "2026-04-08T14-30-api-refactor",
  "title": "API 에러 처리 리팩토링",
  "feature_slug": "api-refactor",
  "status": "completed",
  "current_phase": "review-execute",
  "execution_profile": "medium",
  "plan_status": "approved",
  "plan_version": 1,
  "next_action": null,
  "artifacts": {
    "brief": ".dev-kit/sessions/.../brief.md",
    "plan": ".dev-kit/sessions/.../plan.md",
    "plan_review": ".dev-kit/sessions/.../plan-review.md",
    "review": ".dev-kit/sessions/.../review.md",
    "compound": ".dev-kit/sessions/.../compound.md"
  },
  "compound_status": "extracted",
  "phase_status": {
    "clarify": "completed",
    "planning": "completed",
    "execute": "completed",
    "review-execute": "completed"
  },
  "created_at": "2026-04-08T14:30:00+09:00",
  "updated_at": "2026-04-08T16:00:00+09:00"
}
```

---

## 6. Compound Engineering Plugin과의 비교

| 설계 결정 | Compound CE | Dev Kit 제안 | 이유 |
|---|---|---|---|
| **phase 위치** | 독립 7th 스킬 | review-execute의 부산물 | One Visible Flow 원칙 유지 |
| **트리거** | 수동 (`/ce:compound`) | 반자동 (review 완료 시 질문) | 잊혀지지 않으면서 오버헤드 최소 |
| **저장소** | `docs/solutions/` | `.dev-kit/learnings/` | 워크스페이스 로컬, git 관리 용이 |
| **포맷** | YAML 프론트매터 + Markdown | index.json + Markdown | JSON Source of Truth 원칙 |
| **소비** | brainstorm/plan에서 수동 참조 | session-start hook의 passive context + 명시적 phase 활용 | 잊혀지지 않는 소비 보장 |
| **갱신** | `/ce:compound-refresh` 스킬 | 독립 스킬 또는 수동 | 동일하나 사용 빈도 낮을 것으로 예상 |
| **복잡도** | 2개 스킬 (compound + refresh) | state.json 확장 + hook 확장 | 기존 인프라 재사용 |

---

## 7. 예상 효과

### 7.1 단기

- 같은 실수 반복 감소: 과거 디버깅 인사이트가 SessionStart passive context를 통해 명시적 clarify/planning에 반영
- 결정 근거 보존: "왜 이 선택을 했는지"가 다음 작업에서 참조 가능
- 세션 간 연속성: 독립적인 세션이지만 학습이 연결고리 역할

### 7.2 장기

- `.dev-kit/learnings/`가 프로젝트의 살아있는 지식 베이스가 됨
- 팀 단위 사용 시 개인의 암묵지가 명시적 지식으로 변환
- 학습 갱신(refresh)을 통해 지식 부패 방지

---

## 8. 리스크와 대응

| 리스크 | 대응 |
|---|---|
| 학습이 쓰레기 더미가 됨 | review-execute에서 추출 가이드 제공. "건너뛰기" 옵션 항상 열려 있음 |
| 학습이 너무 많아져 소비 시 노이즈 | reference_count와 last_referenced_at으로 관련도 필터링. 상위 5개만 주입 |
| 학습이 구식이 됨 | refresh 프로세스로 주기적 감사. 90일+ 미참조 학습은 자동 archive 후보 |
| 오버헤드 증가 | "건너뛰기"가 기본 흐름. 추출은 선택적. 1회 추가 질문이 전부 |
| 학습이 프로젝트 특화되어 범용성 상실 | tags와 context_types로 분류. 범용 학습은 다른 프로젝트에서도 이식 가능 |

---

## 9. 구현 우선순위

### Phase 1: 최소 기능

1. `compound_status` 필드를 state.json에 추가
2. review-execute 완료 시 학습 추출 질문 추가
3. `compound.md`를 세션 디렉토리에 저장
4. `learnings/index.json`과 개별 `.md` 파일 생성

### Phase 2: 소비 루프

5. `dev_kit_state.py`에 learnings CRUD 헬퍼 추가
6. `session-start.sh`에 관련 학습 검색 로직 추가
7. clarify, planning SKILL.md에 학습 참조 가이드 추가

### Phase 3: 갱신 관리

8. `learnings-index.schema.json` 추가
9. refresh 프로세스 구현 (독립 스킬 또는 수동 가이드)
10. 학습 통계 출력 (`learnings-summary`)

---

## 10. 결론

복리 학습은 Dev Kit의 1회성 한계를 보완하면서도, Dev Kit의 핵심 철학(One Visible Flow, JSON Source of Truth, 예측 가능성)을 해치지 않는 방식으로 설계할 수 있다.

핵심은 **독립 phase 추가가 아니라 기존 phase의 자연스러운 연장**이며, **소비 경로를 hook이 보장**하여 학습이 축적만 되고 잊히는 일이 없도록 하는 것이다.

Compound Engineering Plugin의 `/ce:compound`에서 영감을 받았지만, Dev Kit의 방식대로 재해석한 것이다 — 더 적은 이동 부품, 더 강한 상태 관리, 더 예측 가능한 동작.

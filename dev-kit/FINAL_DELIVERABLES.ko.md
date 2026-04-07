# Dev Kit 최종 산출물 정리

Dev Kit의 공식 흐름은 항상 `clarify -> planning -> execute -> review-execute`입니다.
최종 산출물은 이 네 phase를 거치며 `.dev-kit/sessions/<session-id>/` 아래에 축적됩니다.

## 핵심 결론

성공적으로 완료된 세션의 기준 산출물은 아래와 같습니다.

| 구분 | 파일 | 성격 | 필수 여부 |
|---|---|---|---|
| 세션 포인터 | `.dev-kit/current.json` | 현재 진행 중 세션 포인터 | 진행 중일 때만 |
| 세션 상태 | `.dev-kit/sessions/<session-id>/state.json` | machine-readable source of truth | 항상 필수 |
| 요구사항 정의 | `.dev-kit/sessions/<session-id>/brief.md` | clarify 결과 | 필수 |
| 승인된 실행 계획 | `.dev-kit/sessions/<session-id>/plan.md` | planning 결과 | 필수 |
| 계획 승인 기록 | `.dev-kit/sessions/<session-id>/plan-review.md` | critic + readiness-checker 집계 결과 | 필수 |
| 실행 최종 검증 | `.dev-kit/sessions/<session-id>/review.md` | review-execute 결과 | 필수 |
| 실행 로그 | `.dev-kit/sessions/<session-id>/progress.md` | task/phase 진행 로그 | execute 시 생성 |
| phase 체크포인트 | `.dev-kit/sessions/<session-id>/checkpoints/*.json` | multi-phase 복구 지점 | 조건부 |
| 재개 스냅샷 | `.dev-kit/sessions/<session-id>/handoff.md` | context reset용 최신 재개 요약 | 조건부 |

## Phase별 산출물

### 1. Clarify

- 산출물: `brief.md`
- 상태 반영: `state.json`, `current.json`
- 역할: 목표, 범위, 제약, 성공 기준, 복잡도 평가를 고정

### 2. Planning

- 산출물: `plan.md`, `plan-review.md`
- 상태 반영: `state.json`, `current.json`
- 역할:
  - 실행자가 추가 판단 없이 수행할 수 있는 승인된 계획 확정
  - `critic`와 `readiness-checker`의 독립 검토 결과를 집계

### 3. Execute

- 산출물: `progress.md`
- 조건부 산출물:
  - `checkpoints/*.json`: multi-phase이고 integration gate 통과 후 생성
  - `handoff.md`: `Context Reset: enabled`일 때 생성
- 상태 반영: `state.json`, `current.json`
- 역할:
  - 승인된 `plan.md`를 그대로 실행
  - task/phase 단위 검증 결과와 재개 정보를 축적

### 4. Review-Execute

- 산출물: `review.md`
- 상태 반영: `state.json`
- 역할:
  - 승인된 `plan.md` 기준으로 최종 결과를 독립 검증
  - PASS면 세션 완료, FAIL이면 `execute`로 되돌림

## 최종 완료 기준

세션이 `completed`로 끝났다고 말하려면 최소한 아래 조건을 만족해야 합니다.

1. `state.json.status`가 `completed`다.
2. `state.json.current_phase`가 `review-execute`다.
3. `state.json.plan_status`가 `approved`다.
4. `artifacts.brief`, `artifacts.plan`, `artifacts.plan_review`, `artifacts.review`가 모두 채워져 있다.
5. `review.md`의 최종 verdict가 `PASS`다.

완료된 세션은 더 이상 active session이 아니므로, 같은 세션을 가리키는 `.dev-kit/current.json`은 제거되는 것이 정상입니다.

## 필수 산출물과 조건부 산출물 구분

### 항상 남아야 하는 것

- `state.json`
- `brief.md`
- `plan.md`
- `plan-review.md`
- `review.md`

### 실행 방식에 따라 달라지는 것

- `progress.md`: execute를 수행하면 생성
- `checkpoints/*.json`: multi-phase일 때만 생성
- `handoff.md`: context reset이 필요한 세션에서만 생성
- `.dev-kit/current.json`: 세션이 진행 중이거나 재개 가능할 때만 유지

## 운영 기준

- 사람 기준 최종 문서 묶음은 `brief.md + plan.md + plan-review.md + review.md`입니다.
- 시스템 기준 정답 소스는 항상 `state.json`입니다.
- `progress.md`, `checkpoints/*.json`, `handoff.md`는 실행 편의와 복구를 위한 보조 산출물이지, 완료 판정의 핵심 문서는 아닙니다.
- execution profile이 `low | medium | high`로 달라져도 핵심 산출물 이름은 바뀌지 않고, 문서의 상세도만 달라집니다.

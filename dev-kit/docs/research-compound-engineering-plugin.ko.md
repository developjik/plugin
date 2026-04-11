# Compound Engineering Plugin 분석

> **분석 대상**: [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)
> **분석 일시**: 2026-04-08
> **버전**: 2.63.1 | **npm**: `@every-env/compound-plugin`

---

## 1. 프로젝트 개요

Every Inc.(every.to)에서 개발한 AI 코딩 에이전트 플러그인 생태계.

**핵심 철학**: "매 엔지니어링 작업 단위가 다음 작업을 더 쉽게 만들어야 한다." 전통적 개발은 기술 부채가 누적되지만, 계획·리뷰·학습의 문서화를 통해 지식이 복리(Compound)로 쌓이는 방식을 추구한다.

**규모**: 약 477개 파일, 50+ 에이전트, 42개 스킬, 마크다운만 154개.

---

## 2. 아키텍처

```
compound-engineering-plugin/
├── src/                          # CLI 변환 엔진 (Bun/TypeScript)
│   ├── index.ts                  # CLI 진입점 (citty 프레임워크)
│   ├── commands/                 # install, convert, sync, list, plugin-path
│   ├── parsers/                  # Claude Code 플러그인 파서
│   ├── converters/               # 10개 타겟 플랫폼 변환기
│   ├── types/                    # 플랫폼별 타입 정의 (10개)
│   ├── targets/                  # 변환 타겟 레지스트리
│   ├── sync/                     # 개인 설정 동기화 로직 (10개 타겟)
│   └── release/                  # 릴리즈 메타데이터 관리
│
├── plugins/
│   └── compound-engineering/     # 메인 플러그인
│       ├── agents/               # 전문화된 하위 에이전트
│       │   ├── review/           # 코드 리뷰 (~30개)
│       │   ├── document-review/  # 문서 리뷰 (7개)
│       │   ├── research/         # 리서치 (7개)
│       │   ├── design/           # 디자인 (3개)
│       │   ├── workflow/         # 워크플로우 (4개)
│       │   └── docs/             # 문서작성 (1개)
│       └── skills/               # 42개 스킬 (슬래시 커맨드)
│
├── tests/                        # ~55개 테스트 파일
├── docs/                         # 브레인스톰, 플랜, 솔루션, 스펙 문서
└── scripts/                      # 릴리즈 자동화 스크립트
```

### 기술 스택

| 항목 | 내용 |
|------|------|
| 런타임 | Bun (TypeScript, ES2022) |
| CLI 프레임워크 | citty |
| 런타임 의존성 | citty, js-yaml 단 2개 |
| 테스트 | Bun 내장 테스트 (~55개 파일) |
| 릴리즈 | semantic-release + release-please |

---

## 3. 핵심 워크플로우: Compound Engineering Cycle

```
Ideate → Brainstorm → Plan → Work → Review → Compound → Repeat
```

각 단계는 스킬(슬래시 커맨드)으로 구현되어 있으며, 사이클이 반복될수록 이전 학습이 다음 사이클의 입력으로 사용된다.

### 3.1 Ideate (`/ce:ideate`)

- **역할**: 발산적 아이디어 생성 + 적대적 필터링
- 코드베이스를 스캔하여 개선 아이디어를 도출
- adversarial 관점에서 아이디어를 공격하여 약한 것을 걸러냄
- Dev Kit에는 없는 "아이디어 생성" 단계

### 3.2 Brainstorm (`/ce:brainstorm`)

- **역할**: WHAT 정의 (요구사항 탐색 및 문서화)
- 인터랙티브 Q&A로 요구사항 문서 산출
- Dev Kit의 `clarify`와 유사하나, 요구사항에만 집중

### 3.3 Plan (`/ce:plan`)

- **역할**: HOW 정의 (구조적 구현 계획 수립)
- 구현 단위, 파일, 테스트 시나리오 포함
- Dev Kit의 `planning`과 가장 직접적으로 대응

### 3.4 Work (`/ce:work`)

- **역할**: 계획 실행
- Git 워크트리 활용
- 태스크 트래킹, 점진적 커밋
- 하위 에이전트 분산 실행
- Dev Kit의 `execute`와 대응

### 3.5 Review (`/ce:review`)

- **역할**: 다중 에이전트 코드 리뷰
- 17개 리뷰어 페르소나 병렬 실행
- 신뢰도 게이팅 + 중복 제거 파이프라인
- 구조화된 JSON으로 결과 수집
- Dev Kit의 `review-execute`보다 훨씬 정교한 리뷰 시스템

### 3.6 Compound (`/ce:compound`)

- **역할**: 학습 내용 문서화
- `docs/solutions/`에 YAML 프론트매터로 지식 축적
- 이 스킬이 Compound Engineering의 이름 유래이자 핵심 차별화 요소

### 3.7 Compound-Refresh (`/ce:compound-refresh`)

- **역할**: 기존 학습 갱신
- 오래된 학습을 keep/update/replace/archive
- 지식이 부패되는 것을 방지

---

## 4. 에이전트 시스템 (50+)

에이전트는 스킬에 의해 호출되는 전문화된 하위 에이전트. 스킬이 "무엇을 할지"를 정의하면, 에이전트가 "어떻게 할지"를 수행한다.

### 4.1 리뷰 에이전트 (~30개)

`/ce:review`에서 활용되는 페르소나 카탈로그. 항상 활성(4개), 조건부(8개), 스택 특화(5개) 레이어로 구성.

| 에이전트 | 역할 |
|----------|------|
| correctness-reviewer | 논리적 정확성, 엣지 케이스 |
| testing-reviewer | 테스트 커버리지, 누락된 케이스 |
| maintainability-reviewer | 가독성, 응집도, 결합도 |
| security-reviewer | 취약점, 인증/인가 |
| performance-reviewer | 병목, 메모리, 응답시간 |
| architecture-strategist | 구조적 일관성, 확장성 |
| adversarial-reviewer | 의도적 공격으로 실패 시나리오 탐색 |
| ... | (총 ~30개) |

### 4.2 문서 리뷰 에이전트 (7개)

| 에이전트 | 역할 |
|----------|------|
| coherence-reviewer | 문서 일관성 |
| design-lens-reviewer | 디자인 관점 검토 |
| feasibility-reviewer | 실현 가능성 |
| product-lens-reviewer | 제품 관점 |
| scope-guardian-reviewer | 범위 통제 |
| security-lens-reviewer | 보안 관점 |
| adversarial-document-reviewer | 문서에 대한 적대적 리뷰 |

### 4.3 리서치 에이전트 (7개)

| 에이전트 | 역할 |
|----------|------|
| best-practices-researcher | 업계 베스트 프랙티스 |
| framework-docs-researcher | 프레임워크 문서 |
| git-history-analyzer | Git 이력 분석 |
| issue-intelligence-analyst | 이슈 인텔리전스 |
| learnings-researcher | 과거 학습 검색 |
| repo-research-analyst | 리포 분석 |
| slack-researcher | Slack 채널 정보 |

### 4.4 기타 에이전트

- **디자인** (3개): design-implementation-reviewer, design-iterator, figma-design-sync
- **워크플로우** (4개): bug-reproduction-validator, lint, pr-comment-resolver, spec-flow-analyzer

---

## 5. 전체 스킬 목록 (42개)

### 코어 워크플로우 (7개)

| 스킬 | 설명 |
|------|------|
| `/ce:ideate` | 발산적 아이디어 생성 + 적대적 필터링 |
| `/ce:brainstorm` | 요구사항 탐색 및 문서화 |
| `/ce:plan` | 구조적 구현 계획 수립 |
| `/ce:work` | 계획 실행 (워크트리, 태스크 트래킹) |
| `/ce:review` | 17개 페르소나 다중 에이전트 리뷰 |
| `/ce:compound` | 학습 내용 문서화 |
| `/ce:compound-refresh` | 기존 학습 갱신 |

### Git 워크플로우 (4개)

git-clean-gone-branches, git-commit, git-commit-push-pr, git-worktree

### 워크플로우 유틸리티 (12개)

changelog, feature-video, reproduce-bug, report-bug-ce, resolve-pr-feedback, sync, test-browser, test-xcode, onboarding, todo-resolve, todo-triage, todo-create

### 개발 프레임워크 (4개)

agent-native-architecture, andrew-kane-gem-writer, dhh-rails-style, dspy-ruby, frontend-design

### 기타 (15개)

- **리뷰 & 품질**: claude-permissions-optimizer, document-review, setup
- **자동화 & 도구**: agent-browser, gemini-imagegen, orchestrating-swarms, rclone
- **콘텐츠**: every-style-editor, proof
- **실험적**: `/lfg` (완전 자율 파이프라인), `/slfg` (스웜 모드)

---

## 6. 크로스 플랫폼 변환 시스템

이 저장소의 가장 독특한 측면. Claude Code 플러그인을 10개 AI 코딩 플랫폼으로 자동 변환하는 CLI 시스템.

### 지원 타겟 (10개)

| 타겟 | 출력 경로 | 변환 특징 |
|------|-----------|-----------|
| OpenCode | `~/.config/opencode/` | commands → .md, opencode.json 딥머지 |
| Codex | `~/.codex/` | prompt + skill 페어 생성 |
| Droid | `~/.factory/` | 도구명 매핑 (Bash→Execute 등) |
| Pi | `~/.pi/agent/` | MCPorter 연동 |
| Gemini | `.gemini/` | .toml 명령어, 디렉토리 네임스페이스 |
| Copilot | `.github/` | .agent.md + 프론트매터, COPILOT_MCP_ 프리픽스 |
| Kiro | `.kiro/` | JSON + .md 프롬프트, stdio MCP만 |
| Windsurf | `.windsurf/` | 글로벌/워크스페이스 스코프 |
| OpenClaw | `~/.openclaw/extensions/` | TypeScript 스킬 + extension.json |
| Qwen | `~/.qwen/extensions/` | .yaml 에이전트 |

### 변환 범위

- 에이전트 호출 패턴 (`Task agent-name(args)`)
- 슬래시 커맨드 참조
- 경로 매핑 (`.claude/` → `.github/` 등)
- 환경변수 변환
- MCP 설정 변환

### CLI 명령어

```bash
compound install --target copilot    # 특정 타겟에 설치
compound convert ./my-plugin         # 로컬 플러그인 변환
compound sync                        # Claude Code 설정 동기화
compound list                        # 사용 가능한 플러그인 나열
compound plugin-path                 # 캐시된 브랜치 경로 출력
```

---

## 7. 주요 설계 결정

### 7.1 스킬 격리 원칙

각 스킬 디렉토리는 완전히 자립적이어야 한다. 다른 스킬의 파일을 참조하면 변환 시 깨지므로, 공통 파일이 필요하면 복제한다.

### 7.2 플랫폼 독립 변수 금지

`${CLAUDE_PLUGIN_ROOT}` 같은 플랫폼 특화 변수를 스킬 내용에 직접 사용하지 않는다. 대신 상대 경로를 사용하고, 불가피한 경우 fallback 명령을 포함한다.

### 7.3 페르소나 기반 다중 에이전트 리뷰

`/ce:review`는 17개의 전문화된 리뷰어 페르소나를 병렬로 실행하고, 구조화된 JSON으로 결과를 수집한 뒤 신뢰도 게이팅과 중복 제거 파이프라인으로 최종 리포트를 생성한다.

### 7.4 적대적(Adversarial) 접근

adversarial-reviewer, adversarial-document-reviewer 등이 구현을 의도적으로 공격하여 실패 시나리오를 찾아낸다.

### 7.5 학습의 복리 축적

`/ce:compound`로 해결된 문제를 `docs/solutions/`에 YAML 프론트매터와 함께 문서화. `/ce:compound-refresh`로 오래된 학습을 갱신. `/ce:brainstorm`과 `/ce:plan`에서 과거 학습을 자동 참조.

### 7.6 자율 실행 모드

`/lfg` 스킬은 plan → work → review → todo-resolve → test-browser → feature-video의 완전 자율 파이프라인을 실행한다.

### 7.7 명시적 매핑 원칙

플랫폼 간 변환 시 암묵적 매직보다 명시적 매핑을 선호하며, 타겟 특화 동작을 전용 변환기/라이터에 캡슐화한다.

---

## 8. 학습 축적 상세 (`/ce:compound`)

Compound Engineering의 핵심 메커니즘. 각 작업에서 얻은 인사이트를 구조화하여 저장하고, 이후 작업에서 자동으로 참조한다.

### 학습 문서 형식

```yaml
---
title: "Async Error Handling Pattern"
date: 2026-04-08
tags: [async, error-handling, typescript]
context: "Node.js 서비스에서 Promise.all 실패 시 개별 에러 복구가 필요한 경우"
---

## 문제
Promise.all에서 하나의 promise가 실패하면 전체가 실패하는 문제

## 해결
Promise.allSettle + 필터 패턴 사용

## 교훈
- Promise.all은 all-or-nothing이므로 부분 실패가 예상되면 allSettle 사용
- 에러 타입별 복구 전략을 미리 정의해야 함
```

### 학습 생애주기

1. **작성**: `/ce:compound`가 review 이후 자동 또는 수동으로 학습 추출
2. **참조**: 이후 `/ce:brainstorm`, `/ce:plan`에서 관련 학습을 자동 검색하여 컨텍스트로 주입
3. **갱신**: `/ce:compound-refresh`가 오래된 학습을 감사하여 keep/update/replace/archive 분류
4. **폐기**: 더 이상 유효하지 않은 학습은 archive 처리

---

## 9. Dev Kit과의 비교

| 관점 | Dev Kit | Compound Engineering |
|------|---------|---------------------|
| **철학** | 규율적 (discipline) | 복리적 (compound) |
| **코어 사이클** | 4단계 선형 | 7단계 순환 |
| **상태 관리** | JSON Schema 기반 정교함 | 스킬별 개별 관리 |
| **에이전트 수** | 없음 (역할 기반) | 50+ 전문 에이전트 |
| **리뷰** | critic + readiness-checker (2개) | 17개 페르소나 다중 에이전트 |
| **학습 축적** | 없음 | `/ce:compound` + `/ce:compound-refresh` |
| **크로스 플랫폼** | Claude Code + Codex | 10개 플랫폼 |
| **의존성** | 거의 없음 | Bun + citty + js-yaml |
| **강점** | 예측 가능성, 경량, 상태 정교 | 규모, 자동화, 복리 학습 |

---

## 10. 핵심 인사이트

1. **복리 학습이 진짜 차별화 요소** — 나머지는 다른 도구에서도 찾을 수 있지만, 작업 완료 후 학습을 추출하고 이를 미래 작업의 passive context로 제공해 명시적 phase에서 활용하는 메커니즘은 업계에서 유일무이
2. **크로스 플랫폼 변환은 엔지니어링 투어 드포스** — 10개 플랫폼의 서로 다른 설정 포맷, 명령어 체계, 환경변수를 자동 변환하는 것은 상당한 엔지니어링 노력
3. **스킬 격리 원칙은 실용적** — 플랫폼 독립성을 위해 자립성을 선택한 것은 트레이드오프이지만, 크로스 플랫폼 변환이 핵심 가치라면 정당화됨
4. **상태 관리는 Dev Kit이 더 강함** — Compound CE는 세션 상태를 체계적으로 관리하지 않음. Dev Kit의 JSON Schema 기반 상태 머신이 더 견고함
5. **에이전트 수가 많은 건 양날의 검** — 50+ 에이전트는 강력하지만, 유지보수 부담이 크고 사용자가 전체를 파악하기 어려움

# `oh-my-codex` 저장소 상세 분석

분석 대상: `https://github.com/Yeachan-Heo/oh-my-codex`  
분석 시점: `2026-04-10`  
분석 방식: 원격 저장소를 shallow clone 해서 코드, 문서, 워크플로우 정의, CI/릴리스 메타데이터를 직접 읽고 정리. GitHub 공개 저장소 페이지도 함께 확인.

## 한 줄 요약

`oh-my-codex`는 단순한 프롬프트/스킬 모음이 아니다. OpenAI Codex CLI 위에 설치되는 "운영 레이어"에 가깝고, `setup`으로 설정과 훅을 주입하고, `skills`와 `AGENTS.md`로 작업 방식을 정의하며, `tmux` 기반 팀 런타임과 MCP 서버, HUD, 알림, Rust 네이티브 사이드카까지 얹어서 Codex를 더 강한 작업 환경으로 바꾸려는 레포다.

## 스냅샷 요약

- GitHub 공개 페이지 기준 레포 상태 (`2026-04-10` 확인):
  - Public repository
  - Star 약 `20k`
  - Fork 약 `1.8k`
  - Open issues `9`
  - Open pull requests `2`
  - Commit 표기 `1,485`
- 현재 패키지 버전: `0.12.4`
- 로컬 clone 기준 추적 파일 수: `756`
- `src/` TypeScript 파일 수: `435`
- 테스트 파일 수(`src` + `crates` 기준): `224`
- 스킬 디렉터리 수: `36`
- 프롬프트 파일 수: `33`
- Rust crate 수: `5`
- `docs/` 파일 수: `126`
- `missions/` 디렉터리 수: `13`
- `playground/` 디렉터리 수: `4`
- GitHub Actions 워크플로우: `ci.yml`, `release.yml`, `pr-check.yml`

주의:
- Star/fork/issue/PR/commit 수치는 GitHub UI 기준 스냅샷이라 이후 바뀔 수 있다.
- 커밋 수는 shallow clone이 아니라 GitHub 저장소 페이지에서 확인한 값이다.

## 이 저장소를 어떻게 봐야 하나

이 레포는 동시에 네 가지 성격을 가진다.

1. Codex CLI용 설치형 런타임 도구
2. 워크플로우 스킬/프롬프트 배포 저장소
3. `tmux` 기반 장기 실행 팀 오케스트레이터
4. 실험/검증을 포함한 AI 코딩 운영체제 같은 제품 레포

핵심은 "Codex 자체를 대체"하는 것이 아니라, Codex를 실행 엔진으로 남겨 둔 채 그 위에 더 강한 기본값과 절차를 올리는 것이다.

## 저장소의 큰 구조

```text
oh-my-codex/
|
+-- src/                         # TypeScript 제어 평면
|   |
|   +-- cli/                    # omx 명령 진입점과 하위 명령
|   +-- team/                   # tmux 팀 런타임, worktree, mailbox, state
|   +-- hooks/                  # Codex hook/overlay/routing
|   +-- mcp/                    # state/memory/code_intel/trace 서버
|   +-- hud/                    # 상태 표시용 HUD
|   +-- notifications/          # Discord/Slack/Telegram/OpenClaw 알림
|   +-- runtime/                # Rust 런타임 bridge
|   +-- autoresearch/           # guided research loop
|   `-- scripts/                # build/test/generate/notify 보조 스크립트
|
+-- skills/                     # workflow skill 정의
+-- prompts/                    # 역할별 role prompt
+-- crates/                     # Rust 네이티브 바이너리/런타임
+-- docs/                       # 사용자 문서 + 내부 계약/리포트
+-- missions/                   # dogfooding/실험 과제
+-- playground/                 # 데모/실험 샘플
+-- templates/                  # 설치/생성용 템플릿
+-- AGENTS.md                   # 최상위 운영 계약
+-- README.md                   # 사용자 온보딩
+-- package.json                # npm 패키지 및 CLI 메타데이터
`-- Cargo.toml                  # Rust workspace
```

## 이 레포가 실제로 하는 일

### 1. `omx`라는 설치형 Codex 보강 CLI 제공

루트 `package.json`을 보면 이 패키지는 `omx`라는 바이너리를 제공한다. 주된 표면은 아래와 같다.

- `omx`
- `omx setup`
- `omx uninstall`
- `omx doctor`
- `omx team`
- `omx ralph`
- `omx autoresearch`
- `omx explore`
- `omx sparkshell`
- `omx hud`
- `omx tmux-hook`
- `omx hooks`
- `omx state`
- `omx agents`, `omx agents-init`
- `omx session`

즉 사용자는 이 레포를 "문서 읽는 저장소"로만 쓰는 게 아니라, 글로벌 npm 패키지로 설치해 Codex 런타임을 직접 바꾸는 도구로 쓰게 된다.

### 2. `setup`으로 Codex 환경을 실제로 수정

`src/cli/setup.ts`와 `src/config/generator.ts`를 보면 `omx setup`은 꽤 공격적인 설치 작업을 한다.

- `config.toml` 병합
- OMX top-level 설정 주입
- feature flag 주입
- MCP server 설정 병합
- prompt 설치
- skill 설치
- native agent TOML 생성
- scope별 `AGENTS.md` 배치
- `.codex/hooks.json`의 OMX 관리 항목 갱신
- `.omx/` 상태/백업 경로 생성

이 말은 곧 OMX가 "Codex 옆에 붙는 헬퍼"가 아니라 "Codex의 기본 동작 방식을 재정의하는 관리자"라는 뜻이다.

### 3. `AGENTS.md`와 `skills/`를 중심으로 작업 방식을 제품화

이 저장소의 가장 중요한 문서는 README보다 `AGENTS.md`다.

`AGENTS.md`는 다음을 중앙 계약으로 둔다.

- 언제 직접 실행하고 언제 계획/팀 모드로 갈지
- 어떤 키워드가 어떤 스킬로 라우팅되는지
- 검증 루프를 어떻게 강제할지
- 팀/서브에이전트/모델 라우팅을 어떻게 할지
- `.omx/` 상태와 실행 프로토콜을 어떻게 유지할지

즉 이 레포의 제품 중심은 코드가 아니라 "행동 규약"이다.  
`skills/deep-interview/SKILL.md`, `skills/ralplan/SKILL.md`, `skills/team/SKILL.md` 같은 파일은 단순 설명서가 아니라 실행 절차서다.

### 4. `tmux` 기반 실전형 멀티에이전트 런타임 제공

`src/team/runtime.ts`와 `skills/team/SKILL.md`를 보면 OMX의 차별점은 진짜 `tmux` pane 기반 팀 런타임이다.

핵심 요소:

- 리더와 워커를 분리된 pane/session으로 띄움
- `.omx/state/team/<team>/...` 아래에 상태 파일 기록
- worker inbox, mailbox, dispatch request, heartbeat 관리
- 선택적으로 git worktree 분리
- startup / resume / status / shutdown lifecycle 제공
- HUD와 resize hook, notification hook까지 결합

이건 "한 대화 안에서 서브에이전트 몇 개 돌리는 것"보다 훨씬 운영 시스템에 가깝다.

### 5. MCP 서버를 번들링해서 로컬 상태/메모리/트레이스를 노출

`src/mcp/bootstrap.ts` 기준 자동 시작 대상 서버는 네 개다.

- `state`
- `memory`
- `code_intel`
- `trace`

이 서버들은 stdio transport로 붙고, `setup` 과정에서 Codex 설정에 녹아들 수 있다.  
즉 OMX는 프롬프트 레이어만이 아니라 로컬 도구 인터페이스 계층도 제공한다.

### 6. Rust 네이티브 바이너리로 일부 성능/런타임 문제를 분리

Rust workspace 구성:

- `omx-explore`
- `omx-mux`
- `omx-runtime`
- `omx-runtime-core`
- `omx-sparkshell`

역할을 보면:

- `omx-explore-harness`: 읽기 전용 repository lookup harness
- `omx-sparkshell`: shell-native sidecar
- `omx-runtime`: 런타임 상태 조작/스냅샷 담당
- `omx-runtime-core`, `omx-mux`: 공용 코어와 보조 계층

즉 전체 제품은 TypeScript만으로 끝나지 않고, 실행 성능과 상태 일관성이 중요한 부분을 Rust로 밀어 넣고 있다.

## 아키텍처를 어떻게 읽을 수 있나

### ASCII 다이어그램 1: 전체 동작 계층

```text
User
 |
 v
omx CLI (TypeScript)
 |
 +-- setup/config merge
 |    |- config.toml
 |    |- hooks.json
 |    |- prompts/
 |    |- skills/
 |    `- AGENTS.md
 |
 +-- workflow layer
 |    |- $deep-interview
 |    |- $ralplan
 |    |- $team
 |    `- $ralph
 |
 +-- runtime layer
 |    |- .omx/state
 |    |- HUD
 |    |- notifications
 |    `- tmux workers / worktrees
 |
 +-- local tool layer
 |    |- MCP servers
 |    |- explore
 |    `- sparkshell
 |
 `-- native sidecars (Rust)
      |- omx-runtime
      |- omx-explore-harness
      `- omx-sparkshell
```

### 1. "프롬프트 팩"이 아니라 "Codex 운영체제"에 가까운 설계

README는 OMX를 Codex CLI용 workflow layer라고 소개하지만, 코드 기준으로 보면 실체는 그보다 더 넓다.

- 설치 관리
- 모델/reasoning 기본값 관리
- state persistence
- lifecycle hook 관리
- tmux pane orchestration
- notification routing
- MCP bootstrap
- native sidecar packaging

그래서 이 레포는 "좋은 프롬프트 묶음"보다 "Codex 사용 방식을 강하게 opinionated하게 표준화하는 런타임"으로 이해하는 게 맞다.

### 2. `AGENTS.md`를 최상위 헌법으로 두는 구조

이 저장소에서 `prompts/*.md`는 중요하지만, 그보다 위에 `AGENTS.md`가 있다.  
`AGENTS.md`는:

- 모드 선택 규칙
- delegation 규칙
- keyword routing
- verification 규약
- team pipeline
- model routing

을 통합한다.

이 설계의 장점:

- 개별 prompt가 제각각 행동하지 않음
- 설치 후 사용자 프로젝트 전체에 일관된 운영 계약 부여 가능
- 팀/스킬/프롬프트가 같은 철학으로 움직임

비용:

- 새 사용자가 이해해야 할 개념량이 많아짐
- 실제 실행 문제 발생 시 문서 계약과 런타임 구현 둘 다 추적해야 함

### 3. `.omx/`를 파일 기반 상태 머신으로 쓰는 구조

`deep-interview`, `ralplan`, `team`, `autoresearch` 전부 `.omx/`를 적극 사용한다.

대표 예:

- `.omx/context/`
- `.omx/specs/`
- `.omx/interviews/`
- `.omx/state/`
- `.omx/logs/`
- `.omx/backups/`

이 접근의 장점:

- 세션 복구가 쉬움
- 툴 간 공유 상태가 명시적임
- 사람도 파일을 열어 상태를 읽을 수 있음
- 장기 실행 워크플로우에 강함

단점:

- 파일 계약이 많아져서 복잡도가 높음
- 여러 기능이 같은 상태 루트를 만지면 회복성보다 결합도가 커질 수 있음

### 4. TypeScript 제어 평면 + Rust 데이터 평면의 과도기적 혼합

`src/runtime/bridge.ts`는 매우 중요한 신호를 준다.

- 의미 있는 상태 mutation은 Rust `omx-runtime`으로 라우팅
- 상태 조회는 Rust가 쓴 compatibility JSON을 읽음
- `OMX_RUNTIME_BRIDGE=0`이면 TypeScript direct path로 fallback

이건 OMX가 Rust-first runtime으로 천천히 이동 중이라는 뜻이다.

장점:

- 런타임 핵심부를 더 결정적으로 만들 수 있음
- 상태 일관성과 성능을 개선할 여지가 큼

리스크:

- TS와 Rust 양쪽에 의미가 중복될 수 있음
- bridge/fallback이 공존하는 동안 디버깅 난이도가 올라감

### 5. `explore`와 `sparkshell`을 분리한 read-only 경량 경로

`src/cli/explore.ts`와 `src/cli/sparkshell.ts`는 단순 보조 명령이 아니다.

설계 의도는 분명하다.

- 간단한 read-only lookup은 무거운 일반 에이전트 추론 대신 전용 경로로 보내기
- shell 메타문자를 막거나 허용 범위를 제한하기
- 긴 출력이나 특정 read-only git/find/rg 계열은 네이티브 sidecar로 흘리기

즉 OMX는 "모든 걸 무거운 에이전트 호출로 처리"하지 않고, lookup/inspection은 별도 경량 경로로 최적화하려 한다.

### 6. 팀 모드를 Codex native subagent와 구분하는 철학이 선명함

`skills/team/SKILL.md`는 team runtime과 native subagent를 명확히 분리한다.

- native subagent: 한 세션 안의 bounded parallelism
- `omx team`: durable tmux workers, shared state, mailbox, lifecycle, worktree가 필요한 경우

이 구분은 꽤 건강하다.  
즉 OMX는 "병렬 처리"를 한 가지 방식으로만 밀지 않고, 세션 내부 fanout과 장기 지속 팀 런타임을 다른 문제로 본다.

## ASCII 다이어그램 2: 대표 워크플로우

```text
Ambiguous request
   |
   v
$deep-interview
   |
   v
.omx/specs / .omx/context
   |
   v
$ralplan
   |
   +-- Planner
   +-- Architect
   `-- Critic
   |
   v
Approved plan
   |
   +--> $ralph        # single-owner persistence loop
   |
   `--> $team         # tmux-based coordinated execution
            |
            +-- worker panes
            +-- inbox/mailbox/dispatch
            +-- heartbeat/HUD/notifications
            `-- verify -> shutdown
```

## 주요 디렉터리별 역할

| 경로 | 역할 |
| --- | --- |
| `src/cli/` | `omx` 하위 명령의 실제 진입점 |
| `src/team/` | 팀 런타임, pane 관리, worktree, dispatch, state |
| `src/hooks/` | Codex hook 연결, overlay, routing, keyword detection |
| `src/mcp/` | state/memory/code_intel/trace MCP 서버 |
| `src/notifications/` | Discord/Slack/Telegram 알림 및 reply listener |
| `src/openclaw/` | OpenClaw 게이트웨이/커스텀 알림 라우팅 |
| `src/runtime/` | Rust `omx-runtime` bridge |
| `src/config/` | `config.toml`, hook, model, MCP registry 병합 로직 |
| `skills/` | 사용자 트리거형 workflow skill 집합 |
| `prompts/` | 역할별 프롬프트 surface |
| `crates/` | Rust 네이티브 실행 파일 및 코어 라이브러리 |
| `docs/` | 제품 문서, 계약 문서, 리포트, QA/benchmark 문서 |
| `missions/` | 제품 기능을 과제로 실험/검증하는 공간 |
| `playground/` | 데모나 실험 샘플 |

## 스킬/프롬프트 시스템 분석

### 핵심 스킬 축

`src/catalog/manifest.json` 기준 중심축은 아래로 읽힌다.

- 실행 계열:
  - `autopilot`
  - `ralph`
  - `ultrawork`
  - `team`
- 계획 계열:
  - `plan`
  - `ralplan`
  - `deep-interview`
- 유틸리티:
  - `doctor`
  - `help`
  - `note`
  - `trace`
  - `hud`
  - `omx-setup`
- shortcut/alias:
  - `build-fix`
  - `code-review`
  - `security-review`
  - `web-clone`
  - `frontend-ui-ux`
  - `deepsearch`

즉 스킬 체계는 "탐색 -> 계획 -> 실행 -> 검증 -> 운영"을 거의 전 주기로 덮는다.

### 역할 프롬프트는 별도 카탈로그로 존재

`prompts/`에는 아래 같은 역할 프롬프트가 있다.

- `executor`
- `planner`
- `architect`
- `debugger`
- `verifier`
- `designer`
- `writer`
- `researcher`
- `code-reviewer`
- `security-reviewer`
- `team-orchestrator`
- `team-executor`

이 말은 스킬이 workflow surface라면, prompt는 role surface다.  
OMX는 이 둘을 분리해서 생각한다.

### 모델 정책도 제품의 일부다

`src/config/models.ts` 기준 기본 모델은 다음처럼 잡혀 있다.

- frontier default: `gpt-5.4`
- standard default: `gpt-5.4-mini`
- spark default: `gpt-5.3-codex-spark`

즉 이 레포는 단지 "어떤 프롬프트를 쓸지"만이 아니라 "어떤 종류의 모델을 어떤 lane에 배치할지"까지 제품 범위로 본다.

## 운영 성숙도 신호

이 저장소는 아이디어 저장소 수준을 넘어선다. 근거는 꽤 많다.

### 1. CI가 넓고 구체적임

`ci.yml` 기준:

- Rust format check
- Rust clippy
- Node lint
- Node typecheck
- no-unused check
- dist build artifact
- 테스트를 여러 lane으로 분리 실행
- generated catalog docs check
- team/state coverage gate
- full TypeScript coverage report

즉 "프롬프트 레포인데 테스트가 없는" 타입이 아니다.

### 2. 릴리스 파이프라인이 네이티브 자산까지 배포

`release.yml` 기준:

- npm 버전과 Cargo workspace 버전 동기화 검증
- Linux gnu/musl, macOS intel/arm, Windows용 native artifact 빌드
- release asset manifest 생성
- smoke verify
- packed install smoke test
- npm publish

이건 취미성 프롬프트 레포보다 훨씬 제품 레포에 가깝다.

### 3. `doctor`가 단순 상태 출력이 아니라 진단 도구

`src/cli/doctor.ts`는 단순히 "설치됨/안 됨"만 말하지 않는다.

- Codex CLI 존재
- Node 버전
- explore harness 준비 상태
- config 설치 여부
- explore routing 설정
- prompts/skills/AGENTS/MCP 상태
- team runtime stale/orphan 상태

즉 사용자가 망가진 런타임을 복구할 수 있는 최소한의 진단 계층을 제공한다.

## 이 저장소의 강점

### 1. 범용성보다 운영 일관성을 선택한 점

이 레포는 사용자가 아무렇게나 쓰도록 두지 않는다.  
`deep-interview -> ralplan -> team/ralph` 같은 표준 흐름을 강하게 권한다.

이 철학은 맞는 사용자에게는 큰 장점이다.

- 덜 헤맨다
- 긴 작업에 강하다
- 검증 누락이 줄어든다
- 팀 모드의 역할이 분명하다

### 2. 장기 실행/복구/관찰 가능성에 진심

`.omx/` 상태 파일, HUD, notify hook, mailbox, heartbeat, doctor, session search, trace MCP를 보면 이 레포는 "한 번 답 잘 주기"보다 "몇 시간짜리 작업을 망가지지 않게 끌고 가기"에 더 관심이 많다.

### 3. 네이티브 사이드카 도입이 전략적으로 맞음

읽기 전용 탐색이나 shell/native 실행, 핵심 런타임 상태 처리는 TypeScript보다 별도 바이너리로 분리하는 편이 낫다.  
이 레포는 그 점을 일찍 받아들인 것으로 보인다.

### 4. 문서와 코드가 둘 다 두껍다

- README와 docs가 풍부하고
- 스킬이 상세하며
- 코드도 크고
- 테스트도 많다

즉 사용자-facing 설명과 내부 구현이 둘 다 얇지 않다.

## 이 저장소의 약점과 리스크

### 1. 표면적이 너무 넓다

이 레포는 다음을 한 레포 안에 모두 담고 있다.

- CLI
- setup/uninstall
- hooks
- tmux team runtime
- MCP
- notifications
- HUD
- native sidecars
- docs generator
- skills/prompts
- research workflows

이런 저장소는 강력하지만, 어느 한 부분이 깨져도 사용자 경험 전체가 흔들리기 쉽다.

### 2. 설치가 침습적이다

`omx setup`은 config, hook, prompt, skill, AGENTS를 실제로 건드린다.  
즉 사용자는 "기능 추가"가 아니라 "환경 관리 권한"을 OMX에 넘기는 셈이다.

이건 파워 유저에게는 괜찮지만, 라이트 유저에게는 진입 장벽이 된다.

### 3. macOS/Linux + tmux 편향이 분명하다

README 자체가 기본 권장 경로를 macOS/Linux + Codex CLI로 좁힌다.  
native Windows와 Codex App은 기본 경험이 아니라고 분명히 말한다.

즉 제품 포지셔닝은 선명하지만, 범용 호환성은 아직 약하다.

### 4. 문서 계약과 구현 계약의 동시 유지 비용이 높다

이 저장소는 다음의 드리프트 위험이 있다.

- README
- docs 사이트
- skill 문서
- prompt 문서
- catalog manifest
- 실제 구현 코드

이미 이를 방지하려는 `generate-catalog-docs --check` 같은 장치가 있지만, 표면이 넓어서 완전히 피하기는 어렵다.

### 5. TS와 Rust의 이중 권위가 당분간 유지보수 부담이 될 수 있다

bridge/fallback 구조는 좋은 과도기 전략이지만, 긴 기간 유지되면:

- 어느 쪽이 진실 원본인지 헷갈리고
- 버그가 bridge인지 runtime인지 구분하기 어려워지며
- 테스트 매트릭스가 커진다

## 누구에게 잘 맞는가

잘 맞는 사용자:

- Codex CLI를 이미 자주 쓰는 사람
- macOS/Linux + `tmux` 환경에 익숙한 사람
- 장기 실행 작업, 병렬 작업, 검증 루프가 중요한 사람
- 작업 방식을 표준화하고 싶은 개인/소규모 팀

덜 맞는 사용자:

- 그냥 가벼운 프롬프트 팩만 원하는 사람
- Codex App 중심 사용자
- 설정 파일과 훅을 건드리는 설치를 꺼리는 사람
- `tmux`/worktree/상태 파일 기반 운영을 번거롭게 느끼는 사람

## 개인적인 총평

`oh-my-codex`는 "Codex에 스킬 몇 개 추가한 저장소"로 보면 과소평가다.  
실제로는 Codex를 중심으로 한 개발 작업을 하나의 운영 체계로 묶으려는 시도에 가깝다.

이 레포의 진짜 강점은 프롬프트 퀄리티 자체보다도:

- 실행 전 명확화
- 계획 승인
- 장기 상태 보존
- 병렬 런타임 제어
- 검증과 복구 도구

를 하나의 제품으로 연결했다는 점이다.

반대로 가장 큰 약점도 여기서 나온다.  
좋은 날에는 "강한 운영 레이어"지만, 나쁜 날에는 "배워야 할 개념과 만져야 할 설정이 많은 복합 시스템"이 된다.

그럼에도 불구하고, 현재 공개된 AI 코딩 워크플로우 저장소들 가운데서는 꽤 높은 수준의 제품화와 운영 성숙도를 보여 주는 편이다.  
특히 `tmux` 기반 팀 오케스트레이션, `.omx/` 상태 모델, Rust sidecar 도입, CI/릴리스 파이프라인까지 연결한 점은 이 레포를 단순 문서형 skill 저장소와 분명히 구분한다.

## 추천 읽기 순서

처음 파악할 때는 아래 순서가 효율적이다.

1. `README.md`
2. `AGENTS.md`
3. `skills/deep-interview/SKILL.md`
4. `skills/ralplan/SKILL.md`
5. `skills/team/SKILL.md`
6. `src/cli/index.ts`
7. `src/cli/setup.ts`
8. `src/team/runtime.ts`
9. `src/runtime/bridge.ts`
10. `src/config/generator.ts`
11. `src/config/models.ts`

## 결론

`oh-my-codex`는 Codex CLI를 더 잘 쓰게 해 주는 부가 도구가 아니라, Codex 중심 개발 방식을 재설계하려는 런타임 프레임워크다.

정리하면:

- 프롬프트 레포인가? 절반만 맞다.
- CLI 제품인가? 맞다.
- 멀티에이전트 런타임인가? 맞다.
- 설치형 운영 레이어인가? 가장 정확하다.

그래서 이 저장소를 평가할 때는 "스킬 개수"보다:

- 설치 범위
- 상태 모델
- 팀 런타임 안정성
- 네이티브 보조 바이너리 전략
- CI/릴리스 완성도

를 기준으로 보는 편이 훨씬 정확하다.

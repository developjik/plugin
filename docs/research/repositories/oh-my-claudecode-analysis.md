# `oh-my-claudecode` 저장소 상세 분석

분석 대상: `https://github.com/Yeachan-Heo/oh-my-claudecode`  
분석 시점: `2026-04-10`  
분석 방식: 원격 저장소를 shallow clone 해서 코드, 문서, 스킬, 에이전트, 설치/런타임 계층, CI/릴리스 메타데이터를 직접 읽고 정리. GitHub 공개 저장소 페이지도 함께 확인.

## 한 줄 요약

`oh-my-claudecode`는 Claude Code용 플러그인 저장소이면서 동시에 npm CLI 제품이고, 그 위에 in-session skill 시스템, tmux 기반 외부 CLI 팀 런타임, MCP 도구 서버, 자동 업데이트/캐시 동기화, 그리고 Codex/Gemini 연동까지 얹은 "Claude Code용 통합 오케스트레이션 플랫폼"에 가깝다.

## 스냅샷 요약

- GitHub 공개 페이지 기준 레포 상태 (`2026-04-10` 확인):
  - Public repository
  - Star 약 `26.9k`
  - Fork 약 `2.5k`
  - Open issues `0`
  - Open pull requests `0`
  - Commit 표기 `2,478`
- 현재 패키지 버전: `4.11.4`
- `.claude-plugin/plugin.json` 버전: `4.11.4`
- `.claude-plugin/marketplace.json` 버전: `4.11.4`
- 로컬 clone 기준 추적 파일 수: `5,019`
- `src/` TypeScript 파일 수: `926`
- 테스트 파일 수(`src` + `tests` 기준): `465`
- 에이전트 프롬프트 파일 수: `19`
- 스킬 디렉터리 수: `37`
- `docs/` 파일 수: `32`
- `dist/` 파일 수: `3,701`
- GitHub Actions 워크플로우 수: `6`
- 벤치마크 디렉터리: `code-reviewer`, `debugger`, `executor`, `harsh-critic` 중심

주의:
- Star/fork/issue/PR/commit 수치는 GitHub UI 스냅샷이라 이후 변동될 수 있다.
- 추적 파일 수가 큰 이유는 `dist/` 산출물과 테스트/벤치마크/문서가 함께 커밋돼 있기 때문이다.

## 이 저장소를 어떻게 봐야 하나

이 레포는 동시에 다섯 가지 정체성을 가진다.

1. Claude Code marketplace/plugin 배포 저장소
2. npm 전역 설치형 CLI 도구 (`omc`)
3. Claude Code 세션 안에서 동작하는 skill/agent 운영 레이어
4. tmux 기반 외부 CLI 워커 런타임
5. Codex/Gemini까지 끌어오는 다중 모델 오케스트레이션 허브

핵심 메시지는 단순하다.  
"Claude Code를 배우지 말고 OMC를 쓰라"는 README 문구 그대로, Claude Code의 원래 표면 위에 더 강한 기본값과 운영 절차를 씌우는 제품이다.

## 저장소의 큰 구조

```text
oh-my-claudecode/
|
+-- .claude-plugin/               # Claude Code plugin + marketplace 메타데이터
+-- agents/                       # 사용자-facing agent prompt 원본
+-- skills/                       # in-session skill 정의
+-- src/                          # TypeScript 소스
|   |
|   +-- cli/                      # omc CLI 엔트리와 명령 구현
|   +-- installer/                # ~/.claude 설치/병합/업데이트
|   +-- hooks/                    # Claude Code shell hook bridge
|   +-- mcp/                      # OMC custom tools server
|   +-- team/                     # tmux 팀 런타임 + bridge + 작업 상태
|   +-- features/                 # magic keywords, delegation, auto-update
|   +-- agents/                   # agent registry와 tier/model 규칙
|   +-- notifications/            # Discord/Slack/OpenClaw/알림 계층
|   +-- interop/                  # OMC-OMX / 외부 도구 연동
|   `-- tools/                    # LSP/AST/state/notepad/memory/trace 도구
|
+-- dist/                         # 커밋된 빌드 산출물
+-- bridge/                       # CJS wrapper / runtime 진입 파일
+-- docs/                         # 아키텍처, 기능, 훅, 설치, 참조 문서
+-- benchmarks/                   # agent prompt 성능 평가
+-- missions/                     # autoresearch/미션 샘플
+-- tests/                        # fixture 기반 테스트
+-- hooks/                        # 설치 대상 hook 자산
+-- templates/                    # hook/rules 템플릿
+-- README*.md                    # 다국어 온보딩 문서
+-- AGENTS.md                     # 최상위 운영 계약
+-- CLAUDE.md                     # Claude용 런타임 지침 표면
`-- package.json                  # npm 패키지 메타데이터
```

## 이 레포가 실제로 하는 일

### 1. Claude Code plugin으로 설치된다

README 기준 권장 설치는 Claude Code marketplace/plugin 경로다.

```bash
/plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode
/plugin install oh-my-claudecode
```

`.claude-plugin/plugin.json`과 `.claude-plugin/marketplace.json`이 실제 배포 메타데이터를 들고 있고, 레포는 plugin-first 제품으로 설계돼 있다.

### 2. 동시에 `omc`라는 npm CLI도 제공한다

`package.json` 기준 실행 바이너리는 다음 세 이름으로 연결된다.

- `oh-my-claudecode`
- `omc`
- `omc-cli`

세 엔트리 모두 `bridge/cli.cjs`를 바라본다.  
즉 이 레포는 plugin만이 아니라 독립 실행형 CLI 제품으로도 배포된다.

### 3. 세션 안에서는 skill 시스템으로 동작한다

사용자가 Claude Code 세션 안에서 쓰는 핵심 표면은 `/oh-my-claudecode:<skill>` 혹은 README가 보여 주는 간단한 `/team`, `/autopilot`, `/deep-interview` 같은 진입점이다.

실제 스킬 군:

- `autopilot`
- `ralph`
- `ralplan`
- `team`
- `ccg`
- `deep-interview`
- `ultrawork`
- `verify`
- `visual-verdict`
- `omc-setup`
- `omc-doctor`
- `mcp-setup`
- `trace`
- `skill`

즉 이 레포는 "Claude에게 프롬프트 몇 개 추가"하는 수준이 아니라, 작업 모드를 skill로 제품화한다.

### 4. 팀 오케스트레이션이 두 종류다

이 저장소를 이해할 때 가장 중요한 특징 중 하나다.

#### A. `/team` - Claude Code native teams

`skills/team/SKILL.md` 기준, `/team`은 Claude Code의 네이티브 팀 기능을 활용한 staged pipeline이다.

파이프라인:

`team-plan -> team-prd -> team-exec -> team-verify -> team-fix`

이 경로는 세션 내부에서 작업을 조직하고, lead/teammate 구조와 task dependency를 Claude Code 고유 표면 위에서 운용한다.

#### B. `omc team` - tmux CLI workers

README와 `src/cli/team.ts`, `src/team/runtime-cli.ts`를 보면 `omc team`은 완전히 다른 런타임이다.

- `claude` CLI pane
- `codex` CLI pane
- `gemini` CLI pane
- tmux session / pane / worktree / team-state 파일

즉 이름은 같지만, `/team`과 `omc team`은 같은 기능의 UI 래퍼가 아니라 서로 다른 실행 계층이다.

### 5. 외부 모델도 OMC 안으로 끌어온다

이 저장소는 Claude 중심이지만 Claude-only는 아니다.

대표 사례:

- `omc ask codex`
- `omc ask gemini`
- `/ccg` = Codex + Gemini advisor를 동시에 쓰고 Claude가 합성
- `omc team N:codex`
- `omc team N:gemini`

즉 OMC는 Claude Code용 제품이지만, 다른 모델을 조언자나 외부 워커로 흡수하는 허브 역할도 한다.

### 6. 설치 이후에는 `~/.claude/`를 적극 관리한다

`src/installer/index.ts`를 보면 OMC installer는 꽤 침습적이다.

- `~/.claude/agents`
- `~/.claude/skills`
- `~/.claude/hooks`
- `~/.claude/hud`
- `settings.json`
- `CLAUDE.md`
- `.omc-version.json`

을 설치/갱신하고, 필요하면 MCP registry까지 동기화한다.

즉 "설치하면 끝"이 아니라 "사용자 Claude 환경을 관리하는 관리자"에 가깝다.

### 7. 내장 MCP 도구 서버를 제공한다

`src/mcp/omc-tools-server.ts`는 이 레포의 또 다른 핵심이다.

카테고리별로 보면:

- LSP 도구
- AST 도구
- Python REPL
- skill/state/notepad/memory/trace 도구
- shared memory 도구
- wiki 도구
- deepinit manifest 도구
- 선택적 interop 도구

즉 OMC는 orchestration prompt 레이어만이 아니라, Claude 세션 안에서 쓸 로컬 도구 서버도 함께 제공한다.

## 아키텍처 핵심 분석

### ASCII 다이어그램 1: 배포/설치 표면

```text
Repository
   |
   +-- .claude-plugin/          -> Claude Code marketplace install
   |
   +-- package.json + bridge/   -> npm global install (omc)
   |
   +-- src/                     -> source of truth
   |
   `-- dist/                    -> committed build artifacts
                |
                v
            omc setup
                |
                +-- ~/.claude/agents
                +-- ~/.claude/skills
                +-- ~/.claude/hooks
                +-- ~/.claude/hud
                +-- settings.json
                +-- CLAUDE.md
                `-- unified MCP registry sync
```

### 1. plugin-first + npm-first를 동시에 품은 이중 배포 구조

이 저장소의 가장 큰 특징은 배포 표면이 하나가 아니라는 점이다.

- Claude marketplace/plugin 설치
- npm 글로벌 설치
- 로컬 checkout + `--plugin-dir` 개발 모드

특히 `docs/REFERENCE.md`와 installer 로직을 보면 `omc --plugin-dir <path>` + `omc setup --plugin-dir-mode` 조합이 로컬 개발용 정석으로 정리돼 있다.

이 구조의 장점:

- 일반 사용자는 plugin-first로 쉽게 시작 가능
- 파워 유저는 CLI/runtime path를 직접 관리 가능
- 플러그인 개발자는 cache 없는 local checkout 기반으로 빠르게 반복 가능

비용:

- 설치 경로가 여러 개라 문제 재현이 복잡해진다
- plugin cache / marketplace clone / npm runtime / local checkout 사이의 상태 불일치 위험이 커진다

### 2. `dist/`와 `bridge/`가 함께 커밋되는 "소스 + 제품" 레포

`tracked_files`가 5천 개를 넘는 이유는 `dist/`가 레포에 포함되기 때문이다.  
이건 단순 개발 저장소보다 "배포 가능한 제품 미러" 성격이 강하다는 뜻이다.

장점:

- npm publish나 plugin sync 시 산출물 확인이 명확하다
- 사용자가 소스만 받아도 빌드 산출물과 배포 자산을 같이 볼 수 있다

비용:

- PR diff가 커지기 쉽다
- 소스와 빌드 산출물의 동기화 관리가 필요하다

### 3. team이 하나가 아니라 둘이라는 점이 핵심 설계 포인트

이 레포는 `/team`과 `omc team`을 일부러 분리한다.

- `/team`: Claude Code native team workflow
- `omc team`: tmux 기반 외부 CLI worker runtime

이 분리는 생각보다 중요하다.

왜냐하면 OMC는 "Claude Code 내부 협업"과 "외부 CLI 프로세스를 pane으로 띄워 병렬 처리"를 서로 다른 문제로 취급하기 때문이다.

이 설계의 장점:

- Claude native UX를 해치지 않음
- Codex/Gemini 같은 외부 모델도 동일한 팀 개념 안에 수용 가능
- 세션 내부 fanout과 장기 tmux orchestration을 각각 최적화할 수 있음

이 설계의 비용:

- 사용자 입장에서 이름이 비슷하지만 다른 시스템 둘을 이해해야 함
- 팀 상태와 실패 모드가 두 갈래로 늘어난다

### ASCII 다이어그램 2: OMC의 이중 팀 모델

```text
User request
   |
   +-- /team "task"
   |      |
   |      +-- Claude Code native teams
   |      +-- TeamCreate / TaskCreate / SendMessage
   |      `-- staged pipeline inside Claude session
   |
   `-- omc team 2:codex "task"
          |
          +-- tmux session / split panes
          +-- runtime-cli.cjs
          +-- .omc/state/team/<team>
          +-- claude/codex/gemini workers
          `-- monitor / shutdown / resume
```

### 4. Claude Agent SDK 제약을 보완하는 계층이 많다

`src/features/delegation-enforcer.ts`는 이 레포의 매우 중요한 힌트다.

문제:
- Claude Code / Claude Agent SDK는 하위 agent 호출 때 모델이 자동 상속되지 않는 경우가 있다.

해결:
- agent/task 호출 시 모델 파라미터를 강제로 주입
- non-Claude provider일 때는 반대로 `forceInherit`를 켜서 Claude 계열 alias를 제거
- Bedrock/Vertex 모델 ID 형식도 별도로 보정

즉 OMC는 "좋은 프롬프트"뿐 아니라 "Claude Agent SDK의 운영상 빈틈"을 메우는 접착 계층이 많다.

### 5. hook 시스템은 쉘 훅 + Node bridge 혼합 구조

`src/hooks/index.ts`를 보면 훅 계층은 꽤 넓다.

- keyword detector
- ralph loop / PRD / verifier
- todo continuation
- rules injector
- orchestrator pre/post-tool logic
- auto slash command
- comment checker
- recovery handlers

그리고 문서/코드 설명상 실제 구조는:

1. Claude Code가 shell hook 실행
2. shell script가 Node/TypeScript bridge 호출
3. bridge가 JSON 응답을 돌려줌

즉 OMC는 Claude Code native hook surface를 가볍게 쓰는 게 아니라, 훅을 사실상 런타임 미들웨어처럼 사용한다.

### 6. unified MCP registry sync는 Claude 전용 제품을 넘어선 흔적

`src/installer/mcp-registry.ts`를 보면 이 레포는 Claude 설정만 보지 않는다.

- Claude MCP config path
- Codex `config.toml`
- global OMC registry

사이를 동기화하는 로직이 있다.

이건 재미있는 신호다.  
`oh-my-codex`가 별도 레포로 발전했지만, 이 저장소도 이미 다중 하네스 환경을 의식한 운영 레이어를 갖고 있었던 셈이다.

### 7. 자동 업데이트가 단순 버전 체크를 넘어서 캐시/마켓플레이스 동기화까지 감당

`src/features/auto-update.ts`는 단순 "새 버전 있으면 알려주기" 수준이 아니다.

- GitHub release 확인
- 설치된 plugin root 탐지
- marketplace clone fast-forward
- plugin cache sync
- stale cache purge

즉 OMC는 배포 표면이 여러 개라서, 업데이트 로직도 여러 표면을 동시에 맞춰야 한다.

이건 성숙도의 증거이기도 하고, 동시에 시스템 복잡도의 증거이기도 하다.

### 8. 프롬프트/에이전트 품질을 벤치마크하려는 흔적이 분명함

`benchmarks/run-all.ts`와 관련 디렉터리를 보면 최소한 다음 agent class에 대해 평가 체계를 둔다.

- `harsh-critic`
- `code-reviewer`
- `debugger`
- `executor`

즉 OMC는 프롬프트를 정성적으로만 관리하지 않고, baseline 비교와 회귀 확인까지 시도한다.

이건 보통의 skill/plugin 저장소보다 제품 성숙도가 높은 신호다.

## 주요 디렉터리별 역할

| 경로 | 역할 |
| --- | --- |
| `.claude-plugin/` | Claude Code plugin/marketplace 배포 메타데이터 |
| `agents/` | 사용자-facing agent prompt 원본 |
| `skills/` | in-session skill 집합 |
| `src/cli/` | `omc` CLI 명령 구현 |
| `src/installer/` | 설치, setup, hook/HUD/config 병합 |
| `src/hooks/` | Claude Code native hook bridge |
| `src/mcp/` | OMC custom tools server |
| `src/tools/` | LSP, AST, state, memory, trace 등 실제 도구 |
| `src/team/` | native/CLI 팀 런타임 핵심 |
| `src/features/` | auto-update, magic keywords, delegation enforcer |
| `src/interop/` | OMC-OMX 및 외부 도구 연동 |
| `bridge/` | CJS 진입 파일과 런타임 브리지 |
| `dist/` | 커밋된 빌드 산출물 |
| `docs/` | 사용자 문서 + 설계 문서 + 운영 참고서 |
| `benchmarks/` | 프롬프트 벤치마크 |
| `missions/` | autoresearch/mission 샘플 |

## CLI 표면 분석

`src/cli/index.ts`를 기준으로 보면 `omc`는 생각보다 CLI 표면이 넓다.

대표 명령:

- `omc`
- `omc launch`
- `omc interop`
- `omc ask`
- `omc config`
- `omc update`
- `omc install`
- `omc wait`
- `omc status`
- `omc daemon`
- `omc teleport`
- `omc session`
- `omc doctor`
- `omc setup`
- `omc hud`
- `omc mission-board`
- `omc team`
- `omc autoresearch`
- `omc ralphthon`

즉 이 레포는 세션 안 skill만 제공하는 저장소가 아니라, 바깥에서 Claude를 감싸는 운영용 CLI를 상당히 넓게 제공한다.

## 모델/에이전트 정책

### 기본 모델 계층

`src/config/models.ts` 기준 기본값:

- LOW = `claude-haiku-4-5`
- MEDIUM = `claude-sonnet-4-6`
- HIGH = `claude-opus-4-6`

추가로:

- external provider default:
  - Codex = `gpt-5.3-codex`
  - Gemini = `gemini-3.1-pro-preview`

즉 이 레포는 "작업을 어느 agent에 줄지"뿐 아니라 "어떤 모델 tier를 어떤 lane에 붙일지"를 명시적으로 제품화한다.

### 에이전트 레지스트리

실제 `agents/`에 있는 베이스 prompt는 `19`개다.

예:

- `explore`
- `analyst`
- `planner`
- `architect`
- `debugger`
- `executor`
- `verifier`
- `code-reviewer`
- `security-reviewer`
- `test-engineer`
- `designer`
- `writer`
- `document-specialist`
- `critic`

이건 README/marketplace가 말하는 "28 agent variants"보다 작아 보이는데, 이는 tier variant와 alias/derived registry를 포함한 제품 표면과 실제 base prompt 파일 수가 다르기 때문으로 읽힌다.  
즉 raw 파일 수와 사용자-facing agent count는 정확히 같은 개념이 아니다.

## 운영 성숙도 신호

### 1. 테스트 커버리지가 양적으로도 많다

`src/__tests__`와 `src/team/__tests__`를 보면:

- installer
- hooks
- HUD
- job state
- team runtime
- plugin-dir mode
- model routing
- delegation enforcement
- MCP server
- session history

등이 폭넓게 테스트된다.

즉 이 레포는 단순 문서형 skill 저장소가 아니라, 실제 런타임 제품처럼 테스트되는 쪽이다.

### 2. CI가 배포 품질까지 본다

`ci.yml` 기준:

- lint
- type check
- test
- build
- dist size check
- version consistency check
- `npm pack` 후 전역 설치 smoke test

즉 "빌드는 되는데 패키지는 깨진" 상황까지 방지하려고 한다.

### 3. 문서 표면도 충분히 두껍다

`docs/`에는 아래처럼 제품 운영 문서가 분화돼 있다.

- `ARCHITECTURE.md`
- `FEATURES.md`
- `HOOKS.md`
- `REFERENCE.md`
- `MIGRATION.md`
- `LOCAL_PLUGIN_INSTALL.md`
- `SYNC-SYSTEM.md`
- `TOOLS.md`
- `PERFORMANCE-MONITORING.md`
- `DELEGATION-ENFORCER.md`

즉 OMC는 기능만 있는 게 아니라 "어떻게 이해하고 운영할지"를 문서로도 꽤 잘 드러낸다.

### 4. 릴리스/버전 관리도 자동화가 많다

`scripts/release.ts` 기준:

- semver bump
- PR 메타데이터 기반 release note 생성
- changelog/release body 작성
- package/plugin/marketplace 버전 동기화

즉 수동 배포보다는 도구화된 릴리스 경로를 갖고 있다.

## 강점

### 1. Claude Code 사용자 경험을 매우 넓게 덮는다

이 레포 하나로:

- 설치
- setup
- 세션 내 skill
- 팀 orchestration
- 외부 모델 advisor
- HUD
- 훅
- MCP tools
- auto-update

까지 이어진다.

즉 사용자는 여러 조각을 직접 조합하지 않아도 된다.

### 2. plugin-first와 CLI-first를 모두 지원하는 점이 강력하다

일반 사용자에게는 plugin 설치가 쉽고, 파워 유저에게는 `omc` CLI와 tmux runtime이 있다.  
여기에 `--plugin-dir` 개발 모드까지 있어서 사용자층이 넓다.

### 3. Claude-native와 외부 워커를 섞을 수 있다

Claude Code용 하네스인데도:

- Codex
- Gemini
- tmux pane worker
- `/ccg` advisor synthesis

를 지원한다는 건 꽤 큰 차별점이다.

### 4. 프롬프트만이 아니라 운영 문제를 푼다

delegation enforcer, plugin cache sync, marketplace clone sync, hook bridge, provider-specific model normalization 같은 코드를 보면 이 레포는 프롬프트보다 "실전 운영의 귀찮은 문제"를 많이 해결한다.

## 약점과 리스크

### 1. 표면적이 매우 넓다

이 레포는 다음을 한꺼번에 담고 있다.

- plugin metadata
- npm CLI
- installer
- hooks
- HUD
- MCP tools
- agent registry
- skill system
- native teams
- tmux teams
- external provider interop
- auto-update
- docs
- benchmarks

이런 레포는 강력하지만, 한 부분의 복잡성이 다른 부분으로 쉽게 전파된다.

### 2. 사용자가 이해해야 할 런타임 모델이 둘 이상이다

특히 아래 조합은 초보자에게 헷갈릴 수 있다.

- `/team` vs `omc team`
- plugin install vs npm install
- marketplace clone vs plugin cache vs local checkout
- Claude-only flow vs Codex/Gemini advisor flow

즉 "Zero learning curve"라는 슬로건은 진입은 쉽게 만들 수 있어도, 깊게 들어가면 시스템 자체는 꽤 복잡하다.

### 3. 설치가 침습적이다

`omc setup`은 `~/.claude/` 안쪽 여러 파일과 디렉터리를 실제로 손댄다.  
따라서 사용자 환경을 넓게 통제하는 대신, 설정 충돌이나 업데이트 이슈가 생길 여지도 커진다.

### 4. 커밋된 `dist/`는 편리하지만 드리프트 비용이 있다

배포 관점에선 편하지만:

- diff noise
- 리뷰 피로
- source/dist mismatch 가능성

을 만든다.

### 5. 메타데이터 표면 드리프트가 이미 보인다

관찰된 예시:

- `package.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`은 모두 `4.11.4`
- 하지만 루트 `CLAUDE.md`의 버전 마커는 `4.9.1`
- 반면 `docs/CLAUDE.md`는 `4.11.4`

즉 핵심 버전 표면 대부분은 동기화돼 있지만, 모든 표면이 항상 같이 움직이는 것은 아니다.  
이런 저장소일수록 "단일 진실 원본" 관리가 매우 중요하다.

## 누구에게 잘 맞는가

잘 맞는 사용자:

- Claude Code를 장시간 진지하게 쓰는 사용자
- 세션 내부 skill과 외부 CLI 런타임을 둘 다 활용하고 싶은 사용자
- 팀 orchestration, verification, persistence를 중요하게 보는 사용자
- Codex/Gemini를 보조 모델로도 함께 쓰고 싶은 사용자

덜 맞는 사용자:

- 단순한 프롬프트 팩만 원하는 사용자
- `~/.claude/`를 적극적으로 건드리는 도구를 꺼리는 사용자
- 팀/runtime/hook/cache 개념을 최소화하고 싶은 사용자

## 개인적인 총평

`oh-my-claudecode`는 Claude Code용 plugin 저장소라고 부를 수는 있지만, 그 말만으로는 실제 범위를 절반도 설명하지 못한다.

실제로는:

- Claude Code 운영체계
- 설치 관리자
- 런타임 확장기
- 팀 오케스트레이터
- 외부 모델 브리지

를 한 레포에 담은 통합 하네스에 더 가깝다.

`oh-my-codex`보다 더 오래 자란 느낌이 나는 이유도 여기 있다.  
plugin-first 역사, 커밋된 `dist`, 광범위한 installer/hook/update 계층, 그리고 Claude native 기능과 tmux CLI 기능이 공존하는 구조 때문에 "하네스 제품"으로서의 무게가 더 크다.

반대로 가장 큰 약점도 그 무게에서 나온다.  
좋은 날에는 매우 강한 생산성 레이어지만, 나쁜 날에는 너무 많은 설치 표면과 런타임 모델이 한꺼번에 얽힌 복합 시스템이 된다.

그럼에도 현재 공개된 Claude Code 계열 하네스들 가운데서는 제품화, 운영 성숙도, 확장성 모두 높은 편이라고 보는 게 맞다.

## 추천 읽기 순서

처음 파악할 때는 아래 순서가 좋다.

1. `README.md`
2. `docs/GETTING-STARTED.md`
3. `docs/REFERENCE.md`
4. `AGENTS.md`
5. `skills/team/SKILL.md`
6. `skills/ccg/SKILL.md`
7. `src/cli/index.ts`
8. `src/installer/index.ts`
9. `src/team/runtime-cli.ts`
10. `src/team/runtime.ts` 또는 `src/team/runtime-v2.ts`
11. `src/mcp/omc-tools-server.ts`
12. `src/features/delegation-enforcer.ts`
13. `src/features/auto-update.ts`

## 결론

`oh-my-claudecode`는 "Claude Code용 멀티에이전트 플러그인"이라고 부를 수는 있지만, 정확히는 "Claude Code를 중심으로 한 개발 환경 전체를 표준화하고 확장하는 통합 오케스트레이션 프레임워크"라고 보는 편이 더 맞다.

정리하면:

- 플러그인인가? 맞다.
- CLI 제품인가? 맞다.
- 팀 런타임인가? 맞다.
- 외부 모델 브리지인가? 그것도 맞다.
- 설치형 운영 레이어인가? 가장 정확하다.

그래서 이 저장소를 평가할 때는 스킬 개수만 보기보다:

- 배포 표면의 수
- 설치/업데이트 복잡도
- 팀 런타임 분기 구조
- 모델 라우팅과 provider 적응 계층
- 테스트/벤치마크/CI 완성도

를 기준으로 보는 게 훨씬 정확하다.

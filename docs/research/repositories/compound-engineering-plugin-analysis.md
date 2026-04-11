# EveryInc `compound-engineering-plugin` 저장소 상세 분석

분석 대상: `https://github.com/EveryInc/compound-engineering-plugin`  
분석 시점: 2026-04-09  
분석 방식: 원격 저장소를 shallow clone 해서 코드, 문서, 테스트, 릴리스 메타데이터를 직접 읽고 정리

## 한 줄 요약

이 저장소는 단일 플러그인 레포가 아니라, Claude Code용 플러그인을 기준 포맷으로 삼아 여러 AI 코딩 도구용 포맷으로 변환/설치하는 Bun + TypeScript CLI와, 그 위에서 돌아가는 실제 플러그인 콘텐츠(`compound-engineering`, `coding-tutor`)를 함께 담은 "플러그인 마켓플레이스 + 변환 엔진" 레포다.

핵심 철학은 "한 번의 엔지니어링 작업이 다음 작업을 더 쉽게 만들어야 한다"는 것이고, 이를 위해 브레인스토밍, 계획, 실행, 리뷰, 학습 축적을 각각 스킬과 에이전트로 구조화해 둔 것이 가장 큰 특징이다.

## 스냅샷 요약

- 현재 패키지 버전: `@every-env/compound-plugin` `2.63.1`
- 루트 README 기준 지원 대상: Claude Code, Codex, OpenCode, Droid, Pi, Gemini, Copilot, Kiro, Windsurf, OpenClaw, Qwen
- 실제 플러그인 마켓플레이스 구성: `compound-engineering`, `coding-tutor`
- `plugins/compound-engineering` 기준 구성 수:
  - 에이전트 51개
  - 스킬 44개
- 테스트 파일 수: 49개
- 문서 자산:
  - `docs/plans` 36개
  - `docs/solutions` 22개
  - `docs/brainstorms` 18개
- 원격 저장소 refs 규모:
  - heads 193개
  - tags 98개
- `src`, `plugins/compound-engineering`, `tests` 합산 총 라인 수: 60,837

주의:
- 분석은 shallow clone 기준이라 전체 커밋 수/기여자 수는 정확히 계산하지 않았다.
- 대신 원격 heads/tags, 코드/문서 구조, changelog 상단, 테스트와 릴리스 메타데이터를 근거로 성숙도를 판단했다.

## ASCII 다이어그램 1: 저장소의 큰 구조

```text
compound-engineering-plugin
|
+-- src/                           # Bun CLI + parser + converter + writer + sync engine
|   |
|   +-- commands/                 # install, convert, list, plugin-path, sync
|   +-- parsers/                  # Claude plugin / Claude home parser
|   +-- converters/               # Claude -> Codex/OpenCode/... 변환기
|   +-- targets/                  # 각 타깃 포맷 writer
|   +-- sync/                     # ~/.claude -> 타 도구 설정 sync
|   +-- utils/                    # frontmatter, files, model normalization 등
|   `-- release/                  # 버전/설명/메타데이터 동기화
|
+-- plugins/
|   |
|   +-- compound-engineering/     # 핵심 플러그인 콘텐츠
|   |   |
|   |   +-- agents/               # review / research / design / docs / workflow
|   |   +-- skills/               # ce:brainstorm, ce:plan, ce:work, ce:review, ...
|   |   +-- .claude-plugin/       # Claude plugin manifest
|   |   `-- .cursor-plugin/       # Cursor plugin manifest
|   |
|   `-- coding-tutor/             # 보조 플러그인
|
+-- docs/                         # brainstorms / plans / solutions / specs
+-- tests/                        # converter / writer / cli / parser 테스트
`-- .claude-plugin/               # marketplace manifest
```

## 이 저장소가 실제로 하는 일

### 1. 플러그인 콘텐츠 저장소

`plugins/compound-engineering`은 실제 사용자 가치가 있는 본체다. 여기에는:

- 워크플로우 스킬
  - `ce:brainstorm`
  - `ce:plan`
  - `ce:work`
  - `ce:review`
  - `ce:compound`
- 보조 스킬
  - git 워크플로우
  - 버그 재현
  - 문서 리뷰
  - Slack 조사
  - 온보딩
  - 브라우저/Xcode 테스트
- 서브에이전트
  - correctness / testing / maintainability / security / performance / API / data migration / design / docs / research persona

즉 "플러그인"이라기보다, 에이전트 기반 개발 프로세스를 문서와 프롬프트로 제품화한 저장소에 가깝다.

### 2. 포맷 변환기

루트의 `src/`는 Claude Code 기준 포맷을 읽어서 다른 도구 포맷으로 바꿔 주는 엔진이다.

핵심 흐름:

1. `src/commands/install.ts`
   - 플러그인 이름/경로/브랜치를 입력받음
   - 번들된 로컬 플러그인 또는 GitHub 브랜치를 resolve
2. `src/parsers/claude.ts`
   - `.claude-plugin/plugin.json`
   - `agents/`
   - `commands/`
   - `skills/`
   - `hooks`
   - `.mcp.json`
   를 읽어서 `ClaudePlugin` 객체로 만듦
3. `src/targets/index.ts`
   - 타깃별 converter/writer를 라우팅
4. `src/converters/*`
   - 각 도구의 규칙에 맞게 중간 bundle 생성
5. `src/targets/*`
   - 실제 파일 쓰기, config merge, backup 처리

### 3. 설정 sync 도구

`src/commands/sync.ts`는 `~/.claude/`를 기준으로 Codex/OpenCode/Gemini/Windsurf 등 다른 도구 설정으로 동기화한다.  
즉 이 레포는 "플러그인 배포"만 하는 것이 아니라 "개인 에이전트 개발환경 전체를 표준화하는 허브" 역할도 한다.

## ASCII 다이어그램 2: 설치/변환 파이프라인

```text
user command
   |
   v
compound-plugin install <plugin> --to <target>
   |
   +--> resolve plugin path
   |     |- local path
   |     |- bundled plugin under plugins/
   |     `- git clone from GitHub branch
   |
   +--> loadClaudePlugin()
   |     |- read manifest
   |     |- read agents
   |     |- read commands
   |     |- read skills
   |     |- read hooks
   |     `- read MCP servers
   |
   +--> target converter
   |     |- claude-to-codex
   |     |- claude-to-opencode
   |     |- claude-to-gemini
   |     `- ...
   |
   +--> target writer
   |     |- write prompts / skills / agents
   |     |- merge target config
   |     `- backup existing files when needed
   |
   `--> installed target layout
         |- ~/.codex/...
         |- ~/.config/opencode/...
         |- ~/.pi/agent/...
         `- other target homes
```

## 핵심 아키텍처 분석

### 1. "Claude를 소스 오브 트루스"로 둔 author-once 전략

이 저장소의 가장 중요한 설계 결정은 Claude plugin 포맷을 canonical source로 두는 것이다.

근거 파일:
- `src/parsers/claude.ts`
- `src/commands/install.ts`
- `src/commands/convert.ts`

의미:
- 실제 스킬/에이전트는 Claude 스타일로 한 번 작성
- 다른 도구용 포맷은 변환기로 생성
- 콘텐츠와 런타임 적응 계층을 분리

장점:
- 스킬 본문과 운영 철학을 한곳에서 관리할 수 있음
- 신규 타깃 추가 시 기존 콘텐츠를 재활용 가능
- 릴리스 관리가 단일 콘텐츠 계층에 집중됨

비용:
- Claude 문법/구조를 중심으로 사고해야 해서 다른 하네스의 고유 기능은 1급 시민이 되기 어려움
- 변환기가 복잡해질수록 타깃별 미묘한 의미 차이가 누적될 수 있음

### 2. 콘텐츠 중심 구조: 코드보다 문서가 제품

이 레포에서 핵심 제품은 TypeScript 런타임이 아니라 `SKILL.md`, agent markdown, reference 문서들이다.

예:
- `plugins/compound-engineering/skills/ce-plan/SKILL.md`
- `plugins/compound-engineering/skills/ce-review/SKILL.md`
- `plugins/compound-engineering/skills/ce-work/SKILL.md`
- `plugins/compound-engineering/skills/ce-compound/SKILL.md`

특징:
- 프롬프트가 단순 설명이 아니라 실행 절차서처럼 작성됨
- 서브에이전트 dispatch 조건, 질문 규칙, deepening flow, headless/autofix/report-only mode까지 문서 안에 명시됨
- `references/`, `assets/`, `scripts/`를 활용해 prompt carrying cost를 줄이려는 최적화가 많이 들어가 있음

이건 일반적인 "프롬프트 모음집"보다 훨씬 운영체제적이다.

### 3. converter + writer 분리

`src/converters/*`와 `src/targets/*`가 분리돼 있는 점이 깔끔하다.

- converter의 역할:
  - 의미 변환
  - 이름 정규화
  - frontmatter/본문 재가공
  - MCP/hook 표현식 변환
- writer의 역할:
  - 실제 파일 경로 결정
  - 백업
  - config merge
  - 출력 포맷 보존

예:
- `src/converters/claude-to-codex.ts`
- `src/targets/codex.ts`
- `src/converters/claude-to-opencode.ts`
- `src/targets/opencode.ts`

이 분리는 신규 타깃 추가 시 유지보수성을 크게 높인다.

### 4. install과 sync의 역할 분리

- `install` / `convert`
  - 플러그인 콘텐츠 자체를 특정 타깃 포맷으로 설치
- `sync`
  - 사용자의 `~/.claude` 설정과 skills/MCP를 다른 환경으로 전파

이 둘을 분리한 것은 실용적이다.  
플러그인 배포 문제와 사용자 홈 설정 동기화 문제는 겉보기에 비슷하지만, 실제로는 책임이 다르다.

## `compound-engineering` 플러그인 자체 분석

### 1. 핵심 워크플로우는 사실상 "개발 프로세스 제품화"

README의 주 흐름은 다음과 같다.

```text
Brainstorm -> Plan -> Work -> Review -> Compound -> Repeat
```

이 구조를 보면 이 플러그인은 코드 생성 도구라기보다 "에이전트 시대용 개발 방법론"을 내장한 도구다.

각 단계의 성격:

- `ce:brainstorm`
  - WHAT 정의
  - 요구사항/문제 정의를 문서로 남김
- `ce:plan`
  - HOW 정의
  - 구현 단위, 테스트 시나리오, 리스크, 의존성 정리
- `ce:work`
  - 실제 구현
  - 브랜치/worktree/todo/task 기준 실행
- `ce:review`
  - 다중 persona 리뷰
  - headless/autofix/report-only 모드 지원
- `ce:compound`
  - 해결한 문제를 `docs/solutions`에 저장
  - 다음 작업의 초기 비용을 낮춤

즉 "요구사항 문서 -> 계획 문서 -> 실행 -> 리뷰 -> 학습 문서"라는 순환 고리를 명시적으로 시스템화했다.

### 2. `ce:review`가 특히 강하다

`plugins/compound-engineering/skills/ce-review/SKILL.md`는 이 저장소의 가장 정교한 자산 중 하나다.

강한 점:
- always-on reviewer + conditional reviewer 조합
- severity와 action routing 분리
- `safe_auto`, `gated_auto`, `manual`, `advisory` 같은 후속 처리 클래스 정의
- `interactive`, `autofix`, `report-only`, `headless` 모드 분화
- PR/branch/base ref scope resolution 로직까지 문서에 명시

이 설계는 "리뷰를 대충 여러 agent에게 던진다" 수준이 아니라, 결과의 운영 정책까지 포함한 워크플로우 설계다.

### 3. `ce:plan`과 `ce:brainstorm`는 문서 품질 관리가 핵심

`ce:brainstorm`와 `ce:plan`은 단순 계획 생성기가 아니라, "좋은 문서가 좋은 실행을 만든다"는 철학을 강하게 반영한다.

특징:
- repo-relative path 강제
- 질문 도구 우선 사용 규칙
- origin document 계승
- blocking question 분류
- plan depth 분류
- local research + optional external research
- test scenario completeness 요구
- deepening mode 제공

이건 prompt engineering이라기보다 문서 주도 개발에 가깝다.

### 4. `ce:compound`는 학습 축적 장치다

`ce:compound`는 해결한 문제를 `docs/solutions/`에 저장하고 중복 문서/유사 문서까지 감지한다.

이 기능의 의미:
- 개인 메모를 넘어 팀 지식 저장소를 유지
- 관련 문서와의 overlap 검사
- schema 기반 frontmatter
- session history / auto memory / 기존 docs 검색을 통한 지식 연결

"작업을 끝내는 것"보다 "다음 유사 작업의 비용을 줄이는 것"을 목표에 포함시킨 점이 이 레포 이름과 철학에 잘 맞는다.

## 변환 엔진 분석

### 1. Codex 변환은 단순 복사가 아니라 호출 모델 재설계

`src/converters/claude-to-codex.ts`를 보면:

- command를 prompt + generated skill 조합으로 변환
- canonical workflow skill(`ce:` prefix)은 별도 workflow prompt를 생성
- deprecated alias(`workflows:`)는 제외하거나 canonical로 매핑
- slash/skill invocation을 Codex에 맞게 재작성

즉 Codex 지원은 "파일 확장자만 바꾸는 수준"이 아니라, Codex의 prompt/skill 실행 모델에 맞게 호출 체계를 다시 짜는 작업이다.

### 2. OpenCode 변환은 hook/MCP 적응이 깊다

`src/converters/claude-to-opencode.ts`는:

- allowed tools -> permission block 매핑
- Claude hook event -> OpenCode plugin event 매핑
- subagent model omission 로직
- model provider normalization
- MCP local/remote server 변환

를 처리한다.

특히 `PreToolUse`를 try/catch로 감싸는 부분은 특정 플랫폼 버그나 병렬 호출 실패 경험이 실제 설계에 반영된 흔적이다.

### 3. writer 계층은 사용자 설정 보존에 신경 쓴다

예:
- `src/targets/opencode.ts`
  - 기존 `opencode.json` merge
  - malformed JSON이어도 사용자 데이터 파괴를 피하려는 fallback
- `src/targets/codex.ts`
  - managed block 방식으로 `config.toml` 병합
  - legacy marker 제거
  - 기존 파일 backup

이건 "설치 스크립트가 사용자 환경을 망가뜨리면 안 된다"는 관점이 강하다.

## 운영/릴리스/문서화 방식 분석

### 1. 문서가 단순 결과물이 아니라 운영 로그다

`docs/brainstorms`, `docs/plans`, `docs/solutions`가 실제 워크플로우 산출물로 사용된다.

의미:
- brainstorming 결과가 requirements가 됨
- plan은 living document가 됨
- solution docs는 팀 학습 자산이 됨

일반 레포라면 `docs/`가 부수적일 수 있지만, 여기서는 거의 실행 상태 저장소 역할을 한다.

### 2. release metadata sync가 별도 계층으로 존재

`src/release/metadata.ts`는:
- plugin/version/description 동기화
- marketplace manifest 정합성 유지
- compound-engineering과 coding-tutor 양쪽 관리

를 맡는다.

즉 릴리스 시 "버전 번호 올리기"만 있는 것이 아니라, 다양한 manifest의 설명과 버전 드리프트를 제어한다.

### 3. AGENTS 규약이 매우 강함

`plugins/compound-engineering/AGENTS.md`는 사실상 contributor operating manual이다.

눈에 띄는 규칙:
- 일반 PR에서 버전 bump 금지
- README count 정확도 요구
- skill frontmatter 형식 엄격 관리
- reference inclusion 규칙
- cross-platform 질문/태스크 추상화 규칙
- shell 남용 금지
- pass-paths-not-content 원칙

즉 이 팀은 "에이전트가 수정 가능한 문서 저장소"를 운영하기 위한 메타 규칙까지 명시하고 있다.

## 테스트 전략 분석

테스트 파일명과 내용을 보면, 테스트 초점은 대략 다음에 있다.

- parser correctness
- converter correctness
- target writer correctness
- CLI command behavior
- config merge / path sanitization / codex writer / sync 동작

대표 파일:
- `tests/cli.test.ts`
- `tests/converter.test.ts`
- `tests/codex-writer.test.ts`
- `tests/sync-droid.test.ts`
- `tests/sync-openclaw.test.ts`

해석:
- 강점: 포맷 변환과 파일 출력 안정성은 비교적 촘촘히 검증
- 한계: 실제 각 하네스(Codex/OpenCode/Gemini 등) 안에서 end-to-end로 돌려 보는 라이브 통합 테스트는 코드상으로는 상대적으로 덜 보임

이는 자연스러운 trade-off다. 지원 대상이 너무 많아서, 완전한 실환경 E2E는 유지비가 크다.

## 이 저장소의 강점

### 1. 프롬프트/스킬을 "제품"으로 다룸

대충 쌓인 prompt collection이 아니라:
- 구조
- 정책
- 리뷰
- 버전 관리
- 테스트
- 릴리스
를 모두 갖췄다.

### 2. cross-platform 전략이 실용적

완벽한 공통 추상화보다 "Claude를 canonical로 두고 타깃별 보정"을 택했다.  
이 방식은 이론적으로 우아하진 않아도, 실제 운영 속도는 빠르다.

### 3. 운영 경험이 코드와 문서에 축적돼 있다

CHANGELOG 상단만 봐도:
- token cost 절감
- conditional visual aids
- headless mode
- config merge 보존
- Windows path compatibility
- stale cache / branch install / worktree flow

같이 현업에서 실제로 부딪힌 문제가 빠르게 제도화되고 있다.

### 4. 플러그인 자체가 자기개선 구조를 가짐

`ce:compound`, `docs/solutions`, `document-review`, `review persona`, `agent-native` 규칙은 모두 "에이전트 개발 경험을 다시 에이전트 시스템에 넣는 루프"를 만든다.

## 약점과 리스크

### 1. 시스템의 본질이 markdown 문서라 정적 검증 한계가 있음

스킬 본문이 길고 복잡해서:
- 의미적 충돌
- 절차 중복
- 오래된 지침
- 타깃별 변환 후 의미 왜곡
이 생기기 쉽다.

테스트가 이를 일부 막아 주지만, 문서 의미 전체를 완전히 검증하긴 어렵다.

### 2. 지원 타깃이 많아질수록 의미 드리프트 위험이 커짐

지원 대상이 10개 이상이라:
- prompt model
- hooks
- MCP config
- skill invocation 방식
- path/namespace 제약
이 모두 달라진다.

지금 구조는 이를 꽤 잘 다루고 있지만, 장기적으로 converter 복잡도가 계속 올라갈 가능성이 높다.

### 3. `compound-engineering` 자체의 carrying cost도 커지고 있음

에이전트 51개, 스킬 44개는 이미 작은 시스템이 아니다.  
이 레포 철학이 "carrying cost를 줄이자"인데, 플러그인 자체가 큰 운영 비용을 갖게 될 위험도 동시에 존재한다.

실제로 changelog에 token cost 절감, late-sequence extraction, conditional references 같은 항목이 반복해서 나오는 이유도 여기 있다.

### 4. 캐시 브랜치 체크아웃 전략은 실용적이지만 공격적임

`src/commands/plugin-path.ts`는 캐시 디렉터리에서는 `git reset --hard origin/<branch>`를 사용한다.

평가:
- 장점: deterministic cache 갱신이 단순하고 안정적
- 주의점: 캐시 디렉터리라는 전제 하에서는 괜찮지만, 사용자가 이 경로를 임의로 수정하는 워크플로우라면 로컬 변경이 사라진다

## 확장성 관점에서 본 설계

신규 타깃 추가는 비교적 예측 가능하다.

필요한 작업:
- `src/types/<target>.ts`
- `src/converters/claude-to-<target>.ts`
- `src/targets/<target>.ts`
- `src/sync/<target>.ts`
- `src/targets/index.ts`
- `src/sync/registry.ts`
- 테스트 추가

즉 확장 지점이 코드 구조상 명확하다.

반대로 신규 핵심 스킬 추가는 문서/정책/README/table/count/test까지 손대야 해서 생각보다 더 엄격하다.  
이건 불편하지만, 품질 통제를 위해 의도된 불편으로 보인다.

## 실무적으로 본 결론

이 레포는 "AI 코딩 도구용 프롬프트 모음" 수준을 넘어서 있다.  
더 정확하게는:

- 개발 방법론을 스킬로 구조화한 콘텐츠 저장소
- 그 콘텐츠를 여러 하네스로 배포하는 변환/설치 엔진
- 생성된 산출물을 다시 지식화해 다음 작업에 반영하는 학습 시스템

의 세 층이 합쳐진 레포다.

가장 인상적인 점은 `compound-engineering` 자체가 코드 생성보다 "요구사항 정리 -> 계획 -> 실행 -> 리뷰 -> 학습 축적"에 더 큰 비중을 둔다는 점이다.  
즉 생산성 향상을 "더 빨리 코드를 쓰는 것"이 아니라 "잘못된 작업, 빠진 요구사항, 반복되는 조사 비용을 줄이는 것"으로 정의하고 있다.

## 추천 관찰 포인트

이 레포를 더 깊게 파고들 때 우선순위는 아래 순서가 좋다.

1. `plugins/compound-engineering/skills/ce-review/SKILL.md`
   - 운영 정책까지 포함한 리뷰 시스템의 핵심
2. `plugins/compound-engineering/skills/ce-plan/SKILL.md`
   - 문서 주도 개발 철학이 가장 강하게 드러남
3. `src/parsers/claude.ts`
   - canonical source loader
4. `src/converters/claude-to-codex.ts`
   - Codex용 호출 모델 재구성의 핵심
5. `src/converters/claude-to-opencode.ts`
   - hook/MCP/tool permission 변환의 핵심
6. `src/targets/codex.ts`, `src/targets/opencode.ts`
   - 사용자 환경을 보존하는 writer 전략
7. `src/commands/install.ts`, `src/commands/plugin-path.ts`, `src/commands/sync.ts`
   - 실제 배포/개발/branch testing UX의 핵심

## 분석 기준 파일

직접 읽고 근거로 사용한 대표 파일:

- `README.md`
- `package.json`
- `.claude-plugin/marketplace.json`
- `plugins/compound-engineering/README.md`
- `plugins/compound-engineering/AGENTS.md`
- `plugins/compound-engineering/.claude-plugin/plugin.json`
- `plugins/compound-engineering/.cursor-plugin/plugin.json`
- `plugins/compound-engineering/skills/ce-brainstorm/SKILL.md`
- `plugins/compound-engineering/skills/ce-plan/SKILL.md`
- `plugins/compound-engineering/skills/ce-work/SKILL.md`
- `plugins/compound-engineering/skills/ce-review/SKILL.md`
- `plugins/compound-engineering/skills/ce-compound/SKILL.md`
- `src/index.ts`
- `src/commands/install.ts`
- `src/commands/convert.ts`
- `src/commands/plugin-path.ts`
- `src/commands/list.ts`
- `src/commands/sync.ts`
- `src/parsers/claude.ts`
- `src/targets/index.ts`
- `src/targets/codex.ts`
- `src/targets/opencode.ts`
- `src/converters/claude-to-codex.ts`
- `src/converters/claude-to-opencode.ts`
- `src/sync/registry.ts`
- `src/sync/codex.ts`
- `src/release/metadata.ts`
- `tests/cli.test.ts`
- `tests/converter.test.ts`
- `CHANGELOG.md`


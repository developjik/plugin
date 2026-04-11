# Harness Design Kit

[English](./README.md) | 한국어

Harness Design Kit은 Anthropic의 2026년 3월 24일 글 [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)의 핵심 워크플로우를 Codex와 Claude Code용 로컬 플러그인으로 옮긴 것입니다.

이 플러그인은 워크플로우 계층용 경량 로컬 런타임을 포함합니다.

- planner, generator, evaluator 역할 분리
- 구현 전에 sprint contract 합의
- build 후 final-pass QA를 위한 `continuous` 프로필
- 명시적 점수 기준을 가진 프런트엔드 generator-evaluator 반복
- threshold를 실제로 검증하는 machine-readable evaluation 점수 기록
- priority weight를 실제로 검사하는 프런트엔드 weighted evaluation 요약
- 긴 작업을 위한 파일 기반 handoff
- compaction과 context reset의 명시적 선택
- `always`, `final-pass`, `edge-only`, `off` 같은 evaluator 정책 모드
- phase 전환, 이벤트 로그, handoff 생성, auto-reset 승격
- reset으로 올리기 전에 continuous 세션용 compaction 체크포인트 생성
- native OpenAI 또는 Anthropic provider, 혹은 외부 runner 명령으로 planner, generator, evaluator, compactor 단계를 실행하는 오케스트레이터
- reset으로 올리기 전에 전용 compactor actor가 `compact-state.md`를 다시 쓰고 같은 세션에서 compact resume를 수행하는 경로
- refine, pivot, accept를 자동으로 기록하는 프런트엔드 candidate 추적
- evaluator 프롬프트에 calibration anchor를 자동으로 주입하는 경로
- 캐시된 로컬 Playwright 런타임을 사용해 browser audit 결과, 선택적 flow 스크립트, command check를 남기는 live QA 헬퍼

반대로 이 플러그인이 제공하지 않는 것도 분명히 합니다. 원격 resume 서비스, sandbox pool, credential vault 같은 hosted platform 기능은 없습니다.

## 포함된 구성요소

- `skills/harness-orchestrator/`
  - 장시간 앱 개발용 메인 워크플로우
- `skills/frontend-design-loop/`
  - 디자인 중심 generator-evaluator 루프
- `skills/evaluator-calibration/`
  - 평가자의 엄격도와 일관성을 보정하는 스킬
- `skills/context-reset-handoff/`
  - 긴 세션이 흔들릴 때 쓰는 구조화된 reset 스킬
- `agents/`
  - planner, generator, compactor, design-evaluator, qa-evaluator 프롬프트
- `scripts/harness_state.py`
  - 로컬 세션 상태 엔진, 검증기, handoff 작성기
- `scripts/harness_run.py`
  - phase 전환과 auto-reset 체크를 담당하는 런타임 헬퍼
- `scripts/harness_orchestrator.py`
  - native 또는 외부 runner를 통해 planner, generator, compactor, evaluator 단계를 실행하는 오케스트레이터
- `scripts/harness_runner.py`
  - OpenAI Responses, Anthropic Messages, 외부 runner 브리지
- `scripts/live_eval.py`
  - 대상 URL을 검사하고 가능하면 Playwright 스크린샷까지 남기는 live QA 헬퍼
- `schema/`
  - 세션과 artifact 계약 스키마
- `templates/`
  - 새 세션용 구조화된 템플릿
- `fixtures/`
  - evaluator calibration 예시
- `hooks/`
  - 이벤트 기록과 reset 체크를 수행하는 훅

## 로컬 상태 구조

워크스페이스 루트 아래에 다음 구조를 사용합니다.

```text
.harness-design-kit/
├── current.json
└── sessions/
    └── <session-id>/
        ├── state.json
        ├── events.jsonl
        ├── product-spec.md
        ├── design-brief.md
        ├── sprint-contract.md
        ├── evaluation.md
        ├── progress.md
        ├── compact-state.md
        └── handoff.md
```

## 언제 쓰는가

다음 상황에 맞습니다.

- 짧은 아이디어를 실제 제품 명세와 여러 단계의 빌드 흐름으로 키워야 할 때
- 특히 프런트엔드처럼 주관적 품질이 중요할 때
- 단일 패스 생성이 약하거나 일관되지 않을 때
- 긴 작업에서 명시적인 handoff가 필요할 때

작고 결정적이며 직접 검증이 쉬운 작업에는 더 단순한 워크플로우가 낫습니다.

## 빠른 시작

레포 밖에서 사용할 때는 `PLUGIN_ROOT`를 설치된 플러그인 디렉터리로 설정하세요. 이 레포 안에서는 아래 예시가 기본적으로 `./harness-design-kit`를 사용합니다.

1. 세션 초기화:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" init "Build a browser-based DAW" app
   ```

2. 현재 phase와 다음 actor 확인:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_run.py" status
   ```

   혹은 환경과 세션 상태를 한 번에 점검:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" doctor
   ```

3. 메인 워크플로우 시작:

   ```text
   Use Harness Design Kit. Start harness-orchestrator for this app idea.
   ```

4. 현재 gate를 통과했으면 phase 전진:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_run.py" advance
   ```

   `final-pass` 모드에서는 `build`에서 빠져나오기 전에 evaluator gate를 요청해야 합니다.

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" request-final-pass "ready for final QA"
   ```

5. 앱 contract 초안이 준비되면 evaluator review용으로 제안:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" propose-contract generator
   ```

6. 프런트엔드 전용 작업:

   ```text
   Use frontend-design-loop for this landing page.
   ```

7. 작업이 흔들리기 시작하면:

   ```text
   Use context-reset-handoff and prepare a clean resume artifact.
   ```

8. 혹은 직접 reset artifact 생성:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" prepare-reset "repeated evaluator failures"
   ```

   같은 세션을 유지한 채 compaction 체크포인트만 남기려면:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" prepare-compaction "conversation drifted but should stay in the same session"
   ```

9. 현재 앱 URL에 대해 live QA 실행:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/live_eval.py" run --url http://localhost:3000
   ```

   재사용 가능한 브라우저 flow를 QA에 포함하려면:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" set-qa-flow "${PLUGIN_ROOT:-./harness-design-kit}/templates/qa-flow.json"
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/live_eval.py" run --url http://localhost:3000 --flow "${PLUGIN_ROOT:-./harness-design-kit}/templates/qa-flow.json"
   ```

10. paused handoff를 새 child session으로 재개:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" resume-from-handoff "fresh context resume"
   ```

11. native provider를 설정하고 오케스트레이터 실행:

   ```bash
   export HARNESS_DESIGN_KIT_PROVIDER=openai
   export OPENAI_API_KEY=...
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_orchestrator.py" run-loop --max-steps 8
   ```

   Anthropic을 쓸 수도 있습니다.

   ```bash
   export HARNESS_DESIGN_KIT_PROVIDER=anthropic
   export ANTHROPIC_API_KEY=...
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_orchestrator.py" run-loop --max-steps 8
   ```

12. 또는 외부 runner 경로를 강제로 사용:

   ```bash
   export HARNESS_DESIGN_KIT_PROVIDER=external
   export HARNESS_DESIGN_KIT_AGENT_RUNNER='python3 /absolute/path/to/runner.py'
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_orchestrator.py" run-loop --max-steps 8
   ```

## Native Runner 설정

- `HARNESS_DESIGN_KIT_PROVIDER`
  - `openai`, `anthropic`, `external`
- `HARNESS_DESIGN_KIT_MODEL`
  - 모든 actor에 대한 공통 fallback 모델
- `HARNESS_DESIGN_KIT_MODEL_PLANNER`
  - planner 전용 override
- `HARNESS_DESIGN_KIT_MODEL_GENERATOR`
  - generator 전용 override
- `HARNESS_DESIGN_KIT_MODEL_EVALUATOR`
  - evaluator 전용 override
- `HARNESS_DESIGN_KIT_COMPACTION_MODEL`
  - compactor 전용 override, 없으면 evaluator 모델 사용
- `HARNESS_DESIGN_KIT_OPENAI_BASE_URL`
  - OpenAI 호환 gateway를 쓸 때 선택적 base URL
- `HARNESS_DESIGN_KIT_AGENT_RUNNER`
  - `HARNESS_DESIGN_KIT_PROVIDER=external`일 때만 필요

## 설치

- [Codex 로컬 플러그인 설치 가이드](../docs/guides/install/codex-local-plugin-install.ko.md)
- [Claude Code 로컬 플러그인 설치 가이드](../docs/guides/install/claude-code-local-plugin-install.ko.md)

설치 후 사용할 수 있는 진입점:

- `/harness-design-kit:help`
- `harness-orchestrator`
- `frontend-design-loop`
- `evaluator-calibration`
- `context-reset-handoff`

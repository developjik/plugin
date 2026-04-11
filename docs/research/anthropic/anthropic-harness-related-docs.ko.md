# Anthropic/Claude 하네스 관련 문서 정리

- 작성일: 2026-04-09
- 범위: Anthropic 공식 Engineering 글과 Claude 공식 문서 중 `harness`, `agent scaffold`, `long-running agent`, `multi-agent architecture`, `context engineering`, `tool design`, `agent eval`과 직접 연결되는 문서
- 제외: 웨비나, 홍보성 제품 소개, 하네스와 직접 관련이 약한 일반 공지

## 한눈에 보는 결론

Anthropic의 최근 흐름은 단순히 "좋은 모델"을 만드는 데 있지 않다. 점점 더 긴 작업을 안정적으로 수행하도록 하기 위해 다음 축을 함께 설계하고 있다.

1. 하네스 구조 자체
2. 컨텍스트 압축과 외부 메모리
3. 도구 인터페이스
4. 평가자와 QA 루프
5. 멀티에이전트 분업
6. 하네스가 바뀌어도 유지되는 안정적 인터페이스

가장 중요한 메시지는 이것이다.

- 하네스는 모델의 한계를 가정한 설계물이다.
- 모델이 좋아지면 그 가정은 빠르게 낡는다.
- 그래서 고정된 하네스를 믿기보다, 바뀌는 하네스 위에 오래 버티는 인터페이스를 설계해야 한다.

## ASCII 다이어그램 1: 전체 진화 흐름

```text
2024
  |
  +--> Building effective agents
        - 기본 패턴 정리
        - workflow vs agent
        - orchestrator-workers
        - evaluator-optimizer
  |
2025
  |
  +--> Claude Code best practices
  |     - verify first
  |     - explore -> plan -> code
  |     - multi session / subagents
  |
  +--> Multi-agent research system
  |     - orchestrator-worker production 사례
  |     - parallel search + memory + citation
  |
  +--> Writing effective tools
  |     - agent-friendly tool contracts
  |
  +--> Effective context engineering
  |     - compaction
  |     - note-taking / memory
  |     - sub-agent architectures
  |
  +--> Effective harnesses for long-running agents
        - initializer + coding agent
        - artifacts + git + end-to-end testing
  |
2026
  |
  +--> Demystifying evals for AI agents
  |     - agent harness vs evaluation harness 구분
  |
  +--> Harness design for long-running application development
  |     - planner + generator + evaluator
  |     - frontend design + full-stack coding
  |
  +--> Scaling Managed Agents
        - harness assumptions go stale
        - brain / hands / session decoupling
        - stable interfaces over changing harnesses
```

## 포함한 문서 목록

### 직접 관련 문서

1. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)  
   2024-12-19
2. [Claude Code: Best practices for agentic coding](https://code.claude.com/docs/en/best-practices)  
   원 엔트리: Anthropic Engineering 2025-04-18, 현재는 Claude Code Docs로 리다이렉트
3. [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)  
   2025-06-13
4. [Writing effective tools for AI agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents)  
   2025-09-11
5. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)  
   2025-09-29
6. [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)  
   2025-11-26
7. [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)  
   2026-01-09
8. [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)  
   2026-03-24
9. [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents)  
   2026-03-25

## ASCII 다이어그램 2: 문서 간 관계도

```text
Building effective agents
    |
    +--> Multi-agent research system
    |       |
    |       +--> Effective context engineering
    |
    +--> Writing effective tools
    |       |
    |       +--> Effective context engineering
    |
    +--> Claude Code best practices
    |       |
    |       +--> Effective harnesses for long-running agents
    |       |       |
    |       |       +--> Harness design for long-running application development
    |       |               |
    |       |               +--> Scaling Managed Agents
    |       |
    |       +--> Demystifying evals for AI agents
    |
    +--> Effective context engineering
            |
            +--> Managed Agents
```

## 1. Building effective agents

- URL: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- 날짜: 2024-12-19
- 역할: Anthropic의 하네스 사고방식을 가장 먼저 체계화한 출발점

### 핵심 주장

- 복잡한 프레임워크보다 단순하고 조합 가능한 패턴이 더 잘 작동한다.
- `workflow`와 `agent`를 구분해야 한다.
- 기본 빌딩 블록은 `retrieval + tools + memory`가 붙은 `augmented LLM`이다.
- 생산 환경에서 자주 쓰는 패턴으로 prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer를 제시한다.

### 하네스 관점에서의 의미

이 글은 아직 특정 하네스 구현을 말하진 않지만, 뒤 글들에서 계속 반복되는 구조를 거의 다 예고한다.

- research 시스템의 orchestrator-worker
- frontend/design 반복의 evaluator-optimizer
- long-running coding의 agent loop
- context engineering과 tool design의 중요성

### ASCII 다이어그램

```text
                 +-------------------+
                 |   Augmented LLM   |
                 | tools / memory /  |
                 | retrieval         |
                 +---------+---------+
                           |
         +-----------------+------------------+
         |                 |                  |
         v                 v                  v
   prompt chaining      routing        parallelization
                                              |
                                              v
                                   orchestrator-workers
                                              |
                                              v
                                   evaluator-optimizer
                                              |
                                              v
                                           agents
```

### 왜 중요한가

이 글이 이후 Anthropic 문서들의 공통 문법이 된다. 후속 글들은 대부분 이 글의 패턴을 실제 제품과 운영 문제에 맞게 구체화한 것이다.

## 2. Claude Code: Best practices for agentic coding

- URL: [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)
- 날짜: 2025-04-18 엔지니어링 게시, 현재는 Claude Code Docs로 제공
- 역할: 연구 글의 아이디어를 현장 사용법으로 내린 운영 가이드

### 핵심 주장

- 가장 높은 레버리지는 `Claude가 자기 작업을 검증할 수 있게 만드는 것`이다.
- 권장 흐름은 `explore -> plan -> implement -> commit`이다.
- 긴 세션에서는 컨텍스트가 빠르게 오염되므로 `/clear`, resume, compaction, subagent 활용이 중요하다.
- 병렬 세션, writer/reviewer 패턴, fan-out 작업이 실무에서 효과적이다.

### 하네스 관점에서의 의미

이 문서는 연구 하네스를 "사람이 직접 운용하는 세미-자동 하네스"로 바꿔 읽게 해준다.

- 사람이 plan mode로 planner 역할을 보조
- 별도 세션이 reviewer/evaluator 역할 수행
- screenshots/tests가 success criteria 역할 수행
- multi-session이 lightweight multi-agent 역할 수행

### ASCII 다이어그램

```text
User
  |
  v
Explore ----> Plan ----> Implement ----> Verify ----> Commit
  |             |             |              |
  |             |             |              +--> tests / screenshots / outputs
  |             |             |
  |             |             +--> subagents / extra sessions
  |             |
  |             +--> explicit plan / checkpoints
  |
  +--> read files / inspect codebase first
```

### 왜 중요한가

Anthropic이 이론적으로 말한 하네스 원칙이 실제 코딩 도구 UX에서 어떻게 쓰이는지 보여준다. 뒤의 장기 실행 하네스 글과 직접 이어진다.

## 3. How we built our multi-agent research system

- URL: [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- 날짜: 2025-06-13
- 역할: orchestrator-worker가 실제 제품에서 어떻게 작동하는지 보여주는 첫 대형 사례

### 핵심 주장

- research는 단일 에이전트보다 멀티에이전트에 잘 맞는다.
- 리드 에이전트가 전략을 세우고, 서브에이전트들이 병렬로 탐색한다.
- 각 서브에이전트는 자기 컨텍스트 윈도우 안에서 깊게 탐색한 뒤, 압축된 결과만 리드 에이전트에 돌려준다.
- 메모리와 thinking을 활용해 긴 탐색을 유지한다.
- 병렬화는 품질뿐 아니라 속도에도 크게 기여했다.

### ASCII 다이어그램

```text
                +------------------+
                |   User Query     |
                +---------+--------+
                          |
                          v
                +------------------+
                |  Lead Agent      |
                | plan / memory    |
                +----+----+----+---+
                     |    |    |
          -----------+    |    +-----------
          |               |                |
          v               v                v
   +-------------+ +-------------+ +-------------+
   | Subagent A  | | Subagent B  | | Subagent C  |
   | search loop | | search loop | | search loop |
   +------+------+ +------+------+ +------+------+
          |               |                |
          +------- summaries / findings ---+
                          |
                          v
                +------------------+
                |  Lead Synthesis  |
                +---------+--------+
                          |
                          v
                +------------------+
                | Citation Agent   |
                +---------+--------+
                          |
                          v
                      Final Answer
```

### 하네스 관점에서의 의미

이 글은 멀티에이전트가 항상 좋은 것이 아니라는 점도 같이 말한다.

- 병렬화 가치가 큰 문제에 적합
- 서로 강하게 얽힌 코딩 작업에는 아직 덜 적합
- 토큰 비용이 매우 빠르게 증가

즉, "모든 것을 멀티에이전트로"가 아니라 "작업 구조가 병렬화 가능할 때만"이라는 기준을 제시한다.

## 4. Writing effective tools for AI agents — with agents

- URL: [Writing effective tools for AI agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- 날짜: 2025-09-11
- 역할: 하네스의 외곽을 이루는 `tool contract`를 다룬 문서

### 핵심 주장

- 에이전트 성능은 도구 품질에 크게 좌우된다.
- 도구는 많을수록 좋은 것이 아니라, 작업 단위를 잘 추상화해야 한다.
- `list everything`류 도구보다 `search relevant subset`류 도구가 에이전트에 맞다.
- 이름공간(namespacing), 명확한 파라미터명, 적절한 verbosity 제어가 중요하다.
- 평가를 만들고, 그 평가에 맞춰 Claude에게 도구 자체를 개선하게 할 수 있다.

### ASCII 다이어그램

```text
Bad tool design
  agent -> list_all_contacts -> huge output -> context waste -> mistakes

Better tool design
  agent -> search_contacts("jane") -> small relevant output -> next action

Best pattern
  agent -> get_customer_context(customer_name)
        -> relevant summary + IDs when needed
```

### 하네스 관점에서의 의미

좋은 하네스는 좋은 프롬프트만으로 만들어지지 않는다. 에이전트가 사용하는 도구가 context-efficient해야 하며, 그 자체가 하네스의 일부라는 점을 명확히 해준다.

## 5. Effective context engineering for AI agents

- URL: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- 날짜: 2025-09-29
- 역할: 하네스 설계의 중심 문제를 `prompt`에서 `context curation`으로 이동시킨 문서

### 핵심 주장

- prompt engineering보다 더 넓은 개념이 context engineering이다.
- 컨텍스트는 무한 자원이 아니라, attention budget을 소모하는 유한 자원이다.
- 긴 작업을 위해 compaction, structured note-taking, sub-agent architecture가 필요하다.
- 좋은 원칙은 `가장 작은 고신호 토큰 집합`을 유지하는 것이다.

### ASCII 다이어그램

```text
raw universe of information
    |
    +--> system prompt
    +--> tools
    +--> examples
    +--> message history
    +--> files / links / notes
    |
    v
context engineering
    |
    +--> keep high-signal tokens
    +--> discard low-value noise
    +--> retrieve just-in-time
    |
    +--> compaction
    +--> note-taking / memory
    +--> sub-agents
```

### 장기 작업용 하위 패턴

```text
1) Compaction
   long trace -> summarize -> new context

2) Note-taking
   work -> write NOTES.md / memory -> reload later

3) Sub-agents
   lead agent -> focused subagents -> condensed summaries
```

### 하네스 관점에서의 의미

뒤에 나오는 장기 코딩 하네스와 Managed Agents 문서는 사실상 이 글의 응용편이다. 특히 다음 세 가지가 핵심 축이 된다.

- compaction / context reset
- notes / progress artifacts
- sub-agent 분업

## 6. Effective harnesses for long-running agents

- URL: [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- 날짜: 2025-11-26
- 역할: 장기 코딩 하네스를 처음으로 아주 구체적으로 공개한 문서

### 핵심 주장

- compaction만으로는 장시간 코딩 품질 유지에 부족하다.
- 초기 환경을 만드는 `initializer agent`와, 이후 점진적으로 전진하는 `coding agent`를 분리한다.
- 상태 전달은 `init.sh`, `claude-progress.txt`, `feature_list.json`, git commit으로 수행한다.
- 항상 한 번에 한 feature만 진행하게 하고, 세션 끝에는 깨끗한 상태를 남기게 한다.
- end-to-end 브라우저 테스트 도구를 주면 성능이 크게 좋아진다.

### ASCII 다이어그램

```text
            +----------------------+
            | User Prompt          |
            +----------+-----------+
                       |
                       v
            +----------------------+
            | Initializer Agent    |
            | - init.sh            |
            | - claude-progress    |
            | - feature_list.json  |
            | - initial commit     |
            +----------+-----------+
                       |
                       v
            +----------------------+
            | Coding Agent Session |
            | 1 feature at a time  |
            +----------+-----------+
                       |
          +------------+-------------+
          |                          |
          v                          v
   read progress + git        run app + e2e test
          |                          |
          +------------+-------------+
                       |
                       v
            update feature status
            write progress note
            git commit
                       |
                       v
                 next session
```

### 핵심 산출물 구조

```text
repo/
  init.sh
  claude-progress.txt
  feature_list.json
  .git/
```

### 하네스 관점에서의 의미

Anthropic이 "장시간 실행"을 위해 가장 먼저 택한 실전 해법은 메모리 마법이 아니라 `구조화된 산출물`이었다. 이 문서는 후속 글의 기반이 된다.

## 7. Demystifying evals for AI agents

- URL: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- 날짜: 2026-01-09
- 역할: 하네스를 평가하는 별도의 `evaluation harness` 사고를 정리

### 핵심 주장

- agent를 평가하려면 transcript와 최종 outcome을 분리해서 봐야 한다.
- `agent harness`와 `evaluation harness`는 다르다.
- agent harness는 모델이 도구를 써서 행동하게 하는 시스템이다.
- evaluation harness는 그 agent를 여러 태스크에서 실행하고 채점하고 집계하는 인프라다.

### ASCII 다이어그램

```text
Agent Harness
  task -> model + tools + loop -> actions -> final state

Evaluation Harness
  suite of tasks
      |
      v
  run agent harness many times
      |
      v
  graders / assertions / aggregation
      |
      v
  performance signal
```

### 하네스 관점에서의 의미

앞선 문서들이 "에이전트를 어떻게 움직일까"에 집중했다면, 이 문서는 "그 하네스가 실제로 좋아졌는지 어떻게 알까"를 다룬다. 이후의 planner/generator/evaluator 구조를 읽을 때 중요한 전제다.

## 8. Harness design for long-running application development

- URL: [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- 날짜: 2026-03-24
- 역할: 2025년 long-running harness를 한 단계 확장한 문서

### 핵심 주장

- 긴 작업의 두 큰 문제는 `context degradation`과 `self-evaluation leniency`다.
- 프런트엔드 디자인에서는 generator와 evaluator를 분리하고, 디자인 품질을 채점 가능한 기준으로 바꿨다.
- 장기 풀스택 코딩에서는 planner, generator, evaluator의 3에이전트 구조를 사용했다.
- evaluator가 실제 앱을 Playwright로 탐색하면서 기준 미달 스프린트를 fail 처리한다.
- 스프린트 전 generator와 evaluator가 sprint contract를 합의한다.
- 더 강한 모델에서는 예전 하네스 구성 일부가 필요 없어질 수 있다.

### ASCII 다이어그램

```text
Frontend loop

+-------------+      build UI      +-------------+
| Generator   | -----------------> | Live Page   |
+------+------+                    +------+------+ 
       ^                                   |
       | scores / critique                 | inspect / click
       |                                   v
+------+------+
| Evaluator   |
| design rubric|
+-------------+
```

```text
Long-running app harness

   user prompt
       |
       v
 +-------------+
 | Planner     |
 | full spec   |
 +------+------+ 
        |
        v
 +-------------+      sprint contract      +-------------+
 | Generator   | <-----------------------> | Evaluator   |
 | build sprint|                           | QA / score  |
 +------+------+                           +------+------+
        |                                         |
        +---------------- app under test ---------+
```

### 하네스 관점에서의 의미

이 글은 2025년의 `initializer + coding agent` 모델에서 한 단계 더 나간다.

- 초기 환경 세팅 중심에서 계획-생성-평가 분업으로 이동
- 단순 progress artifacts에서 explicit contract와 rubric으로 이동
- 기능 검증뿐 아니라 디자인 품질과 제품 깊이까지 평가 범위를 넓힘

## 9. Scaling Managed Agents: Decoupling the brain from the hands

- URL: [Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents)
- 날짜: 2026-03-25
- 역할: 하네스가 자주 바뀐다는 현실을 전제로, 그 위의 안정 인터페이스를 설계한 글

### 핵심 주장

- 하네스는 모델의 한계에 대한 가정을 담고 있고, 그 가정은 모델이 좋아지면 stale해진다.
- 따라서 구현이 아니라 인터페이스를 안정화해야 한다.
- Managed Agents는 `session`, `harness`, `sandbox`를 분리한다.
- brain과 hands를 decouple하면 보안, 복구, 확장성, latency가 좋아진다.
- harness는 더 이상 컨테이너 안에 있지 않고, sandbox를 하나의 tool처럼 호출한다.

### ASCII 다이어그램

```text
Before: coupled

  +--------------------------------------+
  | container                            |
  |  brain + harness + code execution    |
  |  credentials nearby                  |
  +--------------------------------------+

Problems:
  - crash domain too large
  - credentials close to generated code
  - slow startup
  - hard to swap harness logic
```

```text
After: decoupled

          +----------------------+
          |      Session         |
          | append-only events   |
          +----------+-----------+
                     ^
                     | getSession / emitEvent / wake
                     |
          +----------+-----------+
          |   Brain + Harness    |
          | Claude + orchestration|
          +----+-------------+---+
               |             |
   execute()   |             | tool / MCP calls
               v             v
      +---------------+   +----------------+
      | Sandbox / Hand|   | External Tools |
      +---------------+   +----------------+
```

### 하네스 관점에서의 의미

이 글은 이제 "더 좋은 하네스를 만들자"에서 한 단계 더 나아간다.

- 하네스는 계속 바뀔 것이므로
- 하네스 자체를 제품의 stable abstraction으로 삼으면 안 되고
- session, execution hand, orchestration 사이의 경계를 인터페이스로 고정해야 한다

즉, Anthropic의 사고가 `pattern design`에서 `platform architecture`로 확장된 순간이라고 볼 수 있다.

## 문서별 핵심 차이

```text
Document                                   Main Question
-----------------------------------------  ----------------------------------------
Building effective agents                  어떤 기본 패턴들이 유효한가?
Claude Code best practices                 사람이 실제로 어떻게 운용해야 하는가?
Multi-agent research system                멀티에이전트는 어디에서 강한가?
Writing effective tools                    도구 계약을 어떻게 설계해야 하는가?
Effective context engineering              긴 작업의 컨텍스트를 어떻게 관리할까?
Effective harnesses for long-running       컨텍스트 리셋 환경에서 코딩을 어떻게 이어갈까?
Demystifying evals                         하네스 성능을 어떻게 측정할까?
Harness design for long-running apps       계획/생성/평가 루프로 품질을 어떻게 더 끌어올릴까?
Scaling Managed Agents                     자주 바뀌는 하네스 위에 무엇을 안정화할까?
```

## ASCII 다이어그램 3: Anthropic 하네스 사고의 압축 모델

```text
                   +----------------------+
                   |  User Goal / Task    |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |  Planner / Strategy  |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |  Agent Harness       |
                   |  loop + tools + mem  |
                   +----+------------+----+
                        |            |
                        |            +--> context engineering
                        |                 - compaction
                        |                 - notes / memory
                        |                 - subagents
                        |
                        +--> tool design
                        |    - agent-friendly APIs
                        |    - token efficiency
                        |
                        +--> execution environments
                        |    - sandboxes
                        |    - MCP tools
                        |
                        +--> structured artifacts
                        |    - plans
                        |    - contracts
                        |    - progress logs
                        |    - git history
                        |
                        +--> evaluator / QA loop
                             - tests
                             - browser automation
                             - LLM judge

                              |
                              v
                   +----------------------+
                   |  Evaluation Harness  |
                   |  trials / graders    |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |  Product / Platform  |
                   |  stable interfaces   |
                   +----------------------+
```

## 전체 흐름을 한 문장씩 요약하면

1. `Building effective agents`는 기본 패턴 카탈로그다.
2. `Claude Code best practices`는 그 패턴을 실제 코딩 습관으로 번역한다.
3. `Multi-agent research system`은 멀티에이전트가 병렬 탐색에서 강하다는 것을 보인다.
4. `Writing effective tools`는 도구가 곧 하네스라는 점을 강조한다.
5. `Effective context engineering`은 긴 작업의 병목이 프롬프트가 아니라 컨텍스트라고 정리한다.
6. `Effective harnesses for long-running agents`는 장기 코딩을 artifacts 중심으로 안정화한다.
7. `Demystifying evals`는 하네스를 평가하는 별도 인프라가 필요하다고 말한다.
8. `Harness design for long-running application development`는 planner/generator/evaluator 루프로 품질을 더 끌어올린다.
9. `Scaling Managed Agents`는 하네스가 계속 바뀌므로 stable interface를 먼저 설계해야 한다고 결론낸다.

## 실무적으로 읽는 순서 추천

### 빠르게 전체 그림을 잡고 싶을 때

1. Building effective agents
2. Effective context engineering
3. Effective harnesses for long-running agents
4. Harness design for long-running application development
5. Scaling Managed Agents

### 실제 제품/플랫폼을 설계하려 할 때

1. Building effective agents
2. Writing effective tools
3. Demystifying evals
4. Effective context engineering
5. Multi-agent research system
6. Effective harnesses for long-running agents
7. Harness design for long-running application development
8. Scaling Managed Agents

### Claude Code 운영 관점에서 읽을 때

1. Claude Code best practices
2. Effective context engineering
3. Effective harnesses for long-running agents
4. Harness design for long-running application development

## 최종 정리

Anthropic의 하네스 관련 문서들을 시간순으로 보면 사고가 분명히 진화한다.

1. 처음에는 `좋은 에이전트 패턴`을 정리한다.
2. 다음에는 `도구`, `컨텍스트`, `병렬 분업`, `검증`을 세분화한다.
3. 그 다음에는 장기 코딩 하네스를 artifacts와 evaluator 중심으로 구체화한다.
4. 마지막에는 "하네스는 계속 바뀐다"는 현실을 받아들이고, stable interface를 앞세운 플랫폼 설계로 이동한다.

즉, Anthropic이 말하는 하네스는 단순한 프롬프트 모음이 아니다. 그것은 다음을 모두 포함하는 운영 시스템이다.

- 역할 분리
- 도구 계약
- 컨텍스트 큐레이션
- 상태 전달 산출물
- 검증 루프
- 평가 인프라
- 그리고 시간이 지나도 살아남는 인터페이스

## 출처

- [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Writing effective tools for AI agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents)

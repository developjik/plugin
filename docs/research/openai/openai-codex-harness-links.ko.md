# OpenAI/Codex 하네스 관점 링크 조사

- 작성일: 2026-04-09
- 범위: OpenAI 공식 도메인(`openai.com`, `developers.openai.com`, `platform.openai.com`) 기준
- 기준: `Codex`, `agent harness`, `tools`, `evals`, `background execution`, `computer environment`, `sandbox`, `AGENTS.md`, `App Server`, `multi-agent orchestration`와 직접 연결되는 문서

## 한눈에 보는 결론

OpenAI/Codex의 최근 하네스 관점은 크게 네 축으로 정리된다.

1. `Codex core harness`
2. `stable integration surface`
3. `hosted runtime and tools`
4. `operational scaffolding`

Anthropic이 planner/generator/evaluator 같은 역할 분리를 강조한다면, OpenAI는 최근 공식 글에서 다음을 더 강하게 밀고 있다.

- agent loop의 저수준 구조
- App Server 같은 안정적 통신/세션 계층
- shell + container + skills + compaction이 붙은 실행 환경
- AGENTS.md, background tasks, evals, guardrails 같은 운영 장치

## 가장 직접적인 핵심 글

### 1. Harness engineering: leveraging Codex in an agent-first world

- 링크: [https://openai.com/index/harness-engineering/](https://openai.com/index/harness-engineering/)
- 날짜: 2026-02-11
- 성격: OpenAI/Codex 하네스 관점의 대표 글

핵심 포인트:

- agent-first world에서 제품/팀 운영을 어떻게 다시 설계하는지 설명
- `AGENTS.md는 백과사전이 아니라 목차`라는 운영 철학
- `docs/`를 system of record로 유지
- `Ralph Wiggum loop` 같은 반복 개선 루프
- background Codex tasks로 quality grades와 targeted refactoring PR 생성

### 2. Unrolling the Codex agent loop

- 링크: [https://openai.com/index/unrolling-the-codex-agent-loop/](https://openai.com/index/unrolling-the-codex-agent-loop/)
- 날짜: 2026-01-23
- 성격: Codex 하네스의 가장 저수준 설명

핵심 포인트:

- user input -> model inference -> tool calls -> environment updates -> assistant message의 반복 구조 설명
- context window, compaction, prompt caching 문제를 깊게 다룸
- sandbox, developer messages, environment context, MCP tools의 상호작용 설명

### 3. Unlocking the Codex harness: how we built the App Server

- 링크: [https://openai.com/index/unlocking-the-codex-harness/](https://openai.com/index/unlocking-the-codex-harness/)
- 날짜: 2026-02-04
- 성격: Codex를 다양한 클라이언트에서 재사용하기 위한 안정 계층 설명

핵심 포인트:

- App Server를 JSON-RPC 프로토콜이자 long-lived process로 설계
- thread manager가 thread별 core session을 관리
- CLI, Desktop, Web, IDE, 파트너 통합이 공통 하네스를 공유할 수 있게 함

### 4. From model to agent: Equipping the Responses API with a computer environment

- 링크: [https://openai.com/index/equip-responses-api-computer-environment/](https://openai.com/index/equip-responses-api-computer-environment/)
- 날짜: 2026-03-11
- 성격: Responses API를 agent runtime으로 확장하는 설명

핵심 포인트:

- Responses API가 shell tool, hosted container, skills, compaction을 묶어 오케스트레이션
- 병렬 shell sessions와 bounded output으로 context 효율 관리
- 장시간 작업을 위한 native compaction 지원

### 5. Introducing Codex

- 링크: [https://openai.com/index/introducing-codex/](https://openai.com/index/introducing-codex/)
- 날짜: 2025-05-16
- 업데이트: 2025-06-03
- 성격: Codex의 기본 실행 모델 설명

핵심 포인트:

- 각 task가 repository가 preload된 isolated cloud sandbox에서 실행
- 초기에는 인터넷 접근 비활성, 이후 업데이트에서 인터넷 접근 옵션 제공
- 잘 쪼개진 작업, test/log 기반 검증, AGENTS.md 활용 강조

### 6. How OpenAI uses Codex

- 링크: [https://openai.com/business/guides-and-resources/how-openai-uses-codex/](https://openai.com/business/guides-and-resources/how-openai-uses-codex/)
- 성격: 내부 팀의 실무 운영 습관 정리

핵심 포인트:

- `Ask Mode -> Code Mode`의 2단계 흐름
- 잘 스코프된 작업을 선호
- startup script, env, internet access 조정으로 오류율 감소
- `AGENTS.md`로 지속 컨텍스트 공급
- `Best-of-N`으로 여러 해법을 병렬 탐색

## 직접 연관된 공식 엔지니어링 글

### 7. Inside OpenAI’s in-house data agent

- 링크: [https://openai.com/index/inside-our-in-house-data-agent/](https://openai.com/index/inside-our-in-house-data-agent/)
- 날짜: 2026-01-29

하네스 연결 포인트:

- closed-loop self-correction
- context layering
- memory
- evals API 활용
- internal knowledge + web search + notebooks + reports를 묶는 agent workflow

### 8. How we used Codex to build Sora for Android in 28 days

- 링크: [https://openai.com/index/shipping-sora-for-android-with-codex/](https://openai.com/index/shipping-sora-for-android-with-codex/)
- 날짜: 2025-12-12

하네스 연결 포인트:

- 실제 제품 개발에서 Codex를 어떤 작업 단위에 붙였는지 보여줌
- 설계, 구현, 검토, 반복의 실무 사례로 읽을 수 있음

### 9. Building more with GPT-5.1-Codex-Max

- 링크: [https://openai.com/index/gpt-5-1-codex-max/](https://openai.com/index/gpt-5-1-codex-max/)
- 날짜: 2025-11-19

하네스 연결 포인트:

- long-running tasks
- native compaction
- 코드 리뷰와 multi-hour task suitability

## 플랫폼/문서 쪽 핵심 가이드

### 10. Background mode

- 링크: [https://developers.openai.com/api/docs/guides/background](https://developers.openai.com/api/docs/guides/background)

하네스 연결 포인트:

- 장시간 작업을 비동기로 실행하는 공식 패턴
- Codex, Deep Research류 long-running task에 직접 연결
- polling/webhook 기반 결과 수집

### 11. Evaluate agent workflows

- 링크: [https://developers.openai.com/api/docs/guides/agent-evals](https://developers.openai.com/api/docs/guides/agent-evals)

하네스 연결 포인트:

- agent workflow 단위 평가
- trace grading
- task success와 tool-use quality를 함께 측정

### 12. Safety in building agents

- 링크: [https://developers.openai.com/api/docs/guides/agent-builder-safety](https://developers.openai.com/api/docs/guides/agent-builder-safety)

하네스 연결 포인트:

- prompt injection 대응
- data exfiltration 방지
- approval 경계와 restricted actions
- monitoring과 traces

### 13. Prompt caching

- 링크: [https://developers.openai.com/api/docs/guides/prompt-caching](https://developers.openai.com/api/docs/guides/prompt-caching)

하네스 연결 포인트:

- long-running Codex loop의 비용과 latency 최적화
- exact-prefix caching이 agent loop 비용 구조에 중요

### 14. Models overview

- 링크: [https://developers.openai.com/api/docs/models](https://developers.openai.com/api/docs/models)

### 15. All models

- 링크: [https://developers.openai.com/api/docs/models/all](https://developers.openai.com/api/docs/models/all)

하네스 연결 포인트:

- coding, computer use, subagents, long-running tasks에 적합한 모델 계열의 현재 위치 확인

## Codex/agent용 모델 링크

### 16. GPT-5.3-Codex

- 링크: [https://developers.openai.com/api/docs/models/gpt-5.3-codex](https://developers.openai.com/api/docs/models/gpt-5.3-codex)

### 17. GPT-5.2-Codex

- 링크: [https://developers.openai.com/api/docs/models/gpt-5.2-codex](https://developers.openai.com/api/docs/models/gpt-5.2-codex)

### 18. GPT-5.1-Codex

- 링크: [https://developers.openai.com/api/docs/models/gpt-5.1-codex](https://developers.openai.com/api/docs/models/gpt-5.1-codex)

### 19. GPT-5.1-Codex-Max

- 링크: [https://developers.openai.com/api/docs/models/gpt-5.1-codex-max](https://developers.openai.com/api/docs/models/gpt-5.1-codex-max)

### 20. GPT-5-Codex

- 링크: [https://developers.openai.com/api/docs/models/gpt-5-codex](https://developers.openai.com/api/docs/models/gpt-5-codex)

### 21. computer-use-preview

- 링크: [https://developers.openai.com/api/docs/models/computer-use-preview](https://developers.openai.com/api/docs/models/computer-use-preview)

### 22. GPT-5.4

- 링크: [https://developers.openai.com/api/docs/models/gpt-5.4](https://developers.openai.com/api/docs/models/gpt-5.4)

### 23. GPT-5.4 mini

- 링크: [https://developers.openai.com/api/docs/models/gpt-5.4-mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini)

## 보조 링크

### 24. Codex product page

- 링크: [https://openai.com/codex](https://openai.com/codex)

### 25. Codex use cases

- 링크: [https://developers.openai.com/codex/use-cases](https://developers.openai.com/codex/use-cases)

### 26. A practical guide to building agents

- 링크: [https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)

하네스 연결 포인트:

- OpenAI의 일반 agent orchestration 철학
- Codex 전용 문서는 아니지만 하네스 설계에 직접 도움

## 관점별로 묶으면

### A. Codex core harness

- [Harness engineering](https://openai.com/index/harness-engineering/)
- [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
- [Introducing Codex](https://openai.com/index/introducing-codex/)
- [How OpenAI uses Codex](https://openai.com/business/guides-and-resources/how-openai-uses-codex/)

### B. Stable integration surface

- [Unlocking the Codex harness](https://openai.com/index/unlocking-the-codex-harness/)
- [Background mode](https://developers.openai.com/api/docs/guides/background)

### C. Hosted runtime and tools

- [From model to agent](https://openai.com/index/equip-responses-api-computer-environment/)
- [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [Safety in building agents](https://developers.openai.com/api/docs/guides/agent-builder-safety)

### D. Evaluation and operational scaffolding

- [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals)
- [Inside OpenAI’s in-house data agent](https://openai.com/index/inside-our-in-house-data-agent/)
- [A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)

## 빠르게 읽는 순서 추천

1. [Harness engineering](https://openai.com/index/harness-engineering/)
2. [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
3. [Unlocking the Codex harness](https://openai.com/index/unlocking-the-codex-harness/)
4. [From model to agent](https://openai.com/index/equip-responses-api-computer-environment/)
5. [Background mode](https://developers.openai.com/api/docs/guides/background)
6. [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals)
7. [Safety in building agents](https://developers.openai.com/api/docs/guides/agent-builder-safety)

## OpenAI/Codex 하네스 관점 압축 요약

OpenAI/Codex의 최근 하네스 사고는 다음 흐름으로 읽을 수 있다.

1. Codex는 단순 코드 생성기가 아니라 tool-calling agent loop다.
2. 이 loop는 sandbox, approvals, prompt caching, compaction 같은 운영 계층과 묶여 있다.
3. 여러 클라이언트가 같은 하네스를 쓰려면 App Server 같은 안정된 세션/프로토콜 계층이 필요하다.
4. Responses API는 shell, hosted container, skills, compaction을 묶어 범용 agent runtime으로 확장되고 있다.
5. 실무에서는 AGENTS.md, background tasks, Best-of-N, evals, review loops가 하네스의 운영 장치 역할을 한다.

## 참고

이 문서는 링크 조사 인덱스다. 원하면 다음 단계로 Anthropic 시리즈처럼 아래 형식으로 확장할 수 있다.

- 문서별 1페이지 요약 시리즈
- Anthropic vs OpenAI 하네스 비교 문서
- OpenAI/Codex 전용 ASCII 다이어그램 문서

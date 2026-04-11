# A practical guide to building agents

- 원문: [A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
- 출처: OpenAI
- 문서 유형: Guide/PDF

## 한줄 요약

OpenAI는 agent를 만들 때 orchestration, tools, memory, guardrails, evals를 처음부터 함께 설계해야 한다고 본다.

## 이 글이 답하는 질문

특정 제품이 아니라 일반적인 OpenAI agent 시스템을 만들 때 어떤 설계 축을 먼저 잡아야 하는가?

## 핵심 주장

- agent는 단일 모델 호출이 아니라 상태와 도구를 가진 시스템이다.
- memory와 tools는 별도 추가 기능이 아니라 기본 설계 요소다.
- guardrails는 함수나 별도 agent로도 구현할 수 있다.
- failure thresholds, retries, action limits 같은 운영 규칙이 필요하다.

## ASCII 다이어그램

```text
user goal
   |
   v
planner / orchestrator
   |
   +--> tools
   +--> memory
   +--> guardrails
   +--> evals
   |
   v
task execution loop
```

## 하네스 관점의 의미

Codex 전용 문서는 아니지만, OpenAI가 agent 하네스를 어떤 일반 원리로 보는지 가장 넓게 정리한 문서다. Codex 관련 글을 읽을 때 상위 개념 정리용으로 좋다.

## 실무 포인트

- orchestration과 safety를 분리하지 말 것
- retry 정책과 fail-fast 기준을 함께 설계할 것
- evals를 나중에 붙일 기능으로 미루지 말 것

## 기억할 문장

agent는 모델 위에 덧붙인 기능이 아니라, 도구와 기억과 안전장치가 얹힌 운영 시스템이다.

# Prompt caching

- 원문: [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- 출처: OpenAI API Docs
- 문서 유형: Guide

## 한줄 요약

장시간 agent loop에서는 prompt caching이 단순 비용 절감 기능이 아니라, 하네스 성능 자체를 좌우하는 핵심 최적화다.

## 이 글이 답하는 질문

agent가 긴 컨텍스트를 반복해서 사용할 때 비용과 latency를 어떻게 줄일 것인가?

## 핵심 주장

- prefix가 안정적일수록 cache hit가 좋아진다.
- system/developer context, tool definitions, environment metadata가 자주 바뀌면 캐시 이점이 줄어든다.
- agent loop는 같은 전반부 컨텍스트를 반복 사용하므로 caching 효과가 크다.

## ASCII 다이어그램

```text
request N
  [stable prefix][changing tail]

request N+1
  [stable prefix][new tail]

=> reuse cached prefix
```

## 하네스 관점의 의미

Codex agent loop 글과 강하게 연결된다. 좋은 하네스는 reasoning만 잘하는 게 아니라, prompt shape를 안정시켜 cache-friendly하게 설계해야 한다.

## 실무 포인트

- 도구 목록과 순서를 자주 바꾸지 말 것
- 불필요한 전역 지시문 변형을 줄일 것
- 긴 대화에서는 prefix 안정성도 성능 설계의 일부다

## 기억할 문장

agent 하네스의 비용 구조는 모델 가격만이 아니라, prompt prefix를 얼마나 안정적으로 유지하느냐에도 달려 있다.

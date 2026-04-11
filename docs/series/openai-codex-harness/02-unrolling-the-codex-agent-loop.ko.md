# Unrolling the Codex agent loop

- 원문: [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
- 출처: OpenAI
- 게시일: 2026-01-23

## 한줄 요약

Codex는 답변 모델이 아니라 `도구 호출과 환경 변경을 반복하는 agent loop`이며, 이 loop를 안정적으로 굴리는 것이 하네스의 핵심이다.

## 이 글이 답하는 질문

Codex는 한 번의 응답 뒤에 멈추는 대신 어떤 구조로 도구를 호출하고 환경을 바꾸며 작업을 끝내는가?

## 핵심 주장

- 한 turn 안에는 모델 추론과 tool calls가 여러 번 반복될 수 있다.
- agent의 진짜 출력은 assistant message만이 아니라, 로컬 환경에 남긴 코드 변경까지 포함한다.
- 긴 turn은 context window를 빠르게 잠식하므로 compaction과 prompt caching이 매우 중요하다.
- sandbox 설정, developer messages, user instructions, MCP tools 목록이 모두 prompt 구성에 영향을 준다.

## ASCII 다이어그램

```text
user input
   |
   v
model inference
   |
   +--> tool calls? ---- yes ----> run tools / mutate env
   |                                 |
   |                                 v
   |<-------- tool outputs in context
   |
   +--> no ----> assistant message + stop
```

## 하네스 관점의 의미

이 글은 Codex 하네스를 가장 저수준으로 설명한다. OpenAI가 하네스를 볼 때 핵심은 "좋은 프롬프트"가 아니라 prompt assembly, sandbox policy, tool enumeration, caching, compaction 같은 실행 계층 전체라는 점이다.

## 실무 포인트

- tool 목록과 순서를 안정적으로 유지해야 cache hit가 좋아진다.
- 환경 설정이 바뀌면 prompt prefix도 깨지므로 비용이 커진다.
- 긴 agent turn은 설계 단계부터 context budget을 염두에 둬야 한다.

## 기억할 문장

Codex의 핵심 단위는 한 번의 답변이 아니라, 종료 조건에 도달할 때까지 이어지는 tool-driven turn이다.

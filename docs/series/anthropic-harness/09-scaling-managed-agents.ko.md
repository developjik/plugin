# Scaling Managed Agents: Decoupling the brain from the hands

- 원문: [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents)
- 출처: Anthropic Engineering
- 게시일: 2026-03-25

## 한줄 요약

하네스는 계속 바뀌므로, 그 위에 올라가는 제품은 세션과 실행 환경을 분리한 안정적 인터페이스를 중심으로 설계해야 한다.

## 이 글이 답하는 질문

모델이 빨리 좋아지는 상황에서, 자주 바뀌는 하네스 위에 어떻게 오래 가는 플랫폼을 만들 것인가?

## 핵심 주장

- 하네스는 모델 한계에 대한 가정을 담고 있고, 그 가정은 곧 stale해진다.
- brain, harness, sandbox를 강하게 묶어두면 보안과 확장성 문제가 생긴다.
- session을 append-only event log처럼 두고, sandbox를 tool처럼 호출하는 구조가 더 안정적이다.

## ASCII 다이어그램

```text
Before: coupled

  +--------------------------------------+
  | container                            |
  |  brain + harness + code execution    |
  |  credentials nearby                  |
  +--------------------------------------+
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

## 하네스 관점의 의미

이 글은 Anthropic 하네스 사고의 최신 단계다. 이제 초점은 "더 좋은 하네스" 자체보다, 하네스가 교체돼도 유지되는 session API와 execution boundary에 있다.

## 실무 포인트

- 하네스 구현을 제품 API로 굳히지 말라.
- 실행 환경과 오케스트레이션을 분리하라.
- 생성 코드와 자격 증명이 같은 공간에 있지 않게 하라.

## 기억할 문장

변하는 하네스에 오래 버티는 제품을 올리려면, 하네스가 아니라 인터페이스를 안정화해야 한다.

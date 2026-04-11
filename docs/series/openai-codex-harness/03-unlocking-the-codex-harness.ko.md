# Unlocking the Codex harness: how we built the App Server

- 원문: [Unlocking the Codex harness: how we built the App Server](https://openai.com/index/unlocking-the-codex-harness/)
- 출처: OpenAI
- 게시일: 2026-02-04

## 한줄 요약

OpenAI는 Codex를 여러 클라이언트에서 재사용하기 위해 하네스 자체를 App Server라는 안정된 세션/프로토콜 계층으로 분리했다.

## 이 글이 답하는 질문

CLI, Desktop, Web, IDE 같은 여러 프런트엔드가 같은 Codex 코어를 어떻게 공유할 수 있는가?

## 핵심 주장

- App Server는 JSON-RPC 프로토콜이자 long-lived process다.
- thread manager가 thread마다 core session을 하나씩 관리한다.
- client는 로컬 UI일 수 있지만, 실제 Codex core와의 통신은 안정된 server boundary를 통해 이뤄진다.
- 이렇게 해야 backwards compatibility, 이벤트 스트리밍, 여러 통합면을 함께 유지할 수 있다.

## ASCII 다이어그램

```text
CLI / Desktop / Web / IDE
           |
           v
      App Server
   +-------+--------+
   | JSON-RPC       |
   | thread manager |
   | message proc   |
   +---+--------+---+
       |        |
       v        v
   core thread  core thread
```

## 하네스 관점의 의미

이 문서는 하네스를 단순 로컬 루프가 아니라 플랫폼 계층으로 끌어올린다. OpenAI는 여기서부터 Codex를 "agent runtime core"로 다루기 시작한다.

## 실무 포인트

- 클라이언트 기능 추가와 agent core 변경을 분리할 수 있다.
- 세션 상태를 오래 유지하는 구조가 가능해진다.
- 통합 API를 안정화하면 제품 확장이 쉬워진다.

## 기억할 문장

하네스가 제품의 중심이 되면, 하네스도 서버처럼 안정된 인터페이스를 가져야 한다.

# Introducing Codex

- 원문: [Introducing Codex](https://openai.com/index/introducing-codex/)
- 출처: OpenAI
- 게시일: 2025-05-16

## 한줄 요약

Codex는 각 작업을 독립 cloud sandbox에서 수행하는 소프트웨어 엔지니어링 에이전트로 소개되며, 잘 쪼갠 작업과 검증 가능한 환경을 전제로 설계된다.

## 이 글이 답하는 질문

Codex라는 제품은 어떤 실행 모델과 보안 모델 위에서 돌아가는가?

## 핵심 주장

- 각 task는 repository가 preload된 isolated cloud sandbox에서 실행된다.
- 초기에는 인터넷이 막혀 있었고, 이후 선택적 인터넷 접근 옵션이 추가됐다.
- Codex는 코드 작성, 버그 수정, PR 제안, 코드베이스 질의에 적합하다.
- OpenAI 내부에서는 반복적이고 잘 스코프된 작업 위주로 먼저 사용했다.

## ASCII 다이어그램

```text
task A -> sandbox A -> result / patch
task B -> sandbox B -> result / patch
task C -> sandbox C -> result / patch
```

## 하네스 관점의 의미

OpenAI식 Codex 하네스의 기본 철학은 "각 작업을 격리된 실행 단위로 만든다"는 데 있다. 이 기본 모델이 뒤의 App Server, agent loop, background mode 설명으로 이어진다.

## 실무 포인트

- 작은 작업 단위로 쪼갤수록 효과가 좋다.
- setup script와 dependency 환경이 매우 중요하다.
- sandbox isolation은 보안뿐 아니라 재현성에도 도움된다.

## 기억할 문장

Codex의 기본 단위는 IDE 안의 보조 답변이 아니라, 독립적으로 실행되는 클라우드 작업이다.

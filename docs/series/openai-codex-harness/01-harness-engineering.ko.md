# Harness engineering: leveraging Codex in an agent-first world

- 원문: [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)
- 출처: OpenAI
- 게시일: 2026-02-11

## 한줄 요약

OpenAI는 Codex 시대의 핵심 경쟁력이 모델 자체보다 `하네스를 어떻게 운영하느냐`에 있다고 본다.

## 이 글이 답하는 질문

에이전트가 코드베이스 안에서 장기적으로 유용하게 일하도록 하려면 팀의 운영 방식과 산출물을 어떻게 바꿔야 하는가?

## 핵심 주장

- `AGENTS.md`는 장문의 백과사전이 아니라, 에이전트가 필요한 문서를 찾아가게 하는 목차에 가까워야 한다.
- 진짜 source of truth는 `docs/` 아래 구조화된 문서에 둬야 한다.
- agent-first 개발에서는 사람이 매번 붙잡고 있는 대신, background tasks와 cleanup loops를 운영 체계로 만든다.
- quality grades, targeted refactoring PR, 자동 점검 루프 같은 운영 장치가 하네스의 일부가 된다.

## ASCII 다이어그램

```text
repo
  |
  +--> AGENTS.md      -> short routing guide
  +--> docs/          -> system of record
  +--> setup scripts  -> environment bootstrap
  +--> background jobs-> cleanup / grading / refactors
```

## 하네스 관점의 의미

이 글은 OpenAI 쪽에서 가장 직접적으로 "하네스 엔지니어링"을 이름 붙여 설명한 문서다. 프롬프트보다 운영 산출물, 반복 루프, 자동 점검, 문서 구조가 더 중요하다는 점을 분명히 한다.

## 실무 포인트

- AGENTS.md를 너무 길게 만들지 말 것
- 문서 저장소를 코드 저장소와 함께 관리할 것
- background Codex 작업을 장기 운영 루프로 설계할 것

## 기억할 문장

에이전트 시대의 하네스는 프롬프트 모음이 아니라, 문서 구조와 운영 루프까지 포함한 개발 시스템이다.

# From model to agent: Equipping the Responses API with a computer environment

- 원문: [From model to agent: Equipping the Responses API with a computer environment](https://openai.com/index/equip-responses-api-computer-environment/)
- 출처: OpenAI
- 게시일: 2026-03-11

## 한줄 요약

OpenAI는 Responses API를 단순 inference API가 아니라 `shell + container + skills + compaction`이 붙은 agent runtime으로 확장하고 있다.

## 이 글이 답하는 질문

Responses API만으로 장시간 도구 실행형 에이전트를 어떻게 만들 수 있는가?

## 핵심 주장

- 모델이 shell 명령을 제안하면 Responses API가 container runtime으로 넘기고 결과를 다시 컨텍스트에 넣는다.
- 여러 shell 세션을 병렬로 실행할 수 있다.
- output cap으로 대용량 로그가 컨텍스트를 오염시키지 않게 막는다.
- native compaction을 통해 장시간 작업에서도 중요한 맥락을 유지한다.
- skills는 반복 가능한 workflow logic을 재사용층으로 제공한다.

## ASCII 다이어그램

```text
prompt
  |
  v
Responses API
  |
  +--> model decides next action
  |
  +--> shell tool call?
         |
         v
     container runtime
         |
         v
   bounded output stream
         |
         v
   back into model context
```

## 하네스 관점의 의미

OpenAI는 agent harness를 앱 내부 구현물이 아니라 플랫폼 기능으로 끌어올리고 있다. 이 글은 그 전환을 가장 명확하게 보여준다.

## 실무 포인트

- custom client loop를 다 직접 구현하지 않아도 된다.
- output bounding과 compaction은 긴 작업에서 필수다.
- skills를 도메인별 재사용 단위로 설계할 수 있다.

## 기억할 문장

모델이 agent가 되려면 reasoning만이 아니라 실행 환경과 맥락 유지 장치가 함께 제공돼야 한다.

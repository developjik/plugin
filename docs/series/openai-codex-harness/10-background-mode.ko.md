# Background mode

- 원문: [Background mode](https://developers.openai.com/api/docs/guides/background)
- 출처: OpenAI API Docs
- 문서 유형: Guide

## 한줄 요약

Background mode는 장시간 에이전트 작업을 request-response 한 번에 끝내지 않고, 비동기 작업으로 분리하는 공식 패턴이다.

## 이 글이 답하는 질문

몇 분 이상 걸리는 긴 agent task를 API 레벨에서 어떻게 안정적으로 운영할 것인가?

## 핵심 주장

- `background=true`로 긴 응답을 비동기 실행할 수 있다.
- 클라이언트는 polling 또는 webhook으로 결과를 회수한다.
- 장시간 작업은 사용자 상호작용과 분리해야 안정적이다.
- background response는 저장 특성 때문에 ZDR 제약과도 연결된다.

## ASCII 다이어그램

```text
client request
   |
   v
create background job
   |
   +--> return job/reference immediately
   |
   +--> run long task asynchronously
   |
   +--> poll or webhook for completion
```

## 하네스 관점의 의미

이 가이드는 OpenAI가 long-running agents를 API 수준에서 정식 지원하기 시작했음을 보여준다. Codex류 agent를 제품에 넣을 때 중요한 운영 패턴이다.

## 실무 포인트

- 동기 요청 안에 긴 agent loop를 억지로 넣지 말 것
- polling UX와 실패 복구를 함께 설계할 것
- 작업 상태를 외부 저장소와 연결할 것

## 기억할 문장

긴 에이전트 작업은 대화의 일부가 아니라 작업 시스템의 일부로 다뤄야 한다.

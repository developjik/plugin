# Inside OpenAI’s in-house data agent

- 원문: [Inside OpenAI’s in-house data agent](https://openai.com/index/inside-our-in-house-data-agent/)
- 출처: OpenAI
- 게시일: 2026-01-29

## 한줄 요약

OpenAI의 내부 데이터 에이전트는 고품질 분석을 위해 rich context, memory, self-correction, evals를 하나의 closed loop로 묶는다.

## 이 글이 답하는 질문

복잡한 데이터 분석 업무를 장시간 자율적으로 수행하는 에이전트는 어떤 하네스를 필요로 하는가?

## 핵심 주장

- agent는 고정 스크립트를 따르지 않고 중간 결과를 보고 스스로 접근을 수정한다.
- high-quality context가 없으면 강한 모델도 내부 용어와 지표를 자주 오해한다.
- memory와 learned usage가 장기 품질에 큰 영향을 준다.
- notebooks, reports, SQL, web search를 하나의 workflow 안에서 묶는다.

## ASCII 다이어그램

```text
question
  |
  v
discover data -> inspect schema -> query -> validate result
                                ^               |
                                |               v
                                +---- revise if wrong
```

## 하네스 관점의 의미

Codex 전용 글은 아니지만, OpenAI가 실제 내부 agent를 어떻게 구성하는지 보여준다. 특히 self-correction과 context layering을 하네스 문제로 다루는 점이 중요하다.

## 실무 포인트

- 도메인 문맥을 외부 문서와 메타데이터로 충분히 제공할 것
- 중간 결과 검증 루프를 agent 안에 넣을 것
- evals 없이 agent 품질을 믿지 말 것

## 기억할 문장

좋은 분석 agent는 정답을 한 번에 내는 시스템이 아니라, 틀린 중간 결과를 스스로 감지하고 수정하는 루프다.

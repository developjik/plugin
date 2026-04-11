# Evaluate agent workflows

- 원문: [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals)
- 출처: OpenAI API Docs
- 문서 유형: Guide

## 한줄 요약

좋은 agent harness는 실행만 잘하는 것이 아니라, trace와 결과를 함께 평가하는 체계를 갖춰야 한다.

## 이 글이 답하는 질문

에이전트 워크플로가 실제로 좋아졌는지 어떻게 측정할 것인가?

## 핵심 주장

- agent workflow는 최종 답변만 보면 안 된다.
- trace grading이 중요하다.
- task success뿐 아니라 tool-use quality, policy adherence, step quality도 평가할 수 있다.
- eval datasets와 반복 실행이 regression 방지에 필요하다.

## ASCII 다이어그램

```text
task set
  |
  v
run agent workflow
  |
  +--> final outputs
  +--> traces / tool calls / intermediate steps
  |
  v
graders
  |
  v
scores / regressions / improvements
```

## 하네스 관점의 의미

OpenAI도 Anthropic과 마찬가지로 하네스와 eval을 분리해서 본다. 이 문서는 agent를 만들고 끝내지 말고, 평가 파이프라인도 같이 설계하라고 요구한다.

## 실무 포인트

- 결과만 채점하지 말고 과정을 채점할 것
- trace 데이터는 버리지 말 것
- 자동화된 regression suite를 만들 것

## 기억할 문장

에이전트 하네스를 운영한다는 것은 실행 루프와 평가 루프를 함께 운영한다는 뜻이다.

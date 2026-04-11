# Demystifying evals for AI agents

- 원문: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- 출처: Anthropic Engineering
- 게시일: 2026-01-09

## 한줄 요약

에이전트를 잘 만들려면 에이전트 하네스와 그것을 측정하는 평가 하네스를 분리해서 생각해야 한다.

## 이 글이 답하는 질문

에이전트 성능을 신뢰할 만하게 측정하려면 무엇을 구분해서 봐야 하는가?

## 핵심 주장

- transcript와 outcome은 다르다.
- task, trial, grader, transcript, outcome, evaluation suite를 분리해야 한다.
- `agent harness`는 행동 시스템이고, `evaluation harness`는 그 행동 시스템을 반복 실행하고 채점하는 인프라다.

## ASCII 다이어그램

```text
Agent Harness
  task -> model + tools + loop -> actions -> final state

Evaluation Harness
  suite of tasks
      |
      v
  run agent harness repeatedly
      |
      v
  graders / assertions / aggregation
      |
      v
  performance signal
```

## 하네스 관점의 의미

많은 팀이 "에이전트를 만들었다"와 "에이전트가 좋아졌다"를 혼동한다. Anthropic은 이 문서에서 두 번째 문제를 푸는 별도 시스템이 필요하다고 못박는다.

## 실무 포인트

- 결과 문장보다 실제 환경 상태를 채점하라.
- 한 번의 실행이 아니라 여러 trial을 보라.
- 회귀(regression)를 막으려면 eval suite가 필요하다.

## 기억할 문장

하네스를 만드는 일과 하네스를 측정하는 일은 서로 다른 엔지니어링 문제다.

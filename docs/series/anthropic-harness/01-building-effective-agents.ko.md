# Building effective agents

- 원문: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- 출처: Anthropic Engineering
- 게시일: 2024-12-19

## 한줄 요약

Anthropic은 좋은 에이전트 시스템이 복잡한 프레임워크보다 단순하고 조합 가능한 패턴 위에서 더 잘 만들어진다고 본다.

## 이 글이 답하는 질문

LLM 기반 시스템을 만들 때 언제 `workflow`를 쓰고, 언제 `agent`를 써야 하는가?

## 핵심 주장

- `workflow`는 미리 짜놓은 코드 경로로 LLM과 도구를 오케스트레이션하는 방식이다.
- `agent`는 LLM이 도구 사용과 다음 행동을 동적으로 결정하는 방식이다.
- 대부분의 성공 사례는 거대한 프레임워크보다 단순한 패턴의 조합으로 만들어졌다.

## 핵심 패턴

1. Prompt chaining
2. Routing
3. Parallelization
4. Orchestrator-workers
5. Evaluator-optimizer

## ASCII 다이어그램

```text
                +-------------------+
                |   Augmented LLM   |
                | tools / memory /  |
                | retrieval         |
                +---------+---------+
                          |
        +-----------------+------------------+
        |                 |                  |
        v                 v                  v
  prompt chaining      routing        parallelization
                                             |
                                             v
                                  orchestrator-workers
                                             |
                                             v
                                  evaluator-optimizer
                                             |
                                             v
                                          agents
```

## 하네스 관점의 의미

이 글은 뒤에 나오는 모든 Anthropic 하네스 문서의 설계 언어를 만든다. 장기 실행 하네스, 멀티에이전트 리서치, 평가자 분리, QA 루프는 모두 여기서 제시한 기본 패턴의 응용으로 볼 수 있다.

## 실무 포인트

- 일단은 가장 단순한 패턴부터 시작하라.
- 병렬화 가치가 없는 작업에 멀티에이전트를 남발하지 말라.
- 평가자와 생성자를 분리하면 품질 개선 루프를 만들기 쉽다.

## 기억할 문장

좋은 에이전트 시스템은 대개 복잡한 프레임워크의 승리가 아니라, 단순한 패턴을 올바르게 조합한 결과다.

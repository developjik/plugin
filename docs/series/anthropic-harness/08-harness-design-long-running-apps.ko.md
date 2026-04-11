# Harness design for long-running application development

- 원문: [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- 출처: Anthropic Engineering
- 게시일: 2026-03-24

## 한줄 요약

긴 앱 개발에서는 planner, generator, evaluator를 분리하고, 주관적 품질까지 rubric으로 채점 가능하게 만들면 단일 에이전트보다 더 높은 결과 품질을 얻을 수 있다.

## 이 글이 답하는 질문

장시간 자율 코딩에서 컨텍스트 붕괴와 자기평가 편향을 동시에 어떻게 다룰 것인가?

## 핵심 주장

- 긴 작업은 맥락 붕괴와 `self-evaluation leniency`가 문제다.
- 디자인 품질은 rubric으로 쪼개면 채점 가능한 문제가 된다.
- 생성과 평가를 분리하면 더 강한 반복 개선 루프가 생긴다.
- 풀스택 코딩에서는 planner / generator / evaluator 3에이전트 구조가 효과적이었다.

## ASCII 다이어그램

```text
Frontend loop

+-------------+      build UI      +-------------+
| Generator   | -----------------> | Live Page   |
+------+------+                    +------+------+ 
       ^                                   |
       | scores / critique                 | inspect / click
       |                                   v
+------+------+
| Evaluator   |
| rubric      |
+-------------+
```

```text
Long-running app harness

   user prompt
       |
       v
 +-------------+
 | Planner     |
 | full spec   |
 +------+------+ 
        |
        v
 +-------------+      sprint contract      +-------------+
 | Generator   | <-----------------------> | Evaluator   |
 | build sprint|                           | QA / score  |
 +------+------+                           +------+------+
        |                                         |
        +---------------- app under test ---------+
```

## 하네스 관점의 의미

이 글은 장기 코딩 하네스를 단순 handoff 구조에서 `계획 + 생성 + 평가` 구조로 확장한다. 특히 평가자는 기능 검증뿐 아니라 디자인, 제품 깊이, 코드 품질까지 본다.

## 실무 포인트

- rubric 없는 반복은 막연한 재생성으로 흐르기 쉽다.
- 스프린트 전에 완료 기준을 계약처럼 합의하는 것이 중요하다.
- 더 강한 모델에서는 예전 분해 방식 일부를 제거해도 된다.

## 기억할 문장

생성자와 평가자를 분리하면, 에이전트는 자기확신이 아니라 외부 피드백을 기준으로 진화한다.

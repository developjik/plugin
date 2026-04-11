# Claude Code: Best practices for agentic coding

- 원문: [Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- 출처: Claude Code Docs
- 최초 엔지니어링 게시: 2025-04-18

## 한줄 요약

Claude Code를 잘 쓰는 핵심은 "바로 코딩시키기"가 아니라, 검증 기준을 먼저 주고 탐색과 계획을 분리하는 것이다.

## 이 글이 답하는 질문

사람이 Anthropic식 하네스를 수동 운영한다면 어떤 습관이 가장 효과적인가?

## 핵심 주장

- Claude가 스스로 검증할 수 있게 하면 품질이 크게 좋아진다.
- 권장 흐름은 `explore -> plan -> implement -> verify -> commit`이다.
- 긴 세션에서는 컨텍스트 오염이 누적되므로 적극적으로 `/clear`, resume, subagent, 병렬 세션을 사용해야 한다.
- writer/reviewer 패턴은 자기확신 편향을 줄이는 쉬운 방법이다.

## ASCII 다이어그램

```text
User
  |
  v
Explore ----> Plan ----> Implement ----> Verify ----> Commit
  |             |             |              |
  |             |             |              +--> tests / screenshots / outputs
  |             |             |
  |             |             +--> extra sessions / subagents
  |             |
  |             +--> explicit plan
  |
  +--> read codebase first
```

## 하네스 관점의 의미

이 문서는 연구용 하네스를 일상 코딩 워크플로로 번역한다. 사람은 planner를 보조하고, 별도 세션은 evaluator 역할을 하고, tests와 screenshots는 외부 검증 장치가 된다.

## 실무 포인트

- "고쳐줘"보다 "테스트를 돌려서 통과시키고, 스크린샷 비교까지 해"가 훨씬 낫다.
- 코드 수정 전에 먼저 읽고 계획하게 하라.
- 같은 세션에서 두 번 이상 같은 실수를 반복하면 새 세션으로 갈아타는 편이 낫다.

## 기억할 문장

자기 검증 경로가 없는 에이전트는 결국 사람을 유일한 QA 루프로 만든다.

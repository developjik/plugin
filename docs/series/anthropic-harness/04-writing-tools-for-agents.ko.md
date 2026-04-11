# Writing effective tools for AI agents

- 원문: [Writing effective tools for AI agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- 출처: Anthropic Engineering
- 게시일: 2025-09-11

## 한줄 요약

좋은 에이전트 성능은 좋은 프롬프트보다, 에이전트가 이해하기 쉬운 도구 인터페이스에 더 크게 좌우될 때가 많다.

## 이 글이 답하는 질문

에이전트가 잘 쓰는 도구는 일반 API와 무엇이 다른가?

## 핵심 주장

- 도구는 모호하지 않아야 한다.
- 입력 파라미터는 사람이 아니라 에이전트 입장에서 명확해야 한다.
- 한 번에 너무 많은 데이터를 반환하는 도구는 컨텍스트를 낭비한다.
- 이름이 비슷하거나 기능이 겹치는 도구 세트는 실수를 부른다.

## ASCII 다이어그램

```text
Bad
  agent -> list_all_contacts -> giant output -> context waste -> confusion

Better
  agent -> search_contacts("jane") -> small relevant output -> next step

Best
  agent -> get_customer_context(customer_name)
        -> summary + IDs + likely next actions
```

## 하네스 관점의 의미

하네스는 프롬프트와 오케스트레이션만이 아니다. 도구의 입력 형식, 반환 크기, 이름 규칙, 에러 표면까지 모두 하네스의 일부다.

## 실무 포인트

- `user`보다 `user_id`가 낫다.
- "전부 보여줘"보다 "필요한 부분만 검색"이 낫다.
- 도구 설명은 팀 신입에게 설명하듯 써라.

## 기억할 문장

에이전트는 나쁜 도구 위에서 똑똑하게 행동하지 못한다.

# How we used Codex to build Sora for Android in 28 days

- 원문: [How we used Codex to build Sora for Android in 28 days](https://openai.com/index/shipping-sora-for-android-with-codex/)
- 출처: OpenAI
- 게시일: 2025-12-12

## 한줄 요약

이 글은 Codex를 실제 모바일 제품 개발 속도에 붙였을 때, 어떤 종류의 작업을 분담시키고 어떤 방식으로 사람이 검토하는지 보여주는 사례다.

## 이 글이 답하는 질문

실제 제품 팀이 Codex를 붙였을 때 어떤 작업 단위와 협업 방식이 현실적인가?

## 핵심 주장

- Codex는 반복적 구현, 보일러플레이트, 테스트, 정리 작업에서 생산성을 크게 높인다.
- 인간은 제품 판단, 최종 리뷰, 우선순위 조정에 집중한다.
- 작업을 작게 쪼개고 병렬로 던질수록 이득이 커진다.

## ASCII 다이어그램

```text
product goal
   |
   +--> human: product decisions / review
   |
   +--> Codex: scoped tasks / fixes / tests / scaffolding
```

## 하네스 관점의 의미

이 문서는 Codex 하네스가 연구 데모가 아니라 실제 shipping workflow에 들어가고 있음을 보여준다. 하네스의 성공 기준이 "완전 자율"이 아니라 "팀 throughput 증가"라는 점도 드러난다.

## 실무 포인트

- 에이전트에 넘길 작업은 독립성과 검증 가능성이 중요하다.
- 사람의 제품 감각과 최종 승인 루프는 여전히 필요하다.
- 병렬 task queue 운영이 효과적이다.

## 기억할 문장

제품 개발에서 좋은 에이전트 하네스는 사람을 없애는 구조가 아니라, 사람의 판단을 더 비싼 곳에 쓰게 만드는 구조다.

# How OpenAI uses Codex

- 원문: [How OpenAI uses Codex](https://openai.com/business/guides-and-resources/how-openai-uses-codex/)
- 출처: OpenAI

## 한줄 요약

OpenAI 내부 팀은 Codex를 가장 잘 쓰기 위해 `Ask Mode -> Code Mode`, AGENTS.md, Best-of-N, 환경 튜닝 같은 운영 습관을 정착시키고 있다.

## 이 글이 답하는 질문

Codex를 실제 팀 개발 흐름에서 꾸준히 가치 있게 쓰려면 어떤 습관이 필요한가?

## 핵심 주장

- 큰 변경은 Ask Mode로 계획부터 세운 뒤 Code Mode로 넘기는 것이 좋다.
- Codex는 대개 1시간 내외의 잘 스코프된 작업에서 가장 안정적이다.
- startup script, env vars, internet access를 반복적으로 개선해야 오류율이 낮아진다.
- AGENTS.md는 지속적 컨텍스트 공급 장치다.
- Best-of-N은 복잡한 작업에서 여러 해법을 빠르게 비교하는 방식이다.

## ASCII 다이어그램

```text
Ask Mode -> plan
   |
   v
Code Mode -> implement
   |
   v
verify / compare / pick best
```

## 하네스 관점의 의미

이 문서는 OpenAI가 Codex 하네스를 제품 기능만으로 보지 않고, 팀의 사용 습관과 환경 설정까지 포함한 운영 체계로 본다는 점을 보여준다.

## 실무 포인트

- 코드 쓰기 전에 계획부터 받기
- 작업 크기를 일부러 작게 유지하기
- repo마다 AGENTS.md를 유지하기

## 기억할 문장

좋은 Codex 결과는 좋은 모델에서만 나오는 게 아니라, 좋은 작업 단위와 좋은 환경 설정에서 나온다.

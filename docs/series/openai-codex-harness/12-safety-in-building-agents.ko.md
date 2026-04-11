# Safety in building agents

- 원문: [Safety in building agents](https://developers.openai.com/api/docs/guides/agent-builder-safety)
- 출처: OpenAI API Docs
- 문서 유형: Guide

## 한줄 요약

에이전트 하네스 설계에서 안전은 부가 기능이 아니라, 도구 권한과 외부 입력을 다루는 핵심 구조 문제다.

## 이 글이 답하는 질문

도구를 가진 agent를 제품에 넣을 때 어떤 안전 경계와 제어 장치가 필요한가?

## 핵심 주장

- prompt injection은 agent 환경에서 더 위험하다.
- 인터넷 접근, 파일 접근, 외부 시스템 액션은 명시적 guardrail이 필요하다.
- structured outputs, approvals, monitoring, tracing이 중요하다.
- data exfiltration과 privilege escalation을 하네스 레벨에서 막아야 한다.

## ASCII 다이어그램

```text
external input
   |
   v
agent reasoning
   |
   +--> safe action? ---- yes ----> run tool
   |
   +--> risky action? --- no -----> require approval / block / log
```

## 하네스 관점의 의미

OpenAI 문맥에서 안전은 moderation 옆의 별도 주제가 아니라, sandbox policy와 tool permission 구조를 설계하는 하네스 문제다.

## 실무 포인트

- destructive actions는 사람이 승인하게 둘 것
- 외부 텍스트를 신뢰 가능한 명령으로 취급하지 말 것
- traces와 logs를 남겨 감사 가능성을 확보할 것

## 기억할 문장

도구를 가진 agent의 안전은 모델의 선의가 아니라, 권한 구조와 승인 경계에서 나온다.

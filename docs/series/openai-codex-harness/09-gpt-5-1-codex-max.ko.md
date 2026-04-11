# Building more with GPT-5.1-Codex-Max

- 원문: [Building more with GPT-5.1-Codex-Max](https://openai.com/index/gpt-5-1-codex-max/)
- 출처: OpenAI
- 게시일: 2025-11-19

## 한줄 요약

더 강한 Codex 계열 모델은 하네스를 단순화할 여지를 주지만, long-running tasks와 review loops 자체를 없애주지는 않는다.

## 이 글이 답하는 질문

모델 성능이 올라가면 Codex 하네스 설계는 어떻게 달라지는가?

## 핵심 주장

- long-running coding task에 더 적합한 모델이 등장했다.
- native compaction과 더 강한 추론이 장시간 작업의 안정성을 높인다.
- 그래도 검증, 리뷰, 적절한 작업 분할은 계속 중요하다.

## ASCII 다이어그램

```text
stronger model
    |
    +--> fewer recoverable failures
    +--> longer coherent runs
    +--> less brittle prompting
    |
    +--> still needs tests / review / harness
```

## 하네스 관점의 의미

이 글은 모델 향상이 하네스를 없애는 것이 아니라, 하네스의 부담을 줄이고 설계의 초점을 옮긴다는 점을 보여준다.

## 실무 포인트

- 모델이 강해질수록 더 큰 작업을 맡길 수는 있다.
- 그렇다고 verification loop를 제거하면 안 된다.
- 하네스는 모델 세대에 맞게 다시 조정해야 한다.

## 기억할 문장

강한 모델은 하네스를 대체하지 않는다. 하네스의 병목을 다른 곳으로 이동시킬 뿐이다.

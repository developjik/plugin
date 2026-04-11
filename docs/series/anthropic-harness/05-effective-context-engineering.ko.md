# Effective context engineering for AI agents

- 원문: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- 출처: Anthropic Engineering
- 게시일: 2025-09-29

## 한줄 요약

에이전트 품질 문제의 중심은 더 이상 프롬프트 자체가 아니라, 매 시점에 무엇을 컨텍스트에 넣고 무엇을 빼는가에 있다.

## 이 글이 답하는 질문

긴 작업에서 컨텍스트 윈도우 한계를 어떻게 우회할 것인가?

## 핵심 주장

- 컨텍스트는 유한한 attention budget이다.
- 좋은 원칙은 `가장 작은 고신호 토큰 집합`을 유지하는 것이다.
- 긴 작업에서는 compaction, note-taking, sub-agent architecture가 핵심 패턴이다.

## ASCII 다이어그램

```text
raw information universe
    |
    +--> system prompt
    +--> tools
    +--> examples
    +--> message history
    +--> files / links / notes
    |
    v
context engineering
    |
    +--> keep high-signal
    +--> discard noise
    +--> retrieve just-in-time
```

```text
long task support

1) Compaction
   long trace -> summarize -> new context

2) Note-taking
   work -> NOTES.md / memory -> reload later

3) Sub-agents
   lead agent -> focused subagents -> condensed summaries
```

## 하네스 관점의 의미

장시간 하네스에서 중요한 것은 "많이 넣는 것"이 아니라 "적절히 버리고 다시 가져오는 것"이다. 이 문서는 이후 long-running harness와 managed agents 글의 공통 토대다.

## 실무 포인트

- CLAUDE.md나 NOTES.md 같은 외부 메모리는 매우 강력하다.
- 대규모 데이터를 사전 적재하지 말고, 파일 경로나 링크 같은 lightweight reference를 유지하라.
- compaction 프롬프트는 recall 우선으로 시작한 뒤 precision을 높여라.

## 기억할 문장

좋은 컨텍스트 엔지니어링은 더 많은 정보를 주는 기술이 아니라, 더 적은 정보로 더 정확히 일하게 만드는 기술이다.

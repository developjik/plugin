# Effective harnesses for long-running agents

- 원문: [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- 출처: Anthropic Engineering
- 게시일: 2025-11-26

## 한줄 요약

장시간 코딩 에이전트를 안정화하려면 한 번에 다 하게 두지 말고, 초기 환경 세팅과 점진적 구현을 분리하고 상태를 파일과 커밋으로 넘겨야 한다.

## 이 글이 답하는 질문

컨텍스트 윈도우를 넘는 장기 코딩 작업을 어떻게 세션 사이에 이어서 수행할 것인가?

## 핵심 주장

- compaction만으로는 충분하지 않다.
- 첫 세션은 `initializer agent`가 환경과 산출물을 준비한다.
- 이후 세션은 `coding agent`가 한 번에 한 feature만 진행한다.
- 세션 끝에는 다음 세션이 바로 이어받을 수 있는 깨끗한 상태를 남긴다.

## ASCII 다이어그램

```text
            +----------------------+
            | User Prompt          |
            +----------+-----------+
                       |
                       v
            +----------------------+
            | Initializer Agent    |
            | - init.sh            |
            | - claude-progress    |
            | - feature_list.json  |
            | - initial commit     |
            +----------+-----------+
                       |
                       v
            +----------------------+
            | Coding Agent Session |
            | 1 feature at a time  |
            +----------+-----------+
                       |
          +------------+-------------+
          |                          |
          v                          v
   read progress + git        run app + e2e test
          |                          |
          +------------+-------------+
                       |
                       v
            update artifacts + commit
                       |
                       v
                  next session
```

## 핵심 산출물

- `init.sh`
- `claude-progress.txt`
- `feature_list.json`
- git history

## 하네스 관점의 의미

Anthropic이 선택한 첫 장기 코딩 해법은 추상적 기억이 아니라 구조화된 handoff artifact였다. 상태를 파일과 git으로 외부화하면 세션 리셋을 견딜 수 있다.

## 실무 포인트

- 항상 작게 끝낼 수 있는 작업 단위로 쪼개라.
- 세션 끝 코드는 main에 머지해도 될 정도로 깨끗해야 한다.
- E2E 테스트가 가능하면 반드시 붙여라.

## 기억할 문장

장기 에이전트의 기억은 대개 모델 안보다 repo 안에 두는 편이 더 믿을 만하다.

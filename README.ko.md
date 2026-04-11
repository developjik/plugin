# Plugins 작업공간

[English](./README.md) | 한국어

이 저장소는 Codex와 Claude Code에서 사용하는 로컬 플러그인 작업공간입니다. 각 플러그인 디렉터리는 매니페스트, 스킬, 훅, 스크립트, 테스트, 문서를 자기 안에서 독립적으로 관리하고, 저장소 루트는 공용 문서와 marketplace 메타데이터를 둡니다.

## 설치

저장소 루트 자체는 플러그인이 아닙니다. 아래 목록에 있는 플러그인 디렉터리 중 하나를 골라 플랫폼별 가이드대로 설치해서 사용하세요.

- [Codex 로컬 플러그인 설치 가이드](./docs/guides/install/codex-local-plugin-install.ko.md)
- [Claude Code 로컬 플러그인 설치 가이드](./docs/guides/install/claude-code-local-plugin-install.ko.md)

## 현재 플러그인 디렉터리

| 플러그인 | 목적 | 문서 |
|---|---|---|
| `dev-kit` | `clarify -> planning -> execute -> review-execute` 흐름과 디버깅, 코드 품질 보조 스킬을 함께 제공하는 구조화된 개발 워크플로우 플러그인 | [영문](./dev-kit/README.md) / [한글](./dev-kit/README.ko.md) |
| `harness-design-kit` | 장시간 앱 개발, 프런트엔드 반복 개선, live evaluation, reset handoff를 위한 planner-generator-evaluator 하네스 플러그인 | [영문](./harness-design-kit/README.md) / [한글](./harness-design-kit/README.ko.md) |
| `skeleton-plugin` | Codex와 Claude Code를 모두 지원하는 플러그인을 만들기 위한 시작 템플릿 | [영문](./skeleton-plugin/README.en.md) / [한글](./skeleton-plugin/README.md) |

위 디렉터리 목록을 현재 작업공간에 실제로 들어 있는 플러그인 기준으로 보면 됩니다.

## 공용 문서

| 경로 | 내용 |
|---|---|
| [Docs 인덱스](./docs/README.ko.md) | 저장소 문서 트리를 한 번에 보는 상위 안내 문서 |
| [`docs/guides/install/`](./docs/guides/install/) | Codex와 Claude Code용 로컬 설치 가이드 모음 (영문/국문) |
| [Anthropic 하네스 시리즈](./docs/series/anthropic-harness/README.ko.md) | Anthropic/Claude 하네스 관련 글을 읽기 쉽게 나눈 한국어 시리즈 |
| [OpenAI/Codex 하네스 시리즈](./docs/series/openai-codex-harness/README.ko.md) | OpenAI/Codex 하네스 관련 글을 읽기 쉽게 나눈 한국어 시리즈 |
| [`docs/research/`](./docs/research/) | 조사 노트, 링크 모음, 저장소 분석 문서 |

## 저장소 구조

```text
plugins/
├── README.md
├── README.ko.md
├── .claude-plugin/
│   └── marketplace.json
├── docs/
│   ├── guides/
│   ├── research/
│   └── series/
├── dev-kit/
├── harness-design-kit/
└── skeleton-plugin/
```

그 외 숨김 워크스페이스 디렉터리는 이 단순화된 트리에서 생략했습니다.

## 이 저장소에서 작업하는 방법

1. 작업할 플러그인 디렉터리로 들어갑니다.
2. 매니페스트, 훅, 스킬, 스크립트를 수정하기 전에 해당 플러그인의 README를 먼저 읽습니다.
3. 플러그인별 상태, 스키마, 테스트, 에셋은 각 플러그인 디렉터리 안에 유지합니다.
4. 여러 플러그인에 공통으로 적용되는 가이드, 번역 시리즈, 조사 문서는 `docs/` 아래에 둡니다.

## 메모

- 저장소 루트는 설치 가능한 플러그인이 아니라 문서와 marketplace 메타데이터를 두는 위치입니다.
- 루트 [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) 에는 현재 작업공간에 있는 디렉터리 외에 초안 메타데이터가 포함될 수 있습니다.

## 언어 메모

- 저장소 루트는 `README.md`를 영어, `README.ko.md`를 한국어 문서로 사용합니다.
- `dev-kit`과 `harness-design-kit`도 같은 영문/국문 구성을 따릅니다.
- `skeleton-plugin`은 영어를 `README.en.md`, 한국어를 `README.md`에 둡니다.
- `docs/series/`와 `docs/research/`의 문서는 현재 한국어 중심입니다.

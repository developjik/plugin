# Plugins 작업공간

[English](./README.md) | 한국어

이 저장소는 Codex와 Claude Code에서 사용하는 로컬 플러그인들을 모아 둔 작업공간입니다. 각 플러그인은 자신의 디렉터리 안에서 매니페스트, 스킬, 훅, 스크립트, 문서를 독립적으로 관리합니다.

## 포함된 플러그인

| 플러그인 | 목적 | 문서 |
|---|---|---|
| `dev-kit` | `clarify -> planning -> execute -> review` 흐름을 사용하는 구조화된 개발 워크플로우 플러그인 | [영문](./dev-kit/README.md) / [한글](./dev-kit/README.ko.md) |
| `skeleton-plugin` | Codex와 Claude Code를 모두 지원하는 플러그인을 만들기 위한 시작 템플릿 | [영문](./skeleton-plugin/README.en.md) / [한글](./skeleton-plugin/README.md) |

## 저장소 구조

```text
plugins/
├── README.md
├── README.ko.md
├── dev-kit/
└── skeleton-plugin/
```

## 이 저장소를 사용하는 방법

1. 작업할 플러그인 디렉터리로 들어갑니다.
2. 매니페스트, 훅, 스킬을 수정하기 전에 해당 플러그인의 README를 먼저 읽습니다.
3. 각 플러그인은 독립적인 패키지라고 보고 별도의 수명주기와 변경 범위를 유지합니다.

## 메모

- 저장소 루트는 문서와 정리를 위한 위치일 뿐, 자체적으로 하나의 플러그인은 아닙니다.
- 플러그인별 상태, 스키마, 테스트, 에셋은 각 플러그인 디렉터리 안에 유지합니다.
- 이 저장소의 문서 언어 규칙은 다음과 같습니다.
  - 저장소 루트와 `dev-kit`에서는 `README.md`를 영어 문서로 사용합니다.
  - 저장소 루트와 `dev-kit`에서는 `README.ko.md`를 한국어 문서로 사용합니다.
  - `skeleton-plugin`은 현재 `README.en.md`를 영어, `README.md`를 한국어로 사용합니다.

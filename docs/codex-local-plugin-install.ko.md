# Codex 로컬 플러그인 설치 가이드

이 문서는 이 저장소에 있는 로컬 플러그인을 Codex에서 설치하고 사용하는 방법을 설명합니다.

공식 배경 문서는 OpenAI Codex 플러그인 문서를 참고합니다.

- [Build plugins](https://developers.openai.com/codex/plugins/build?install-scope=global)

## 개요

Codex는 플러그인 디렉터리를 임의로 스캔해서 바로 로드하지 않습니다. 대신 `marketplace.json`에 등록된 로컬 플러그인을 Plugin Directory에서 설치하는 방식으로 사용합니다.

즉, 로컬 사용을 위해 필요한 것은 두 가지입니다.

1. 플러그인 폴더 안의 Codex 매니페스트
2. Codex가 읽을 수 있는 로컬 marketplace 등록

이 저장소의 `dev-kit`은 이미 Codex 매니페스트를 포함하고 있습니다.

- [dev-kit/.codex-plugin/plugin.json](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/dev-kit/.codex-plugin/plugin.json)

## 설치 방식

Codex 로컬 플러그인 설치는 두 방식이 있습니다.

- repo-scoped marketplace
  - 현재 저장소 안에서만 보이게 등록하는 방식
  - 경로: `$REPO_ROOT/.agents/plugins/marketplace.json`
- personal marketplace
  - 사용자 계정 전체에서 보이게 등록하는 방식
  - 경로: `~/.agents/plugins/marketplace.json`

개인 개발 환경에서는 personal marketplace가 가장 단순합니다.

## 1. 플러그인 구조 확인

플러그인 폴더 안에 최소한 아래 파일이 있어야 합니다.

```text
<plugin>/
└── .codex-plugin/
    └── plugin.json
```

예시:

```text
dev-kit/
└── .codex-plugin/
    └── plugin.json
```

## 2. marketplace 파일 만들기

personal marketplace를 사용할 경우:

```text
~/.agents/plugins/marketplace.json
```

repo-scoped marketplace를 사용할 경우:

```text
$REPO_ROOT/.agents/plugins/marketplace.json
```

## 3. marketplace.json에 로컬 플러그인 등록

예시는 이 저장소의 `dev-kit`를 personal marketplace에 등록하는 설정입니다.

```json
{
  "name": "local-plugins",
  "interface": {
    "displayName": "Local Plugins"
  },
  "plugins": [
    {
      "name": "dev-kit",
      "source": {
        "source": "local",
        "path": "./Library/Mobile Documents/com~apple~CloudDocs/plugins/dev-kit"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
```

주의:

- personal marketplace에서는 경로 기준점이 홈 디렉터리(`~`)입니다.
- repo-scoped marketplace에서는 경로 기준점이 해당 저장소 루트입니다.
- `source.path`는 marketplace 파일 위치 기준 상대경로로 잡는 것이 가장 안전합니다.

예를 들어 현재 저장소 루트에 repo-scoped marketplace를 만들면 `dev-kit` 경로는 다음처럼 둘 수 있습니다.

```json
{
  "source": {
    "source": "local",
    "path": "./dev-kit"
  }
}
```

## 4. Codex 재시작

`marketplace.json`을 추가하거나 수정한 뒤에는 Codex를 재시작합니다.

## 5. Plugin Directory에서 설치

Codex 재시작 후:

1. Plugin Directory를 엽니다.
2. `Local Plugins` marketplace가 보이는지 확인합니다.
3. 그 안에서 원하는 플러그인(`dev-kit`)을 선택합니다.
4. 설치를 진행합니다.

설치 후에는 Codex가 내부 캐시에 복사한 버전을 사용할 수 있으므로, 플러그인 소스를 수정했다면 재시작 후 다시 확인하는 것이 안전합니다.

## 확인 방법

다음 순서로 확인하면 됩니다.

1. Codex를 재시작합니다.
2. Plugin Directory에서 `Local Plugins`가 보이는지 확인합니다.
3. `dev-kit`가 목록에 보이는지 확인합니다.
4. 설치 후 새 대화에서 플러그인에 포함된 skill이나 동작이 노출되는지 확인합니다.

## 문제 해결

### marketplace가 보이지 않을 때

- `marketplace.json` 경로가 맞는지 확인합니다.
- JSON 문법 오류가 없는지 확인합니다.
- Codex를 완전히 재시작했는지 확인합니다.

### 플러그인이 목록에 안 뜰 때

- 대상 플러그인 폴더에 `.codex-plugin/plugin.json`이 있는지 확인합니다.
- `source.path`가 marketplace 파일 기준 상대경로로 맞는지 확인합니다.

### 설치 후 변경사항이 반영되지 않을 때

- Codex를 재시작합니다.
- 필요하면 플러그인을 다시 설치하거나 다시 로드합니다.
- Codex가 설치 시점의 복사본을 사용하고 있을 가능성을 먼저 의심합니다.

## 이 저장소에서의 예시

현재 저장소에서는 `dev-kit`를 local plugin으로 등록해 사용할 수 있습니다.

- 저장소 루트: [/Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins)
- 플러그인 경로: [/Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins/dev-kit](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/dev-kit)
- 개인용 marketplace 예시 경로: [/Users/developjik/.agents/plugins/marketplace.json](/Users/developjik/.agents/plugins/marketplace.json)

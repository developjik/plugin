# Claude Code 로컬 플러그인 설치 가이드

이 문서는 이 저장소에 있는 로컬 플러그인을 Claude Code에서 설치하고 사용하는 방법을 설명합니다.

공식 문서는 Anthropic Claude Code 플러그인 문서를 기준으로 합니다.

- [Discover and install prebuilt plugins through marketplaces](https://code.claude.com/docs/en/discover-plugins)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)

## 개요

Claude Code는 로컬 플러그인 폴더를 임의로 스캔해서 바로 쓰지 않습니다. 먼저 marketplace를 등록한 다음, 그 marketplace에서 원하는 플러그인을 설치하는 방식입니다.

공식 문서 기준 핵심 흐름은 다음과 같습니다.

1. `.claude-plugin/marketplace.json` 이 있는 marketplace를 준비한다.
2. `/plugin marketplace add ...` 로 marketplace를 등록한다.
3. `/plugin install plugin-name@marketplace-name` 으로 플러그인을 설치한다.
4. `/reload-plugins` 로 현재 세션에 반영한다.

## 이 저장소의 현재 상태

이 저장소는 이미 Claude Code용 marketplace를 포함하고 있습니다.

- marketplace 파일: [/.claude-plugin/marketplace.json](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/.claude-plugin/marketplace.json)
- `dev-kit` 매니페스트: [/dev-kit/.claude-plugin/plugin.json](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/dev-kit/.claude-plugin/plugin.json)
- `skeleton-plugin` 매니페스트: [/skeleton-plugin/.claude-plugin/plugin.json](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/skeleton-plugin/.claude-plugin/plugin.json)

현재 marketplace 이름은 `developjik-plugins` 입니다.

## 설치 방법

### 방법 1: 저장소 디렉터리를 marketplace로 추가

Claude Code 세션을 이 저장소 루트에서 열고 다음 명령을 실행합니다.

```text
/plugin marketplace add /Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins
```

공식 문서상 로컬 디렉터리에 `.claude-plugin/marketplace.json` 이 있으면, 디렉터리 경로 자체를 marketplace source로 추가할 수 있습니다.

### 방법 2: marketplace.json 파일 경로를 직접 추가

같은 내용을 파일 경로로 직접 추가할 수도 있습니다.

```text
/plugin marketplace add /Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins/.claude-plugin/marketplace.json
```

## 플러그인 설치

marketplace 등록 후 원하는 플러그인을 설치합니다.

`dev-kit` 설치:

```text
/plugin install dev-kit@developjik-plugins
```

`skeleton-plugin` 설치:

```text
/plugin install skeleton-plugin@developjik-plugins
```

공식 문서 기준 기본 설치 scope는 `user` 입니다. 즉, 기본값으로는 내 Claude Code 환경 전체에서 사용할 수 있게 설치됩니다.

다른 scope가 필요하면 `/plugin` 인터페이스에서 선택합니다.

- `user`
  - 내 모든 프로젝트에서 사용
- `project`
  - 현재 저장소에 공유 설정으로 설치
- `local`
  - 현재 저장소에서만 개인적으로 사용

## 현재 세션에 반영

설치 직후 현재 세션에 반영하려면 다음 명령을 실행합니다.

```text
/reload-plugins
```

공식 문서상 install, enable, disable 이후에는 `/reload-plugins` 로 재시작 없이 반영할 수 있습니다.

## 확인 방법

다음 순서로 확인하면 됩니다.

1. `/plugin marketplace list` 로 `developjik-plugins` 가 등록되었는지 확인합니다.
2. `/plugin` 을 열고 `Installed` 탭에서 `dev-kit` 또는 `skeleton-plugin` 이 보이는지 확인합니다.
3. `/reload-plugins` 실행 후 plugin counts가 갱신되는지 확인합니다.
4. 플러그인에서 제공하는 skill, hook, MCP 동작이 실제로 노출되는지 확인합니다.

## 변경 반영 방식

공식 문서에 따르면 설치된 플러그인은 캐시에 복사되어 사용될 수 있습니다. 따라서 plugin 디렉터리 밖의 파일을 참조하는 상대 경로는 깨질 수 있고, 소스를 바꾼 뒤에는 다시 설치 또는 재로드가 필요할 수 있습니다.

plugin을 수정한 뒤에는 보통 다음 순서가 안전합니다.

1. `/plugin marketplace update developjik-plugins`
2. 필요하면 `/plugin uninstall dev-kit@developjik-plugins`
3. 다시 `/plugin install dev-kit@developjik-plugins`
4. `/reload-plugins`

## 문제 해결

### `/plugin` 명령이 없을 때

공식 문서 기준 먼저 버전을 확인합니다.

```text
claude --version
```

버전이 낮으면 Claude Code를 업데이트한 뒤 터미널을 다시 열고 재시작합니다.

### marketplace가 로드되지 않을 때

- 추가한 경로에 `.claude-plugin/marketplace.json` 이 실제로 있는지 확인합니다.
- JSON 문법 오류가 없는지 확인합니다.
- 경로를 디렉터리 대신 marketplace 파일 직접 경로로 다시 넣어 봅니다.

### 플러그인 설치 후 동작이 안 보일 때

- `/reload-plugins` 를 실행합니다.
- `/plugin` 의 `Installed` 탭에서 enable 상태인지 확인합니다.
- 필요하면 uninstall 후 reinstall 합니다.

### 스킬이 안 나타날 때

공식 문서상 캐시 문제일 수 있습니다. 필요하면 캐시를 지우고 다시 설치합니다.

```text
rm -rf ~/.claude/plugins/cache
```

그 뒤 Claude Code를 다시 시작하고 플러그인을 재설치합니다.

### 디버깅이 필요할 때

공식 문서에는 다음 도구가 안내되어 있습니다.

```text
claude --debug
```

또는 plugin 검증:

```text
claude plugin validate
```

## 이 저장소에서 바로 쓰는 가장 짧은 절차

이 저장소 루트에서 Claude Code를 연 뒤 다음 순서로 실행하면 됩니다.

```text
/plugin marketplace add /Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins
/plugin install dev-kit@developjik-plugins
/reload-plugins
```

# Plugin Skeleton

Codex plugin과 Claude Code plugin을 모두 지원하는 통합 스켈레톤입니다. 필요한 구성요소는 모두 포함하지만, 실제 동작 로직은 넣지 않은 최소 형태를 기본으로 둡니다.

영문 문서는 [README.en.md](./README.en.md)를 참고하세요.

## 목적

이 플러그인은 시작용 템플릿입니다. Codex와 Claude Code 양쪽 플랫폼에서 동작하는 plugin을 만들 때 필요한 표준 파일과 폴더를 한 번에 갖추고, 구현 세부사항은 비워 두거나 placeholder로 남겨 둡니다.

## 지원 플랫폼

| 구성요소 | Codex | Claude Code | 비고 |
|---------|:-----:|:-----------:|------|
| `skills/` | O | O | 동일 형식 (`SKILL.md`) |
| `commands/` | O | O | 슬래시 커맨드 (`.md`) |
| `hooks/hooks.json` | O | O | 동일 형식 (호환) |
| `.mcp.json` | O | O | 동일 형식 |
| `.app.json` | O | - | Codex 전용 |
| `.codex-plugin/` | O | - | Codex 매니페스트 |
| `.claude-plugin/` | - | O | Claude Code 매니페스트 |

## 포함된 구성요소

### 플랫폼 매니페스트

- `.codex-plugin/plugin.json`
  - Codex 필수 plugin manifest 파일입니다.
  - 플러그인 이름, 메타데이터, UI 표시 정보(`interface` 블록), 번들된 구성요소의 상대 경로를 정의합니다.

- `.claude-plugin/plugin.json`
  - Claude Code plugin manifest 파일입니다.
  - 플러그인 이름, 메타데이터, 번들된 구성요소의 상대 경로를 정의합니다.
  - Codex와 달리 `interface` 블록이 없고, 더 간결한 형태입니다.

### 공유 구성요소 (양쪽 플랫폼 호환)

- `skills/`
  - 번들된 skill을 넣는 폴더입니다.
  - skill 하나당 전용 폴더 하나와 그 안의 `SKILL.md`를 둡니다.
  - 재사용 가능한 워크플로우 지시문을 plugin 안에 넣고 싶을 때 사용합니다.

- `commands/`
  - 슬래시 커맨드를 넣는 폴더입니다.
  - `.md` 파일 하나가 하나의 커맨드가 됩니다 (예: `help.md` → `/skeleton:help`).
  - 사용자가 직접 호출하는 명령을 정의할 때 사용합니다.

- `hooks/hooks.json`
  - hook 설정 파일입니다. 두 플랫폼 모두 동일한 형식을 사용합니다.
  - 포함된 hook 타입:
    - `SessionStart` — 세션 시작/재개 시
    - `PreToolUse` — 도구 사용 전
    - `PostToolUse` — 도구 사용 후
    - `PostToolUseFailure` — 도구 사용 실패 시 (Claude Code)
    - `UserPromptSubmit` — 프롬프트 제출 시
    - `Notification` — 알림 발생 시 (Claude Code)
    - `Stop` — 세션 중지 시
    - `SubagentStop` — 서브에이전트 중지 시 (Claude Code)

- `hooks/*.sh`
  - 공통 hook 진입점을 위한 placeholder shell script입니다.
  - 경로 참조는 `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-.}}` 형태로 양쪽 플랫폼 환경변수를 모두 지원합니다.

- `.mcp.json`
  - MCP server 정의용 placeholder 파일입니다.
  - plugin이 MCP server를 직접 노출하거나 연결할 때 사용합니다.

### Codex 전용 구성요소

- `.app.json`
  - app 또는 connector 매핑용 placeholder 파일입니다.
  - plugin이 앱이나 외부 connector 정의를 함께 번들할 때 사용합니다.

### 공용 디렉토리

- `scripts/`
  - plugin이나 bundled skill에서 쓰는 로컬 helper script 폴더입니다.
  - setup 도구, validator, generator, 작은 자동화 스크립트를 두기에 적합합니다.

- `assets/`
  - 아이콘, 로고, 스크린샷 같은 시각 리소스를 두는 폴더입니다.

## 권장 다음 단계

1. 대상 플랫폼의 매니페스트에서 `[TODO: ...]` placeholder를 실제 값으로 바꿉니다.
   - Codex만: `.codex-plugin/plugin.json`
   - Claude Code만: `.claude-plugin/plugin.json`
   - 양쪽 모두: 두 파일 모두 수정
2. `skills/` 아래 starter skill을 실제 skill로 교체합니다.
3. `commands/` 아래 help.md를 실제 커맨드로 교체하거나, 커맨드를 추가합니다.
4. 필요한 hook만 남기고 나머지는 제거합니다.
5. 필요한 경우에만 MCP server, app 매핑, script, asset을 추가합니다.

## 메모

- 이것은 완성된 plugin이 아니라 전체 골격입니다.
- 빈 디렉터리는 필요한 곳에 `.gitkeep`로 유지됩니다.
- hooks 형식은 두 플랫폼에서 호환되므로, 하나의 `hooks.json`으로 양쪽을 지원합니다.
- 단일 플랫폼만 지원할 경우 불필요한 매니페스트 디렉토리를 삭제해도 됩니다.

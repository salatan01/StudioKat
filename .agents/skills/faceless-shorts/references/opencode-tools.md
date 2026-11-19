# OpenCode tool map

`SKILL_DIR` is the directory containing `SKILL.md`. Every path below is relative to it.
There are no Claude-specific calls.

| Action | OpenCode tool |
|---|---|
| Read a file | `read` |
| Create or replace a file | `write` |
| Targeted edit | `edit` |
| Run a command | `shell` |
| Find files | `glob` |
| Search contents | `grep` |
| Fetch a URL | `webfetch` |
| Load this skill | `skill` with id `faceless-shorts` |
| Zapier publishing | `execute` with `tools.zapier.*` |

Path rules:

- Always use `SKILL_DIR/...` for skill files and `projects/<id>/faceless/...` for a project.
- Never write to `~/faceless-shorts/` from an OpenMontage pipeline. The adapter owns the workspace path.
- The browser is resolved from `CHROME`, `HYPERFRAMES_BROWSER_PATH`, or `REMOTION_BROWSER_EXECUTABLE`.
- To preview a project, use `xdg-open`/`open`, or return the local path.

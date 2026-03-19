---
name: batch-install-robotics-skills
description: Batch installs robotics skill repositories into ~/.cursor/skills with PowerShell (Windows) or Bash (Mac/Linux). Use when the user asks to clone multiple Cursor skills from GitHub, set up robotics skills in one run, or refresh installed skill repos.
---

# Batch Install Robotics Skills

## Purpose
Install or update a fixed set of robotics-related skill repositories under `~/.cursor/skills`.

## Use This Skill When
- The user provides multiple GitHub skill repositories to clone.
- The user asks to set up Cursor skills in one batch.
- The user wants to update already installed skill repositories.

## Repository List
This skill installs the following repositories:

1. `https://github.com/anthropics/skills.git`
2. `https://github.com/composiohq/composio.git`
3. `https://github.com/microsoft/promptflow-skills.git`
4. `https://github.com/run-llama/llama-lab-skills.git`
5. `https://github.com/ollama/ollama-skills.git`
6. `https://github.com/huggingface/skills.git`
7. `https://github.com/jmorgancusick/robotics-skills.git`
8. `https://github.com/anthonyjcrane/robotics-control-skills.git`
9. `https://github.com/ndrwn/cursor-robotics-skills.git`
10. `https://github.com/neuromorphics/robotics-skills.git`

## Preconditions
1. `git` is available in PATH.
2. Network access to GitHub is available.
3. Cursor uses personal skills from `~/.cursor/skills`.

## Execute (Windows, PowerShell)
Run from this skill folder:

```powershell
powershell -ExecutionPolicy Bypass -File "./scripts/install-robotics-skills.ps1"
```

Optional update mode (pull existing repos):

```powershell
powershell -ExecutionPolicy Bypass -File "./scripts/install-robotics-skills.ps1" -Update
```

## Execute (Mac/Linux, Bash)
Run from this skill folder:

```bash
bash "./scripts/install-robotics-skills.sh"
```

Optional update mode:

```bash
bash "./scripts/install-robotics-skills.sh" --update
```

## Output Semantics
- `OK`: clone or update succeeded.
- `SKIP`: directory already exists and update is not requested.
- `FAIL`: clone/update failed; check URL, permission, or network.

## Notes
- Do not install into `~/.cursor/skills-cursor/`.
- Restart Cursor after install so newly added skills are discovered.
- Scripts are UTF-8 friendly for readable non-ASCII output.

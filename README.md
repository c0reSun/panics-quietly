# claude-statusline

A conversational, newbie-friendly **statusline configurator for [Claude Code](https://claude.com/claude-code)**. Instead of a config file you edit blind, an AI walks you through what to show — explaining when each indicator is useful and when it's just noise — then writes the config for you.

![deps](https://img.shields.io/badge/deps-python3%20only-brightgreen)
![tested](https://img.shields.io/badge/tested-on%20exactly%20one%20Mac-yellow)
![QA](https://img.shields.io/badge/QA-vibes%20%2B%20a%20sandbox-orange)
![license](https://img.shields.io/badge/license-MIT-blue)

```
ctx [██░░░░░░░░░░] .18/1 | 5h [███|█▓▓▓▓▓▓▓] 48% Δ-1:33 ⏷3:20 | 7d [█|▒▒▒▒▒░░░░░] 9% ⏷5d22 | Opus 4.8 · high~
```

## What it does

- **Context gauge** — bar + tokens used / window limit (in millions): `.18/1`.
- **Rate-limit windows (5h / 7d)** with a real forecast:
  - `|` **pace marker** — where you'd be if you spent evenly over time.
  - **projection zone** — `▒` projected use within budget, `▓` red if you'll blow the limit.
  - `Δ-1:33` — *how long you'll sit blocked* if you keep this pace (only shows when you're ahead; silent when safe).
  - `⏷3:20` — time until the window resets.
- **model · effort** — live effort is muted-gold with a `~` when it's `auto` (fluid), bright when pinned.

Everything is read from the Claude Code statusline JSON payload. **The only dependency is `python3`** — no external tools, no hardcoded paths, no OS specifics.

## Install

```sh
git clone https://github.com/<you>/claude-statusline ~/.claude/skills/statusline
```

Then in Claude Code:

```
/statusline
```

The skill detects your environment, does a glyph check (so it can fall back to ASCII bars if your terminal/font can't render `█ ▒ ░ ⏷ Δ`), offers three presets with live previews, and writes everything for you. The status bar updates on the next refresh — no restart.

## Presets

| preset | shows |
|---|---|
| **minimal** | context + model |
| **balanced** *(recommended for newcomers)* | context + one limit window + model |
| **full** | context + 5h & 7d with pace/projection/Δ forecast + model · effort |

## Manual use (no conversation)

```sh
# switch profile
python3 ~/.claude/skills/statusline/scripts/apply.py --profile minimal
# restore whatever statusline you had before
python3 ~/.claude/skills/statusline/scripts/apply.py --restore-previous
# preview any profile with synthetic data
python3 ~/.claude/skills/statusline/engine.py --demo --profile full
```

Profiles are plain, commented `.conf` files in `~/.claude/statusline/profiles/` — edit them by hand anytime. Every choice is just information, never a lock-in.

## How it works

A stable **engine** (`engine.py`) renders an active **declarative manifest** (the profile) on every frame. Switching profiles is a pointer change, not a regenerate. The manifest reserves a `rules:` section for future context-based auto-switching (not built yet). Design notes: [SPEC.md](SPEC.md). Indicator explanations: [CATALOG.md](CATALOG.md).

## Heads-up

- The interactive prompts come in **English or Українська** — the skill asks which at the start. Code, manifests, and docs are English-canonical.
- **QA disclaimer, honestly:** tested on exactly one Mac, by hand, in a sandbox, with a lot of `| sed 's/\x1b\[[0-9;]*m//g'`. No CI, no unit tests. It degrades to empty output rather than breaking your terminal, but: works-on-my-machine™. Issues and PRs welcome.

## License

[MIT](LICENSE)

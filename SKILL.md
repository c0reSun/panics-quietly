---
name: statusline
description: AI-driven, newbie-friendly configurator for the Claude Code statusline (status bar). Walks anyone through choosing what to show via conversation, explains when each indicator is useful vs noise, renders live previews, and writes the config. Use when the user wants to set up, customize, change, simplify, or explain their statusline / status bar, pick indicators, switch profiles, restore their old bar, or runs /statusline.
---

# statusline

Conversational, reversible statusline setup. One stable engine renders a declarative
profile each frame, reading everything from the Claude Code JSON payload (only `python3`
needed). Full design: see [SPEC.md](SPEC.md). Indicator explanations: [CATALOG.md](CATALOG.md).

**Language:** first ask which language to use — **English** or **Українська** — then run
the entire conversation (greetings, glyph-check, preset names, every question, and the
CATALOG explanations) in that language. The skill's files are English-canonical; you are
fluent in both, so localize on the fly.

**Tone throughout:** every choice is *just information, never a lock-in*. Remind the user
they can pick "describe my own", re-run `/statusline`, switch profiles, or hand-edit the
`.conf` files anytime. Mark a recommended option in each question.

## Commands you use

- Preview a profile (synthetic data, looks alive):
  `python3 engine.py --demo --profile <minimal|balanced|full|custom> [--ascii]`
- Apply: `python3 scripts/apply.py --profile <name> [--glyphs unicode|ascii]`
- Restore the user's old bar: `python3 scripts/apply.py --restore-previous`

Paths are relative to this skill dir. State (active profile, editable `profiles/*.conf`,
`state.json`, backups) lives in `~/.claude/statusline/`.

## Workflow

1. **Pick language.** Ask once (single-select): **English** or **Українська**. Do everything
   after this in that language. Files are English-canonical; localize output on the fly.

2. **Detect environment, quietly.** Confirm `python3` exists (`command -v python3`). If
   missing, say plainly it's required and how to install; stop. Note the OS only if needed.

3. **Glyph-check through the user's eyes** (the script can't see their font). Print the test
   row and ask whether every symbol renders sharply (not boxes / `?`):
   `… →  █ ▒ ░ | ⏷ Δ`
   (EN: "Do you see all of these clearly?" · UA: "Бачиш усі ці символи чітко?")
   If any don't render → pass `--glyphs ascii` everywhere below.

4. **Greet in 2 lines:** what a statusline is, and that every choice is reversible info.

5. **Offer 3 presets** with live previews rendered by the engine (show each, colorized):
   - **minimal** — quiet, nothing scary.
   - **balanced** *(recommend to newcomers)* — context + one limit window.
   - **full** — full pace/projection/Δ forecast.
   Single-select question; show the rendered line for each as the preview.

6. **Optional drill-in.** If they want to tweak individual indicators, explain each from
   CATALOG.md (what / why / when it's noise), default to the preset's choice. Write their
   custom selection to `~/.claude/statusline/profiles/custom.conf` (copy a preset, toggle
   lines, keep the inline comments) and apply `--profile custom`. If they mention wanting
   different bars per project/model, offer `rule:` lines (syntax in CATALOG.md) — add them
   to their active profile's `.conf`.

7. **Final preview → confirm → apply.** Run `apply.py`. It backs up any existing bar as
   the restorable `previous` config before switching. Tell them the bar updates on the next
   refresh (no restart) and how to change later: re-run `/statusline`, edit the `.conf`, or
   `apply.py --restore-previous`.

8. **Remember.** `apply.py` records the active/chosen profile in `state.json`. If the user
   rejects something or you hit friction (a confusing step, a manual fix after), append a
   short note to `state.json` (`rejected` / `friction`) so the next run doesn't re-ask.

## Notes

- Never break the bar: the engine degrades to empty output on any error, and falls back to
  a built-in `balanced`-style config if a manifest is missing.
- `rule:` lines in manifests auto-switch profiles by context (`dir=` path prefix,
  `model=` substring; first match wins, no chaining). Presets ship them commented out.
- v1 scope is the statusline only. Don't touch other settings, skills, or CLAUDE.md.

# CLAUDE.md — Panics Quietly

Conversational statusline configurator for Claude Code. The slash command is `/statusline`.

## Layout

- `engine.py` — the stable renderer. Reads the statusline JSON payload from stdin, renders
  the active profile manifest. **python3 is the only dependency** — keep it that way.
- `engine.sh` — thin wrapper; finds python3, exits silently if missing.
- `profiles/*.conf` — shipped presets (minimal / balanced / full). Seeded once into
  `~/.claude/statusline/profiles/` by `scripts/apply.py`; after that they belong to the
  user — never overwrite seeded copies.
- `SKILL.md` — the conversation flow. `CATALOG.md` — indicator explanations (the script the
  AI localizes from). `SPEC.md` — design decisions (Ukrainian).

## Rules

- **Never break the bar.** Any error path must degrade to empty output, never a traceback.
  Missing profile → built-in fallback. Missing JSON fields → hide the section.
- Files are English-canonical (except SPEC.md). The conversation is bilingual (EN/UA),
  localized live from the canonical texts — don't fork translated copies of files.
- Don't write outside `~/.claude/statusline/` and the `statusLine` key in
  `~/.claude/settings.json`.
- `rule:` lines in manifests auto-switch profiles (`dir=` path prefix, `model=` substring;
  first match wins, no chaining). Presets ship them commented out.

## Testing

```sh
python3 engine.py --demo --profile full          # synthetic preview
python3 engine.py --demo --profile full --ascii  # ASCII fallback
echo '{}' | python3 engine.py                    # must print empty, not crash
# strip colors for eyeballing: ... | sed 's/\x1b\[[0-9;]*m//g'
```

No CI yet — test the demo profiles and the empty-payload path by hand before committing.

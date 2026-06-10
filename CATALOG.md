# Indicator catalog

Plain-language explanations for the `/statusline` conversation. For each indicator:
*what it is / why it helps / when it's noise*. Keys in parentheses are the names used in the
`.conf` manifest. Deliver these to the user in the language they chose (translate as needed).

## Context

**ctx bar + tokens** `[█░░░] .11/1` *(key `ctx`, param `tokens`)*
How much of the context window is used, and the full window size (in millions of tokens).
Why: see when you're getting close to compaction. When it's noise: almost never — this is
the baseline.

**ctx %** *(key `ctx_pct`)*
The same thing as a percentage. When it's noise: duplicates the bar and the token count →
off by default.

## Cost

**$ cost** `$1.23` *(key `cost`)*
Money spent this session. Why: keep an eye on spend. When it's noise: on a flat-rate /
subscription plan it doesn't matter.

## Plan limits (windows)

**5h / 7d limit — bar + %** `5h [████] 48%` *(keys `limit_5h`, `limit_7d`)*
How much of your plan quota you've used in the last 5 hours / 7 days. Why: don't slam into
the ceiling. When it's noise: if you're always far from the limit. 7d is often overkill for
newcomers.

Window params:

- **marker** `|` — where you'd be if you spent evenly over time. Tells you at a glance
  whether you're ahead or behind. Green = within pace, red = ahead. *Noise:* confusing to a
  newcomer without explanation.
- **projection** `▒ / ▓` — where you'll end up at the current rate. Grey `▒` = projected use
  within budget, red `▓` = you'll blow the limit. *Noise:* advanced for a newcomer.
- **delta** `Δ-1:20` — how long you'll sit blocked if you exhaust the window at this rate.
  The most actionable number — it names the consequence. Shows only when you're ahead;
  silent when safe. *Noise:* if you rarely hit the ceiling.
- **reset** `⏷3:21` — when the window resets. Why: know how long to wait.

## Right side

**model** `Opus 4.8` *(key `model`)*
Which model is active. Why: confirmation. When it's noise: rarely changes.

**effort** `high~` *(key `effort`)*
The effort level. Shows the **live** level of the current session (from the JSON payload),
not just the configured default. Auto marker: if the default is `auto`, the level is
**fluid** (the model picked it, may change) → muted gold with a tilde `high~`. If it's
pinned (`/effort high`) → bright `high`, no marker. Why: see both what's running now and
whether it's temporary. When it's noise: if you don't use effort.

## Glyphs

**glyphs** `unicode | ascii`
`unicode` — nice blocks `█▒░⏷Δ`. `ascii` — `#=-@!` for terminals/fonts that can't render
unicode (detected by the glyph-check, through the user's eyes).

## Auto-switching rules

**rule:** `rule: <condition> -> profile=<name>` *(lines in any profile `.conf`)*
Switch profiles automatically, checked on every render of the *active* profile. First
matching rule wins; the target profile's own rules are not followed (no chains, no loops).

- `rule: model=haiku -> profile=minimal` — `model` is a case-insensitive substring of the
  model id/name. Why: a light model rarely needs the full forecast.
- `rule: dir=~/Projects/Work -> profile=full` — `dir` is a path-prefix match on the current
  workspace directory. Why: different projects, different dashboards.

When it's noise: if you always want the same bar — most people do; this is opt-in and the
presets ship with rules commented out.

#!/usr/bin/env python3
"""Statusline engine — renders the active manifest profile from the Claude Code
statusline JSON payload. Single dependency: python3. No external tools.

Usage:
  echo "$JSON" | engine.py                 # render active profile from stdin
  engine.py --demo --profile balanced      # render a preset with synthetic data
  engine.py --demo --profile full --ascii  # force ASCII glyphs (fallback)

State dir defaults to $HOME/.claude/statusline (override with --state DIR).
"""
import sys, os, json, time, argparse

RED = '\033[31m'; GRN = '\033[32m'; DIM = '\033[90m'
CYN = '\033[36m'; YLW = '\033[33m'; RST = '\033[0m'
DYL = '\033[38;5;136m'  # приглушене золото — auto-ефорт (колір лишається, але темніший)
EMP = '\033[38;5;238m'  # тьмяне порожнє — найслабша інтенсивність, відступає у фон

GLYPHS = {
    'unicode': dict(full='█', over='▓', safe='▒', empty='░', mark='|', reset='⏷', delta='Δ'),
    'ascii':   dict(full='#', over='+', safe='=', empty='-', mark='|', reset='@', delta='!'),
}

WINDOWS = {'limit_5h': ('five_hour', 18000), 'limit_7d': ('seven_day', 604800)}
RED_AT = 80  # ctx tokens turn red above this %


# ---------- manifest ----------
def load_manifest(path):
    """Parse `key = on/off params  # comment`. Returns {key: {'on':bool,'params':{...}}}
    plus '_glyphs' and '_rules' (parsed `rule:` lines, see parse_rule)."""
    cfg = {'_glyphs': 'unicode'}
    if not path or not os.path.exists(path):
        return None
    for raw in open(path, encoding='utf-8'):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if line.startswith('rule:'):
            r = parse_rule(line[5:])
            if r:
                cfg.setdefault('_rules', []).append(r)
            continue
        if line.startswith('rule'):     # bare `rules:` section header
            continue
        if '=' not in line:
            continue
        key, rest = (s.strip() for s in line.split('=', 1))
        toks = rest.split()
        if key == 'glyphs':
            cfg['_glyphs'] = toks[0] if toks else 'unicode'
            continue
        on = not toks or toks[0] not in ('off', 'no', '0', 'false')
        params = {}
        for t in toks:
            if t in ('on', 'off', 'yes', 'no', '0', '1', 'true', 'false'):
                continue
            if '=' in t:
                k, v = t.split('=', 1); params[k] = v
            else:
                params[t] = True
        cfg[key] = {'on': on, 'params': params}
    return cfg


# ---------- rules (auto-switching) ----------
def parse_rule(text):
    """`dir=~/path -> profile=name` or `model=substr -> profile=name` → (kind, value, profile)."""
    if '->' not in text:
        return None
    cond, target = (s.strip() for s in text.split('->', 1))
    if not target.startswith('profile=') or '=' not in cond:
        return None
    prof = target.split('=', 1)[1].strip()
    kind, val = (s.strip() for s in cond.split('=', 1))
    if kind not in ('dir', 'model') or not val or not prof:
        return None
    return (kind, val, prof)


def match_rules(rules, d):
    """First matching rule wins → target profile name, else None.
    dir = path-prefix match on the workspace dir; model = substring of id/display_name."""
    m = d.get('model') or {}
    model = (' '.join(str(m.get(k) or '') for k in ('id', 'display_name'))
             if isinstance(m, dict) else str(m)).lower()
    cwd = (d.get('workspace') or {}).get('current_dir') or d.get('cwd') or ''
    for kind, val, prof in rules:
        if kind == 'model' and val.lower() in model:
            return prof
        if kind == 'dir':
            want = os.path.expanduser(val).rstrip('/')
            if want and (cwd == want or cwd.startswith(want + '/')):
                return prof
    return None


# ---------- pieces ----------
def bar(pct, width, pace, g):
    """pace<0 → plain fill (ctx). Else: filled=█, marker=|, projection zone, empty."""
    pct = max(0, min(100, int(pct))); filled = pct * width // 100
    out = []
    if pace is not None and pace >= 0:
        pace_pos = pace * width // 100
        over = pct > pace
        proj = pct / pace * 100 if pace > 0 and pct > 0 else pct
        proj_pos = int(min(proj, 100) * width // 100)
        over_budget = proj > 100
        for i in range(width):
            if i == pace_pos:
                out.append((RED if over else GRN) + g['mark'] + RST)
            elif i < filled:
                out.append(g['full'])
            elif i < proj_pos:
                out.append((RED + g['over'] if over_budget else DIM + g['safe']) + RST)
            else:
                out.append(EMP + g['empty'] + RST)
    else:
        out = [g['full']] * filled + [EMP + g['empty'] + RST] * (width - filled)
    return '[' + ''.join(out) + ']'


def pct_str(pct):
    pct = int(pct)
    return f'{RED}{pct}%{RST}' if pct > RED_AT else f'{pct}%'


def delta(usage, pace, win, g):
    """Signed gap, shown only when ahead: how long you'll sit blocked. Silent if safe."""
    if pace <= 0 or usage <= 0:
        return ''
    ef = pace / 100.0
    gap = ef * (100 - usage) / usage - (1 - ef)
    if gap >= 0:
        return ''
    secs = int(-gap * win)
    if win >= 604800:
        dd, hh = secs // 86400, (secs % 86400) // 3600
        s = f'{dd}d{hh}' if dd else f'{hh}h'
    else:
        h, m = secs // 3600, (secs % 3600) // 60
        s = f'{h}:{m:02d}' if h else f':{m:02d}'
    return f' {RED}{g["delta"]}-{s}{RST}'


def fmt_reset(secs):
    if secs <= 0:
        return ''
    if secs >= 86400:
        return f'{secs // 86400}d{(secs % 86400) // 3600}'
    h, m = secs // 3600, (secs % 3600) // 60
    return f'{h}:{m:02d}' if h else f':{m:02d}'


def m_str(tokens, total=False):
    s = f'{tokens / 1e6:.2f}'
    if total:                       # total: drop trailing zeros (1.00→1, 0.20→.2)
        s = s.rstrip('0').rstrip('.') or '0'
    return s[1:] if s.startswith('0.') else s   # drop leading zero (.11)


# ---------- render ----------
def render(d, cfg):
    g = GLYPHS.get(cfg.get('_glyphs', 'unicode'), GLYPHS['unicode'])
    now = time.time()
    groups = []

    # ctx
    c = cfg.get('ctx')
    if c and c['on']:
        cw = d.get('context_window', {}) or {}
        pct = int(cw.get('used_percentage', 0) or 0)
        tot = int(cw.get('context_window_size', 0) or 0)
        cu = cw.get('current_usage', {}) or {}
        used = sum(int(cu.get(k, 0) or 0) for k in
                   ('input_tokens', 'output_tokens',
                    'cache_creation_input_tokens', 'cache_read_input_tokens'))
        width = int(c['params'].get('width', 12))
        part = f'ctx {bar(pct, width, None, g)}'
        if 'tokens' in c['params'] and (used or tot):
            um = m_str(used); tm = m_str(tot, total=True)
            um = f'{RED}{um}{RST}' if pct > RED_AT else um
            part += f' {um}/{tm}'
        elif cfg.get('ctx_pct', {}).get('on'):
            part += f' {pct_str(pct)}'
        groups.append(part)

    # cost
    cc = cfg.get('cost')
    if cc and cc['on']:
        cost = (d.get('cost', {}) or {}).get('total_cost_usd', 0) or 0
        if cost:
            groups.append(f'${cost:.2f}')

    # rate-limit windows
    rl = d.get('rate_limits', {}) or {}
    for key in ('limit_5h', 'limit_7d'):
        lc = cfg.get(key)
        if not (lc and lc['on']):
            continue
        field, win = WINDOWS[key]
        w = rl.get(field) or {}
        if not w:
            continue
        usage = int(w.get('used_percentage', 0) or 0)
        resets = float(w.get('resets_at', 0) or 0)
        pace = -1
        if resets > 0:
            elapsed = max(0, min(win, win - (resets - now)))
            pace = int(elapsed / win * 100)
        p = lc['params']
        width = int(p.get('width', 12))
        marker = pace if 'marker' in p else -1
        label = '5h' if key == 'limit_5h' else '7d'
        seg = f'{label} {bar(usage, width, marker if "projection" in p or "marker" in p else -1, g)} {pct_str(usage)}'
        if 'delta' in p:
            seg += delta(usage, pace, win, g)
        if 'reset' in p:
            rs = fmt_reset(int(resets - now)) if resets > 0 else ''
            if rs:
                seg += f' {g["reset"]}{rs}'
        groups.append(seg)

    # right side: model · effort
    right = []
    mc = cfg.get('model')
    if mc and mc['on']:
        m = d.get('model') or {}
        name = (m.get('display_name') or m.get('id') or '') if isinstance(m, dict) else str(m)
        name = name.replace('claude-', '').replace('-latest', '')
        if name:
            right.append(f'{CYN}{name}{RST}')
    ec = cfg.get('effort')
    if ec and ec['on']:
        live = d.get('effort')
        if isinstance(live, dict):
            live = live.get('level') or live.get('value') or ''
        try:
            default = open(os.path.expanduser('~/.claude/.effort')).read().strip()
        except OSError:
            default = ''
        is_auto = default in ('', 'auto')      # дефолт auto → рівень плинний
        eff = live or default
        if eff == 'auto':
            right.append(f'{DYL}auto{RST}')
        elif eff and is_auto:                  # auto обрав рівень: приглушене золото + ~
            right.append(f'{DYL}{eff}~{RST}')
        elif eff:                              # закріплений рівень: яскравий
            right.append(f'{YLW}{eff}{RST}')
    if right:
        groups.append(f' {DIM}·{RST} '.join(right))

    return ' | '.join(groups)


# ---------- demo data ----------
def demo_json():
    now = time.time()
    return {
        'context_window': {
            'used_percentage': 11, 'context_window_size': 1000000,
            'current_usage': {'input_tokens': 2, 'output_tokens': 1655,
                              'cache_creation_input_tokens': 79,
                              'cache_read_input_tokens': 108000},
        },
        'rate_limits': {
            'five_hour':  {'used_percentage': 48, 'resets_at': now + 12060},  # ahead → Δ
            'seven_day':  {'used_percentage': 9,  'resets_at': now + 514080},  # safe
        },
        'cost': {'total_cost_usd': 1.23},
        'model': {'display_name': 'Opus 4.8'},
        'effort': 'auto',
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile')
    ap.add_argument('--state', default=os.path.expanduser('~/.claude/statusline'))
    ap.add_argument('--demo', action='store_true')
    ap.add_argument('--ascii', action='store_true')
    args = ap.parse_args()

    d = demo_json() if args.demo else _read_stdin()

    name = args.profile
    if not name:
        try:
            name = open(os.path.join(args.state, 'active')).read().strip()
        except OSError:
            name = 'balanced'
    cfg = load_manifest(os.path.join(args.state, 'profiles', f'{name}.conf'))
    if cfg is None:
        cfg = _builtin(name)
    target = match_rules(cfg.get('_rules', []), d)
    if target and target != name:        # redirect once; target's own rules are not followed
        cfg = (load_manifest(os.path.join(args.state, 'profiles', f'{target}.conf'))
               or _builtin(target))
        cfg.pop('_rules', None)
    if args.ascii:
        cfg['_glyphs'] = 'ascii'

    try:
        print(render(d, cfg))
    except Exception:
        # never break the user's terminal — degrade to nothing
        print('')


def _read_stdin():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _builtin(name):
    """Fallback configs if manifest files are missing — bar never breaks."""
    base = {'_glyphs': 'unicode'}
    full = {
        **base,
        'ctx': {'on': True, 'params': {'width': '12', 'tokens': True}},
        'limit_5h': {'on': True, 'params': {'width': '12', 'marker': True,
                     'projection': True, 'delta': True, 'reset': True}},
        'limit_7d': {'on': True, 'params': {'width': '12', 'marker': True,
                     'projection': True, 'delta': True, 'reset': True}},
        'model': {'on': True, 'params': {}}, 'effort': {'on': True, 'params': {}},
    }
    if name == 'minimal':
        return {**base, 'ctx': {'on': True, 'params': {'width': '12', 'tokens': True}},
                'model': {'on': True, 'params': {}}}
    if name == 'balanced':
        return {**base, 'ctx': {'on': True, 'params': {'width': '12', 'tokens': True}},
                'limit_5h': {'on': True, 'params': {'width': '12', 'reset': True}},
                'model': {'on': True, 'params': {}}}
    return full


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Deterministic apply step for the /statusline skill.

- seeds the 3 preset manifests into the state dir (once),
- backs up any existing statusLine command as the `previous` profile,
- sets the active profile (optionally patching its glyph mode),
- points settings.json `statusLine.command` at the engine,
- records memory in state.json.

Usage:
  apply.py --profile balanced [--glyphs ascii]
  apply.py --restore-previous
"""
import sys, os, json, shutil, time, argparse

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser('~')
STATE = os.path.join(HOME, '.claude', 'statusline')
SETTINGS = os.path.join(HOME, '.claude', 'settings.json')
ENGINE = os.path.join(SKILL, 'engine.sh')
PRESETS = ('minimal', 'balanced', 'full')


def ensure_dirs():
    for d in (STATE, os.path.join(STATE, 'profiles'), os.path.join(STATE, 'backups')):
        os.makedirs(d, exist_ok=True)


def seed_presets():
    """Copy shipped presets into state once, so user edits persist and skill
    updates never clobber them."""
    for name in PRESETS:
        dst = os.path.join(STATE, 'profiles', f'{name}.conf')
        if not os.path.exists(dst):
            src = os.path.join(SKILL, 'profiles', f'{name}.conf')
            if os.path.exists(src):
                shutil.copy2(src, dst)


def load_settings():
    if os.path.exists(SETTINGS):
        try:
            return json.load(open(SETTINGS))
        except Exception:
            return {}
    return {}


def save_settings(s):
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    if os.path.exists(SETTINGS):
        shutil.copy2(SETTINGS, os.path.join(STATE, 'backups',
                     f'settings.json.{int(time.time())}'))
    json.dump(s, open(SETTINGS, 'w'), indent=2, ensure_ascii=False)
    open(SETTINGS, 'a').write('\n')


def load_state():
    p = os.path.join(STATE, 'state.json')
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception:
            pass
    return {'active': None, 'chosen': [], 'rejected': [], 'friction': []}


def save_state(st):
    json.dump(st, open(os.path.join(STATE, 'state.json'), 'w'),
              indent=2, ensure_ascii=False)


def backup_previous(settings):
    """If an existing statusLine command isn't already ours, preserve it so the
    user can restore their old bar (`previous` profile = restore old command)."""
    cmd = (settings.get('statusLine') or {}).get('command', '')
    if not cmd or 'statusline/engine' in cmd:
        return None
    ts = int(time.time())
    info = {'command': cmd, 'saved_at': ts}
    # copy the referenced script file if it's a local path we can find
    for tok in cmd.split():
        if os.path.exists(tok) and os.path.isfile(tok):
            dst = os.path.join(STATE, 'backups', f'{os.path.basename(tok)}.{ts}')
            shutil.copy2(tok, dst)
            info['script_backup'] = dst
            break
    json.dump(info, open(os.path.join(STATE, 'backups', 'previous.command'), 'w'),
              indent=2)
    return info


def patch_glyphs(name, glyphs):
    path = os.path.join(STATE, 'profiles', f'{name}.conf')
    if not os.path.exists(path):
        return
    lines, found = [], False
    for line in open(path, encoding='utf-8'):
        if line.split('#', 1)[0].strip().startswith('glyphs'):
            lines.append(f'glyphs = {glyphs}\n'); found = True
        else:
            lines.append(line)
    if not found:
        lines.insert(0, f'glyphs = {glyphs}\n')
    open(path, 'w', encoding='utf-8').writelines(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile')
    ap.add_argument('--glyphs', choices=['unicode', 'ascii'])
    ap.add_argument('--restore-previous', action='store_true')
    args = ap.parse_args()

    ensure_dirs()
    seed_presets()
    settings = load_settings()
    st = load_state()

    if args.restore_previous:
        prev = os.path.join(STATE, 'backups', 'previous.command')
        if not os.path.exists(prev):
            print('No previous statusline saved.'); return
        info = json.load(open(prev))
        settings.setdefault('statusLine', {})['type'] = 'command'
        settings['statusLine']['command'] = info['command']
        save_settings(settings)
        print(f'Restored previous statusline: {info["command"]}')
        return

    if not args.profile:
        print('--profile required'); sys.exit(1)

    prev = backup_previous(settings)
    if args.glyphs:
        patch_glyphs(args.profile, args.glyphs)

    open(os.path.join(STATE, 'active'), 'w').write(args.profile + '\n')
    settings.setdefault('statusLine', {})['type'] = 'command'
    settings['statusLine']['command'] = f'bash {ENGINE}'
    save_settings(settings)

    st['active'] = args.profile
    if args.profile not in st['chosen']:
        st['chosen'].append(args.profile)
    if prev:
        st['previous_backup'] = prev
    save_state(st)

    print(f'Applied profile "{args.profile}". statusLine.command -> bash {ENGINE}')
    if prev:
        print(f'Previous bar saved (restore with: apply.py --restore-previous)')


if __name__ == '__main__':
    main()

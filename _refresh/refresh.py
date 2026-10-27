#!/usr/bin/env python3
"""KP Zero Dose dashboard - data refresh orchestrator.

  python _refresh/refresh.py status
  python _refresh/refresh.py run [--only chd,snd,icm] [--dry-run] [--force] [--no-stamp] [--note TEXT]
  python _refresh/refresh.py inject --const ZD --from payload.json [--dry-run] [--note TEXT]
  python _refresh/refresh.py publish [--message TEXT]

`run` re-extracts every file-based dataset whose source export is newer than the last
applied refresh, swaps the embedded JSON payload in all four dashboard variants,
bumps the PKT timestamps, appends a version.txt note and (with --publish) commits,
pushes and verifies the GitHub Pages build.

`--publish` only commits what this script wrote. Every payload is one `const NAME = ...` line, so a
run touches one line per dataset plus the visible `Updated ...` stamp chip; if a variant carries any
other changed line, the publish is refused (exit 3) and the files stay on disk uncommitted - a
scheduled refresh will not carry a hand-edited feature out under a data-refresh message.
`--allow-pending` says you mean it.

Login-gated portals (NEOC, IDIMS, EPI-MIS web) are never fetched by this script and no
credentials are read, stored or prompted for. See SOURCES.md.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

PY = sys.executable
SIZE_FLOOR, SIZE_CEIL = 0.2, 5.0
PKT = datetime.timezone(datetime.timedelta(hours=5), 'PKT')


def sh(args, cwd=None, quiet=False):
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       shell=(os.name == 'nt' and isinstance(args, str)))
    out = p.stdout.decode('utf-8', 'replace')
    if not quiet:
        sys.stdout.write(out)
    return p.returncode, out


def pkt_now():
    return datetime.datetime.now(PKT)


# ---------------------------------------------------------------- status

def source_line(entry):
    rec = srcutil.newest(entry)
    if not rec:
        return None, 'no matching file found'
    size = ('%.1f MB' % (rec['size'] / 1048576.0)) if rec['size'] >= 1048576 else ('%.0f KB' % (rec['size'] / 1024.0))
    return rec, '%s  (%s, %s)' % (rec['path'], srcutil.mtime_str(rec), size)


def payload_would_change(ds, e, rec, head):
    """Regenerate this payload into a throwaway file and compare it with the embedded one.

    A file-id mismatch alone proves nothing: a year-to-date export can never feed the monthly
    archive, and a dataset injected from out/*.json records that path instead of the export it
    was built from, so both look stale for ever. Only a payload that actually differs is stale.
    """
    out_path = os.path.join(srcutil.OUT, 'probe_%s.json' % e['const'].lower())
    try:
        extract(ds, e, out_path, rec['path'])
        fresh = srcutil.read_text(out_path).strip()
        json.loads(fresh)
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)
    return fresh != dashpatch.get_payload(head, e['const']).strip()


def applied_after(last, rec):
    """True when the recorded apply happened at or after this file was written.

    A refresh driven from a generated out/<const>.json records that path, not the export behind
    it, so its file id can never match a discovered file and the dataset would look stale for
    ever. Wall-clock order is the honest cheap test for those.
    """
    at = (last or {}).get('at') or ''
    try:
        when = datetime.datetime.strptime(at[:16], '%Y-%m-%dT%H:%M')
    except ValueError:
        return False
    return when >= datetime.datetime.fromtimestamp(rec['mtime'])


def deep_verdict(ds, e, rec, head):
    """Never let a probe failure masquerade as a verdict about the data."""
    try:
        changed = payload_would_change(ds, e, rec, head)
    except Exception as ex:
        why = (str(ex).strip().splitlines() or [ex.__class__.__name__])[-1]
        return 'DEEP CHECK FAILED - %s' % why[:110]
    return 'STALE - payload would change' if changed else 'up to date (newest export adds nothing)'


def cmd_status(cfg, a):
    st = srcutil.load_state()
    now = pkt_now()
    rows = []
    print('KP Zero Dose dashboard - source status   (%s PKT)' % now.strftime('%d-%b-%Y %H:%M'))
    print('repo: %s' % cfg['repo'])
    head = srcutil.read_text(os.path.join(cfg['repo'], 'index.html'))
    print('embedded stamp: %s' % _stamp_of(head))
    print('')
    print('AUTO (refresh.py run can update these)')
    for ds, e in cfg['auto'].items():
        rec, desc = source_line(e)
        last = st['datasets'].get(ds)
        fid = srcutil.file_id(rec)
        if last is None:
            verdict = 'NEVER APPLIED'
        elif last.get('file_id') == fid:
            verdict = 'up to date'
        elif a.deep and rec:
            verdict = deep_verdict(ds, e, rec, head)
        elif rec and applied_after(last, rec):
            verdict = 'up to date (applied after this export)'
        else:
            verdict = 'NEWER FILE THAN LAST APPLY - run status --deep to check the payload'
        payload = dashpatch.get_payload(head, e['const'])
        rows.append((ds, e, rec, verdict))
        print('  %-4s %-8s %-46s %s' % (ds, e['const'], e['label'][:46], verdict))
        print('       source : %s' % (desc or '-'))
        if last:
            print('       applied: %s PKT from %s (%s chars)' % (
                last.get('at', '?')[:16], os.path.basename(last.get('source', {}).get('path', '?')),
                format(last.get('chars', 0), ',')))
        print('       payload: %s chars embedded' % format(len(payload), ','))
    print('')
    print('MANUAL (export from the portal, then inject - never auto-fetched)')
    for ds, e in cfg['manual'].items():
        rec, desc = source_line(e) if (e.get('roots') and e.get('patterns')) else (None, 'in-dashboard import')
        consts = ','.join(e.get('const') or []) or 'localStorage'
        print('  %-6s %-18s %s' % (ds, consts, e['label']))
        print('         portal : %s' % e.get('portal', '-'))
        if desc:
            print('         newest : %s' % desc)
        print('         howto  : %s' % e.get('howto', '-'))
    print('')
    stale = [r[0] for r in rows if r[3].startswith(('STALE', 'NEWER FILE')) or r[3] == 'NEVER APPLIED']
    print('next: %s' % ('python _refresh/refresh.py run --only %s' % ','.join(stale) if stale
                         else 'all auto sources up to date - nothing to refresh'))
    if any(r[3].startswith('NEWER FILE') for r in rows):
        print('     python _refresh/refresh.py status --deep  regenerates those payloads and reports only '
              'the ones that actually differ')
    if a.json:
        print(json.dumps({'auto': [{'id': r[0], 'verdict': r[3],
                                    'source': r[2]} for r in rows]}, default=str, indent=1))
    return 0


def _stamp_of(text):
    m = re.search(r'Updated ' + dashpatch.STAMP_RE, text)
    return m.group(1) if m else '?'


# ---------------------------------------------------------------- run

def extract(ds, entry, out_path, source=None):
    script = os.path.join(srcutil.HERE, entry['extractor'])
    args = [PY, script, '--out', out_path]
    if source:
        args += ['--source', source]
    print('# extracting %s from %s ...' % (ds, os.path.basename(source) if source else 'newest match'))
    rc, out = sh(args)
    if rc != 0:
        raise RuntimeError('extractor %s failed (rc=%d):\n%s' % (entry['extractor'], rc, out))
    summary = ''
    for line in out.splitlines():
        if line.startswith('OK %s ' % ds):
            summary = line.split(' ', 3)[3] if line.count(' ') >= 3 else ''
    return summary.strip(), out


def cmd_run(cfg, a):
    st = srcutil.load_state()
    only = [x.strip() for x in a.only.split(',')] if a.only else list(cfg['auto'])
    bad = [x for x in only if x not in cfg['auto']]
    if bad:
        raise SystemExit('unknown dataset(s) %s - auto datasets are %s' % (bad, list(cfg['auto'])))

    todo, skipped = [], []
    for ds in only:
        e = cfg['auto'][ds]
        if a.source:
            if len(only) != 1:
                raise SystemExit('--source needs a single dataset: use --only %s' % ds)
            if not os.path.exists(a.source):
                raise SystemExit('--source file not found: %s' % a.source)
            rec = srcutil.stat_rec(a.source)
        else:
            rec = srcutil.newest(e)
        if not rec:
            skipped.append((ds, 'no source file found under %s' % e['roots']))
            continue
        last = st['datasets'].get(ds)
        if last and last.get('file_id') == srcutil.file_id(rec) and not a.force:
            skipped.append((ds, 'source unchanged since %s' % (last.get('at', '?')[:16])))
            continue
        todo.append((ds, e, rec, last))

    print('refresh: %d to extract, %d skipped' % (len(todo), len(skipped)))
    for ds, why in skipped:
        print('  skip %-4s %s' % (ds, why))
    if not todo:
        print('NOTHING_TO_DO')
        return 0

    payloads = {}
    for ds, e, rec, last in todo:
        out_path = os.path.join(srcutil.OUT, e['const'].lower() + '.json')
        summary, raw = extract(ds, e, out_path, rec['path'])
        rec = _used_rec(ds, raw, rec)
        js = srcutil.read_text(out_path).strip()
        json.loads(js)
        payloads[ds] = {'const': e['const'], 'json': js, 'summary': summary,
                        'rec': rec, 'path': out_path, 'srcs': _src_names(ds, raw)}
        print('  %-4s %-6s %9s chars  %s' % (ds, e['const'], format(len(js), ','), summary))

    _, vs = dashpatch.load_variants(cfg)
    changed = []
    for ds, p in payloads.items():
        old = dashpatch.get_payload(vs[0].text, p['const'])
        ratio = len(p['json']) / float(max(len(old), 1))
        if not (SIZE_FLOOR <= ratio <= SIZE_CEIL) and not a.force:
            raise SystemExit('ABORT: %s payload would change from %s to %s chars (%.2fx) - '
                             'outside the %.1f-%.1fx safety window. Re-run with --force if intended.'
                             % (p['const'], format(len(old), ','), format(len(p['json']), ','),
                                ratio, SIZE_FLOOR, SIZE_CEIL))
        n = 0
        for v in vs:
            if dashpatch.swap_payload(v, p['const'], p['json']):
                n += 1
        if n:
            changed.append(ds)
            print('  swap %-6s in %d/%d variants' % (p['const'], n, len(vs)))
        else:
            print('  swap %-6s: payload already identical (no change)' % p['const'])

    if not changed:
        print('NO_CHANGE (all regenerated payloads are byte-identical to what is embedded)')
        for ds, p in payloads.items():
            st['datasets'][ds] = _state_entry(p, _stamp_of(vs[0].text))
        if not a.dry_run:
            srcutil.save_state(st)
        return 0

    old_stamp = dashpatch.get_stamp(vs[0])
    new_stamp = old_stamp if a.no_stamp else dashpatch.pkt_stamp(pkt_now())
    for v in vs:
        v.require(dashpatch.get_stamp(v) == old_stamp, 'stamp mismatch across variants')
        if not a.no_stamp:
            dashpatch.set_stamp(v, new_stamp, old_stamp)
    dashpatch.commit_variants(vs)
    sums = dashpatch.check_identical(cfg, vs)

    note = a.note or _auto_note(changed, payloads, new_stamp, old_stamp)
    print('')
    print('variants:')
    for v in vs:
        print('  %-42s %+8d chars  %s' % (v.rel, v.delta(), '; '.join(v.changes) or 'unchanged'))
    print('identical group md5: %s' % sums)
    print('stamp: %s -> %s' % (old_stamp, new_stamp))
    print('version note: %s' % note[:160])

    if a.dry_run:
        print('')
        print('DRY RUN - nothing written')
        return 0

    dashpatch.write_variants(vs)
    touched = dashpatch.append_version(cfg, note)
    for ds in changed:
        st['datasets'][ds] = _state_entry(payloads[ds], new_stamp)
    st['last_run'] = {'at': pkt_now().isoformat(timespec='seconds'), 'datasets': changed,
                      'stamp': new_stamp, 'dry_run': False}
    srcutil.save_state(st)
    print('')
    for v in vs:
        print('WROTE %s (%s bytes)' % (v.rel, format(os.path.getsize(v.path), ',')))
    for p in touched:
        print('WROTE %s' % os.path.relpath(p, cfg['repo']))
    print('REFRESHED %s' % ','.join(changed))
    if a.publish:
        return publish(cfg, a, changed, new_stamp)
    print('next: review, then  python _refresh/refresh.py publish')
    return 0


def _src_paths(ds, raw):
    """Paths the extractor reported reading on its `SRC <ds> <slot> <path>` lines.

    Extractors decorate the tail in different ways (`(4 files)`, a summary after two spaces, a
    second path after a pipe), so only a bare trailing count is removed here; anything that is not
    one real path stays out of the list and out of the caller that trusts it."""
    paths = []
    for line in (raw or '').splitlines():
        if line.startswith('SRC %s ' % ds):
            parts = line.split(' ', 3)
            if len(parts) == 4:
                p = re.sub(r'\s+\([^)]*\)$', '', parts[3].strip())
                if p and p not in paths:
                    paths.append(p)
    return [p for p in paths if len(p.split(' | ')) == 1]


def _skipped(ds, raw):
    """Whether the extractor named a source file it refused to use (`SKIP <ds> ...`)."""
    return any(l.startswith('SKIP %s ' % ds) for l in (raw or '').splitlines())


def _used_rec(ds, raw, rec):
    """Credit the file actually read when the extractor walked back past a newer one.

    The portal saves the SNID Sept 2026 round both UC-wise and as a district roll-up under one name
    pattern; the newest match on disk can therefore be a file the extractor skipped, and recording
    it as the source of a payload built from the table it refused would miscredit the round. Only
    single-path reports that name a skip qualify - multi-file datasets report one of several paths.
    """
    if rec is None or not _skipped(ds, raw):
        return rec
    paths = [p for p in _src_paths(ds, raw) if os.path.isfile(p)]
    if len(paths) == 1 and os.path.normcase(paths[0]) != os.path.normcase(rec['path']):
        return srcutil.stat_rec(paths[0])
    return rec


def _src_names(ds, raw):
    """Basenames of every file the extractor reported reading (`SRC <ds> <slot> <path>`).

    Without this a multi-source dataset is credited in version.txt to whichever single
    file happened to be newest on disk."""
    return list(dict.fromkeys(os.path.basename(p) for p in _src_paths(ds, raw)))


def _state_entry(p, stamp):
    rec = p['rec']
    return {'source': {'path': rec['path'], 'name': os.path.basename(rec['path']),
                       'mtime': rec.get('mtime', 0), 'size': rec.get('size', 0)},
            'file_id': srcutil.file_id(rec),
            'payload_sha1': srcutil.sha1_text(p['json']),
            'chars': len(p['json']), 'summary': p['summary'], 'stamp': stamp,
            'at': pkt_now().isoformat(timespec='seconds')}


def _auto_note(changed, payloads, new_stamp, old_stamp):
    parts = []
    for ds in changed:
        p = payloads[ds]
        parts.append('%s re-extracted from %s (%s): %s' % (
            p['const'], ', '.join(p.get('srcs') or [os.path.basename(p['rec']['path'])]),
            srcutil.mtime_str(p['rec']), p['summary']))
    return 'Data refresh %s PKT: %s.%s' % (
        new_stamp, '; '.join(parts),
        '' if new_stamp == old_stamp else ' Timestamp refresh %s PKT.' % new_stamp)


# ---------------------------------------------------------------- inject

def cmd_inject(cfg, a):
    """Swap one embedded payload from a JSON file you produced yourself (manual datasets)."""
    raw = srcutil.read_text(a.from_json).strip()
    obj = json.loads(raw)
    # keep the producer's own formatting when it is already embed-safe
    js = raw if ('\n' not in raw and '\r' not in raw and '</' not in raw) else srcutil.dumps(obj)
    _, vs = dashpatch.load_variants(cfg)
    old = dashpatch.get_payload(vs[0].text, a.const)
    if old == js:
        print('NO_CHANGE (%s payload already identical)' % a.const)
        return 0
    ratio = len(js) / float(max(len(old), 1))
    if not (SIZE_FLOOR <= ratio <= SIZE_CEIL) and not a.force:
        raise SystemExit('ABORT: %s would change %s -> %s chars (%.2fx); use --force if intended'
                         % (a.const, format(len(old), ','), format(len(js), ','), ratio))
    for v in vs:
        dashpatch.swap_payload(v, a.const, js)
    old_stamp = dashpatch.get_stamp(vs[0])
    new_stamp = old_stamp if a.no_stamp else dashpatch.pkt_stamp(pkt_now())
    if not a.no_stamp:
        for v in vs:
            dashpatch.set_stamp(v, new_stamp, old_stamp)
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    note = a.note or 'Data refresh %s PKT: %s payload replaced from %s (%s chars).%s' % (
        new_stamp, a.const, os.path.basename(a.from_json), format(len(js), ','),
        '' if a.no_stamp else ' Timestamp refresh %s PKT.' % new_stamp)
    for v in vs:
        print('  %-42s %+8d chars  %s' % (v.rel, v.delta(), '; '.join(v.changes) or 'unchanged'))
    print('stamp: %s -> %s' % (old_stamp, new_stamp))
    print('version note: %s' % note[:160])
    if a.dry_run:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    dashpatch.append_version(cfg, note)
    st = srcutil.load_state()
    st['datasets'][a.const.lower()] = {
        'source': {'path': os.path.abspath(a.from_json), 'name': os.path.basename(a.from_json),
                   'mtime': os.path.getmtime(a.from_json), 'size': os.path.getsize(a.from_json)},
        'file_id': 'manual|%s' % os.path.basename(a.from_json),
        'payload_sha1': srcutil.sha1_text(js), 'chars': len(js),
        'summary': 'manual inject', 'stamp': new_stamp,
        'at': pkt_now().isoformat(timespec='seconds')}
    srcutil.save_state(st)
    print('INJECTED %s (%s chars)' % (a.const, format(len(js), ',')))
    if a.publish:
        return publish(cfg, a, [a.const.lower()], new_stamp)
    print('next: python _refresh/refresh.py publish')
    return 0


# ---------------------------------------------------------------- publish

def git(args, cwd, check=True, quiet=False):
    p = subprocess.run(['git'] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode('utf-8', 'replace')
    if not quiet:
        sys.stdout.write(out)
    if check and p.returncode != 0:
        raise SystemExit('git %s failed:\n%s' % (' '.join(args), out))
    return p.returncode, out


def payload_line_re(cfg):
    """A matcher for the only lines this route writes into the variants: the payload consts.

    Every embedded dataset is one physical `const NAME = {...};` line, so a refresh touches exactly
    one line per dataset and nothing else. Anything else that differs in a variant came from a
    patch module or a hand edit, and a scheduled refresh must not commit that under its own
    message. Sources are read out of sources.json, never hardcoded, so a new dataset cannot widen
    what the guard waves through by accident.
    """
    names = set()
    for group in ('auto', 'manual'):
        for e in (cfg.get(group) or {}).values():
            const = e.get('const')
            if isinstance(const, str):
                const = [const]
            for n in const or ():
                if not re.fullmatch('[A-Za-z_$][A-Za-z0-9_$]*', n):
                    raise SystemExit('sources.json const %r is not a plain identifier' % n)
                names.add(n)
    if not names:
        raise SystemExit('sources.json lists no payload consts - cannot tell what this route wrote')
    return re.compile('^ *(?:const|let|var) (?:%s)(?![A-Za-z0-9_$]) *=' % '|'.join(sorted(names)))


def pending_foreign(cfg, allowed):
    """Per variant, the working-tree lines this route did not write - added and removed.

    Line level, not path level: the variant HTML *is* this route's own output, so a feature edit and
    a payload swap land in the same file and a path allowlist proves nothing. Two shapes belong to
    the route: a line declaring one of the payload consts from sources.json, and a line carrying a
    visible stamp chip, which is what set_stamp moves. Both sides of the diff are read because a
    feature that only deletes lines has nothing added to give itself away.
    """
    chip = re.compile('[Uu]pdated ' + dashpatch.STAMP_RE)
    out = {}
    for rel in cfg['variants']:
        rc, diff = git(['diff', '--unified=0', 'HEAD', '--', rel], cfg['repo'], quiet=True)
        if rc != 0:
            raise SystemExit('publish guard: git diff failed for %s' % rel)
        bad = []
        for ln in diff.split('\n'):
            sign = ln[:1]
            if sign not in ('+', '-') or ln.startswith('+++') or ln.startswith('---'):
                continue
            txt = ln[1:].rstrip('\r')
            if allowed.match(txt) or chip.search(txt):
                continue
            bad.append((sign, txt))
        if bad:
            out[rel] = bad
    return out


def publish(cfg, a, changed, stamp):
    repo = cfg['repo']
    rc, out = git(['status', '--porcelain'], repo, quiet=True)
    if not out.strip():
        print('publish: working tree clean, nothing to commit')
        return 0
    # the guard reads four 17 MB diffs, so it only runs when a variant is actually dirty - with the
    # variants untouched there are no site bytes left for this commit to carry
    rc, vdirty = git(['status', '--porcelain', '--'] + list(cfg['variants']), repo, quiet=True)
    foreign = pending_foreign(cfg, payload_line_re(cfg)) if vdirty.strip() else {}
    total = sum(len(v) for v in foreign.values())
    if foreign and not getattr(a, 'allow_pending', False):
        print('publish refused: %d line(s) in the variants are not lines this route wrote' % total)
        for rel, lines in sorted(foreign.items()):
            added = sum(1 for sign, _ in lines if sign == '+')
            print('  %s  +%d / -%d line(s)' % (rel, added, len(lines) - added))
            for sign, ln in lines[:4]:
                print('    %s %s%s' % (sign, ln[:160], ' ...' if len(ln) > 160 else ''))
            if len(lines) > 4:
                print('    ... %d more' % (len(lines) - 4))
        print('Nothing was staged or pushed - the refreshed payload is still on disk. Land that '
              'work as its own commit first, or re-run with --allow-pending to publish both.')
        return 3
    if foreign:
        print('publish: --allow-pending, carrying %d line(s) this route did not write in %s' % (
            total, ', '.join(sorted(foreign))))
    print('publish: pending changes')
    sys.stdout.write(out)
    paths = [v.replace('/', os.sep) for v in cfg['variants']]
    paths += [v.replace('/', os.sep) for v in cfg.get('version_files') or []]
    paths += [os.path.join('_refresh', 'state.json')]
    git(['add', '--'] + [p for p in paths if os.path.exists(os.path.join(repo, p))], repo)
    rc, staged = git(['diff', '--cached', '--name-only'], repo, quiet=True)
    print('staged: %s' % staged.replace('\n', ' '))
    if not staged.strip():
        print('publish: nothing this route writes has changed - the dirty files are tooling only, '
              'so there is nothing to commit. Commit those yourself, or leave them.')
        return 0
    msg = a.message or 'Refresh dashboard data (%s)' % ', '.join(changed)
    git(['commit', '-m', msg], repo)
    rc, out = git(['push'], repo, check=False)
    print('push: %s' % (out.strip() or 'ok'))
    return verify_pages(cfg, repo)


def _curl(args, tok=None):
    """curl with the auth header fed through stdin so the token never lands in argv."""
    cmd = ['curl', '-s'] + (['--config', '-'] if tok else []) + args
    inp = ('-H "Authorization: token %s"\n' % tok).encode('utf-8') if tok else b''
    p = subprocess.run(cmd, input=inp, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def verify_pages(cfg, repo, wait=180):
    rc, url = git(['remote', 'get-url', 'origin'], repo, quiet=True)
    url = url.strip()
    if 'github.com' not in url:
        print('verify: origin is not GitHub (%s) - skipping Pages check' % url)
        return 0
    owner, name = url.rstrip('/').split('github.com:')[-1].split('/')[-2:]
    if name.endswith('.git'):
        name = name[:-4]
    p = subprocess.run('printf "protocol=https\\nhost=github.com\\n\\n" | git credential fill',
                       cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    tok = ''
    for line in p.stdout.decode('utf-8', 'replace').splitlines():
        if line.startswith('password='):
            tok = line.split('=', 1)[1].strip()
    if not tok:
        print('verify: no stored GitHub credential found - check the push manually')
        return 0
    api = 'https://api.github.com/repos/%s/%s' % (owner, name)
    live = 'https://%s.github.io/%s/index.html' % (owner, name)
    t0 = time.time()
    status = '?'
    while time.time() - t0 < wait:
        rc, out = _curl(['-H', 'Accept: application/vnd.github+json',
                         '%s/pages/builds/latest' % api], tok)
        try:
            b = json.loads(out)
        except ValueError:
            b = {}
        status = b.get('status') or b.get('message') or '?'
        if status not in ('queued', 'building', None):
            break
        time.sleep(10)
    print('verify: latest Pages build status = %s (after %.0fs)' % (status, time.time() - t0))
    rc, out = _curl(['-I', '%s?cb=%d' % (live, int(time.time()))])
    hdrs = dict((l.split(':', 1)[0].strip().lower(), l.split(':', 1)[1].strip())
                for l in out.splitlines() if ':' in l)
    local = srcutil.read_text(os.path.join(repo, 'index.html'))
    raw = len(local.encode('utf-8'))
    expect = raw - local.count('\r\n')
    got = int(hdrs.get('content-length') or -1)
    ok = got in (raw, expect)
    print('verify: live content-length %s vs local %s (LF-normalised %s) -> %s' % (
        format(got, ','), format(raw, ','), format(expect, ','),
        'MATCH' if ok else 'DIFFERS'))
    print('verify: last-modified %s' % hdrs.get('last-modified', '?'))
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--repo', help='operate on another checkout of the dashboard (default: sources.json)')
    sub = ap.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('status', parents=[common], help='show every dataset, its newest source file and whether it is stale')
    s.add_argument('--json', action='store_true')
    s.add_argument('--deep', action='store_true',
                   help='for each file-id mismatch, regenerate the payload and report whether it actually differs (slow)')

    r = sub.add_parser('run', parents=[common], help='re-extract stale file-based datasets and swap them into all 4 variants')
    r.add_argument('--only', help='comma-separated dataset ids (default: all auto)')
    r.add_argument('--source', help='explicit source file (only with a single --only dataset)')
    r.add_argument('--dry-run', action='store_true')
    r.add_argument('--force', action='store_true', help='re-extract even if the source is unchanged; skip size guard')
    r.add_argument('--no-stamp', action='store_true', help='leave the PKT timestamps alone')
    r.add_argument('--note', help='version.txt note (default: auto-generated)')
    r.add_argument('--publish', action='store_true', help='commit, push and verify Pages after writing')
    r.add_argument('--message', help='commit message for --publish')
    r.add_argument('--allow-pending', action='store_true',
                   help='with --publish, also commit variant edits this route did not write')

    i = sub.add_parser('inject', parents=[common], help='swap one payload from a JSON file (manual datasets)')
    i.add_argument('--const', required=True, help='embedded const name, e.g. ZD, EPI, CQ')
    i.add_argument('--from', dest='from_json', required=True, help='path to the payload JSON')
    i.add_argument('--dry-run', action='store_true')
    i.add_argument('--force', action='store_true')
    i.add_argument('--no-stamp', action='store_true')
    i.add_argument('--note')
    i.add_argument('--publish', action='store_true')
    i.add_argument('--message')
    i.add_argument('--allow-pending', action='store_true')

    p = sub.add_parser('publish', parents=[common],
                       help='commit + push the refreshed payloads and verify the Pages build')
    p.add_argument('--message')
    p.add_argument('--changed', default='dashboard data')
    p.add_argument('--allow-pending', action='store_true')

    a = ap.parse_args()
    cfg = srcutil.load_sources()
    if getattr(a, 'repo', None):
        cfg['repo'] = os.path.abspath(a.repo)
        if not os.path.exists(os.path.join(cfg['repo'], 'index.html')):
            raise SystemExit('--repo %s has no index.html' % cfg['repo'])
    os.makedirs(srcutil.OUT, exist_ok=True)
    if a.cmd == 'status':
        return cmd_status(cfg, a)
    if a.cmd == 'run':
        return cmd_run(cfg, a)
    if a.cmd == 'inject':
        return cmd_inject(cfg, a)
    if a.cmd == 'publish':
        a.publish = True
        return publish(cfg, a, [a.changed], dashpatch.pkt_stamp(pkt_now()))
    return 2


if __name__ == '__main__':
    sys.exit(main())

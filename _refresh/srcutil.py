"""Shared helpers: source discovery, state file, JSON payload IO."""
import fnmatch
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(HERE, 'sources.json')
STATE = os.path.join(HERE, 'state.json')
OUT = os.path.join(HERE, 'out')


def outp(*a):
    return os.path.join(HERE, *a)


def load_sources():
    with io.open(SOURCES, encoding='utf-8') as f:
        return json.load(f)


def load_state():
    if not os.path.exists(STATE):
        return {'datasets': {}}
    with io.open(STATE, encoding='utf-8') as f:
        return json.load(f)


def save_state(st):
    with io.open(STATE, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(st, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')


def repo_root(cfg=None):
    return (cfg or load_sources())['repo']


def _match(name, patterns, excludes):
    if any(fnmatch.fnmatch(name, x) for x in excludes):
        return False
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def discover(entry):
    """All candidate source files for a dataset entry, newest mtime first."""
    pats = entry.get('patterns') or []
    exc = entry.get('exclude') or ['~$*']
    found = []
    for root in entry.get('roots') or []:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            for fn in filenames:
                if not _match(fn, pats, exc):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    stt = os.stat(p)
                except OSError:
                    continue
                found.append({'path': p, 'name': fn, 'mtime': stt.st_mtime, 'size': stt.st_size})
    found.sort(key=lambda d: -d['mtime'])
    return found


def newest(entry):
    f = discover(entry)
    return f[0] if f else None


def stat_rec(path):
    st = os.stat(path)
    return {'path': path, 'name': os.path.basename(path), 'mtime': st.st_mtime, 'size': st.st_size}


def file_id(rec):
    if not rec:
        return None
    return '%s|%d|%d' % (rec['path'], int(rec['mtime']), rec['size'])


def sha1_text(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]


def read_text(p):
    with io.open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_text(p, s):
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def dumps(obj):
    """Compact JSON safe to embed inside a <script> block."""
    s = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    s = s.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    s = s.replace('</', '<\\/')
    assert '\n' not in s and '\r' not in s
    json.loads(s.replace('<\\/', '</'))
    return s


def mtime_str(rec):
    if not rec:
        return '-'
    import datetime
    return datetime.datetime.fromtimestamp(rec['mtime']).strftime('%d-%b-%Y %H:%M')


def say(*a):
    print(*a)
    sys.stdout.flush()

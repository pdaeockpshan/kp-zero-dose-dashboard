"""Master-only payload swap: python _refresh/mset.py NAME FILE.json

refresh.py inject writes every variant, restamps the header and appends a version note.
While the other three variants are deliberately held back, the master has to absorb a
payload on its own, so this swaps one const in index.html only and touches nothing else.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    name, src = sys.argv[1], sys.argv[2]
    raw = srcutil.read_text(src).strip()
    obj = json.loads(raw)
    js = raw if ('\n' not in raw and '\r' not in raw and '</' not in raw) else srcutil.dumps(obj)
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    old = dashpatch.get_payload(v.text, name)
    if old == js:
        print('NO_CHANGE %s' % name)
        return 0
    dashpatch.swap_payload(v, name, js)
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('SET %s %s -> %s chars (%s)' % (name, format(len(old), ','), format(len(js), ','),
                                          '; '.join(v.changes)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""Scheduled watcher: refresh+publish the dashboard when a new EOC NEAP export lands.

The EOC pre-campaign pages are login-gated, so the sanctioned route is the portal's
own "Export to Excel" (file NEAP.xls) from a signed-in browser. This watcher does
not touch the portal: it only looks at the Downloads folder. When the newest
NEAP*.xls/csv is newer than the last refresh and at least MIN_AGE seconds old (so
both the district-wise and UC-wise exports have landed), it runs:

    _refresh/refresh.py run --only neap --publish

`refresh.py publish` carries only the lines this route writes - the payload `const` lines and the
stamp - and refuses (exit 3, nothing committed) when a variant also carries site edits of its own,
which is how the 26-Oct-2026 run published unfinished work. Then the reason and the offending lines
are in neap_auto.log, the refreshed payload waits on disk uncommitted, and `state.json` already
records the export as applied, so this watcher will not offer it again: the next publish - a human
commit of the pending site work, or the next export that lands cleanly - is what carries it.

Install (current user, every 30 minutes, only while logged on):
    schtasks /Create /TN "KP Dashboard NEAP auto-refresh" ^
      /TR "\"<pythonw.exe>\" \"<repo>\\_refresh\\neap_auto.py\"" /SC MINUTE /MO 30 /IT /F
"""
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import srcutil

LOG = os.path.join(HERE, 'neap_auto.log')
LOCK = os.path.join(HERE, 'neap_auto.lock')
MIN_AGE = 300
TIMEOUT = 1200


def log(msg):
    line = '%s %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(line)
    try:
        with open(LOG, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')
    except OSError:
        pass


def state_mtime():
    try:
        with open(os.path.join(HERE, 'state.json'), encoding='utf-8') as fh:
            return float(json.load(fh)['datasets']['neap']['source']['mtime'])
    except (OSError, ValueError, KeyError, TypeError):
        return 0.0


def main():
    cfg = srcutil.load_sources()
    recs = srcutil.discover(cfg['auto']['neap'])
    if not recs:
        return 0
    newest = recs[0]
    if newest['mtime'] <= state_mtime() + 1:
        return 0
    age = time.time() - newest['mtime']
    if age < MIN_AGE:
        log('new NEAP file %s is %ds old - waiting for the second export' % (newest['name'], age))
        return 0
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        try:
            if time.time() - os.path.getmtime(LOCK) > 7200:
                os.remove(LOCK)
        except OSError:
            pass
        log('another run holds the lock - skipping')
        return 0
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        log('new NEAP export: %s (%s, %d bytes) - refreshing' % (
            newest['name'],
            datetime.datetime.fromtimestamp(newest['mtime']).strftime('%d-%b-%Y %H:%M'),
            newest['size']))
        p = subprocess.run(
            [sys.executable, os.path.join(HERE, 'refresh.py'), 'run', '--only', 'neap',
             '--publish', '--message', 'Auto-refresh NEAP from EOC pre-campaign export'],
            cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT)
        for ln in ((p.stdout or '') + (p.stderr or '')).splitlines():
            log(ln)
        log('refresh exit=%d' % p.returncode)
        return p.returncode
    except subprocess.TimeoutExpired:
        log('refresh timed out after %ds' % TIMEOUT)
        return 1
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == '__main__':
    sys.exit(main())

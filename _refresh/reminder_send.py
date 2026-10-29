# -*- coding: utf-8 -*-
"""Sends the daily MPQA trigger reminder through the Outlook that is already signed in.

Reads the TRIG payload from the built dashboard, composes the same text the dashboard's
Daily reminder dialog shows, and hands the mail to Outlook. No password is read or stored;
the mail goes out from whichever account Outlook is signed into.

    python _refresh/reminder_send.py              preview only: writes the .eml and prints it
    python _refresh/reminder_send.py --compose    open it as an unsent draft in your mail app
    python _refresh/reminder_send.py --send       send it through classic Outlook
    python _refresh/reminder_send.py --send --force    send again for the same portal read

    python _refresh/reminder_send.py --schedule 10:00 --mode compose    weekdays 10:00, draft
    python _refresh/reminder_send.py --status                           next run and last runs
    python _refresh/reminder_send.py --unschedule                       remove the task

--send needs classic Outlook signed in on this PC. The new Outlook for Windows has no COM
interface, so on a machine that only runs the new Outlook use --compose: the .eml carries To,
Cc, subject, body and (with --csv) the attachment, and opens as a draft with the Send button
left to you. Both Outlooks honour the X-Unsent header that produces that draft.

Refuses to send when nothing is pending, when the portal read has not changed since the
last send (so a stale page cannot repeat yesterday's reminder), or when To/Cc are unset.

The scheduled task runs in your own session, so a draft window appears on the desktop; it is
registered for Mon-Sat and refuses nothing except what the guards above already refuse.

Kept outside the repo: %LOCALAPPDATA%\\kp-dashboard\\ holds the recipients, the send state,
the .eml copies and the log. Nothing here is published and nothing is committed.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOUSE = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'kp-dashboard')
CONFIG = os.path.join(HOUSE, 'reminder_config.json')
STATE = os.path.join(HOUSE, 'reminder_state.json')
OUT = os.path.join(HOUSE, 'out')
LOG = os.path.join(HOUSE, 'reminders.log')

TASK = 'KP dashboard trigger reminder'
TASK_DAYS = 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday'

MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def day(s):
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', s or '')
    return '%s-%s-%s' % (m.group(3), MON[int(m.group(2)) - 1], m.group(1)) if m else str(s or '')


def read_trig(path):
    text = open(path, encoding='utf-8', newline='').read()
    i = text.index('const TRIG = ') + len('const TRIG = ')
    depth, j, instr, esc = 0, i, False, False
    while j < len(text):
        c = text[j]
        if instr:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    break
        j += 1
    return json.loads(text[i:j + 1])


def mpqa(trig):
    t = [x for x in trig['t'] if x['id'] == 'mpqa'][0]
    rows = [{'d': d, 'p': v[2] - v[3], 't': v[2], 'f': v[3]}
            for d, v in t['d'].items() if v[2] - v[3] > 0]
    rows.sort(key=lambda r: (-r['p'], r['d']))
    return t, rows


def load(path, default):
    try:
        return json.load(open(path, encoding='utf-8'))
    except Exception:
        return default


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def log(action, asof, subj, pend, n, to, cc):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write('%s\t%s\t%s\t%s\t%d UCs in %d districts\tto %s\tcc %s\n'
                % (dt.datetime.now().strftime('%d-%b-%Y %H:%M'), asof, action, subj, pend, n, to, cc))


def delta(state, rows):
    prev = (state.get('last') or {})
    before = prev.get('mpqa')
    if not before:
        return None
    now = {r['d']: r['p'] for r in rows}
    cleared = sum(max(0, before.get(d, 0) - now.get(d, 0)) for d in set(before) | set(now))
    newly = sum(max(0, now.get(d, 0) - before.get(d, 0)) for d in set(before) | set(now))
    return {'date': prev.get('asof'), 'cleared': cleared, 'newly': newly}


def body(trig, t, rows, d):
    ad = day(trig['asof'])
    pend = t['tot'][2] - t['tot'][3]
    L = ['Dear EOC-KP,', '',
         'Trigger feedback is still pending for the union councils below, as read from the EOC '
         'control-room triggers on ' + ad + '. Please have the concerned districts enter the '
         'feedback in the portal so the pendency closes. For onward sharing with the concerned districts.',
         '',
         'MPQA trigger - ' + t['camp'] + ' (' + str(pend) + ' UCs pending in ' + str(len(rows)) +
         (' district)' if len(rows) == 1 else ' districts)')]
    for r in rows:
        L.append('- ' + r['d'] + ' - ' + str(r['p']) + ' pending of ' + str(r['t']) + ' flagged')
    L.append('')
    if d:
        net = d['newly'] - d['cleared']
        L.append('Change since the ' + day(d['date']) + ' portal read: ' + str(d['cleared']) +
                 ' UCs cleared, ' + str(d['newly']) + ' newly pending (net ' +
                 ('+' if net > 0 else '') + str(net) + '). Feedback entered lowers the count; '
                 'a newly flagged UC raises it.')
    L.append('KP totals: MPQA trigger ' + str(t['tot'][2]) + ' flagged, ' + str(t['tot'][3]) +
             ' feedback, ' + str(pend) + ' pending.')
    L.append('This reminder covers the MPQA trigger only. ICM and admin-coverage reminders are held '
             'until the campaign round starts on 2 Nov 2026 and the portal begins recording feedback for them.')
    L.append('')
    L.append('Counts are union councils, not children. Portal read ' + ad + ', ' + t['camp'] + ' round.')
    L.append('')
    L.append('Cc: MNE officer, WHO - for information.')
    return '\n'.join(L)


def subject(t, rows, asof):
    pend = t['tot'][2] - t['tot'][3]
    if not pend:
        return 'KP trigger reminder - no feedback pending - read ' + day(asof)
    return 'KP trigger reminder - ' + str(pend) + ' MPQA UCs pending feedback - read ' + day(asof)


def eml(to, cc, subj, text, csv_path=None):
    """X-Unsent makes both classic and new Outlook open the file as an editable draft."""
    from email import policy
    from email.message import EmailMessage
    m = EmailMessage()
    if to:
        m['To'] = to
    if cc:
        m['Cc'] = cc
    m['Subject'] = subj
    m['X-Unsent'] = '1'
    m.set_content(text)
    if csv_path:
        with open(csv_path, 'rb') as f:
            m.add_attachment(f.read(), maintype='text', subtype='csv',
                             filename=os.path.basename(csv_path))
    return m.as_bytes(policy=policy.SMTP)


def outlook_app(wait=20):
    """Classic Outlook holding a live MAPI session, started if it is not running.

    Dispatch hands back an object before any profile is loaded, and the new Outlook has no
    COM surface at all, so the session is probed until it answers or the wait runs out.
    """
    import time
    import win32com.client
    try:
        ol = win32com.client.GetActiveObject('Outlook.Application')
    except Exception:
        try:
            ol = win32com.client.Dispatch('Outlook.Application')
        except Exception as e:
            raise RuntimeError('classic Outlook could not be started: ' + str(e))
    last = None
    deadline = time.time() + wait
    while True:
        try:
            ol.GetNamespace('MAPI').CurrentUser.Address
            return ol
        except Exception as e:
            last = e
        if time.time() >= deadline:
            raise RuntimeError('classic Outlook has no signed-in session (' + str(last) +
                               '); sign in to classic Outlook once, or use --compose')
        time.sleep(0.5)


def outlook(to, cc, subj, text, csv_path=None):
    mail = outlook_app().CreateItem(0)
    mail.To = to
    mail.Cc = cc
    mail.Subject = subj
    mail.Body = text
    if csv_path:
        mail.Attachments.Add(csv_path)
    mail.Send()


def compose(eml_path):
    """Open the .eml as an unsent draft in whichever mail app owns .eml on this PC."""
    os.startfile(eml_path)


def sender_address():
    try:
        import win32com.client
        ol = win32com.client.GetActiveObject('Outlook.Application')
        ns = ol.GetNamespace('MAPI')
        cu = ns.CurrentUser
        try:
            return cu.AddressEntry.GetExchangeUser().PrimarySmtpAddress
        except Exception:
            return cu.Address or '(Outlook current user)'
    except Exception:
        return 'no signed-in classic Outlook on this PC - use --compose'


def csv_for(rows, t, path):
    import csv
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Trigger', 'Campaign', 'District', 'Flagged UCs', 'Feedback', 'Pending'])
        for r in rows:
            w.writerow(['MPQA trigger', t['camp'], r['d'], r['t'], r['f'], r['p']])
        w.writerow(['MPQA trigger', t['camp'], 'KP total', t['tot'][2], t['tot'][3],
                    t['tot'][2] - t['tot'][3]])


def _ps(cmd):
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip() or 'powershell failed')
    return r.stdout.strip()


def schedule(at, mode):
    """Register a per-user task that runs in this session, so a draft window is visible."""
    action = '"%s" %s' % (os.path.join(REPO, '_refresh', 'reminder_send.py'),
                          '--send' if mode == 'send' else '--compose')
    cmd = ("$a = New-ScheduledTaskAction -Execute '%s' -Argument '%s' -WorkingDirectory '%s'; "
           "$t = New-ScheduledTaskTrigger -Weekly -At '%s' -DaysOfWeek %s; "
           "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries "
           "-DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 15); "
           "Register-ScheduledTask -TaskName '%s' -Action $a -Trigger $t -Settings $s "
           "-Description 'KP dashboard MPQA trigger reminder (%s) from %s' -Force | Out-Null; "
           "(Get-ScheduledTaskInfo -TaskName '%s').NextRunTime"
           % (sys.executable, action, REPO, at, TASK_DAYS, TASK, mode, REPO, TASK))
    return _ps(cmd)


def status():
    cmd = ("$t = Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue; "
           "if (-not $t) { 'not registered'; return }; "
           "$i = Get-ScheduledTaskInfo -TaskName '%s'; "
           "'state    : ' + $t.State; "
           "'next run : ' + $i.NextRunTime; "
           "'last run : ' + $i.LastRunTime + '  (result ' + $i.LastTaskResult + ')'; "
           "'action   : ' + $t.Actions[0].Execute + ' ' + $t.Actions[0].Arguments"
           % (TASK, TASK))
    return _ps(cmd)


def unschedule():
    return _ps("Unregister-ScheduledTask -TaskName '%s' -Confirm:$false; "
               "if (Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue) "
               "{ 'still registered' } else { 'removed' }" % (TASK, TASK))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--compose', action='store_true',
                    help='open the message as an unsent draft in your mail app')
    ap.add_argument('--send', action='store_true', help='actually send through classic Outlook')
    ap.add_argument('--force', action='store_true', help='send even if this portal read was already sent')
    ap.add_argument('--csv', action='store_true', help='attach the pending-UC CSV')
    ap.add_argument('--file', default=os.path.join(REPO, 'index.html'))
    ap.add_argument('--schedule', metavar='HH:MM',
                    help='register the Mon-Sat task that runs this at HH:MM')
    ap.add_argument('--mode', choices=['compose', 'send'], default='compose',
                    help='what the scheduled task does (default compose)')
    ap.add_argument('--status', action='store_true', help='show the scheduled task')
    ap.add_argument('--unschedule', action='store_true', help='remove the scheduled task')
    a = ap.parse_args()

    if a.status:
        print(status())
        return 0
    if a.unschedule:
        print(unschedule())
        return 0
    if a.schedule:
        if not re.match(r'^([01]\d|2[0-3]):[0-5]\d$', a.schedule):
            print('Give the time as HH:MM on the 24-hour clock, for example --schedule 10:00.')
            return 2
        try:
            nxt = schedule(a.schedule, a.mode)
        except Exception as e:
            print('Could not register the task: ' + str(e))
            return 6
        print('Scheduled "' + TASK + '" Mon-Sat at ' + a.schedule + ', mode ' + a.mode + '.')
        print('Next run: ' + nxt)
        return 0

    trig = read_trig(a.file)
    t, rows = mpqa(trig)
    pend = t['tot'][2] - t['tot'][3]
    if not pend:
        print('Nothing pending against the MPQA trigger for the ' + day(trig['asof']) + ' read - no mail.')
        return 0

    cfg = load(CONFIG, {})
    to = (cfg.get('to') or '').strip()
    cc = (cfg.get('cc') or '').strip()
    if not to or not cc:
        print('Recipients missing. Write ' + CONFIG + ' as {"to": "...", "cc": "..."}.')
        return 2

    state = load(STATE, {})
    d = delta(state, rows)
    subj = subject(t, rows, trig['asof'])
    text = body(trig, t, rows, d)

    os.makedirs(OUT, exist_ok=True)
    base = 'KP_trigger_reminder_' + trig['asof']
    csv_path = os.path.join(OUT, base + '.csv')
    csv_for(rows, t, csv_path)
    eml_path = os.path.join(OUT, base + '.eml')
    with open(eml_path, 'wb') as f:
        f.write(eml(to, cc, subj, text, csv_path if a.csv else None))

    print('From     : ' + sender_address())
    print('To       : ' + to)
    print('Cc       : ' + cc)
    print('Subject  : ' + subj)
    print('Pending  : ' + str(pend) + ' MPQA UCs in ' + str(len(rows)) + ' districts, read ' + day(trig['asof']))
    print('Files    : ' + eml_path)
    print('           ' + csv_path)
    print('-' * 72)
    print(text)
    print('-' * 72)

    if a.compose:
        try:
            compose(eml_path)
        except Exception as e:
            print('Could not open the draft: ' + str(e))
            return 5
        log('draft', trig['asof'], subj, pend, len(rows), to, cc)
        print('Opened as an unsent draft' + (' with the CSV attached' if a.csv else '') +
              ' in your mail app. Nothing has been sent - the Send button is yours.')
        return 0

    if not a.send:
        print('PREVIEW ONLY. --compose opens it unsent in your mail app; --send sends it '
              'through classic Outlook.')
        return 0

    last = state.get('last') or {}
    if last.get('asof') == trig['asof'] and not a.force:
        print('Already sent for the ' + day(trig['asof']) + ' read at ' + str(last.get('sent_at')) +
              '. Refresh the portal read, or add --force to send again.')
        return 3

    try:
        outlook(to, cc, subj, text, csv_path if a.csv else None)
    except Exception as e:
        print('Outlook could not send: ' + str(e))
        print('Nothing was sent. --compose opens the same message as a draft instead.')
        return 4

    sent_at = dt.datetime.now().strftime('%d-%b-%Y %H:%M')
    state['last'] = {'asof': trig['asof'], 'sent_at': sent_at, 'to': to, 'cc': cc,
                     'subject': subj, 'pending': pend,
                     'mpqa': {r['d']: r['p'] for r in rows}}
    save(STATE, state)
    log('sent', trig['asof'], subj, pend, len(rows), to, cc)
    print('SENT from your Outlook at ' + sent_at + '. Log: ' + LOG)
    return 0


if __name__ == '__main__':
    sys.exit(main())

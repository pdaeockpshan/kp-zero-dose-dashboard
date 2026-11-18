"""Validation refresh 18-Nov-2026: prose + Nov return flag in the master."""
import sys

P = r'C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html'
s = open(P, encoding='utf-8', newline='').read()

EDITS = [
    ('20,313 children validated on 2,867 forms in 791 UCs, 37 districts',
     '20,916 children validated on 2,960 forms in 795 UCs, 37 districts', 1),
    ('20,313 children validated', '20,916 children validated', 2),
    ('97.4% confirmed vaccinated', '97.2% confirmed vaccinated', 2),
    ('entries 20-Jan-2026 to 03-Nov-2026.',
     'entries 20-Jan-2026 to 18-Nov-2026.', 3),
    ('% vaccinated = children the validator confirmed as vaccinated',
     'The 18-Nov-2026 combined export adds 93 SNID Nov-26 validation forms (603 children); the SNID Sep-26 rows are unchanged at 711 children on 180 forms. % vaccinated = children the validator confirmed as vaccinated', 1),
    ('its zero-dose covered figure and validation are the post-campaign returns still awaited',
     'its zero-dose covered figure is the post-campaign return still awaited, and its validation return is coming in (2,580 children on 336 forms through 18-Nov-2026)', 1),
    ('its covered figure, digitization and validation are post-campaign returns that are still awaited. Nov is therefore compared on reported ZDs only',
     'its covered figure and digitization are post-campaign returns that are still awaited, while its validation return is coming in (2,580 children on 336 forms through 18-Nov-2026). Nov is therefore compared on reported ZDs only', 1),
    ('its coverage, IDIMS digitization and validation are the post-campaign returns awaited; LQAS is in; the IDIMS and validation cards stay blank until those returns are compiled rather than showing an earlier round.',
     'its coverage and IDIMS digitization are the post-campaign returns awaited; LQAS and validation are in (2,580 children re-checked on 336 forms so far); the IDIMS card stays blank until that return is compiled rather than showing an earlier round.', 1),
    (". Nov covered, digitization and validation are post-campaign returns and are still awaited.",
     ". Nov validation is coming in; its covered figure and digitization are post-campaign returns and are still awaited.", 1),
    ('validation confirming 97.5% of those checked.',
     'validation confirming 95.9% of the 2,580 children checked so far.', 1),
    ("['Zero-dose validation','SNID November 2026 validation export','Nov-2026','UC']",
     "['Zero-dose validation','SNID November 2026 validation export','18-Nov-2026','UC']", 1),
    ('; the zero-dose covered figure and validation are the post-campaign returns still awaited`:\'LQAS is in; coverage and validation are the post-campaign returns still awaited\'',
     '; the zero-dose covered figure is the post-campaign return still awaited, while validation is coming in`:\'LQAS and validation are in; coverage is the post-campaign return still awaited\'', 1),
    ('LQAS is in; the covered figure and validation are the post-campaign returns awaited.',
     'LQAS and validation are in; the covered figure is the post-campaign return awaited.', 1),
    ('LQAS in; covered and validation awaited',
     'LQAS and validation in; covered awaited', 1),
    ('Its covered figure, IDIMS digitization and validation are the post-campaign returns awaited, with LQAS already in',
     'Its covered figure and IDIMS digitization are the post-campaign returns awaited, with LQAS and validation already in', 1),
    ('its covered figure and validation are the post-campaign returns still awaited. Deselect a campaign',
     'its covered figure is the post-campaign return still awaited; its validation return is coming in. Deselect a campaign', 1),
    ('the covered figure, digitization and validation are the post-campaign returns still awaited. ',
     'the covered figure and digitization are the post-campaign returns still awaited, and validation is coming in. ', 1),
    ('its covered figure and validation arrive with the post-campaign returns.',
     'its covered figure arrives with the post-campaign return; its validation is in.', 1),
    ('const HZNOVRET={dig:false,val:false};', 'const HZNOVRET={dig:false,val:true};', 1),
]

for old, new, n in EDITS:
    got = s.count(old)
    if got != n:
        sys.exit('expected %d of %r, found %d' % (n, old[:70], got))
    s = s.replace(old, new)

assert '\r\n' in s
open(P, 'w', encoding='utf-8', newline='').write(s)
print('patched %d fragments' % len(EDITS))

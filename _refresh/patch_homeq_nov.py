"""Refresh the home 'three questions' block for the concluded SNID Nov-26 round.

Q1 hero currently claims 'the last measured still-missed is 121,677 after SNID
Sept-26', although the Nov close-out carries its own still-missed return
(NOVF: stl 162,874 against a 4,183,183 household target, stp 3.89). Q1 footer
still says 'not yet covered' for a closed round, and Q3's still-missed trend
stops at Sept while its LQAS arm already includes Nov.

This patch reads NOVF.tot directly (same k/index-3 convention the campaign deck
uses) and states the Nov figure on its own household-target basis. Nov is NOT
folded into the register-basis trend, because that trend's denominators are a
different construct; the divergence is labelled instead of blended.
"""
import io
import sys

P = r"C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html"

with io.open(P, encoding="utf-8", newline="") as f:
    t = f.read()

crlf = t.count("\r\n")
lf = t.count("\n")
assert crlf == lf, (crlf, lf)
orig_len = len(t)


def sub(text, a, b):
    n = text.count(a)
    assert n == 1, "anchor hit %d times: %r" % (n, a[:90])
    assert b not in text, "replacement already present: %r" % (b[:90])
    return text.replace(a, b, 1)


# 1. Read the Nov close-out totals alongside the ADV-round line.
A1 = "NVlbl=(typeof ADV!=='undefined'&&ADV&&ADV.c&&ADV.c.length)?ADV.c[ADV.c.length-1].n:'SNID Nov 2026';"
B1 = (A1 + "\r\n"
      " const NVs=(typeof NOVF!=='undefined'&&NOVF&&NOVF.tot&&NOVF.k)?(()=>{const g=k=>NOVF.tot[NOVF.k.indexOf(k)-3];"
      "return {stl:g('stl'),stp:g('stp'),tgt:g('tgt'),sna:g('sna'),srf:g('srf'),slo:g('slo')};})():null;"
      "\r\n"
      " const NVsm=NVs?`Its own still-missed return is in: <b>${fmt(NVs.stl)}</b> (${pc(NVs.stp)} of the ${fmt(NVs.tgt)} household target); the zero-dose covered figure and validation are the post-campaign returns still awaited`:'LQAS is in; coverage and validation are the post-campaign returns still awaited';")
t = sub(t, A1, B1)

# 2. Q1 hero: replace the stale Sept still-missed claim.
A2 = ("\u2014 the round has concluded; LQAS is in, and coverage and validation are the post-campaign returns still awaited, "
      "so the last measured still-missed is ${fmt(S.st)} after ${esc(mc)} (${pc(S.stp)} of target)</span>")
B2 = "\u2014 the round has concluded. ${NVsm}</span>"
t = sub(t, A2, B2)

# 3. Q1 footer: a closed round is no longer 'not yet covered'.
A3 = "zero-dose children not yet covered in ${esc(CAMP[cK])}"
B3 = "zero-dose children reported but not covered in ${esc(CAMP[cK])}"
t = sub(t, A3, B3)

# 4. Q1 footer paragraph: carry Nov's still-missed count and composition.
A4 = "and no covered figure yet; LQAS is in, and its coverage and validation are the post-campaign returns awaited."
B4 = ("and no covered figure yet${NVs?' \u2014 its own still-missed return is '+fmt(NVs.stl)+' ('+fmt(NVs.sna)+' not available, '"
      "+fmt(NVs.srf)+' refusals, '+fmt(NVs.slo)+' left over from earlier rounds, against a '+fmt(NVs.tgt)+' household target)':''}. "
      "LQAS is in; the covered figure and validation are the post-campaign returns awaited.")
t = sub(t, A4, B4)

# 5. Q3: name the trend's denominator so it is not read as the household basis.
A5 = "<span>Still missed after catch-up</span>"
B5 = "<span>Still missed after catch-up (% of UC target)</span>"
t = sub(t, A5, B5)

# 6. Q3: add Nov's still-missed return to the round's own line.
A6 = "<span><b>${fmt(NVrep)}</b> recorded \u00b7 LQAS in; covered and validation awaited</span>"
B6 = ("<span><b>${fmt(NVrep)}</b> recorded \u00b7 <b>${NVs?fmt(NVs.stl):'\u2013'}</b> still missed "
      "(${NVs?pc(NVs.stp):'\u2013'} of household target) \u00b7 LQAS in; covered and validation awaited</span>")
t = sub(t, A6, B6)

# 7. Q3 closure hook: say Nov is reported separately, not folded into the signals.
A7 = ".replace(/\u00b7\\s*not yet a UC-level closure measure/,'').trim()}</div>"
B7 = (".replace(/\u00b7\\s*not yet a UC-level closure measure/,'').trim()}. "
      "Nov's own still-missed return is on the household target and is shown separately, not folded into these signals.</div>")
t = sub(t, A7, B7)

# 8. Static section header: the still-missed return is now in too.
A8 = "its LQAS is in; its coverage and validation are the post-campaign returns still awaited"
B8 = "its LQAS and still-missed return are in; its zero-dose covered figure and validation are the post-campaign returns still awaited"
t = sub(t, A8, B8)

assert t.count("\r\n") == t.count("\n"), "CRLF broken"
with io.open(P, "w", encoding="utf-8", newline="") as f:
    f.write(t)

print("ok  %d -> %d chars  (+%d)" % (orig_len, len(t), len(t) - orig_len))
print("crlf lines", t.count("\r\n"))
sys.exit(0)

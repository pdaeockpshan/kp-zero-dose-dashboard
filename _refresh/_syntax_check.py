import re, os, subprocess, sys

t = open('index.html', encoding='utf-8', newline='').read()
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', t, re.S)
print('inline blocks:', len(blocks))
ok = True
for i, b in enumerate(blocks):
    if not b.strip():
        continue
    fn = '_check_%d.js' % i
    open(fn, 'w', encoding='utf-8', newline='').write(b)
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    exe = r'C:/Users/HD/AppData/Local/Programs/Qoder/.qoder-versions/0.5.12/Qoder.exe'
    if not os.path.exists(exe):
        exe = r'C:/Users/HD/AppData/Local/Programs/Qoder/.qoder-versions/0.4.8/Qoder.exe'
    r = subprocess.run([exe, '--check', fn], capture_output=True, text=True, env=env)
    print('block', i, 'len', len(b), 'rc', r.returncode)
    if r.returncode:
        ok = False
        print(r.stdout[-2000:])
        print(r.stderr[-3000:])
    os.remove(fn)
sys.exit(0 if ok else 1)

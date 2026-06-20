#!/usr/bin/env python3
"""Look up unmatched words on Cambridge Dictionary (English-Chinese Traditional)."""
import json, re, time, html as html_mod, csv
from urllib.request import Request, urlopen

WORDS_FILE = "/srv/projects/04-4000-words/data/words.json"
REF_CSV = "/srv/projects/01 data_base/4000w_cambridge_ref.csv"
UNMATCHED_LIST = "/tmp/unmatched_words.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

def lookup(word):
    url = f"https://dictionary.cambridge.org/dictionary/english-chinese-traditional/{word}"
    req = Request(url, headers={"User-Agent": UA})
    try:
        resp = urlopen(req, timeout=15)
        html_text = resp.read().decode('utf-8')
        trans = re.findall(r'class="dtrans[^"]*"[^>]*>([^<]+)', html_text)
        if trans:
            return '；'.join(html_mod.unescape(t) for t in trans)
        m = re.search(r'content="[^"]*translate:\s*([^"]+?)\.\s*Learn more', html_text)
        if m:
            return html_mod.unescape(m.group(1))
    except Exception as e:
        print(f"  ⚠️ {word}: {e}", flush=True)
    return None

# Load unmatched list
with open(UNMATCHED_LIST, encoding='utf-8') as f:
    unmatched_words = set(json.load(f))

# Load words.json
with open(WORDS_FILE, encoding='utf-8') as f:
    data = json.load(f)

# Find and process unmatched
to_lookup = []
for book in data:
    for unit in book['units']:
        for word in unit['words']:
            if word['w'].strip() in unmatched_words:
                to_lookup.append(word)

print(f"Looking up {len(to_lookup)} words on Cambridge Dictionary...", flush=True)
found = 0
failed = []
ref_rows = []

for i, word in enumerate(to_lookup):
    w = word['w'].strip()
    print(f"[{i+1:3d}/{len(to_lookup)}] {w:20s}", end=" ", flush=True)
    
    zh = lookup(w)
    if zh:
        word['zh'] = zh
        found += 1
        ref_rows.append({'word': w, 'zh': zh, 'phonetic': word.get('p', ''), 'source': 'cambridge'})
        print(f"→ {zh[:50]}", flush=True)
    else:
        failed.append(w)
        ref_rows.append({'word': w, 'zh': '', 'phonetic': word.get('p', ''), 'source': 'not_found'})
        print("✗", flush=True)
    
    if i < len(to_lookup) - 1:
        time.sleep(0.7)  # Be nice to Cambridge's servers

# Save words.json
with open(WORDS_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print(f"\n✅ Saved words.json: {found} found, {len(failed)} failed", flush=True)

# Save reference CSV for future projects
if ref_rows:
    with open(REF_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['word', 'zh', 'phonetic', 'source'])
        writer.writeheader()
        writer.writerows(ref_rows)
    print(f"📄 Reference CSV: {REF_CSV}", flush=True)

if failed:
    print(f"\n❌ Failed ({len(failed)}): {', '.join(failed)}")
else:
    print("\n🎉 All words looked up successfully!")

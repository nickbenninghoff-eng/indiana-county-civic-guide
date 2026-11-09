"""Download Commons images listed in meta.json (output of commons_meta.py) into site/images. Images only.
Resumable; waits out HTTP 429 using Retry-After. Files over 9 MB are fetched as a 3840px-wide Commons thumbnail."""
import json, sys, os, time, urllib.request, urllib.parse, urllib.error, re
UA = {"User-Agent": "civic-guide-research/1.0 (local research)"}
meta = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
res = json.load(open(sys.argv[3])) if os.path.exists(sys.argv[3]) else {}
for title, p in meta.items():
    ii = p["imageinfo"][0]; name = title[5:].replace(" ", "_")
    safe = re.sub(r'[^A-Za-z0-9._-]', '_', name)
    dest = os.path.join(outdir, safe)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000 and title in res:
        continue
    big = ii["size"] > 9_000_000
    url = ("https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(name) + "?width=3840") if big else ii["url"].split("?")[0]
    data = None
    for attempt in range(6):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read(); break
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get("Retry-After", "60")) if e.code == 429 else 20
            print("HTTP", e.code, title, "wait", wait, flush=True); time.sleep(min(wait + 5, 650))
        except Exception as e:
            print("err", title, e, flush=True); time.sleep(20)
    if data is None:
        print("FAILED", title, flush=True); continue
    open(dest, "wb").write(data); res[title] = {"file": safe, "bytes": len(data), "resized": big}
    json.dump(res, open(sys.argv[3], "w"), indent=1)
    print("ok", safe, len(data), "resized" if big else "", flush=True)
    time.sleep(10)
print("DONE", flush=True)

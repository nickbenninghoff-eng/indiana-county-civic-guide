"""Fetch Commons imageinfo (size, license, artist, credit) for files listed in a TSV of titles. Metadata only."""
import json, sys, urllib.request, urllib.parse
UA={"User-Agent":"civic-guide-research/1.0 (local research)"}
titles=[l.strip() for l in open(sys.argv[1],encoding='utf-8') if l.strip()]
out={}
for i in range(0,len(titles),10):
    chunk=titles[i:i+10]
    q=urllib.parse.urlencode({"action":"query","format":"json","prop":"imageinfo","iiprop":"url|size|extmetadata","titles":"|".join(chunk)})
    d=json.load(urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php?"+q,headers=UA),timeout=60))
    for p in d["query"]["pages"].values():
        out[p["title"]]=p
json.dump(out,open(sys.argv[2],"w"),indent=1)
for t,p in out.items():
    ii=p.get("imageinfo",[{}])[0]; em=ii.get("extmetadata",{})
    print(t,"|",ii.get("size"),ii.get("width"),ii.get("height"),"|",em.get("LicenseShortName",{}).get("value"),"|",ii.get("url"))

"""Validate the community/people CSVs: parse, headers, column counts, enumerations, source-id integrity, file existence,
neutral wording, summary length. Run: python -P -E tools/validate_community_people.py"""
import csv, os, re, sys

R = r"C:\Users\nickb\local-gov-guide"
ED = R + r"\data\editions\st-joseph"
IN = R + r"\data\indiana"
errs = []
STATUS = {"official", "unofficial", "computed", "from_scan", "secondary", "single_source"}
HEAD = {
    "indicator_values.csv": "geo_type,geo_id,geo_name,indicator_id,value,moe,vintage,pulled_at,status,source_ids,notes",
    "employers.csv": "name,sector,employees,as_of,selection_rule,status,source_ids,notes",
    "timeline.csv": "date,category,title,description,status,confidence,source_ids",
    "people.csv": "person_id,name,offices_summary,parties,criteria,in_office_now,summary,documented_findings,image_id,status,confidence,source_ids,notes",
    "images.csv": "image_id,subject,file_page_url,direct_url,license,credit,local_file,notes",
    "research_on_voting.csv": "study_id,authors,title,outlet,date,geography,period,method,finding_summary,limits,url,status",
    "sources_community.csv": "id,url,title,publisher,accessed,kind,notes",
    "sources_people.csv": "id,url,title,publisher,accessed,kind,notes",
    "gaps_community_people.csv": "area,item,why_missing,how_to_fill",
}
BANNED = re.compile(r"\b(flip|flipped|sweep|swept|landslide|seized|won back|wave|safe|target|vulnerable)\b", re.I)


def count_sent(s):
    for ab in ("U.S.", "St.", "Jr.", "Sen.", "Rep.", "Gov.", "Dr.", "Mr.", "Mrs.", "J."):
        s = s.replace(ab, ab.replace(".", "~"))
    return len([x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z'])", s.strip()) if x])


def load(path, header):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if ",".join(rows[0]) != header:
        errs.append("%s: header mismatch" % path)
    for i, r in enumerate(rows[1:], 2):
        if len(r) != len(rows[0]):
            errs.append("%s line %d: %d cols" % (path, i, len(r)))
    return [dict(zip(rows[0], r)) for r in rows[1:]]


data = {}
for fn, h in HEAD.items():
    data[fn] = load(ED + "\\" + fn, h)
ind = load(IN + r"\indicators.csv", "indicator_id,label,definition,universe,source_dataset,table_variable,moe_rule,display_rule")

src = {r["id"] for r in data["sources_community.csv"]} | {r["id"] for r in data["sources_people.csv"]}
kinds = {"primary", "news", "secondary", "statute", "dataset", "derived"}
for fn in ("sources_community.csv", "sources_people.csv"):
    ids = [r["id"] for r in data[fn]]
    if len(ids) != len(set(ids)):
        errs.append(fn + ": duplicate ids")
    for r in data[fn]:
        if r["kind"] not in kinds:
            errs.append("%s %s bad kind" % (fn, r["id"]))
for fn in ("indicator_values.csv", "employers.csv", "timeline.csv", "people.csv"):
    for r in data[fn]:
        for s in r["source_ids"].split(";"):
            if s not in src:
                errs.append("%s: unknown source %s" % (fn, s))
        if "status" in r and r["status"] not in STATUS:
            errs.append("%s: bad status %s" % (fn, r["status"]))
ids = {r["indicator_id"] for r in ind}
used = {r["indicator_id"] for r in data["indicator_values.csv"]}
if used - ids:
    errs.append("indicator ids used but undefined: %s" % sorted(used - ids))
print("indicators defined but unused:", sorted(ids - used))
for r in data["indicator_values.csv"]:
    for k in ("value", "moe"):
        if r[k]:
            float(r[k])
cats = {"political", "economic", "government", "legal", "population"}
for r in data["timeline.csv"]:
    if r["category"] not in cats:
        errs.append("timeline bad category " + r["date"])
    if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", r["date"]):
        errs.append("timeline bad date " + r["date"])
    if r["confidence"] not in ("high", "medium", "low"):
        errs.append("timeline conf " + r["date"])
crit = {"TENURE", "FIRST", "HIGHER", "FAMILY", "TURNING_POINT"}
parties = {"D", "R", "L", "I", "G", "NP", "W", "O", ""}
for r in data["people.csv"]:
    if not set(r["criteria"].split(";")) <= crit or not r["criteria"]:
        errs.append("people criteria " + r["person_id"])
    if not set(r["parties"].split(";")) <= parties:
        errs.append("people party " + r["person_id"])
    if r["in_office_now"] not in ("true", "false"):
        errs.append("people in_office " + r["person_id"])
    n = count_sent(r["summary"])
    if not 2 <= n <= 4:
        errs.append("people summary sentences %s=%d" % (r["person_id"], n))
    if r["confidence"] not in ("high", "medium", "low"):
        errs.append("people conf " + r["person_id"])
    if r["image_id"] and r["image_id"] not in {i["image_id"] for i in data["images.csv"]}:
        errs.append("people image " + r["person_id"])
    for bad in ("Shembo", "Seeberg"):
        if bad in ",".join(r.values()):
            errs.append("people contains removed name " + bad)
for r in data["images.csv"]:
    if "Sharp" in r["subject"]:
        errs.append("Sharp image present")
    if not r["local_file"] or not os.path.exists(R + "\\" + r["local_file"].replace("/", "\\")):
        errs.append("image missing local file " + r["image_id"])
    elif os.path.getsize(R + "\\" + r["local_file"].replace("/", "\\")) < 1000:
        errs.append("image tiny " + r["image_id"])
for fn in ("timeline.csv", "people.csv", "employers.csv", "research_on_voting.csv"):
    for r in data[fn]:
        for k, v in r.items():
            if k not in ("url",) and BANNED.search(v):
                errs.append("banned word in %s %s: %s" % (fn, k, BANNED.search(v).group(0)))
print({k: len(v) for k, v in data.items()}, "indicators:", len(ind))
print("ERRORS:" if errs else "OK: all files parse and checks pass")
for e in errs:
    print(" -", e)
sys.exit(1 if errs else 0)

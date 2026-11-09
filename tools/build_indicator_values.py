"""Build data/editions/st-joseph/indicator_values.csv from saved source files (ACS 2020-2024 via Census Reporter
JSON, ACS 2006-2010 Summary File, BLS LAUS JSON, BLS QCEW CSV). Run: python -P -E tools/build_indicator_values.py"""
import csv, json, io, math, os, zipfile

R = r"C:\Users\nickb\local-gov-guide"
D = R + r"\sources\demographics"
OUT = R + r"\data\editions\st-joseph\indicator_values.csv"
PULLED = "2026-11-07"
rows = []


def add(gt, gid, gname, ind, val, moe, vint, status, src, notes=""):
    if val is not None and moe is not None and val != 0:
        cv = moe / 1.645 / abs(val) * 100
        if cv > 30:
            notes = (notes + "; " if notes else "") + "CV>30%% (CV=%.0f%%): treat as unreliable" % cv

    def f(x):
        if x is None:
            return ""
        if isinstance(x, float):
            return ("%.2f" % x).rstrip("0").rstrip(".")
        return str(x)

    rows.append([gt, gid, gname, ind, f(val), f(moe), vint, PULLED, status, src, notes])


tw = json.load(open(D + r"\censusreporter\acs2024_5yr_twp.json"))
cty = json.load(open(D + r"\censusreporter\acs2024_5yr_cty.json"))
bm = json.load(open(D + r"\censusreporter\acs2024_5yr_benchmarks.json"))
GEOS = [("county", "05000US18141", "St. Joseph County, Indiana"),
        ("place", "16000US1871000", "South Bend city, Indiana"),
        ("place", "16000US1849932", "Mishawaka city, Indiana")]
# The 7 incorporated towns. GEOIDs (state 18 + place FIPS) verified against the Census Bureau 2024 Gazetteer place file
# (www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_gaz_place_18.txt).
TOWNS = [("1836306", "Indian Village town"), ("1841670", "Lakeville town"), ("1852704", "New Carlisle town"),
         ("1854918", "North Liberty town"), ("1857114", "Osceola town"), ("1865988", "Roseland town"),
         ("1879694", "Walkerton town")]
for fips, nm in TOWNS:
    GEOS.append(("town", "16000US" + fips, nm + ", Indiana"))
TOWN_IDS = {"16000US" + f for f, _ in TOWNS}
# Census unified school districts that cover St. Joseph County (GEOIDs verified against the Census Bureau 2024 Gazetteer
# unified school district file, 2024_Gaz_unsd_national.txt). Districts can extend outside the county. LaVille School
# Corporation has no entry in that file, so it has no Census district figures.
SCHOOL_DISTRICTS = [("1810290", "South Bend Community School Corporation"), ("1808760", "Penn-Harris-Madison School Corporation"),
                    ("1806840", "Mishawaka School City"), ("1809120", "John Glenn School Corporation"),
                    ("1811910", "Union-North United School Corporation"), ("1807560", "New Prairie United School Corporation")]
for fips, nm in SCHOOL_DISTRICTS:
    GEOS.append(("school_district", "97000US" + fips, nm + ", Indiana"))
SD_IDS = {"97000US" + f for f, _ in SCHOOL_DISTRICTS}


def load_towns():
    """ACS 2020-2024 Summary File (table-based) rows filtered to the towns: {geo_id: {table: {cell_key: (est, moe)}}}.
    Census sentinel codes (-555555555 etc. = not applicable / insufficient sample) become None."""
    out = {}
    files = []
    for sub in ("acs2024_5yr_towns", "acs2024_5yr_districts"):
        td = D + "\\censusreporter\\" + sub
        files += [td + "\\" + fn for fn in sorted(os.listdir(td))]
    for path in files:
        tbl = os.path.basename(path).split("-")[1].split(".")[0].upper()
        rd = csv.reader(open(path, encoding="utf-8"), delimiter="|")
        hdr = next(rd)
        for r in rd:
            gid = r[0][:3] + "00US" + r[0].split("US")[1]
            t = out.setdefault(gid, {}).setdefault(tbl, {"estimate": {}, "error": {}})
            for name, v in zip(hdr[1:], r[1:]):
                k = name.split("_")[1][1:]
                key = tbl + k
                x = None if v in ("", "null") or float(v) <= -222222222 else float(v)
                t["estimate" if name.split("_")[1][0] == "E" else "error"][key] = x
    return out


TOWNDATA = load_towns()
for gid, g in sorted(tw["geography"].items()):
    if not gid.startswith("06000US"):
        continue
    GEOS.append(("county_subdivision", gid, g["name"]))
GEOS += [("state", "04000US18", "Indiana"), ("nation", "01000US", "United States")]


def geo2010(path):
    out = {}
    for r in csv.reader(open(path, encoding="latin-1")):
        if len(r) > 49:
            out[r[48]] = r[4]
    return out


g_in = geo2010(D + r"\acs2010\raw\g20105in.csv")
g_us = geo2010(D + r"\acs2010\raw_us\g20105us.csv")
SEQ = {"B01002": 11, "B01003": 11, "B03002": 13, "B05002": 17, "B15002": 40, "B17001": 44, "B19013": 53,
       "B19301": 59, "C24050": 75, "B25003": 95, "B25064": 98, "B25070": 98, "B25077": 99}
START = {"B01002": 162, "B01003": 192, "B03002": 38, "B05002": 13, "B15002": 90, "B17001": 7, "B19013": 177,
         "B19301": 172, "C24050": 143, "B25003": 11, "B25064": 54, "B25070": 107, "B25077": 83}
cache = {}


def load2010(prefix, folder, seq, kind):
    k = (prefix, seq, kind)
    if k in cache:
        return cache[k]
    z = zipfile.ZipFile("%s\\acs2010\\%s\\20105%s%04d000.zip" % (D, folder, prefix, seq))
    name = [n for n in z.namelist() if n.startswith(kind)][0]
    d = {}
    for r in csv.reader(io.TextIOWrapper(z.open(name), encoding="latin-1")):
        d[r[5]] = r
    cache[k] = d
    return d


def cell(vint, geo, table, n):
    gt, gid = geo[0], geo[1]
    if vint == 2024 and (gid in TOWN_IDS or gid in SD_IDS):
        t = TOWNDATA[gid][table]
        k = "%s%03d" % (table, n)
        return (t["estimate"].get(k), t["error"].get(k))
    if vint == 2024:
        src = bm if gt in ("state", "nation") else (tw if gt == "county_subdivision" else cty)
        t = src["data"][gid][table]
        k = "%s%03d" % (table, n)
        e, m = t["estimate"].get(k), t["error"].get(k)
        return (None if e is None else float(e), None if m is None else float(m))
    prefix, folder, gmap = ("in", "raw", g_in) if gt != "nation" else ("us", "raw_us", g_us)
    lr = gmap.get(gid)
    if lr is None:
        raise KeyError(gid)
    seq = SEQ[table]
    er = load2010(prefix, folder, seq, "e")[lr]
    mr = load2010(prefix, folder, seq, "m")[lr]
    i = START[table] - 1 + (n - 1)

    def f(x):
        return None if x in ("", ".", "-") else float(x)

    return f(er[i]), f(mr[i])


def ssum(cells):
    if any(c[0] is None for c in cells):
        return (None, None)
    return (sum(c[0] for c in cells), math.sqrt(sum((c[1] or 0) ** 2 for c in cells)))


def prop(num, den):
    if num[0] is None or den[0] in (None, 0):
        return (None, None)
    p = num[0] / den[0]
    mn, md = num[1] or 0, den[1] or 0
    t = mn ** 2 - p ** 2 * md ** 2
    moe = (math.sqrt(t) if t >= 0 else math.sqrt(mn ** 2 + p ** 2 * md ** 2)) / den[0]
    return (p * 100, moe * 100)


VINT = {2024: ("ACS 2020-2024 5-year", "COM-001", "2024 inflation-adjusted dollars"),
        2010: ("ACS 2006-2010 5-year", "COM-002", "2010 inflation-adjusted dollars")}
RACE = [("race_white_nh_pct", 3), ("race_black_nh_pct", 4), ("race_aian_nh_pct", 5), ("race_asian_nh_pct", 6),
        ("race_nhpi_nh_pct", 7), ("race_other_nh_pct", 8), ("race_two_or_more_nh_pct", 9), ("race_hispanic_pct", 12)]
IND_ID = ["agri_mining", "construction", "manufacturing", "wholesale", "retail", "transport_utilities", "information",
          "finance_real_estate", "professional_admin", "education_health", "arts_food_accom", "other_services",
          "public_admin"]

for vy in (2024, 2010):
    vint, src, dollar = VINT[vy]
    for geo in GEOS:
        gt, gid, gname = geo
        try:
            cell(vy, geo, "B01003", 1)
        except KeyError as e:
            print("missing geo", vy, gid, repr(e))
            continue

        def d(t, n):
            return cell(vy, geo, t, n)

        small = ("township-level small-area estimate" if gt == "county_subdivision" else
                 "small-town estimate: margins of error are large, read the CV flag" if gid in TOWN_IDS else
                 ("school district can extend outside St. Joseph County; figures cover everyone living in the district"
                  + ("; district boundaries in the 2006-2010 vintage may differ from 2020-2024" if vy == 2010 else ""))
                 if gid in SD_IDS else "")

        def put(ind, est, status="computed", note=""):
            # Town rows for 2024 come from the Census Bureau's table-based Summary File, not Census Reporter.
            s_id = ("COM-043" if (vy == 2024 and gid in TOWN_IDS) else
                    "COM-044" if (vy == 2024 and gid in SD_IDS) else src)
            add(gt, gid, gname, ind, est[0], est[1], vint, status, s_id, "; ".join(x for x in (note, small) if x))

        put("pop_total", d("B01003", 1), "official", "ACS 5-year period estimate, not a census count")
        put("median_age", d("B01002", 1), "official")
        tot = d("B03002", 1)
        for ind, n in RACE:
            put(ind, prop(d("B03002", n), tot), "computed", "B03002 cell %d / cell 1" % n)
        put("foreign_born_pct", prop(d("B05002", 13), d("B05002", 1)), "computed", "B05002 cell 13 / cell 1")
        if vy == 2024:
            ba = ssum([d("B15003", n) for n in (22, 23, 24, 25)])
            den = d("B15003", 1)
            note = "B15003 cells 22-25 / cell 1; population 25+"
        else:
            ba = ssum([d("B15002", n) for n in (15, 16, 17, 18, 32, 33, 34, 35)])
            den = d("B15002", 1)
            note = "B15002 cells 15-18 and 32-35 / cell 1 (B15003 did not exist in this vintage); population 25+"
        put("bachelors_plus_pct", prop(ba, den), "computed", note)
        put("median_hh_income", d("B19013", 1), "official", dollar)
        put("per_capita_income", d("B19301", 1), "official", dollar)
        put("poverty_pct", prop(d("B17001", 2), d("B17001", 1)), "computed", "B17001 cell 2 / cell 1")
        below = ssum([d("B17001", n) for n in list(range(4, 10)) + list(range(18, 24))])
        above = ssum([d("B17001", n) for n in list(range(33, 39)) + list(range(47, 53))])
        put("child_poverty_pct", prop(below, ssum([below, above])), "computed",
            "under-18 below poverty / under-18 with poverty status determined (B17001 cells 4-9,18-23 over 4-9,18-23,33-38,47-52)")
        put("owner_occupied_pct", prop(d("B25003", 2), d("B25003", 1)), "computed", "owner-occupied / occupied units")
        put("median_home_value", d("B25077", 1), "official", dollar + "; owner-occupied units")
        put("median_gross_rent", d("B25064", 1), "official", dollar)
        rb = ssum([d("B25070", n) for n in (7, 8, 9, 10)])
        t1, nc = d("B25070", 1), d("B25070", 11)
        rd = (t1[0] - nc[0], math.sqrt((t1[1] or 0) ** 2 + (nc[1] or 0) ** 2)) if t1[0] is not None and nc[0] is not None else t1
        put("rent_burdened_pct", prop(rb, rd), "computed",
            "B25070 cells 7-10 / (cell 1 minus cell 11 'not computed'); renter households paying 30%+ of income")
        ctot = d("C24050", 1)
        for iid, n in zip(IND_ID, range(2, 15)):
            put("emp_ind_" + iid + "_pct", prop(d("C24050", n), ctot), "computed",
                "C24050 cell %d / cell 1; employed civilians 16+ by place of residence" % n)
        put("emp_ind_employed_total", ctot, "official", "employed civilian population 16+ (denominator for emp_ind_*)")

# 2020 Census total population (P1_001N, PL 94-171 redistricting file) for every guide geography except state/nation.
PL = {}
for ln in open(D + r"\decennial2020\pl2020_P1_001N_st_joseph_geos.psv", encoding="utf-8").read().splitlines()[1:]:
    k, v = ln.split("|")
    PL[k] = int(v)
for gt, gid, gname in GEOS:
    if gt in ("state", "nation"):
        continue
    note = "2020 Census count (PL 94-171 P1_001N); a count, not a sample estimate"
    if gt == "school_district":
        note += "; school district can extend outside St. Joseph County"
    add(gt, gid, gname, "pop_census_2020", PL[gid[:3] + "0000US" + gid.split("US")[1]], None, "2020 Census", "official",
        "COM-045", note)

SB = {1850: 1652, 1860: 3832, 1870: 7206, 1880: 13280, 1890: 21819, 1900: 35999, 1910: 53684, 1920: 70983,
      1930: 104193, 1940: 101268, 1950: 115911, 1960: 132445, 1970: 125850, 1980: 109727, 1990: 105511,
      2000: 107789, 2010: 101168, 2020: 103453}
CO = {1930: 160033, 1940: 161823, 1950: 205058, 1960: 238614, 1970: 245045, 1980: 241617, 1990: 247052,
      2000: 265559, 2010: 266931, 2020: 272912}
MI = {1930: 28630, 1940: 28298, 1950: 32918, 1960: 33361, 1970: 36060, 1980: 40201, 1990: 42608, 2000: 46557,
      2010: 48252, 2020: 51063}
for gt, gid, nm, ser in (("county", "05000US18141", "St. Joseph County, Indiana", CO),
                         ("place", "16000US1871000", "South Bend city, Indiana", SB),
                         ("place", "16000US1849932", "Mishawaka city, Indiana", MI)):
    for y, v in ser.items():
        add(gt, gid, nm, "pop_total", v, None, "Decennial census %d" % y, "secondary", "COM-005",
            "Wikipedia table citing Census Bureau decennial counts; re-pull from census.gov recommended")
add("place", "16000US1871000", "South Bend city, Indiana", "pop_total", 103201, None, "Census population estimate 2025",
    "secondary", "COM-005", "Wikipedia-reported 2025 estimate; not a census count")
RACE20 = {("county", 2010): (75.56, 12.52, 1.87, 2.27, 7.27), ("county", 2020): (69.09, 12.98, 2.41, 4.94, 9.74),
          ("place", 2010): (55.82, 26.19, 1.28, 3.15, 12.96), ("place", 2020): (50.16, 25.23, 1.50, 5.47, 16.67)}
for (gt, y), vals in RACE20.items():
    gid, nm = (("05000US18141", "St. Joseph County, Indiana") if gt == "county"
               else ("16000US1871000", "South Bend city, Indiana"))
    for ind, v in zip(("race_white_nh_pct", "race_black_nh_pct", "race_asian_nh_pct", "race_two_or_more_nh_pct",
                       "race_hispanic_pct"), vals):
        add(gt, gid, nm, ind, v, None, "Decennial census %d (PL 94-171)" % y, "secondary", "COM-006",
            "Wikipedia table derived from Census PL 94-171; 2020 'two or more races' partly reflects Census processing changes")


def laus(path):
    out = {}
    for s in json.load(open(path))["Results"]["series"]:
        for x in s["data"]:
            if x["period"] == "M13":
                out[(s["seriesID"], int(x["year"]))] = float(x["value"])
    return out


L = {}
for f in ("bls-laus\\bls_2000.json", "bls-laus\\bls_2010.json", "bls-laus\\bls_2020.json",
          "bls-laus\\bench_2006.json", "bls-laus\\bench_2016.json", "bls-laus\\state_a.json", "bls-laus\\state_b.json"):
    L.update(laus(D + "\\" + f))
UN = [("county", "05000US18141", "St. Joseph County, Indiana", "LAUCN181410000000003"),
      ("place", "16000US1871000", "South Bend city, Indiana", "LAUCT187100000000003"),
      ("place", "16000US1849932", "Mishawaka city, Indiana", "LAUCT184993200000003"),
      ("state", "04000US18", "Indiana", "LAUST180000000000003"),
      ("nation", "01000US", "United States", "LNU04000000")]
for gt, gid, nm, sid in UN:
    for (s, y), v in sorted(L.items()):
        if s == sid and y >= 2000:
            note = "annual average, not seasonally adjusted; LAUS estimates are model-based and revised annually"
            if y == 2025:
                note += "; 2025 may be a partial-year average (BLS footnote on the county series: 11-month average excluding October)"
            add(gt, gid, nm, "unemployment_rate", v, None, "BLS LAUS annual average %d" % y, "official", "COM-003", note)

SECT = {"11": "Agriculture, forestry, fishing and hunting", "21": "Mining, quarrying, and oil and gas extraction",
        "22": "Utilities", "23": "Construction", "31-33": "Manufacturing", "42": "Wholesale trade",
        "44-45": "Retail trade", "48-49": "Transportation and warehousing", "51": "Information",
        "52": "Finance and insurance", "53": "Real estate and rental and leasing",
        "54": "Professional, scientific, and technical services", "55": "Management of companies and enterprises",
        "56": "Administrative and support and waste management", "61": "Educational services",
        "62": "Health care and social assistance", "71": "Arts, entertainment, and recreation",
        "72": "Accommodation and food services", "81": "Other services (except public administration)"}
OWN = {"1": "federal_gov", "2": "state_gov", "3": "local_gov"}
for y in range(2001, 2026):
    p = D + "\\bls-qcew\\qcew_%d.csv" % y
    if not os.path.exists(p):
        continue
    for r in csv.DictReader(open(p, encoding="utf-8")):
        key = None
        if r["agglvl_code"] == "70" and r["own_code"] == "0":
            key = ("qcew_jobs_all_ownerships", "All ownerships, total covered")
        elif r["agglvl_code"] == "71" and r["own_code"] in OWN and r["industry_code"] == "10":
            key = ("qcew_jobs_" + OWN[r["own_code"]], "Government (own_code %s)" % r["own_code"])
        elif r["agglvl_code"] == "71" and r["own_code"] == "5" and r["industry_code"] == "10":
            key = ("qcew_jobs_private", "Private total")
        elif r["agglvl_code"] == "74" and r["own_code"] == "5" and r["industry_code"] in SECT:
            key = ("qcew_jobs_naics_" + r["industry_code"].replace("-", "_"), "Private, " + SECT[r["industry_code"]])
        if not key:
            continue
        dc = r.get("disclosure_code", "").strip()
        val = None if dc == "N" else float(r["annual_avg_emplvl"])
        note = ("annual average employment of jobs located in the county (not residents); NAICS revisions "
                "(2002, 2007, 2012, 2017) limit comparability across years")
        if dc == "N":
            note += "; suppressed for disclosure"
        add("county", "05000US18141", "St. Joseph County, Indiana", key[0], val, None, "QCEW %d annual" % y,
            "official", "COM-004", key[1] + "; " + note)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow("geo_type,geo_id,geo_name,indicator_id,value,moe,vintage,pulled_at,status,source_ids,notes".split(","))
    w.writerows(rows)
print(len(rows), "rows")

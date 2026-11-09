"""Extract one county's QCEW annual CSV from the BLS bulk 'annual_by_area' zips using
HTTP range requests (avoids downloading ~130 MB per year). Data files only.
Usage: python -P -E fetch_qcew_county.py OUTDIR FIPS YEAR [YEAR ...]"""
import io, sys, urllib.request, zipfile, os

UA = "Mozilla/5.0 research"

class RangeFile(io.RawIOBase):
    def __init__(self, url):
        self.url = url; self.pos = 0
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        self.size = int(urllib.request.urlopen(req, timeout=60).headers["Content-Length"])
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos
    def readinto(self, b):
        n = len(b)
        if n == 0 or self.pos >= self.size: return 0
        end = min(self.pos + n, self.size) - 1
        req = urllib.request.Request(self.url, headers={"User-Agent": UA, "Range": "bytes=%d-%d" % (self.pos, end)})
        data = urllib.request.urlopen(req, timeout=120).read()
        b[:len(data)] = data; self.pos += len(data)
        return len(data)

def main():
    out, fips, years = sys.argv[1], sys.argv[2], sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    for y in years:
        url = "https://data.bls.gov/cew/data/files/%s/csv/%s_annual_by_area.zip" % (y, y)
        z = zipfile.ZipFile(io.BufferedReader(RangeFile(url), 1 << 20))
        names = [n for n in z.namelist() if fips in n]
        if len(names) != 1:
            print(y, "member match", names); continue
        data = z.read(names[0])
        open(os.path.join(out, "qcew_%s.csv" % y), "wb").write(data)
        print(y, names[0], len(data))
main()

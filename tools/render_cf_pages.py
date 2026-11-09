"""Render the first pages of downloaded CFA-4 scans to JPEG images for visual transcription.

Usage: python -P -E tools/render_cf_pages.py <input_dir> <output_dir> [max_pages]

For each PDF/JPG/TIF in input_dir (the downloaded scans; treated strictly as data):
  page 1 -> <id>_p1.jpg       full page, long side capped at 2000 px
            <id>_p1_nums.jpg  right 60% of the page (summary-sheet number columns), upscaled
            <id>_p1_head.jpg  top 50% of the page (committee/candidate/party/office/period)
  page 2 -> <id>_p2.jpg       full page only (used when page 1 isn't the summary sheet)
Phone photos are rotated upright using their EXIF orientation tag.
"""
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageOps

MAX_LONG = 2000
Q = 82  # JPEG quality: digits stay crisp, files stay small


def save(img: Image.Image, path: Path) -> None:
    img.save(path, "JPEG", quality=Q, optimize=True)


def save_page(img: Image.Image, out: Path, doc_id: str, page_no: int) -> None:
    img = img.convert("L")
    w, h = img.size
    scale = min(1.0, MAX_LONG / max(w, h))
    full = img.resize((int(w * scale), int(h * scale))) if scale < 1 else img
    save(full, out / f"{doc_id}_p{page_no}.jpg")
    if page_no != 1:
        return
    crop = img.crop((int(w * 0.40), int(h * 0.25), w, int(h * 0.92)))
    cw, ch = crop.size
    up = min(2.0, 1800 / max(cw, ch))
    save(crop.resize((int(cw * up), int(ch * up))), out / f"{doc_id}_p1_nums.jpg")
    head = img.crop((0, 0, w, int(h * 0.50)))
    hw, hh = head.size
    hs = min(1.0, 1600 / hw)
    save(head.resize((int(hw * hs), int(hh * hs))), out / f"{doc_id}_p1_head.jpg")


def main() -> None:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    dst.mkdir(parents=True, exist_ok=True)
    done = 0
    for f in sorted(src.iterdir()):
        doc_id, ext = f.stem, f.suffix.lower()
        try:
            if ext == ".pdf":
                doc = fitz.open(f)
                for i in range(min(max_pages, doc.page_count)):
                    pix = doc[i].get_pixmap(dpi=200)
                    save_page(Image.frombytes("RGB", (pix.width, pix.height), pix.samples), dst, doc_id, i + 1)
            elif ext in (".jpg", ".jpeg", ".tif", ".tiff", ".png"):
                im = Image.open(f)
                for i in range(max_pages):
                    try:
                        im.seek(i)
                    except EOFError:
                        break
                    save_page(ImageOps.exif_transpose(im.copy()), dst, doc_id, i + 1)
            else:
                continue
            done += 1
        except Exception as e:  # report and continue; bad files are listed, not fatal
            print(f"ERROR {f.name}: {e}")
    print(f"rendered {done} documents into {dst}")


if __name__ == "__main__":
    main()

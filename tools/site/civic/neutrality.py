"""Neutrality lint terms (ux-review section 6). Shared by the builder and the checker.

Matched case-insensitively as whole words/phrases in the visible text of generated pages.
'wave' and 'target' are matched as whole words, so 'microwave' or 'targeted' don't count;
add inflections explicitly if they should be banned too.
"""
import re

BANNED_TERMS = [
    "flip", "flips", "flipped", "flipping",
    "sweep", "swept",
    "landslide",
    "seized",
    "won back",
    "wave",
    "safe seat",
    "target",
    "vulnerable",
    "battleground",
]

BANNED_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in BANNED_TERMS) + r")\b", re.I)


def find_banned(text: str) -> list[str]:
    return [m.group(0) for m in BANNED_RE.finditer(text or "")]

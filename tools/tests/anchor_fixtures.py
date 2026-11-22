"""Loads the old-anchor fixtures (tools/tests/fixtures/anchors_before_*.json) for the tests that pin every id a page
had before a change.

The fixtures recorded every id on each page, including the ids of two data-only script blocks,
<script type="application/json" id="here-data"> and id="paths-data". They were never anchors a reader could land on:
a script element is not rendered, so a link to #here-data scrolled nowhere. On 2026-11-18 (maps-cleanup brief, part B
item 2, page weight) that data moved to the shared assets/site-data.js (window.civicData), so the two blocks left every
page. The fixture files are kept exactly as recorded; only these retired data-block ids are left out when loading.
Every other id is still checked as before.
"""
from __future__ import annotations

import json
from pathlib import Path

RETIRED_DATA_IDS = frozenset({"here-data", "paths-data"})


def _strip(o):
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_strip(x) for x in o if not (isinstance(x, str) and x in RETIRED_DATA_IDS)]
    return o


def anchor_fixture(path: Path):
    """The fixture's JSON without the retired data-block ids (in any list, at any depth)."""
    return _strip(json.loads(Path(path).read_text(encoding="utf-8")))

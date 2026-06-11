# ── Prospera SYSTEM HEADER (ADR-0032/SBOM) ──
# 性質:engineering ｜設計:Kevin 架構 ｜執行:AI 工具(claude.ai+Claude Code)
# 驗證:無機制驗證 ｜IP:創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)
"""Build demo v3.0 by downloading the 10 Unsplash bathroom photos used in v2.0,
center-cropping each to 1024x1024 JPEG, base64-encoding, and inlining as
data URIs in a new HTML file. No API key required (direct CDN download)."""
import base64
import io
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image

# Force UTF-8 stdout on Windows (default cp950 can't print Chinese / unicode)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 10 unique Unsplash photo IDs that appear in v2.0 (curated bathroom set)
PHOTO_IDS = [
    "photo-1552321554-5fefe8c9ef14",
    "photo-1584622650111-993a426fbf0a",
    "photo-1600607687939-ce8a6c25118c",
    "photo-1507652313519-d4e9174996dd",
    "photo-1600566753190-17f0baa2a6c3",
    "photo-1620626011761-996317702519",
    "photo-1556909114-f6e7ad7d3136",
    "photo-1600585154340-be6161a56a0c",
    "photo-1600607687644-c7171b42498f",
    "photo-1600607688969-a5bfcd646154",
]

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "demo" / "generated"
CACHE.mkdir(parents=True, exist_ok=True)
SRC_HTML = ROOT / "demo" / "欣轅官網_視覺Demo_v2.0.html"
OUT_HTML = ROOT / "demo" / "欣轅官網_視覺Demo_v3.0.html"

UA = "Mozilla/5.0 (prospera-client-xinyuan/v3-demo build)"


def fetch_and_square(photo_id: str) -> bytes:
    """Download, center-crop to square, resize to 1024x1024, JPEG q85."""
    cache_path = CACHE / f"{photo_id}.jpg"
    if cache_path.exists() and cache_path.stat().st_size > 50_000:
        return cache_path.read_bytes()

    url = f"https://images.unsplash.com/{photo_id}?w=1600&q=90&auto=format&fit=crop"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize(
        (1024, 1024), Image.LANCZOS
    )

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True, progressive=True)
    jpeg = buf.getvalue()
    cache_path.write_bytes(jpeg)
    return jpeg


def main() -> int:
    print(f"Source HTML: {SRC_HTML.name}")
    print(f"Target HTML: {OUT_HTML.name}\n")

    b64_map: dict[str, str] = {}
    total_jpeg = 0
    last_good_jpeg: bytes | None = None
    failed: list[str] = []
    for pid in PHOTO_IDS:
        try:
            jpeg = fetch_and_square(pid)
            last_good_jpeg = jpeg
            tag = "[ok]  "
        except Exception as exc:
            # Reuse most recent successful image so the URL still gets a real
            # data URI and the offline page renders correctly.
            if last_good_jpeg is None:
                # First photo failed — try later photos first, then come back.
                print(f"  [skip] {pid}: {exc}  (will retry after siblings)")
                failed.append(pid)
                continue
            jpeg = last_good_jpeg
            failed.append(pid)
            tag = "[sub] "
            print(f"  [warn] {pid}: {exc}  -> using previous image as substitute")
        total_jpeg += len(jpeg)
        b64 = base64.b64encode(jpeg).decode("ascii")
        b64_map[pid] = b64
        print(f"  {tag}{pid}  JPEG {len(jpeg)//1024:>4} KB   b64 {len(b64)//1024:>4} KB")

    # Retry any pid that failed before we had any successful download
    pending = [pid for pid in PHOTO_IDS if pid not in b64_map]
    for pid in pending:
        if last_good_jpeg is None:
            print(f"  [FAIL] {pid}: no successful download to substitute from")
            return 1
        jpeg = last_good_jpeg
        total_jpeg += len(jpeg)
        b64 = base64.b64encode(jpeg).decode("ascii")
        b64_map[pid] = b64
        print(f"  [sub] {pid}  (substituted with last good image)")

    print(
        f"\n10 images: {total_jpeg/1024:.1f} KB JPEG, "
        f"{sum(len(v) for v in b64_map.values())/1024:.1f} KB base64\n"
    )

    if not SRC_HTML.exists():
        print(f"Missing source: {SRC_HTML}", file=sys.stderr)
        return 2

    html = SRC_HTML.read_text(encoding="utf-8")
    replaced_total = 0
    for pid, b64 in b64_map.items():
        data_uri = f"data:image/jpeg;base64,{b64}"
        # Match any Unsplash CDN URL containing this photo ID
        pattern = re.compile(
            rf"https://images\.unsplash\.com/{re.escape(pid)}\?[^'\"\)\s]+"
        )
        matches = pattern.findall(html)
        if matches:
            html = pattern.sub(data_uri, html)
            replaced_total += len(matches)
            print(f"  {pid}: {len(matches)} URL → data URI")

    # Version bump in title/comment
    html = html.replace(
        "<title>欣轅室內工程｜官網 Demo v2.0</title>",
        "<title>欣轅室內工程｜官網 Demo v3.0</title>",
    )

    # Sanity check: any Unsplash URLs left?
    leftover = re.findall(r"https://images\.unsplash\.com/photo-[\w-]+", html)
    if leftover:
        print(f"\n[WARN] {len(leftover)} Unsplash URL(s) remain unreplaced:")
        for u in leftover[:5]:
            print(f"    {u}")
        return 3

    OUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUT_HTML.stat().st_size / 1024
    print(
        f"\n[DONE] Wrote {OUT_HTML.name}  ({size_kb:.1f} KB, "
        f"{replaced_total} URL replacements)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

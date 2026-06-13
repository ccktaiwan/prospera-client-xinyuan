#!/usr/bin/env python3
"""
system_inventory_gen.py — Prospera SYSTEM_INVENTORY 生成器（SBOM/SPDX 對齊，治理 ground truth）

對齊 STD-SBOM-SPDX（external-alignment）：SPDX 必填(SPDXID/Name/Version/Checksum/★CopyrightText IP 原生)+Prospera 映射。
產 <repo>/SYSTEM_INVENTORY.json（每檔字段）+ 摘要（總檔/有 IP/裸檔/header 統一率/nature 分布）。
完整性＝對照 git ls-files 全檔數（EXTS 源碼+非源碼豁免對帳，不漏才是 ground truth）。

ground_truth_check 結構（G-4 維度3 升級）：
  complete_at_head: 生成時 HEAD hash（HEAD 變動=需重跑）
  src_count_at_head: git ls-files EXTS 源碼數
  inventoried: 實際盤點數（應=src_count）
  complete: inventoried == src_count_at_head
  all_files_count: git ls-files 全檔數（含非源碼）
  all_files_gap: all_files_count - src_count_at_head（非 EXTS 追蹤檔數量）
  non_src_exts_excluded: 豁免副檔名清單（設計上不納源碼盤點）

用法：python system_inventory_gen.py <repo路徑> [--write]   # --write 才寫 JSON，否則只印摘要
"""
import sys
import json
import hashlib
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# G-2 維度1：擴展 EXTS 覆蓋所有可承載 IP 的追蹤格式
EXTS = (".py", ".md", ".yml", ".yaml", ".txt", ".json",
        ".ps1",       # PowerShell，# comment 可承載
        ".html",      # HTML，<!-- --> comment 可承載
        ".gitignore") # gitignore，# comment 可承載
# G-2 具名豁免清單（12 檔）：逐檔列明理由，禁整類一句帶過
NAMED_EXEMPTIONS = {
    "_inbox/_processed/.gitkeep":                                      "空目錄標記（0 bytes），無 IP 承載空間",
    "_inbox/from-claude-ai/.gitkeep":                                  "空目錄標記（0 bytes），無 IP 承載空間",
    "00_governance/task_registry/ARCHIVE/.gitkeep":                    "空目錄標記（0 bytes），無 IP 承載空間",
    "01_docs/.gitkeep":                                                "空目錄標記（0 bytes），無 IP 承載空間",
    "01_docs/merged-governance/governance/verticals/exam/.keep":       "空目錄標記（0 bytes），無 IP 承載空間",
    "00_governance/sessions/_v33_run.log":                             "runtime 自動生成執行日誌，非創作性內容",
    "00_governance/sessions/_v34_run.log":                             "runtime 自動生成執行日誌，非創作性內容",
    "00_governance/sessions/_v34_run2.log":                            "runtime 自動生成執行日誌，非創作性內容",
    "autogov_v2.jsonl":                                                "governance check 自動執行日誌（runtime 生成）",
    "autogov_v3.jsonl":                                                "governance check 自動執行日誌（runtime 生成）",
    "governance/evidence_ledger.jsonl":                                "執行時期 evidence 記錄（runtime append-only）",
    ".github/CODEOWNERS":                                              "GitHub CODEOWNERS 特殊格式，repo 級 IP_NOTICE.md 涵蓋",
}
ARCHIVE_HINT = ("99_archive", "archive", "_archive", "ARCHIVE")
IDEA_HINT = ("docs", "design", "spec", "governance", "architecture", "_inbox", "adr", "ADR")


def _sha256(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception:
        return ""


def _git_sha(repo: Path, rel: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%h", "--", rel],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        return out.stdout.strip()
    except Exception:
        return ""


def _git_head(repo: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        return out.stdout.strip()[:12] if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _nature(rel: str, ext: str) -> str:
    low = rel.lower()
    if any(h.lower() in low for h in ARCHIVE_HINT):
        return "archive"
    if ext in (".json", ".yml", ".yaml", ".gitignore"):
        return "config"
    if ext in (".py", ".ps1"):
        return "engineering"
    if ext == ".html":
        return "doc"
    if ext == ".md" and any(h.lower() in low for h in IDEA_HINT):
        return "idea"
    if ext == ".md":
        return "doc"
    return "data"


def gen(repo: Path) -> dict:
    all_files = subprocess.run(
        ["git", "-C", str(repo), "ls-files"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout.splitlines()
    src = [f for f in all_files if Path(f).suffix.lower() in EXTS]
    non_src = [f for f in all_files if Path(f).suffix.lower() not in EXTS]
    # 非源碼副檔名統計（豁免清單）
    from collections import Counter
    non_src_ext_counts = Counter(Path(f).suffix.lower() for f in non_src)
    head = _git_head(repo)
    items = []
    for rel in sorted(src):
        p = repo / rel
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            txt = ""
        has_ip = "創造性歸 Kevin" in txt
        nature = _nature(rel, ext)
        items.append({
            "SPDXID": f"{repo.name}:{rel}",
            "path": rel,
            "repo": repo.name,
            "dir": str(Path(rel).parent),
            "type": ext,
            "nature": nature,
            "ip": "創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)",
            "header_status": "unified" if has_ip else "bare",
            "checksum_sha256": _sha256(p),
            "version_git_sha": _git_sha(repo, rel),
            "active_or_archive": "archive" if nature == "archive" else "active",
        })
    n = len(items)
    with_ip = sum(1 for i in items if i["header_status"] == "unified")
    natdist = Counter(i["nature"] for i in items)
    inv = {
        "_schema": "Prospera SYSTEM_INVENTORY v2 (SPDX-aligned, G-4 持續收斂)",
        "repo": repo.name,
        "total_src_files": n,
        "ground_truth_check": {
            "complete_at_head": head,
            "src_count_at_head": len(src),
            "inventoried": n,
            "complete": len(src) == n,
            "all_files_count": len(all_files),
            "all_files_gap": len(all_files) - len(src),
            "non_src_exts_excluded": dict(non_src_ext_counts),
            "named_exemptions": {f: NAMED_EXEMPTIONS[f] for f in all_files
                                 if f in NAMED_EXEMPTIONS},
            "note": "HEAD 變動後需重跑以保持 complete_at_head 有效"
        },
        "ip_coverage": {"with_ip": with_ip, "bare": n - with_ip, "pct": round(with_ip / n * 100, 1) if n else 0},
        "nature_distribution": dict(natdist),
        "files": items,
    }
    return inv


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python system_inventory_gen.py <repo路徑> [--write]")
        return 0
    repo = Path(sys.argv[1])
    write = "--write" in sys.argv
    inv = gen(repo)
    gtc = inv["ground_truth_check"]
    print(f"=== SYSTEM_INVENTORY: {inv['repo']} ===")
    print(f"總源碼檔: {inv['total_src_files']}｜ground truth 完整: {gtc['complete']}"
          f"（git_src={gtc['src_count_at_head']}/盤={gtc['inventoried']}）HEAD={gtc['complete_at_head']}")
    print(f"全檔: {gtc['all_files_count']} | 非源碼: {gtc['all_files_gap']} | 豁免ext: {gtc['non_src_exts_excluded']}")
    print(f"IP 覆蓋: {inv['ip_coverage']['with_ip']}/{inv['total_src_files']}（{inv['ip_coverage']['pct']}%）｜裸檔: {inv['ip_coverage']['bare']}")
    print(f"nature 分布: {inv['nature_distribution']}")
    if write:
        out = repo / "SYSTEM_INVENTORY.json"
        out.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ 寫入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

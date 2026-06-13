#!/usr/bin/env python3
"""
apply_system_inventory.py — 一遍三件自動化（盤點+統一header+IP標註+IP_NOTICE+收斂驗證）

可複用逐 repo 調用（治「逐 repo 慢」）。nature 用**命名+內容架構雙信號**判定（可機器判，非語意黑盒）。

nature 判定（命名 signal × 內容 signal，衝突標 ⚠️ 待複核——極少數才真要人看）：
  - idea 想法档（AI 謄寫,IP 完全歸 Kevin）：命名 DESIGN/ARCH/SPEC/ADR/STRATEGY/PHILOSOPHY/README + 內容論述為主
  - engineering 工程档（AI 執行,創造性歸 Kevin/AI 落地）：命名 *.py/_agent/_check/_service/handler/util + 內容 函數/類為主
  - config/產物（repo 級覆蓋）：*.json/*.yml/config/lock/自動產物
  - archive：99archive/ARCHIVE 路徑

處理：idea/doc/engineering → per-file 統一 header+IP；config/archive/data → repo 級 IP_NOTICE 覆蓋（不逐檔）。
已有 IP（創造性歸 Kevin）→ 跳過。.json/.ipynb 無註解 → IP_NOTICE 覆蓋。

用法：python apply_system_inventory.py <repo路徑> [--apply]   # 無 --apply 只報判定/收斂預覽
"""
import sys, re, json, hashlib, subprocess
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXTS = (".py", ".md", ".yml", ".yaml", ".txt", ".json",
        ".ps1",        # G-2 新增
        ".html",       # G-2 新增
        ".gitignore")  # G-2 新增
ARCH = ("99_archive", "/archive", "_archive", "/ARCHIVE", "99archive")
IDEA_NAME = re.compile(r"DESIGN|ARCH|SPEC|ADR|STRATEG|PHILOSOPH|PRINCIPLE|VISION|_design|_spec|README|MAINLINE|META_ALGO|PARADIGM|CONTRACT|ECOSYSTEM|TOPOLOGY", re.I)
ENG_NAME = re.compile(r"_agent|_check|_service|_handler|_util|_engine|_loader|_runtime|_orchestrat|test_|_test|conftest", re.I)
PER_FILE_NATURES = {"idea", "doc", "engineering"}
# G-3 路徑B：可用 comment 承載 IP header 的副檔名（含 G-2 新增）
COMMENT_EXTS = (".py", ".md", ".yml", ".yaml", ".txt", ".ps1", ".gitignore")
# .html 獨立處理（<!-- --> comment，非 #）
HTML_EXTS = (".html",)
IP_NOTICE_FIELD = "創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)"
# G-2 具名豁免（與 system_inventory_gen.py 同步）
NAMED_EXEMPTIONS = {
    "_inbox/_processed/.gitkeep", "_inbox/from-claude-ai/.gitkeep",
    "00_governance/task_registry/ARCHIVE/.gitkeep", "01_docs/.gitkeep",
    "01_docs/merged-governance/governance/verticals/exam/.keep",
    "00_governance/sessions/_v33_run.log",
    "00_governance/sessions/_v34_run.log",
    "00_governance/sessions/_v34_run2.log",
    "autogov_v2.jsonl", "autogov_v3.jsonl",
    "governance/evidence_ledger.jsonl", ".github/CODEOWNERS",
}


def _sha(p):
    try: return hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception: return ""

def _gsha(repo, rel):
    try: return subprocess.run(["git","-C",str(repo),"log","-1","--format=%h","--",rel],capture_output=True,text=True,timeout=10).stdout.strip()
    except Exception: return ""


def judge_nature(rel: str, ext: str, text: str):
    """命名+內容雙信號 → (nature, confidence, conflict_note)。"""
    low = rel.lower()
    if any(h.lower() in ("/"+low) for h in ARCH) or "archive" in low:
        return "archive", "high", ""
    if ext in (".json", ".yml", ".yaml"):
        return "config", "high", ""
    base = Path(rel).name
    # 命名 signal
    if ext == ".py":
        name_sig = "engineering"
    elif ext == ".md":
        name_sig = "idea" if IDEA_NAME.search(base) else "doc"
    elif ext == ".txt":
        name_sig = "data"
    else:
        name_sig = "data"
    # 內容 signal（架構：論述 vs code）
    code_lines = len(re.findall(r"^\s*(def |class |import |from |return |if |for |while )", text, re.M))
    prose_lines = len([l for l in text.splitlines() if l.strip() and not l.strip().startswith(("#", "//", "*"))])
    fence = text.count("```")
    if ext == ".py":
        content_sig = "engineering" if code_lines >= 3 else "idea"  # .py 但幾乎無 code→疑設計
    elif ext == ".md":
        content_sig = "engineering" if (fence >= 4 and code_lines > prose_lines * 0.5) else ("idea" if prose_lines > 10 else "doc")
    else:
        content_sig = name_sig
    # 雙信號一致性
    conflict = ""
    if name_sig == content_sig:
        nature, conf = name_sig, "high"
    elif {name_sig, content_sig} <= {"idea", "doc"}:
        nature, conf = "idea" if "idea" in (name_sig, content_sig) else "doc", "high"
    else:
        nature, conf = name_sig, "review"  # 衝突（如 .py 全是設計注釋）
        conflict = f"⚠️ 命名={name_sig}/內容={content_sig} 衝突,待複核"
    return nature, conf, conflict


def header_for(ext, nature):
    if ext in (".md", ".html"):
        return (f"<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:{nature} | 設計:Kevin 架構 | "
                f"執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | "
                f"IP:創造性歸 Kevin(發明人), AI 為執行工具 -->\n")
    return ("# ── Prospera SYSTEM HEADER (ADR-0032/SBOM) ──\n"
            f"# 性質:{nature} ｜設計:Kevin 架構 ｜執行:AI 工具(claude.ai+Claude Code)\n"
            f"# 驗證:無機制驗證 ｜IP:創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)\n")


def insert_header(text: str, header: str, ext: str) -> str:
    """安全插入 header：strip BOM + 插在 shebang/encoding 宣告後（防破壞 .py 語法）。"""
    text = text.lstrip("﻿")  # 移除 BOM（防插入後 BOM 跑到檔中=語法錯）
    if ext == ".py":
        lines = text.split("\n")
        ins = 0
        if lines and lines[0].startswith("#!"):           # shebang 須留第 1 行
            ins = 1
        # encoding 宣告（coding:）須在前 2 行
        for i in range(ins, min(ins + 2, len(lines))):
            if i < len(lines) and re.search(r"coding[:=]", lines[i]):
                ins = i + 1
        return "\n".join(lines[:ins] + header.rstrip("\n").split("\n") + lines[ins:])
    return header + text


IP_NOTICE_TXT = (
"# IP_NOTICE — {repo}\n\n"
"> 本 repo 全部創造性內容（架構/設計/方案/原創 code/文檔）之 **IP 歸屬 Kevin（發明人）**；"
"AI（claude.ai+Claude Code）為**執行工具**，依 Kevin 設計落地，不取得 IP。\n"
"> 對齊 SPDX `PackageCopyrightText`；標準 ADR-0032 / STD-SBOM-SPDX。"
"本聲明為目錄級預設，覆蓋全 repo 檔（含無法加 header 的 .json 等）。\n\n"
"*SPDX-aligned repo-level copyright: 創造性歸 Kevin(發明人), AI 為執行工具。*\n")


def _add_json_ip_notice(text: str) -> tuple[str, bool]:
    """JSON 加 _ip_notice 欄位（G-3 路徑C）。回傳 (new_text, changed)。

    G-6 修正：先 strip UTF-8 BOM 再 parse（先前 BOM-prefixed JSON 被 json.loads
    以 'Unexpected UTF-8 BOM' 拒收 → 誤判 invalid → 假豁免；strip 後可正常覆蓋，
    寫回為標準無-BOM UTF-8）。
    """
    try:
        data = json.loads(text.lstrip("﻿"))
        if not isinstance(data, dict):
            return text, False
        if "_ip_notice" in data:
            return text, False  # 已有
        # 插入為第一個欄位，保持可讀性
        new_data = {"_ip_notice": IP_NOTICE_FIELD}
        new_data.update(data)
        return json.dumps(new_data, ensure_ascii=False, indent=2), True
    except Exception:
        return text, False  # 非合法 JSON，跳過


def run(repo: Path, apply: bool):
    files = subprocess.run(["git","-C",str(repo),"ls-files"],capture_output=True,text=True,encoding="utf-8",errors="replace").stdout.splitlines()
    src = [f for f in files if Path(f).suffix.lower() in EXTS]
    items, applied, json_ip_added, repo_level, reviews, conf_high = [], 0, 0, 0, [], 0
    for rel in sorted(src):
        p = repo / rel
        if not p.is_file(): continue
        ext = p.suffix.lower()
        try: t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception: continue
        has_ip = "創造性歸 Kevin" in t
        nature, conf, conflict = judge_nature(rel, ext, t)
        if conf == "review": reviews.append((rel, conflict))
        else: conf_high += 1

        # 豁免檔：跳過 IP 補寫，歸 repo_level_covered
        if rel in NAMED_EXEMPTIONS:
            items.append({"SPDXID": f"{repo.name}:{rel}", "path": rel, "repo": repo.name,
                          "type": ext, "nature": "exempt", "nature_confidence": "high",
                          "ip": IP_NOTICE_FIELD,
                          "header_status": "repo_level_covered",
                          "exempt_reason": "named_exemption",
                          "checksum_sha256": _sha(p), "version_git_sha": _gsha(repo, rel),
                          "active_or_archive": "active"})
            repo_level += 1
            continue

        # 路徑B：COMMENT_EXTS + HTML 走 per-file comment header
        do_perfile = (not has_ip) and (ext in COMMENT_EXTS or ext in HTML_EXTS) and (
            nature in PER_FILE_NATURES or ext in (".yml", ".yaml", ".txt", ".ps1", ".gitignore", ".html"))

        # 路徑C：JSON 加 _ip_notice 欄位
        do_json_ip = (not has_ip) and ext == ".json"

        if do_perfile and apply:
            p.write_text(insert_header(t, header_for(ext, nature), ext), encoding="utf-8")
            applied += 1; has_ip = True
        elif do_json_ip and apply:
            new_t, changed = _add_json_ip_notice(t)
            if changed:
                p.write_text(new_t, encoding="utf-8")
                json_ip_added += 1; has_ip = True
            else:
                repo_level += 1  # 非法 JSON 或已有 _ip_notice 但未含偵測字串
        elif not has_ip:
            repo_level += 1  # archive 或真正無法加 IP 者

        items.append({"SPDXID": f"{repo.name}:{rel}", "path": rel, "repo": repo.name,
                      "type": ext, "nature": nature, "nature_confidence": conf,
                      "ip": IP_NOTICE_FIELD,
                      "header_status": "unified" if has_ip else "repo_level_covered",
                      "checksum_sha256": _sha(p), "version_git_sha": _gsha(repo, rel),
                      "active_or_archive": "archive" if nature == "archive" else "active"})
    if apply:
        (repo / "IP_NOTICE.md").write_text(IP_NOTICE_TXT.format(repo=repo.name), encoding="utf-8")
    n = len(items)
    inv = {"_schema": "Prospera SYSTEM_INVENTORY v2 (SPDX-aligned, G-3 IP結構極限)", "repo": repo.name,
           "total_src_files": n,
           "ground_truth_complete": len(src) == n,
           "ip_coverage": {"per_file_or_existing": sum(1 for i in items if i["header_status"]=="unified"),
                           "repo_level_covered": sum(1 for i in items if i["header_status"]=="repo_level_covered")},
           "nature_distribution": dict(Counter(i["nature"] for i in items)),
           "nature_confidence": {"high": conf_high, "review": len(reviews)},
           "files": items}
    if apply:
        (repo / "SYSTEM_INVENTORY.json").write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
    n_unified = inv["ip_coverage"]["per_file_or_existing"]
    n_repo = inv["ip_coverage"]["repo_level_covered"]
    print(f"=== {repo.name} ===")
    print(f"總源碼檔:{n}｜ground truth 完整:{inv['ground_truth_complete']}")
    print(f"IP 覆蓋:per-file/既有 {n_unified}({round(n_unified/n*100 if n else 0,1)}%) + repo級 {n_repo} | 合計100%({n})")
    print(f"本次補 comment header:{applied} | JSON _ip_notice:{json_ip_added} | nature:{inv['nature_distribution']}")
    print(f"nature 判定:high {conf_high}/{n}（{round(conf_high/n*100 if n else 0,1)}%）｜待複核⚠️ {len(reviews)}")
    if reviews[:5]:
        for r, c in reviews[:5]: print(f"   {r}: {c}")
    return inv


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python apply_system_inventory.py <repo> [--apply]"); return 0
    run(Path(sys.argv[1]), "--apply" in sys.argv)
    return 0

if __name__ == "__main__":
    sys.exit(main())

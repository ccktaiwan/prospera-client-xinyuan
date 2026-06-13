#!/usr/bin/env python3
# ── Prospera SYSTEM HEADER (ADR-0032/SBOM) ──
# 性質:engineering ｜設計:Kevin 架構 ｜執行:AI 工具(claude.ai+Claude Code)
# 驗證:無機制驗證 ｜IP:創造性歸 Kevin(發明人), AI 為執行工具 (ADR-0032)
"""
fitness_fabrication_check.py — Fitness D：無來源標記的捏造偵測（PENDING-029，「李醫師」型）

【為何】客戶面交付若出現**具體人名/數字/引述/機構**卻**無來源標記**，疑似 LLM 捏造（如憑空生「李醫師」案例）。
  Fitness A/B 管本體 hardcode / engine 宣稱；本 D 管「具體聲明無出處」——治編造。

【判準】掃文本，鄰近無來源標記（來源:/出處/據/參見/[EV-xxxx]/footnote）時：
  - **blocking（exit 1）**：人名+頭銜 / 百分比 / 金額 / 年份+事件 / 研究引用——精準事實宣稱，需出處。
  - **warning（不影響 exit）**：純敘事引述句「…」——除非鄰近有 blocking token（人名/數字/研究）才升 blocking。

【調校 2026-06-13（治本）】引述句 pattern 原為 blocking，誤擋品牌敘事引述（如 xinyuan 創辦人承諾、品牌命名由來）。
  改：純引述句降 warning；人名/百分比/金額/研究引用維持 blocking（這些準，捏造如「陳大文醫師 95%」仍擋）。

【用法】python fitness_fabrication_check.py <檔案>   # exit 0=clean(含純warning) / 1=有 blocking 疑捏造 / 2=檔不存在
誠實邊界：啟發式（pattern），非語義判真假；目的＝逼「事實宣稱帶出處」，降編造風險。漏報/誤報需人複核。
"""
import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 2026-06-13 調校（治本：xinyuan 真報告品牌敘事引述句誤報）──
# Blocking token（精準事實宣稱，無來源即 exit 1，保留不動——這些準）：
_BLOCKING_PATTERNS = [
    (r"[一-鿿]{1,3}(醫師|醫生|教授|律師|執行長|院長|總監|博士)(?![內外])", "具體人物頭銜"),
    (r"\d{1,3}(\.\d+)?\s*%", "百分比數據"),
    (r"(NT\$|新台幣|US\$|\$|美元|台幣)\s?\d", "金額數據"),
    (r"\d{4}\s*年[一-鿿]{2,}", "年份+事件"),
    (r"根據[一-鿿]{2,8}(研究|報告|調查|統計)", "研究引用"),
]
# 引述句（純啟發式噪音源）：降級 warning，不影響 exit；
#   例外——引述句「鄰近」有 blocking token（人名/數字/研究）＝需出處的事實引述 → 升 blocking。
_QUOTE_PATTERN = (r"[「『][^」』]{8,}[」』]", "引述句")
# 來源標記（鄰近有則視為已標出處）
_SOURCE_MARK = re.compile(r"來源[：:]|出處|據[一-鿿]{0,6}(指出|顯示|報導)|參見|\[EV-\d+\]|footnote|註\d|https?://")


def _has_blocking(chunk: str) -> bool:
    return any(re.search(p, chunk) for p, _ in _BLOCKING_PATTERNS)


def check(text: str) -> dict:
    lines = text.splitlines()
    blocking, warnings = [], []
    for i, line in enumerate(lines):
        # 標題/程式碼/引言區跳過（降誤報）
        if line.strip().startswith(("#", "```", ">", "|", "-", "*")) and "醫師" not in line:
            continue
        window = "\n".join(lines[max(0, i - 1):i + 2])
        if _SOURCE_MARK.search(window):
            continue  # 鄰近已標來源 → 視為已出處，跳過
        # blocking patterns（精準事實宣稱）
        for pat, desc in _BLOCKING_PATTERNS:
            for m in re.finditer(pat, line):
                blocking.append({"line": i + 1, "type": desc, "text": m.group(0)[:30],
                                 "context": line.strip()[:60]})
        # 引述句：鄰近有 blocking token → 需出處(blocking)；否則純敘事(warning)
        for m in re.finditer(_QUOTE_PATTERN[0], line):
            near = _has_blocking(window)
            rec = {"line": i + 1, "type": "引述句" + ("(近事實token,需出處)" if near else "(敘事)"),
                   "text": m.group(0)[:30], "context": line.strip()[:60]}
            (blocking if near else warnings).append(rec)

    def _dedupe(items):
        seen, uniq = set(), []
        for h in items:
            k = (h["line"], h["type"])
            if k not in seen:
                seen.add(k); uniq.append(h)
        return uniq
    b, w = _dedupe(blocking), _dedupe(warnings)
    return {"suspected": len(b), "blocking": b, "warnings": w, "hits": b, "clean": len(b) == 0}


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python fitness_fabrication_check.py <檔案>")
        return 0
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"❌ 檔案不存在：{p}")
        return 2
    r = check(p.read_text(encoding="utf-8", errors="replace"))
    # warnings（敘事引述）：印出供人參考，不影響 exit
    for h in r["warnings"][:15]:
        print(f"  ⚠warn L{h['line']} [{h['type']}]「{h['text']}」：{h['context']}")
    if r["clean"]:
        print(f"✅ Fitness D clean：無 blocking 級疑捏造（{p.name}）；warning {len(r['warnings'])} 處（敘事引述，不擋）")
        return 0
    print(f"⛔ Fitness D BLOCK：{r['suspected']} 處事實聲明無來源標記（疑捏造）— {p.name}")
    for h in r["blocking"][:15]:
        print(f"  L{h['line']} [{h['type']}] 「{h['text']}」：{h['context']}")
    print("→ 客戶面交付：人名/數字/金額/研究引用/需出處引述須帶來源標記（來源:/出處/[EV-xxxx]），否則疑編造。")
    return 1


if __name__ == "__main__":
    sys.exit(main())

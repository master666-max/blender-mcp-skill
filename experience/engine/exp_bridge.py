# -*- coding: utf-8 -*-
"""exp_bridge.py — 经验区（experience/）↔ evo-seat 引擎 的桥接（U-08，v2.8.0）

方向：EXP-*.md（治理层条目，只增不改）→ 引擎 events 账本（演化层，只增不改）。
映射规则见 experience/engine/README.md「字段映射表」。幂等：投影按 entry_id
取最新，重复 import 不产生语义重复（账本按纪律照常追加）。

用法：
  py -X utf8 exp_bridge.py import <引擎库路径> [--zone ..]   # 灌入全部 EXP 条目
  py -X utf8 exp_bridge.py status <引擎库路径>               # 账本/档位/条目概览
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import evo_seat  # noqa: E402  （vendored 微型内核，逐字节未改）

IMP_MAP = {"draft": 3, "pending": 3, "verified": 6, "promoted": 8, "rejected": 1}


def _front(text):
    """行式 frontmatter 解析（不依赖 yaml）。"""
    if not text.startswith("---"):
        raise ValueError("缺 frontmatter")
    head = text.split("---", 2)[1]
    fm = {}
    for ln in head.splitlines():
        m = re.match(r"^([a-z\-]+):\s*(.*)$", ln)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    # 列表值按区块收集（只取 claims 块内的 '- ' 行；evidence 子行不入 claims）
    lists, cur = {}, None
    for ln in head.splitlines():
        km = re.match(r"^([a-z\-]+):\s*$", ln)
        if km:
            cur = km.group(1)
            lists.setdefault(cur, [])
            continue
        km2 = re.match(r"^([a-z\-]+):\s*\S", ln)
        if km2:
            cur = None
            continue
        if cur and re.match(r"^\s+-\s+", ln):
            lists[cur].append(re.sub(r"^\s+-\s+|\"$|^\"", "", ln).strip())
    fm["_claims"] = lists.get("claims", [])
    fm["_evidence"] = lists.get("evidence", [])
    return fm


def _body(text):
    parts = text.split("---", 2)
    return parts[2] if len(parts) >= 3 else ""


def load_zone(zone):
    out = []
    for f in sorted(os.listdir(zone)):
        if not (f.startswith("EXP-") and f.endswith(".md")):
            continue
        text = open(os.path.join(zone, f), encoding="utf-8").read()
        fm = _front(text)
        body = _body(text).strip()
        eid = fm.get("id") or f[:-3]
        claims = list(fm["_claims"])
        content = "；".join(claims) + "\n" + body
        kws = evo_seat.tokens(content)[:24]
        status = fm.get("status", "draft")
        importance = IMP_MAP.get(status)
        if importance is None:
            raise ValueError(f"{eid}: 非法 status {status!r}")
        out.append({
            "id": eid, "entry_id": eid,  # 引擎校验查 id、投影用 entry_id（两者同值）
            "content": content.strip(), "keywords": kws,
            "importance": importance, "type": "procedural",
            "state": "longterm" if status == "promoted" else "intermediate",
            "created_at": fm.get("date", ""), "exp_status": status,
            "legacy": fm.get("legacy", ""),
        })
    return out


def cmd_import(a):
    zone = os.path.abspath(a.zone or os.path.join(HERE, os.pardir))
    d = os.path.dirname(os.path.abspath(a.lib))
    if d:
        os.makedirs(d, exist_ok=True)
    s = evo_seat.Store.open(a.lib)
    if s.level() == "G1" and s.count() == 0:
        s.set_level("G3", "human:bridge")  # 经验区建议默认档 G3（README）
    entries = load_zone(zone)
    for e in entries:
        evo_seat.validate_entry(e)
        s.append("engine:bridge", "memory_append", e)
        if e["state"] == "longterm":
            s.append("engine:bridge", "promotion", {"entry_id": e["entry_id"]})
    s.verify()
    print(f"import: {len(entries)} 条 EXP → {a.lib}（level={s.level()} events={s.count()} 链完整）")


def cmd_status(a):
    s = evo_seat.Store.open(a.lib)
    s.verify()
    ents = {e["id"]: e for e in evo_seat._load_entries(s)}
    states = {}
    for e in ents.values():
        states[e.get("state", "?")] = states.get(e.get("state", "?"), 0) + 1
    print(f"status: level={s.level()} events={s.count()} 链头={s.head()[:16]}…")
    for sid, e in sorted(ents.items()):
        print(f"  {sid}  imp={e.get('importance')}  state={e.get('state')}  {str(e.get('content',''))[:44]}")


def main():
    ap = argparse.ArgumentParser(description="经验区 ↔ evo-seat 桥")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("import")
    p.add_argument("lib")
    p.add_argument("--zone", default=None)
    p = sp.add_parser("status")
    p.add_argument("lib")
    a = ap.parse_args()
    {"import": cmd_import, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()

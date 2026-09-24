# -*- coding: utf-8 -*-
"""exp_hint.py — 经验区检索小工具（U-09：开工前一步的机读半边）

用法（零依赖，只用标准库）：
  py -X utf8 scripts/exp_hint.py                  # 列全部条目（一行一条）
  py -X utf8 scripts/exp_hint.py 烘焙 方向         # 按关键词出命中清单（含量化与复算命令）
  py -X utf8 scripts/exp_hint.py --top 3 导出 glb
  py -X utf8 scripts/exp_hint.py --engine 烘焙 方向 # 走引擎检索（账本需已 init + 桥导入）

两条通路（**缺省永不依赖引擎**）：
  · 文件扫（缺省）：只读 experience/ 下 EXP 条目——零安装，换机/未初始化都能用；
  · 引擎检索（--engine）：代跑 experience/engine/evo_seat.py retrieve——多**命中留痕**
    （谁查过什么入账，可审计）与 last_used 账面刷新；**账本未初始化时自动回退文件扫**。
    口径如实：本区条目全部为 procedural（零衰减），故引擎的「类型衰减排序」在本区
    **无区分度**（各条衰减乘数同为 0）——engine 通路在本区的真实增益 = 命中留痕 + 分词打分。
命中=关键词出现次数加权（id/一句话/claims 权 3，规避法/现象正文权 2，其余权 1）；
同分按编号序。**命中数=全量口径**（先数全部命中、再按 --top 显示前 k 条，超量时注明
——F-167）；--top 须 ≥1（非正数显式报错，F-167）。**无命中照实说「无命中」、不虚构
相关条目**（宁缺勿编）。
"""
import argparse
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP_DIR = os.path.join(ROOT, "experience")
ENGINE = os.path.join(EXP_DIR, "engine", "evo_seat.py")
LEDGER = os.path.join(EXP_DIR, "state", "evo.db")


def engine_retrieve(query, k):
    """走引擎检索（命中留痕+last_used 刷新）。返回 (ok, 输出文本)。"""
    if not os.path.isfile(ENGINE) or not os.path.isfile(LEDGER):
        return False, ("引擎账本未初始化（缺 %s）——先按 experience/engine/README.md 的"
                       " init + 桥导入建库，本次回退文件扫。" % LEDGER)
    p = subprocess.run([sys.executable, "-X", "utf8", ENGINE, "retrieve", LEDGER, query, "-k", str(k)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return False, "引擎检索失败（exit %d）：%s" % (p.returncode, (p.stderr or "").strip()[:200])
    return True, (p.stdout or "").strip()


def parse_entry(path):
    text = open(path, encoding="utf-8").read()
    eid = os.path.splitext(os.path.basename(path))[0]
    m = re.search(r"^id:\s*(\S+)", text, re.M)
    if m:
        eid = m.group(1)
    m = re.search(r"^status:\s*(\S+)", text, re.M)
    status = m.group(1) if m else "?"
    m = re.search(r"^claims:\s*\n((?:[ \t]+- .*\n?)+)", text, re.M)
    claims = [re.sub(r'^\s*- "?|"?\s*$', "", ln) for ln in m.group(1).splitlines()] if m else []
    body = " ".join(re.findall(r"^##\s*规避法\s*\n+(.+?)(?:\n##|\Z)", text, re.S | re.M))
    if not body:
        body = " ".join(re.findall(r"^##\s*现象与根因\s*\n+(.+?)(?:\n##|\Z)", text, re.S | re.M))
    recalc = re.findall(r"recalc:\s*\"?(.+?)\"?$", text, re.M)
    hi = " ".join([eid] + claims)
    low = " ".join(text.split("\n---")[0].split("\n"))
    one = (claims[0] if claims else body or "").strip().replace("\n", " ")
    return {"id": eid, "status": status, "one": one, "hi": hi, "mid": body,
            "low": low, "recalc": recalc, "path": path}


def score(entry, keywords):
    total = 0
    for kw in keywords:
        k = kw.lower()
        total += 3 * entry["hi"].lower().count(k)
        total += 2 * entry["mid"].lower().count(k)
        total += 1 * entry["low"].lower().count(k)
    return total


def clip(s, n=72):
    s = " ".join(s.replace("**", "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    ap = argparse.ArgumentParser(description="经验区检索：给任务关键词，出命中清单")
    ap.add_argument("keywords", nargs="*", help="任务关键词（可多个；留空=列全部）")
    ap.add_argument("--top", type=int, default=5, help="命中清单条数上限（默认 5；须 ≥1）")
    ap.add_argument("--engine", action="store_true",
                    help="走引擎检索（多命中留痕+last_used；账本未初始化则回退文件扫）")
    a = ap.parse_args()
    if a.top < 1:
        print("ERROR: --top 须 ≥1（收到 %d）——拒绝静默钳制（F-167）" % a.top)
        sys.exit(2)
    if not os.path.isdir(EXP_DIR):
        print("ERROR: 未找到经验区目录 experience/（包结构异常）")
        sys.exit(2)
    files = sorted(glob.glob(os.path.join(EXP_DIR, "EXP-*.md")))
    if not files:
        print("ERROR: experience/ 下无 EXP-*.md 条目")
        sys.exit(2)
    entries = [parse_entry(p) for p in files]
    total = len(entries)
    if not a.keywords:
        if a.engine:
            print("（--engine 需配合关键词；本次按全部条目列出）")
        print("经验区全部条目（共 %d 条；详情与晋升去向见 experience/INDEX.md）：" % total)
        for e in entries:
            pad = " " * max(0, 10 - len(e["status"]))
            print("  %-8s [%s]%s %s" % (e["id"], e["status"], pad, clip(e["one"], 64)))
        print("用法：py -X utf8 scripts/exp_hint.py <任务关键词…>")
        return
    if a.engine:
        ok, out = engine_retrieve(" ".join(a.keywords), a.top)
        if ok:
            print("引擎检索（命中留痕已入账；-k %d）：" % a.top)
            print(out if out else "（引擎无输出）")
            print()
            print("—— 以下文件扫为对照（引擎=分词打分+留痕；文件扫=子串加权，零依赖）——")
        else:
            print("engine 通路不可用：" + out)
            print("—— 回退文件扫 ——")
    elif os.path.isfile(LEDGER):
        print("（检测到引擎账本：加 --engine 可用命中留痕/last_used；账本=运行态，不入包）")
    ranked = sorted(((score(e, a.keywords), e) for e in entries),
                    key=lambda t: (-t[0], t[1]["id"]))
    all_hits = [(s, e) for s, e in ranked if s > 0]
    shown = all_hits[: a.top]
    if not all_hits:
        print("命中 0/%d 条（关键词：%s）——无命中照实说，不虚构相关条目。"
              % (total, " ".join(a.keywords)))
        print("建议：换任务名/工具名/现象词重试，或通览 experience/INDEX.md。")
        return
    if len(all_hits) > len(shown):
        print("命中 %d/%d 条（关键词：%s；显示前 %d 条，可用 --top 调整；先读规避法再动手）："
              % (len(all_hits), total, " ".join(a.keywords), len(shown)))
    else:
        print("命中 %d/%d 条（关键词：%s；先读规避法再动手）："
              % (len(all_hits), total, " ".join(a.keywords)))
    for s, e in shown:
        print()
        print("%s [%s] %s   （相关度 %d）" % (e["id"], e["status"], clip(e["one"], 68), s))
        if e["mid"]:
            print("  规避法：%s" % clip(e["mid"], 88))
        if e["recalc"]:
            print("  复算：%s" % clip(e["recalc"][0], 88))
    print()
    print("全文（含证据三件套）在 experience/%s.md；全量索引 experience/INDEX.md" % shown[0][1]["id"])


main()

# -*- coding: utf-8 -*-
"""run-regression-checks.py — 条款指纹全量回归 runner（V-09）

解析同目录 regression-checks.md 的指纹表，逐条按声明的匹配语义（字面量 / re:正则）
对目标文件做子串/正则核验，输出 PASS/FAIL 表。任何一条 FAIL → 退出码 1。
另有台账断言（F-98 治本；F-115 补记两类；F-124/F-125 扩为三类 + fail-closed）：
**④a** = CHANGELOG 最新条目出现的 F-NN 必须已在台账登记；**④b** = 台账 F 编号单调
递增 + CHANGELOG 最新条目版本 == frontmatter；**④c(F-125)** = 台账"已修复"行中
反引号指名的文件必须真实存在（指名到文件与行从声明变成动作）。
**不可核验 = FAIL（F-124 fail-closed）**：CHANGELOG 缺失 / 最新条目标题不可解析 /
frontmatter 版本不可解析时，一律计入 problems → 退出码 3，不再以"不阻塞"警示放行。
退出码表：0 = 全过；1 = 指纹 FAIL；2 = 表格解析失败**或条款集登记断言失败**
（EXPECTED_CLAUSES，F-159）；3 = 台账断言 FAIL（④a/④b/④c，含不可核验）
**或台账集登记断言失败**（EXPECTED_LEDGER_ROWS，F-161）。
4 = 经验区（experience/）结构校验失败（U-07：frontmatter 必填键/出处三件套/
状态合法值/promotion 完整性/INDEX 覆盖——活区管结构不管数量）。

用法（在 skill 根目录或任意位置）：
    py evals/run-regression-checks.py
    py evals/run-regression-checks.py --root <skill根目录>

解析器注意（来自 v1.4 审计 S43 的两个教训）：
1. markdown 表格单元格可能含转义管道 \\| —— 先替换成哨兵再按 | 切分；
2. 目标文件列写的是"references/03"这类短名 —— 按 glob 在 skill 根下解析。
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)
SENTINEL = "\u0001PIPE\u0001"


def load_table(md_path):
    rows = []
    with io_open(md_path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("|"):
                continue
            cells = [c.strip().replace(SENTINEL, "|").strip("`")
                     for c in line.replace("\\|", SENTINEL).split("|")]
            cells = cells[1:-1] if cells and cells[0] == "" else cells
            if len(cells) >= 4 and cells[0].isdigit():
                rows.append({"no": int(cells[0]), "clause": cells[1],
                             "mode": cells[2], "fingerprint": cells[3], "target": cells[4]})
    return rows


def io_open(path):
    import io
    return io.open(path, "r", encoding="utf-8")


def resolve_targets(root, target_cell):
    """目标列可能是 'SKILL.md'、'references/03'、'scripts/xxx.py' 等 —— 解析成实际文件列表。"""
    t = target_cell.strip()
    direct = os.path.join(root, t)
    if os.path.isfile(direct):
        return [direct]
    hits = []
    for pat in (os.path.join(root, t + "*.md"),
                os.path.join(root, t + "*.py"),
                os.path.join(root, "references", t + "*.md"),
                os.path.join(root, "references", t + "*.py"),
                os.path.join(root, "scripts", t + "*.py")):
        hits.extend(glob.glob(pat))
    return sorted(set(hits))


def check(rows, root):
    cache = {}
    results = []
    for row in rows:
        fp = row["fingerprint"].strip()
        mode = row["mode"].strip()
        targets = resolve_targets(root, row["target"])
        if not targets:
            results.append((row, False, "TARGET NOT FOUND: " + row["target"]))
            continue
        matched = False
        detail = ""
        for t in targets:
            if t not in cache:
                with io_open(t) as f:
                    cache[t] = f.read()
            content = cache[t]
            if mode.startswith("re:"):
                pat = fp[3:]
                # F-155 lint：可匹配空串的正则=恒真断言，无判别力 → 按 FAIL 处理
                if re.search(pat, "") is not None:
                    matched = False
                    detail = "VACUOUS PATTERN: 该正则可匹配空串，断言恒真、无判别力（F-155 lint）"
                    break
                hit = re.search(pat, content) is not None
            else:
                hit = fp in content
            if hit:
                matched = True
                detail = os.path.relpath(t, root)
                break
        if not matched and not detail:
            detail = "fingerprint not found in " + row["target"]
        results.append((row, matched, detail))
    return results


def check_changelog_fnn_registered(md):
    """④查治本（F-83/F-98 记账）：CHANGELOG 最新条目中的 F-NN 编号必须已在台账登记。

    正则抽取 CHANGELOG 第一个 "## v" 条目内的 F-NN 集合，与台账行编号集合做差。
    差集非空 → 返回缺失列表（发布前必须补登记或处置）。
    F-108：编号支持带字母后缀（F-87a/F-87b 形态），且两侧同形比较；
    另含"不可见 F 行"自检（严式/宽式计数不等 = 台账存在断言不可见的行）。
    F-124 fail-closed：CHANGELOG 缺失 / 最新条目标题不可解析时，经第三返回值
    fatal 上报（→ problems → exit 3），不再走"仅形态提示不阻塞"的警示通道。
    返回 (missing, visibility_warnings, fatal)。
    """
    changelog = os.path.join(os.path.dirname(md), os.pardir, "CHANGELOG.md")
    changelog = os.path.normpath(changelog)
    if not os.path.isfile(changelog):
        return None, [], ["CHANGELOG.md 缺失 → ④a/④b 无法核验，按 FAIL 处理（F-124 fail-closed）"]
    text = open(changelog, encoding="utf-8").read()
    first = re.search(r"^##[ \t]+(\S.*)$", text, re.M)
    if not first:
        return None, [], ["CHANGELOG 无任何二级标题 → ④a/④b 无法核验，按 FAIL 处理（F-124 fail-closed）"]
    if not first.group(1).startswith("v"):
        return None, [], ["CHANGELOG 首个二级标题不是 '## v<版本>' 形态（实测: '## %s'）→ "
                          "④a/④b 无法核验，按 FAIL 处理（F-124 fail-closed；防④a 静默降级解析次新条目）"
                          % first.group(1)]
    m = re.search(r"^## v\S+", text, re.M)
    if not m:
        return None, [], ["CHANGELOG 版本条目标题不可解析（应以 '## v<版本>' 开头）→ "
                          "④a/④b 无法核验，按 FAIL 处理（F-124 fail-closed）"]
    end = text.find("\n## v", m.start() + 1)
    latest = text[m.start():end if end != -1 else len(text)]
    # F-164：负向后视边界——"UTF-8" 等词内的 F-8 不是发现编号（曾致 ④a 误报）
    claimed = set(re.findall(r"(?<![A-Za-z0-9-])F-(\d+[a-z]?)", latest))
    ledger = open(md, encoding="utf-8").read()
    registered = set(re.findall(r"^\| F-(\d+[a-z]?) \|", ledger, re.M))
    strict = len(re.findall(r"^\| F-\d+ \|", ledger, re.M))
    loose = len(re.findall(r"^\| F-\S+ \|", ledger, re.M))
    warnings = []
    if strict != loose:
        warnings.append("台账存在断言不可见的 F 行（严式 %d / 宽式 %d）——请核对该行形态"
                        % (strict, loose))
    return sorted(claimed - registered), warnings, []


# ---- ④c（F-125）：台账"已修复"行指名的文件必须真实存在 --------------------
# 短名映射：台账行惯用的分册/文件简称 → 包内路径模式。
SHORT_NAMES = {
    "SKILL": ["SKILL.md"], "INSTALL": ["INSTALL.md"], "CHANGELOG": ["CHANGELOG.md"],
    "HANDOFF": ["HANDOFF.md"], "runner": ["evals/run-regression-checks.py"],
    "check-deploy": ["evals/check-deploy.py"], "check-version": ["evals/check-version.py"],
}
# 仅核验这些扩展名（zip 等交付层工件不在包内，不核验——F-131 处置见台账）。
REF_EXTS = (".md", ".py", ".txt")
# 设计上不入包的机器本地文件（F-48：*.local.txt 不入包）——④c 豁免，不判缺失。
EXEMPT_BASENAMES = {"deploy-roots.local.txt"}
TOKEN_RE = re.compile(r"`([^`]+)`")
FILELIKE_RE = re.compile(r"^[\w./\\\-]+(?::\d+(?:-\d+)?)?$")


def resolve_ledger_ref(root, token):
    """把台账行反引号内的文件指名解析成包内实际文件列表。

    返回 ("check", files) 表示该 token 是文件指名且已解析（files 可为空 = 缺失）；
    返回 ("skip", None) 表示该 token 不是文件指名（函数名/锚串/版本号等），不核验。
    F-139 收窄：纯大写/驼峰短名仅在带 `:行号` 后缀时核验（如 `INSTALL:153`）——
    裸专名（`PolyHaven` 等反引号普通名词）不按文件核验，防假阳性。
    """
    n = token.strip()
    had_line_ref = False
    if os.path.basename(n.split(":")[0]) in EXEMPT_BASENAMES:
        return "skip", None
    if ":" in n:
        head, tail = n.split(":", 1)
        if not re.fullmatch(r"\d+(?:-\d+)?", tail):
            return "skip", None  # 如 file.py:func —— 带非行号后缀，不按文件核验
        had_line_ref = True
        n = head
    if not n:
        return "skip", None
    if not FILELIKE_RE.fullmatch(n):
        return "skip", None
    base = n
    if base.upper() in SHORT_NAMES:
        base_key = base.upper()
    elif base in SHORT_NAMES:
        base_key = base
    else:
        base_key = None
    if base_key:
        hits = []
        for rel in SHORT_NAMES[base_key]:
            p = os.path.join(root, rel)
            if os.path.isfile(p):
                hits.append(p)
        return "check", hits
    if re.fullmatch(r"\d{2}", base):  # 分册短名 00~14 → references/NN-*.md
        return "check", sorted(glob.glob(os.path.join(root, "references", base + "-*.md")))
    if had_line_ref and re.fullmatch(r"[A-Z][A-Za-z]+", base):
        # 纯大写/首字母大写短名 + 行号后缀（INSTALL:153 形态；裸驼峰不进此分支）
        p = os.path.join(root, base + ".md")
        return "check", [p] if os.path.isfile(p) else []
    low = base.lower()
    if low.endswith(REF_EXTS):
        cands = [os.path.join(root, base),
                 os.path.join(root, "evals", base),
                 os.path.join(root, "scripts", base),
                 os.path.join(root, "fragments", base),
                 os.path.join(root, "assets", "blender-mcp-bundle", base),
                 os.path.join(root, "nodes", base)]
        if "/" in base or "\\" in base:
            cands = [os.path.join(root, base.replace("\\", "/"))]
        return "check", [c for c in cands if os.path.isfile(c)]
    return "skip", None


def check_ledger_file_refs(md, root):
    """④c（F-125 治本）：台账"已修复/已裁定"行反引号指名的文件必须真实存在。

    把"声称的措施指名到文件与行，并逐条对文件核实"从④的人工声明降下一条机械断言：
    只核验**文件存在性**（行号与内容仍属人工/M13 探针域）。指名了包内不存在的文件
    → 计入 problems（exit 3）。
    """
    problems = []
    ledger = open(md, encoding="utf-8").read()
    for line in ledger.splitlines():
        # F 行与 U 行都纳入 ④c 扫描域（F-108 家族教训：台账断言不可见行=盲区）
        m = re.match(r"^\| ((?:F|U)-\d+[a-z]?) \|", line)
        if not m:
            continue
        fid = m.group(1)
        for tok in TOKEN_RE.findall(line):
            kind, files = resolve_ledger_ref(root, tok)
            if kind == "check" and not files:
                problems.append("%s 行指名的文件不存在或不可解析: `%s`（④c 台账指名核实）"
                                % (fid, tok))
    return problems




def check_experience_zone(root):
    """U-07（v2.7.0）：经验区（experience/）结构校验——活区管结构不管数量。

    校验：INDEX 存在；每条 EXP-*.md frontmatter 必填键齐全（id/date/source/status/
    evidence/claims/recalc-judge）；status 为合法值；evidence 三件套（artifact/quote/
    recalc）非空；promoted 条目必须有 promotion.target；supersedes（如有）指向存在
    条目；INDEX 覆盖每条 id。返回问题列表。
    """
    import glob as _g
    problems = []
    zone = os.path.join(root, "experience")
    index_path = os.path.join(zone, "INDEX.md")
    if not os.path.isfile(index_path):
        return ["EXP-ZONE CHECK FAIL: experience/INDEX.md 缺失（U-07）"]
    legal = {"draft", "verified", "promoted", "pending", "rejected"}
    entries = sorted(_g.glob(os.path.join(zone, "EXP-*.md")))
    ids = set()
    for path in entries:
        fid = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        if not text.startswith("---"):
            problems.append("EXP-ZONE CHECK FAIL: %s 缺 frontmatter" % fid)
            continue
        head = text.split("---", 2)[1]
        for key in ("id:", "date:", "source:", "status:", "evidence:", "claims:", "recalc-judge:"):
            if key not in head:
                problems.append("EXP-ZONE CHECK FAIL: %s 缺必填键 %s" % (fid, key))
        m = re.search(r"status:\s*(\S+)", head)
        if m and m.group(1) not in legal:
            problems.append("EXP-ZONE CHECK FAIL: %s 非法状态 %r（合法值 %s）" % (fid, m.group(1), sorted(legal)))
        for sub in ("artifact:", "quote:", "recalc:"):
            if sub not in head:
                problems.append("EXP-ZONE CHECK FAIL: %s 证据三件套缺 %s" % (fid, sub))
        m = re.search(r"status:\s*(\S+)", head)
        if m and m.group(1) == "promoted" and "promotion:" not in head:
            problems.append("EXP-ZONE CHECK FAIL: %s 状态 promoted 但缺 promotion 块" % fid)
        m = re.search(r"supersedes:\s*(EXP-\d+)", head)
        if m and not os.path.isfile(os.path.join(zone, m.group(1) + ".md")):
            problems.append("EXP-ZONE CHECK FAIL: %s supersedes 指向不存在的条目 %s" % (fid, m.group(1)))
        m = re.search(r"id:\s*(EXP-\d+)", head)
        if m:
            ids.add(m.group(1))
    index_text = open(index_path, encoding="utf-8").read()
    for fid in ids:
        if fid not in index_text:
            problems.append("EXP-ZONE CHECK FAIL: INDEX 未覆盖条目 %s（U-07）" % fid)
    return problems


def check_ledger_invariants(md, skill_version):
    """F-104/F-107 治本（审计建议随 ④a 同批实作；F-124/F-128 修订）：
    a) 台账 F 编号序列严格递增（(num, suffix) 元组序；防插入错位与重复行——F-119）；
    b) CHANGELOG 最新条目的版本号 == SKILL.md frontmatter 版本
       （防"本版缺 CHANGELOG 条目"复发——F-92/F-101 两次同形态）；
    frontmatter 版本不可解析（None）→ 显式入 problems（F-124：此前 ④b 两个分支
    双双静默跳过，P34 实测 exit 0）。
    **共漂移（frontmatter 与 CHANGELOG 同停旧版）不属 ④ 覆盖范围，由 ②查负责**
    （F-128 裁定：原 (c) 存在性断言无法独立检出任何新情形，已删以免虚假保证；
    教训沿 F-122——F-13 类版本失同步的唯一防线是 ②查）。
    返回问题列表（空 = 通过）。编号支持带字母后缀（F-108）。
    """
    problems = []
    ledger = open(md, encoding="utf-8").read()
    # F-161：台账集登记断言——增删台账行须同步修改此数（刻意的登记动作）
    EXPECTED_LEDGER_ROWS = 138
    loose = len(re.findall(r"^\| F-\S+ \|", ledger, re.M))
    if loose != EXPECTED_LEDGER_ROWS:
        problems.append("LEDGER-SET CHECK FAIL: 台账 F 行=%d（期望 %d）——台账行可能被静默增删（F-161；ASCII 标签供探针判定，F-166）"
                        % (loose, EXPECTED_LEDGER_ROWS))
    keys = re.findall(r"^\| F-(\d+)([a-z]?) \|", ledger, re.M)
    pairs = [(int(n), sfx) for n, sfx in keys]
    for (an, asfx), (bn, bsfx) in zip(pairs, pairs[1:]):
        if (bn, bsfx) <= (an, asfx):
            problems.append("台账 F 编号非严格递增: F-%d%s -> F-%d%s（重复或逆序）"
                            % (an, asfx, bn, bsfx))
    if skill_version is None:
        problems.append("SKILL.md metadata.version 不可解析 → ④b 无法核验，"
                        "按 FAIL 处理（F-124 fail-closed）")
        return problems
    changelog = os.path.normpath(os.path.join(os.path.dirname(md), os.pardir, "CHANGELOG.md"))
    if os.path.isfile(changelog):
        text = open(changelog, encoding="utf-8").read()
        m = re.search(r"^## v([0-9][\w.]*)", text, re.M)
        if m and m.group(1) != skill_version:
            problems.append("CHANGELOG 最新条目版本(%s) != frontmatter(%s)"
                            % (m.group(1), skill_version))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    md = os.path.join(HERE, "regression-checks.md")
    rows = load_table(md)
    if not rows:
        print("NO ROWS PARSED — 表格解析失败")
        sys.exit(2)
    # F-159：条款集登记断言——删行/缩表不再静默（新增/删除条款须同步改此数，属刻意的登记动作）
    EXPECTED_CLAUSES = 91
    ids = [r["no"] for r in rows]
    if len(rows) != EXPECTED_CLAUSES or ids != list(range(1, EXPECTED_CLAUSES + 1)):
        print("CLAUSE-SET CHECK FAIL: 条款数=%d（期望 %d）或编号非 1..%d 连续——条款行可能被静默增删（F-159）"
              % (len(rows), EXPECTED_CLAUSES, EXPECTED_CLAUSES))
        sys.exit(2)
    skill_md = os.path.join(root, "SKILL.md")
    skill_version = None
    if os.path.isfile(skill_md):
        m = re.search(r'version:\s*"([^"]+)"', open(skill_md, encoding="utf-8").read())
        if m:
            skill_version = m.group(1)
    results = check(rows, root)
    fails = 0
    print("# 回归指纹核验（%d 条）" % len(results))
    for row, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        print("%s  #%02d  %s  [%s]" % (mark, row["no"], row["clause"], detail))
    print("summary: %d/%d PASS" % (len(results) - fails, len(results)))
    missing, visibility_warnings, fatal = check_changelog_fnn_registered(md)
    for w in visibility_warnings:
        print("LEDGER-VISIBILITY-WARN: " + w + "（行已参与宽式断言，仅形态提示不阻塞）")
    problems = []
    problems.extend(fatal)  # F-124：不可核验 = FAIL，进 problems 而非警示通道
    if missing:
        problems.append("CHANGELOG 最新条目出现但台账未登记: F-" + ", F-".join(missing)
                        + "（④a 台账登记断言）")
    inv = check_ledger_invariants(md, skill_version)
    problems.extend(inv)
    problems.extend(check_ledger_file_refs(md, root))  # ④c（F-125）
    exp_problems = check_experience_zone(root)  # U-07（v2.7.0）：经验区结构校验
    problems.extend(exp_problems)
    if problems:
        for p in problems:
            print("LEDGER-INVARIANT: " + p)
        print("summary④(台账断言): FAIL（F-83/F-98/F-104/F-107/F-124/F-125 治本项）"
              "——问题 %d 处一次性全部列出" % len(problems))
        sys.exit(3 if not exp_problems else 4)
    print("summary④(台账断言): PASS——④a CHANGELOG 最新条目的 F-NN 均已登记；"
          "④b 台账 F 编号严格递增、CHANGELOG 版本与 frontmatter 一致（不可核验即 FAIL，F-124）；"
          "④c 台账指名文件均存在（F-125）；"
          "共漂移由 ②查负责（F-128，非 ④ 域）；"
          "④ 的其余人工核验项见 regression-checks.md ④ 定义段")
    sys.exit(1 if fails else 0)


main()

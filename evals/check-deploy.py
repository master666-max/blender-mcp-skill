# -*- coding: utf-8 -*-
"""check-deploy.py — 部署一致性机器断言（F-46/F-47 整改，发布四查之第 ③ 查的执行体）

两层断言，任一命中 → 退出码 1：
  A. 根集合断言（F-47）：基线根清单 evals/deploy-roots.txt 中的根必须全部实际存在
     （少根 FAIL）；扫描发现的未登记根同样 FAIL（多根 FAIL）——F-46 的失效模式正是
     "项目级根被漏"，只查内容不查集合时，忘传 --root 会让 ③ 查对漏根视而不见。
  B. 内容断言（F-46）：每个基线根与发布 zip 逐文件 SHA256 一致；兼查缺文件、
     .bak 污染（V-06）、同名 bundle 唯一性（V-14）、包外多余文件（WARN）。

    py evals/check-deploy.py --zip ../blender-mcp-v1.10.5.zip
    py evals/check-deploy.py --zip <包> --root <额外根>   # 传入的根也必须已登记

背景：v1.10.3 发布只同步了部分根，同名不同版致运行时载旧版（F-46）；
v1.10.5 把根基线固化进包内并断言集合本身（F-47）；
v1.10.6 拆分内置可移植根与机器专属根（deploy-roots.local.txt 不入包），消除换机两难（F-48）。
"""
import argparse
import hashlib
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOTS_FILE = os.path.join(HERE, "deploy-roots.txt")
# local 查找顺序：本副本 → .zcode 主副本（F-52：从任何副本调用，覆盖都必须一致，
# 不因"从哪个副本跑"而掉根）。两处皆无 → NOTICE（不 FAIL，兼容纯净解压副本自检）。
LOCAL_CANDIDATES = [
    os.path.join(HERE, "deploy-roots.local.txt"),
    os.path.join(os.path.expanduser("~"), ".zcode", "skills", "blender-mcp",
                 "evals", "deploy-roots.local.txt"),
]
PREFIX = "blender-mcp/"
EXEMPT = {"HANDOFF.md", "evals/deploy-roots.local.txt"}


def fail(msg):
    print("DEPLOY-CHECK FAIL:", msg)
    sys.exit(1)


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(p):
    return os.path.normpath(os.path.expanduser(p.strip()))


def _read_roots(path, roots, required):
    if not os.path.isfile(path):
        if required:
            fail("基线清单缺失: " + path)
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            roots.append(norm(line))


def load_baseline():
    """内置可移植根（deploy-roots.txt，必填）+ 机器专属根（.local.txt，可选）合并为基线。

    返回 (roots, local_found_path_or_None)。
    """
    roots = []
    _read_roots(ROOTS_FILE, roots, required=True)
    local_path = next((p for p in LOCAL_CANDIDATES if os.path.isfile(p)), None)
    if local_path:
        _read_roots(local_path, roots, required=False)
    if not roots:
        fail("基线清单为空: " + ROOTS_FILE)
    return roots, local_path


def scan_roots(extra):
    """扫描用户主目录下各 dot 宿主目录的 skills/blender-mcp，合并 --root 显式传入。"""
    found = set()
    home = os.path.expanduser("~")
    for name in os.listdir(home):
        cand = os.path.join(home, name, "skills", "blender-mcp")
        if name.startswith(".") and os.path.isdir(cand):
            found.add(norm(cand))
    for r in extra:
        found.add(norm(r))
    return found


def unique_in_skills_dir(root, problems):
    parent = os.path.dirname(os.path.abspath(root))
    hits = [d for d in os.listdir(parent) if d.lower() == "blender-mcp"]
    if len(hits) != 1:
        problems.append("同名 bundle 不唯一 in %s: %s" % (parent, hits))


def check_root(root, ref, problems, warnings):
    unique_in_skills_dir(root, problems)
    root_files = {}
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            root_files[rel] = full

    n_bad = 0
    for rel in sorted(ref):
        if rel not in root_files:
            problems.append("[%s] 缺文件: %s" % (root, rel))
            n_bad += 1
            continue
        if sha_file(root_files[rel]) != ref[rel]:
            problems.append("[%s] 哈希不一致: %s" % (root, rel))
            n_bad += 1

    for rel in sorted(root_files):
        if rel in ref or rel in EXEMPT:
            continue
        # 执行副产物污染发现根（V-06/.bak、F-71/__pycache__）一律 FAIL
        if rel.endswith(".bak") or "__pycache__" in rel or rel.endswith(".pyc"):
            problems.append("[%s] 执行副产物污染发现根: %s" % (root, rel))
        else:
            warnings.append("[%s] 包外多余文件: %s" % (root, rel))
    return len(ref), n_bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, help="发布 zip 路径")
    ap.add_argument("--root", action="append", default=[],
                    help="额外检查的根（可重复；必须已登记于 deploy-roots.txt）")
    args = ap.parse_args()

    if not os.path.isfile(args.zip):
        fail("zip 不存在: " + args.zip)
    z = zipfile.ZipFile(args.zip)
    ref = {}
    for n in z.namelist():
        if n.startswith(PREFIX):
            ref[n[len(PREFIX):]] = hashlib.sha256(z.read(n)).hexdigest()
    if not ref:
        fail("zip 内无 %s* 条目: %s" % (PREFIX, args.zip))

    baseline, local_path = load_baseline()
    scanned = scan_roots(args.root)

    missing = [r for r in baseline if not os.path.isdir(r)]
    extra = [r for r in scanned if r not in baseline]
    n_found = len(baseline) - len(missing) + len(extra)
    if local_path is None:
        print("NOTICE: 未找到 deploy-roots.local.txt（已尝试本副本与 ~/.zcode 主副本）——"
              "机器专属根（如项目级根）不在本次断言范围，覆盖不完整！")
    else:
        print("NOTICE: 机器专属根清单 = " + local_path)
    print("DEPLOY-CHECK: zip=%s (%d files) | 基线 %d 根, 确认存在 %d 根"
          % (os.path.basename(args.zip), len(ref), len(baseline), n_found))
    if missing:
        for r in missing:
            print("  基线根缺失/未部署: %s" % r)
        fail("根集合断言：基线 %d 根中 %d 根不存在（少根）" % (len(baseline), len(missing)))
    if extra:
        for r in extra:
            print("  发现未登记根: %s" % r)
        fail("根集合断言：发现 %d 个未登记根——更新 deploy-roots.txt 或移除该根（多根）"
             % len(extra))

    problems, warnings = [], []
    for root in baseline:
        if not os.path.isdir(root):
            problems.append("根不存在: " + root)
            continue
        total, n_bad = check_root(root, ref, problems, warnings)
        print("  [%s] %d/%d 一致" % (root, total - n_bad, total))

    for w in warnings:
        print("  WARN:", w)
    if problems:
        for p in problems:
            print("  " + p)
        fail("内容断言：%d 个根存在差异（共 %d 处）" % (len(baseline), len(problems)))
    print("DEPLOY-CHECK PASS: 根集合=%d/基线%d，逐文件哈希全一致（机器专属根：%s）"
          % (n_found, len(baseline),
             ("已覆盖 via " + local_path) if local_path else "未覆盖（NOTICE 见上）"))
    sys.exit(0)


if __name__ == "__main__":
    main()

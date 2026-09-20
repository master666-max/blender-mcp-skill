# -*- coding: utf-8 -*-
"""check-version.py — 版本一致性机器断言（V-13/V-15 整改）

断言三处版本号同步：SKILL.md frontmatter、INSTALL.md 标题、--expected 传入的发布版本。
任何不一致 → 退出码 1。发布（打包 zip）前必须以目标版本号跑一遍：
    py evals/check-version.py --expected 1.6

背景（BMCP-V151 审计 V-13）：v1.5.1 包通篇不含 "1.5.1" 字样——zip 名递增了，
frontmatter 与 INSTALL 标题却停在 1.5，版本自省失效、多候选升级逻辑会静默跳过。
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def fail(msg):
    print("VERSION-CHECK FAIL:", msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected", required=True, help="本次发布的版本号，如 1.6")
    args = ap.parse_args()
    expected = args.expected.strip()

    skill_md = os.path.join(ROOT, "SKILL.md")
    install_md = os.path.join(ROOT, "INSTALL.md")
    for p in (skill_md, install_md):
        if not os.path.isfile(p):
            fail("missing file: " + p)

    with open(skill_md, "r", encoding="utf-8") as f:
        skill = f.read()
    m = re.search(r'version:\s*"([^"]+)"', skill)
    if not m:
        fail("SKILL.md frontmatter has no metadata.version")
    declared = m.group(1).strip()
    if declared != expected:
        fail('SKILL.md metadata.version = "%s" != expected "%s"' % (declared, expected))

    with open(install_md, "r", encoding="utf-8") as f:
        install = f.read()
    title = install.splitlines()[0] if install else ""
    inside = re.findall(r"[（(]([^）)]+)[）)]", title)
    versions = {v.strip().lstrip("vV") for v in inside}
    if expected not in versions:
        fail("INSTALL.md title versions %s do not contain expected %s"
             % (sorted(versions), expected))

    print("VERSION-CHECK PASS: frontmatter=%s, INSTALL title=%s, expected=%s"
          % (declared, expected, expected))


main()

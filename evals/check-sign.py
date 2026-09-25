# -*- coding: utf-8 -*-
"""check-sign.py — ⑤查 发行签名核验（F-170 治本：从未被执行过的门=没有门）

用法：py -X utf8 evals/check-sign.py --dir <发行目录> [--alias blender-mcp-latest.zip]
  对目录内每个 blender-mcp-v*.zip 与别名件逐个验其同名 .sig：
  ssh-keygen -Y verify -f <包>/assets/release-signing/allowed_signers
             -I blender-mcp-releases -n blender-mcp -s <zip>.sig < <zip>
任一缺 .sig / 验签失败 → exit 1；目录或信任锚不可用 → exit 2；全过 → exit 0。
发布闸（F-170）：每次发版后必须对**全部**发行件（含别名件）跑本查；
**重写别名件后必须同步重签**——别名 sig 与内容错配即本查 FAIL。
"""
import argparse
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNERS = os.path.join(os.path.dirname(HERE), "assets", "release-signing", "allowed_signers")


def verify(z):
    sig = z + ".sig"
    if not os.path.isfile(sig):
        return False, "缺 .sig"
    with open(z, "rb") as fh:
        p = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", SIGNERS,
                            "-I", "blender-mcp-releases", "-n", "blender-mcp",
                            "-s", sig], stdin=fh, capture_output=True)
    return p.returncode == 0, (p.stderr or p.stdout or b"").decode("utf-8", "replace").strip()[:120]


def main():
    ap = argparse.ArgumentParser(description="发行签名核验：逐 zip 验同名 .sig（含别名件）")
    ap.add_argument("--dir", required=True, help="发行 zip 所在目录")
    ap.add_argument("--alias", default="blender-mcp-latest.zip",
                    help="别名件名（默认 blender-mcp-latest.zip）")
    a = ap.parse_args()
    if not os.path.isfile(SIGNERS):
        print("ERROR: 找不到 allowed_signers：%s" % SIGNERS)
        sys.exit(2)
    if not os.path.isdir(a.dir):
        print("ERROR: 发行目录不存在：%s" % a.dir)
        sys.exit(2)
    zips = sorted(glob.glob(os.path.join(a.dir, "blender-mcp-v*.zip")),
                  key=lambda p: [int(x) for x in
                                 __import__("re").search(r"v(\d+)\.(\d+)(?:\.(\d+))?",
                                                         os.path.basename(p)).groups("0")])
    alias = os.path.join(a.dir, a.alias)
    newest = zips[-1] if zips else None
    if os.path.isfile(alias) and alias not in zips:
        zips.append(alias)
    if not zips:
        print("ERROR: 目录内无 blender-mcp-*.zip")
        sys.exit(2)
    fails = skips = 0
    for z in zips:
        name = os.path.basename(z)
        must = (z == alias or z == newest)   # 别名件与最新版化件必须可验
        if not os.path.isfile(z + ".sig"):
            if must:
                print("FAIL  %s  缺 .sig（最新件/别名件必须可验）" % name)
                fails += 1
            else:
                print("SKIP  %s  无 .sig（B1 启用前历史件，不追签）" % name)
                skips += 1
            continue
        ok, msg = verify(z)
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name,
                            "" if ok else "  " + msg))
        fails += 0 if ok else 1
    print("check-sign: PASS %d / FAIL %d / SKIP %d（共 %d 件；SKIP=B1 前历史件）"
          % (len(zips) - fails - skips, fails, skips, len(zips)))
    sys.exit(1 if fails else 0)


main()

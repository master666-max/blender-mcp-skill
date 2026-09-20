# -*- coding: utf-8 -*-
"""run-negative-probes.py — M13 反向探针集随包自检（F-156 治本，v2.5.5 起随包）

背景：指纹/围栏的「实质内容零指纹」与「恒真断言」两次空洞（F-149/F-155）都是由
外部审计探针发现的——稳态要可自证，探针集必须随包。本脚本把 M13 反向实测机器化：

对每个内建探针：把 skill 根复制到临时目录 → 施加破坏 → 在副本上跑
run-regression-checks.py → 断言「指定条款 FAIL 且 exit=1」。另含正例对照
（不改动 → 全 PASS exit 0）。任一探针未触发或正例失守 → exit 1。

用法：py evals/run-negative-probes.py [--root <skill根目录>]
发布闸：建议每次发版与 ①查 同跑（见 regression-checks.md 发布前四查注记）。

探针集即「最小回归面」：每条对应一次真实空洞或高风险面（F-148/F-149/F-155 家族）。
新增敏感条款时应同步在此登记一条破坏探针。
**F-163 纪律**：期望标记一律用 ASCII（如 LEDGER-INVARIANT / FAIL #NN）；
若必须含中文，须在**未设任何编码变量**的环境下实测一次——子进程管道打印按平台
编码、本 harness 按 UTF-8 解码，中文标记在默认环境下恒不匹配（假阴性）。
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)

# (探针名, 目标文件相对路径, 旧串, 新串（None=整段删除）, 期望 FAIL 的条款号,
#  期望输出标记[None=默认 FAIL  #条款号], 期望退出码[默认 1])
PROBES = [
    ('P-N85a 删三态表四行（保留引导句）', 'SKILL.md',
     '| `up_to_date` | `source` | 含义 | 处置 |\n   |---|---|---|---|\n   | `true` | `native` | 正常 | 继续 |\n   | `false` | `native` | 协议落后（确认过期） | 按提示重装 addon（INSTALL §2） |\n   | `false` | `missing` | 旧 addon 无 get_addon_info（确认过期） | 同上重装 |\n   | `null` | `error` | 握手瞬断/环境问题 | **重试一次**；仍失败走 §6 排障——**勿判过期** |\n\n   ',
     None, 85, None, 1),
    ('P-N85b 篡改第 2 行处置列', 'SKILL.md',
     '| `false` | `native` | 协议落后（确认过期） | 按提示重装 addon（INSTALL §2） |',
     '| `false` | `native` | 协议落后（确认过期） | 随便处理 |', 85, None, 1),
    ('P-N85c 只删首行', 'SKILL.md',
     '| `true` | `native` | 正常 | 继续 |\n',
     '', 85, None, 1),
    ('P-N85d 反转禁令', 'SKILL.md',
     '勿用 `warning`',
     '可用 `warning`', 85, None, 1),
    ('P-N86 默认通道声明改写', 'SKILL.md',
     '默认通道=brickfly-mcp',
     '默认通道=upstream-mcp', 86, None, 1),
    ('P-N81 围栏锚短语破坏', 'SKILL.md',
     'U-05 解耦围栏',
     'U-05 解耦栏', 81, None, 1),
    ('P-N71 感知自检段破坏', 'SKILL.md',
     '感知自检（U-04，多模态前提）',
     '感知自检（U-04）', 71, None, 1),
    ('P-NL161 删历史台账行 F-100', 'evals/regression-checks.md',
     '| F-100 |',
     None, None, 'LEDGER-INVARIANT', 3),
]


def run(runner, root, cwd):
    # F-163：子进程在管道上按平台默认编码（Windows=GBK）打印，父进程按 UTF-8 解码
    # 会让中文期望标记永不匹配——注入 UTF-8 环境使两侧对称，判定与运行环境无关
    probe_env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    # runner 与其台账/条款表同目录——探针必须跑「副本自带」的 runner，
    # 否则台账类探针（改 evals/regression-checks.md）对原版 HERE 不可见（F-161 探针教训）
    p = subprocess.run([sys.executable, runner, "--root", root],
                       cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=probe_env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    runner = os.path.join(HERE, "run-regression-checks.py")
    tmp = tempfile.mkdtemp(prefix="m13probe_")
    fails = 0
    try:
        # 正例对照：不改动 → 全 PASS
        ctrl = os.path.join(tmp, "ctrl")
        shutil.copytree(root, ctrl,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        rc, out = run(os.path.join(ctrl, "evals", "run-regression-checks.py"), ctrl, HERE)
        if rc == 0 and "PASS" in out:
            print("PASS  正例对照（未改动 → exit 0）")
        else:
            print("FAIL  正例对照：未改动副本上 runner 异常（exit %d）——探针结论不可信" % rc)
            fails += 1

        for pi, (name, rel, old, new, clause, marker, expect_rc) in enumerate(PROBES):
            d = os.path.join(tmp, "probe_%d" % pi)
            shutil.copytree(root, d,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            target = os.path.join(d, rel.replace("/", os.sep))
            text = open(target, encoding="utf-8").read()
            n = text.count(old)
            if n < 1:
                print("FAIL  %s：探针旧串在目标文件中不存在（锚串漂移？先修探针或指纹）" % name)
                fails += 1
                continue
            text = text.replace(old, new if new is not None else "", 1 if new else n)
            open(target, "w", encoding="utf-8", newline="").write(text)
            rc, out = run(os.path.join(d, "evals", "run-regression-checks.py"), d, HERE)
            if clause is not None:
                triggered = ("FAIL  #%02d" % clause) in out or ("FAIL  #%d" % clause) in out
                label = "FAIL #%d" % clause
            else:
                triggered = (marker in out)
                label = marker
            if rc == expect_rc and triggered:
                print("PASS  %s → %s（exit %d）" % (name, label, rc))
            else:
                print("FAIL  %s：期望 %s + exit %d，实测 exit=%d、触发=%s"
                      % (name, label, expect_rc, rc, triggered))
                fails += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = len(PROBES) + 1
    print("summary: %d/%d PASS（含正例对照；破坏探针 %d 条 + 台账集探针 1 条）"
          % (total - fails, total, len(PROBES)))
    sys.exit(1 if fails else 0)


main()

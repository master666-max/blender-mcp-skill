# 工单：WO-R4 — DSH v1.4 审查回写（V-06~V-11 处置）与 v1.5 发布

| 项 | 值 |
|---|---|
| 工单号 | WO-BMCP-R4 |
| 日期 | 2026-09-12 |
| 状态 | **已执行完毕（用户批准，同日交付 v1.5）** |
| 上游 | `Blender技能审计_MCP_v1.4_20260912\`（BMCP-V14-20260912，V-06~V-11 六条发现）|
| 目标产物 | skill v1.5 + 六宿主升级 + v1.5 通用安装包 |

## 处置清单

| # | 发现 | 处置 | 落点 |
|---|---|---|---|
| V-06 | 自测 q6 FAIL 未修就发布（高） | **以 q6 重测证据部分推翻**：环境修复（删两个 .bak 注册）后重测 2/3≥0.5 翻转 PASS，按事先约定处置顺序 description 裁定不改；评测报告已追加重测段 | evals/eval-results-20260912.md |
| V-07 | 评测结果不随包（中） | 结果文件随 v1.5 包分发；regression-checks.md 顶部写最近结论 | evals/ |
| V-08 | 2 条指纹不可直用（中） | 全表改为字面量语义 + 表头声明；#6 改 `属性名必须是字面量`、#7 改 `save_as_mainfile` | evals/regression-checks.md |
| V-09 | 缺 runner（低） | 新增 `evals/run-regression-checks.py`（解析 md 表、字面量/re: 双语义、FAIL 退出码 1） | evals/ |
| V-10 | 评测台架无场景隔离（中） | reviewer prompt 新增「场景纪律」节：快照→EVAL_ 前缀→禁换 world/camera→禁 save_mainfile→副作用清单必填 | evals/trigger-eval-reviewer-prompt.md |
| V-11 | zip ⊊ 工作副本（信息） | 流程注记：验收基线以 zip 哈希为准、EXTRA 留档有回报（已写入审计侧 04 号文件，skill 侧不另立） | — |
| P3 | 新工具缺自检的规律 | 12 分册 §7 新增「新工具纪律」段 | references/12 |

## 执行回执

- `run-regression-checks.py` 首跑即暴露自身 bug（指纹未剥 markdown 反引号 → 3/26 假 FAIL），
  修复后 **26/26 PASS**——V-09 预言的"复查者必付成本"与 P3 新纪律在同一瞬间被自我验证；
- V-02 守卫（v1.4 引入）本轮无改动，DSH 二审已做 4 用例验证；
- v1.5.zip：**41 文件**（V-12 勘误：本回执初稿误写 40，以打包脚本输出与审计实测 41 为准）/ 全项校验 PASS（含 runner 自跑 26/26 前置门槛）；
- 六宿主升级：见同日升级记录（5 根 BACKUP+UPGRADE + ZCode 源头）。

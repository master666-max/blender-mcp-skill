# 贡献指南

## 先读

- `SKILL.md`（入口）与 `INSTALL.md`（安装）
- 本包自带体检：`py evals/run-regression-checks.py`（89 条规则回归）与
  `py evals/run-negative-probes.py`（反向探针自检）——**改动前后都必须全绿**

## 改动分类

| 类型 | 纪律 |
|---|---|
| 门面/社区件（README、SECURITY、CONTRIBUTING、showcase） | 可直接提交，不进发行 zip |
| **发行负载**（SKILL/INSTALL/references/scripts/fragments/nodes/assets/evals/docs/CHANGELOG） | 改动须配套：条款指纹更新、台账登记、版本三处同步（SKILL/INSTALL/zip 名）、四查全过 |
| 代码/手册行为变更 | 同上，另需在 CHANGELOG 记录动机与验证证据 |

## 提交

1. Issue 先行（描述问题与复现）；
2. PR 关联 issue，注明改动分类；
3. 发行负载改动附四查 + M13 自检输出。

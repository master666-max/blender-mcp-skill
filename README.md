# blender-mcp-skill

让 AI 直连你开着的 Blender：建模 / 材质 / 几何节点 / 灯光相机 / 渲染 / 动画 / 资产管理，干完自己看图验收。
14 分册手册 + 离线安装包。Claude Code / Cursor / ZCode / Codex / DSH 通用。

当前版本 v2.5.9。

## 前置

| 件 | 要求 |
|---|---|
| Blender | 5.2 LTS（4.x / 5.x 大部分兼容，差异已在新旧分册标注） |
| 服务端 | `uv tool install ./assets/brickfly-mcp-bundle/brickfly_mcp-2.0.0-py3-none-any.whl` |
| addon | `assets/brickfly-mcp-bundle/brickfly_mcp.py`（addon v1.7 / 协议 7 / 31 工具） |
| 回退通道 | `assets/blender-mcp-bundle/` 或 `uv tool install mcp-for-blender` |

## 装 skill

把整个文件夹复制进客户端技能目录（用户级 / 项目级路径表见 `INSTALL.md` §3）。
入口 `SKILL.md`；手册 `docs/` `references/`；评测 `evals/`；节点与资产 `nodes/` `assets/` `fragments/`。

## 坑（都踩过）

- **服务端别按包名装**。`uv tool install brickfly-mcp` / `uvx brickfly-mcp` 必失败——fork 未上 PyPI。只能装本地 wheel。
- **默认通道与回退通道二选一**。同时启用会撞操作符命名空间和 9876 端口。
- **addon 在 `blender -b` 后台模式拒绝启动**（上游设计，命令需主线程）。无头场景走 `references/10-headless-ci.md` 的 bpy wheel 路线。
- **别拿 `serverInfo.version` 判断版本**。那是 FastMCP 写入的 mcp 依赖包版本。真实版本看 `pip show brickfly-mcp`。
- **版本期望值**：addon [1,7] / 协议 7 / 31 工具。不符按 `SKILL.md` §0 第 2 步处置。
- 2.0 起工具 28 → 31（新增 `describe_node_type` / `bpy_api_lookup` / `export_scene`），协议 5 → 7。旧 addon 会报 `up_to_date: false`，照提示重装。

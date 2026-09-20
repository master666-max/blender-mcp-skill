# ATTRIBUTION — brickfly-mcp fork 包来源与许可

## 这是什么

**brickfly-mcp = 本 skill 收编的自有通道**（解耦报告 S1，2026-09-20）：把上游
`mcp-for-blender` 2.0.0 全量源码 vendor 进来，仅改写**外部身份字段**，行为与上游
2.0.0 逐项对齐（parity，机械 diff 可证）。

## 上游与作者（义务声明）

- **原作者**：Siddharth Ahuja（@sidahuj）
- **上游项目**：MCP for Blender（原名 blender-mcp）
- **上游仓库**：https://github.com/ahujasid/mcp-for-blender
- **vendor 基准**：PyPI `mcp_for_blender-2.0.0-py3-none-any.whl`（files.pythonhosted.org 官方件）
- **原署名**：`Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025`（addon 源码头保留）

## 许可

MIT License（全文见 `LICENSE`，与上游同）。允许再分发，须保留上述版权声明与本文件。

## fork 改写清单（parity diff 的合法差异，全部为身份字段）

| 项 | 上游 | fork |
|---|---|---|
| 发行名 / import 包名 | mcp-for-blender / `blender_mcp` | **brickfly-mcp** / `brickfly_mcp` |
| CLI 入口 | `mcp-for-blender` | **`brickfly-mcp`** |
| serverInfo.name | `BlenderMCP` | `BrickflyMCP` |
| addon 模块文件名 | `blender_mcp.py` | **`brickfly_mcp.py`** |
| addon bl_info 名 / N 面板标签 | MCP for Blender | **Brickfly MCP for Blender** |
| 用户引导文本 | `uvx blender-mcp install-addon` 等 | `brickfly-mcp install-addon` 等（**v2.5.1 起去掉 `uvx` 按名前缀**——fork 未上 PyPI，见 F-141） |
| 其余（协议 7、31 工具、安全模式、五库、telemetry） | — | **逐字节不动**（v2.5.2 起例外见下节） |

## 行为修正（fork 相对上游的一处有意差异，v2.5.2 起）

`get_addon_status` 的**握手失败/无效 payload 两个错误分支**：`up_to_date` 由上游的
`false` 改为 **`null`（三态）**——`false` 的字面含义是「确认过期」，而握手瞬断只是
连接问题；误报过期会引导用户做无意义的重装（F-147）。`source:"error"`/`warning`
非空时请先按连接排障重试。确认过期的分支（addon 无 `get_addon_info`）仍为
`false`。处置判据见 SKILL §0 第 2 步。

## 与上游通道的关系

- **二选一启用**：fork addon 与上游 addon 同时在 Blender 偏好里**启用**会撞
  操作符命名空间与 9876 端口（上游 auto_start 先占，后者拒启）——装了 fork 就
  停用上游 addon（文件可共存，模块名不同不冲突）。
- 上游通道（`assets/blender-mcp-bundle/`）保留作回退与对照，不再默认。

## 完整性校验

`SHA256SUMS.txt` 记录各文件哈希（LF 行尾）；离线安装前重跑 `sha256sum -c SHA256SUMS.txt`。

## 安全提示

威胁模型与上游相同：addon 在本机 9876 端口开启 socket 并接受任意 bpy 代码执行，
启用即接受其威胁模型——建议配合 `BLENDER_MCP_SAFE_MODE=1` 与回环绑定，
详见本 skill `references/11-deployment-security.md`。fork 的供应链优势：发布闸
由本 skill 四查把守，不随上游 latest 漂移。

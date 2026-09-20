# ATTRIBUTION — blender-mcp 捆绑包来源与许可

## 作者与项目

- **作者**：Siddharth Ahuja（@sidahuj）
- **项目**：MCP for Blender（原名 blender-mcp，2026-09-16 v2.0.0 起改用新名）
- **仓库**：https://github.com/ahujasid/mcp-for-blender（旧地址 blender-mcp 重定向）
- **PyPI**：https://pypi.org/project/mcp-for-blender/（旧名 blender-mcp 同版兼容）
- **文件头原署名**：`Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025`

## 本包内容与来源

| 文件 | 版本 | 来源 | 抓取日期 |
|---|---|---|---|
| `addon.py` | addon v1.7 / 协议 7 | PyPI `mcp_for_blender-2.0.0-py3-none-any.whl` 内 `blender_mcp/bundled/addon.py`（v1.6/协议 5 版于 2026-09-12 取自 github.com/ahujasid/blender-mcp main） | 2026-09-19 |
| `mcp_for_blender-2.0.0-py3-none-any.whl` | 2.0.0（PyPI 最新；含 MCP 服务端；项目已由 `blender-mcp` 改名 `mcp-for-blender`，旧名同版兼容；`mcp` 依赖包需另行安装，勿与本项目版本混淆） | PyPI（files.pythonhosted.org 官方源） | 2026-09-19 |
| `LICENSE` | MIT | 同 addon 来源 | 2026-09-12 |

## 完整性校验

`SHA256SUMS.txt` 记录四文件哈希。本包制作时已做来源比对：v1.6 包曾做**本机已装副本
（Blender 5.2 插件目录）== 官方源下载**逐字节比对；v2.0 包 addon.py 与 wheel 均直接取自
PyPI 官方源 wheel 内文件。离线安装前请重跑 `sha256sum -c SHA256SUMS.txt`。

## 许可

MIT License（全文见 `LICENSE`）。允许再分发，须保留上述版权声明与本文件。
本捆绑包为**离线兜底**用途：在线安装永远以官方源为准（`uvx mcp-for-blender install-addon` /
`uv tool install mcp-for-blender`；旧名 `blender-mcp` 同版兼容）。

## 免责与安全提示

- blender-mcp 为第三方社区项目，与 Blender Foundation 无隶属关系；
- 2026-08-10 该项目维护者 GitHub 账号曾被入侵（后恢复）——使用前务必校验哈希；
- `addon.py` 会在本机 9876 端口开启 socket 服务并接受任意 bpy 代码执行，启用即接受
  其威胁模型，建议配合 Safe Mode（`BLENDER_MCP_SAFE_MODE=1`）与回环绑定使用，
  详见本 skill `references/11-deployment-security.md`。

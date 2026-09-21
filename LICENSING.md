# LICENSING — 本仓库的分区许可说明

本仓库**不是**单一许可，采用「**分区许可**」。顶层 [LICENSE](LICENSE) 的 MIT 全文
**只适用于本项目的原创部分**；`assets/` 下的两个捆绑包是**第三方作品 / 派生作品**，
**各自保留其原有许可与署名**。

请按下面的分区对照取用。

---

## 一、本项目原创部分 → MIT

适用顶层 [LICENSE](LICENSE)（Copyright (c) 2026 master666-max）：

```
SKILL.md          INSTALL.md        README.md         CHANGELOG.md
references/       scripts/          nodes/            fragments/
evals/            docs/
```

## 二、`assets/` 下的捆绑包 → 各自保留原许可

这两个目录是**离线安装包**（默认通道 + 回退通道），**不属于本人的原创作品**，
再分发时**必须**保留其目录内的 `LICENSE` 与 `ATTRIBUTION.md`。

### 2.1 `assets/blender-mcp-bundle/` —— 上游（回退通道）

| 项 | 内容 |
|---|---|
| 作品 | **MCP for Blender**（原名 blender-mcp，v2.0.0 起改名） |
| 作者 | **Siddharth Ahuja（@sidahuj）** |
| 仓库 | https://github.com/ahujasid/mcp-for-blender |
| PyPI | https://pypi.org/project/mcp-for-blender/ |
| 本仓库内的许可 | 见 `assets/blender-mcp-bundle/LICENSE`（**MIT，版权归原作者**） |
| 出处与版本溯源 | 见 `assets/blender-mcp-bundle/ATTRIBUTION.md` |
| 完整性校验 | `assets/blender-mcp-bundle/SHA256SUMS.txt` |

### 2.2 `assets/brickfly-mcp-bundle/` —— 本项目自有 fork（默认通道）

| 项 | 内容 |
|---|---|
| 作品 | **brickfly-mcp**（上游 `mcp-for-blender` 2.0.0 的 vendor fork，仅改身份字段） |
| 上游作者 | **Siddharth Ahuja（@sidahuj）** |
| vendor 基准 | PyPI `mcp_for_blender-2.0.0-py3-none-any.whl` |
| 本仓库内的许可 | 见 `assets/brickfly-mcp-bundle/LICENSE`（**MIT，与上游同**） |
| 上游义务声明 + fork 改写清单 | 见 `assets/brickfly-mcp-bundle/ATTRIBUTION.md` |
| 完整性校验 | `assets/brickfly-mcp-bundle/SHA256SUMS.txt` |

> **brickfly-mcp 是派生作品**：上游为 MIT，MIT 允许再分发与修改，
> 但**必须保留原版权声明与许可全文** —— 这两样都随包保留在上述文件中。
> 对原作者的署名义务**不因改名而免除**。

---

## 三、取用速查

| 你想用 | 适用哪个许可 |
|---|---|
| SKILL.md / references / scripts / nodes / fragments / evals | 顶层 `LICENSE`（MIT，master666-max） |
| `assets/blender-mcp-bundle/` 里的任何文件 | 该目录 `LICENSE`（MIT，**Siddharth Ahuja**） |
| `assets/brickfly-mcp-bundle/` 里的任何文件 | 该目录 `LICENSE`（MIT，含上游署名义务） |

⚠️ **不要把本仓库的 MIT 直接套到 `assets/` 上** —— 那会抹掉原作者的署名，
不符合 MIT 自己的保留条款。

---

## 四、为何 LICENSE 文件里不写这段说明

GitHub 的许可证识别器要求 **`LICENSE` 文件只含标准许可全文**；
一旦在全文前后追加说明文字，就会被识别成 `Other / NOASSERTION`
（本账号下 `cbb-pipeline` 就是这样被误标的）。
所以分区说明单独放在本文件，`LICENSE` 保持纯净。

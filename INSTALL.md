# INSTALL — blender-mcp skill 安装说明（v2.7.0）

> 面向 AI 编码代理（ZCode / Claude Code / Cursor / Codex 等）的 Blender 实时操控技能包。
> 让代理通过 blender-mcp 直连真实运行的 Blender：建模、材质、几何节点、灯光相机、渲染出图、
> 动画、场景审计、导入导出，并内置 PRD 反问循环与力大砖飞执行契约。

## 1. 前置条件

| 组件 | 要求 | 说明 |
|---|---|---|
| Blender | **5.2 LTS**（4.x/5.x 大部分兼容，版本差异已在新旧分册标注） | blender.org 下载 |
| Brickfly MCP for Blender 插件（**默认通道**） | addon v1.7 / 协议 7 | 离线包已内附（`assets/brickfly-mcp-bundle/brickfly_mcp.py`），或（**先装好下方 server 后**）`brickfly-mcp install-addon` |
| brickfly-mcp 服务端（**默认通道**） | 按**协议 7 / addon v1.7** 对齐（包体 2.0.0，skill 自有 fork） | `uv tool install ./assets/brickfly-mcp-bundle/brickfly_mcp-2.0.0-py3-none-any.whl`——**fork 未上 PyPI**，`uv tool install brickfly-mcp` / `uvx brickfly-mcp` 按名解析必失败（F-141） |
| （回退）上游通道 | mcp-for-blender / blender-mcp 2.0.0 同版兼容 | `assets/blender-mcp-bundle/` 与 `uv tool install mcp-for-blender`；**回退通道与默认通道行为对齐**（fork=上游 2.0.0 vendor + 身份改写），二选一部署 |

> **U-05 上游解耦（v2.5.0 起）**：默认通道改为 **brickfly-mcp**——本 skill 收编上游
> 2.0.0 全量源码的自有 fork（MIT，仅身份字段改写、行为 parity，diff 可证；详见
> `assets/brickfly-mcp-bundle/ATTRIBUTION.md` 与工作区 `_blender_skill_上游解耦可行性报告_20260920.md`）。
> 动机：上游 24 天 7 发（2.0.0 一天逼出一轮全量适配）、safe mode/telemetry 默认翻转、
> addon 拒后台模式——收编后行为面进入本 skill 指纹网，节奏自主。**上游通道保留为回退**。
> **版本期望值**：`get_addon_status` 期望 addon [1,7] / 协议 7 / 31 工具；不符按 SKILL §0
> 第 2 步处置。**fork 与上游 addon 二选一启用**（同时启用撞操作符命名空间与 9876 端口）。

> **2.0 事实（沿 v2.4.0；F-135 勘误）**：工具 **28 → 31**（计数口径=server.py `@mcp.tool(`
> 静态计数或客户端 tools/list），新增 **3 个**——`describe_node_type` / `bpy_api_lookup` /
> `export_scene`（`disable_telemetry` / `record_trajectory_feedback` 于 1.9.x 已存在）；
> **协议 5 → 7**——旧 addon（v1.6/协议 5）会报 `up_to_date: false`，按提示重装；
> addon 在 `blender -b` 后台模式**拒绝启动**（自 v1.6 起即如此；上游设计，命令需主线程执行），无头场景走
> references/10-headless-ci.md 的 bpy wheel 路线。

> **版本口径注意**【V-01 修正】：内附的 mcp-for-blender/brickfly-mcp **2.0.0** 即要求
> `user_prompt` 参数（沿袭自 1.9.x）；服务端握手自报的 `serverInfo.version`（如 "1.30.0"）
> 是 FastMCP 写入的 **mcp 依赖包版本**，与本参数无关，也**不存在版本漂移**——真实包版本看
> `pip show brickfly-mcp`（或 `pip show mcp-for-blender`）。本包示例已按此写法（SKILL.md §0）。
| 代理客户端 | 支持 Agent Skills 标准（SKILL.md）的任意客户端 | 客户端路径见 §3 |

## 2. 三步安装

### 第 1 步：装 skill（按你的客户端选路径）

把本 `blender-mcp/` 整个文件夹复制到对应目录：

| 客户端 | 用户级（推荐） | 项目级 |
|---|---|---|
| ZCode | `~/.zcode/skills/blender-mcp/` | `<项目>/.zcode/skills/` 或 `<项目>/.agents/skills/` |
| Claude Code | `~/.claude/skills/blender-mcp/` | `<项目>/.claude/skills/` |
| Cursor | `~/.cursor/skills/blender-mcp/`（也兼容读取 `~/.claude/skills/`） | `.cursor/skills/` |
| Codex / 跨工具通用 | `~/.agents/skills/blender-mcp/`（Codex/Copilot CLI/Gemini CLI 均识别） | `<项目>/.agents/skills/` |
| DeepSeek Harness (DSH) | `~/.dsh/skills/blender-mcp/`（rank 400） | `<项目>/.dsh/skills/`（rank 100，**优先选中且无沙箱门槛**） |

> **DSH 注意**【实测】：默认 `workspace-write` 文件沙箱会**拒绝写工作区外的用户级根**
> （`~/.dsh/skills` 报 Access denied）——要么用项目级根（工作区内，无门槛），要么把文件
> 策略调宽再装。DSH 投放后**发现即生效**（无需重启，skill 目录带 watcher）。

> ⚠️ **多客户端同机注意（V-14/V-17）**：上表是"按你的客户端**选一行**"，不是"每行都投"——
> 一台机器装多个客户端时，**跨根同名注册**会让 ZCode 的子代理 skill 调用报 `ambiguous`。
> **特别注意：`.agents` 被 ZCode 与跨工具客户端共用**——装了 ZCode 的机器优先只投
> `~/.zcode/skills`，**不要再投 `~/.agents/skills`**，否则 ZCode 会看到两份同名
> （v1.3~v1.5 三轮实测）。升级后确认 `SKILL.md` 的 `metadata.version` 已随包递增；
> **升级备份移出 skills 根**（见 §4）。

### 第 2 步：装 Blender 侧 addon + 起服务

- **离线（默认通道）**：Blender → Preferences → Add-ons → Install from Disk → 选
  `assets/brickfly-mcp-bundle/brickfly_mcp.py`（**装前先校验**：在该目录跑
  `sha256sum -c SHA256SUMS.txt`；文件名即模块名，离线装用 `brickfly_mcp.py` 可直接得到
  正确模块名）→ 启用插件；
- **server 已装时（默认通道）**：`brickfly-mcp install-addon`（本地入口；**勿用**
  `uvx brickfly-mcp`——fork 未上 PyPI，按名解析必失败，F-141）；升级安装自动保留旧文件为 `.bak`；
- **（回退）上游通道**：`assets/blender-mcp-bundle/addon.py` 或
  `uvx mcp-for-blender install-addon`——**与 fork addon 二选一启用**；
- Blender 侧栏（视口按 `N`）→ "Brickfly MCP for Blender"（回退通道为 "MCP for
  Blender"）→ Start MCP Server（插件默认随 Blender 自启）。**addon 侧不支持
  `blender -b` 后台启动**（自 v1.6 起即显式拒绝；上游设计，命令需主线程执行）。

### 第 3 步：注册 MCP 服务端（客户端配置文件）

ZCode 示例（`~/.zcode/cli/config.json` → `mcp.servers.blender`）：

```json
"blender": {
  "command": "C:\\Users\\<你>\\.local\\bin\\brickfly-mcp.exe",
  "args": [],
  "env": {
    "BLENDER_MCP_SAFE_MODE": "1",
    "DISABLE_TELEMETRY": "true",
    "BLENDER_HOST": "localhost",
    "BLENDER_PORT": "9876"
  }
}
```

四个环境变量建议原样保留（Safe Mode 开 / 遥测关 / 回环绑定 / 端口对齐）。
**通道迁移（U-05）**：旧配置若仍指向 `blender-mcp.exe` / `mcp-for-blender.exe`（上游
通道），把 `command` 改为 `brickfly-mcp.exe` 并重启客户端即切到默认通道；插件侧停用
上游 addon、启用 `Brickfly MCP for Blender`。本机（2026-09-20）ZCode 配置已切，
**DSH cordis 补丁待改**（改完需重启 `dsh web`，见下节）。
**遥测双开关**【实测】：`DISABLE_TELEMETRY=true` 只关**服务端日志侧**；addon 侧
`telemetry_consent` 默认仍是 true（收集 prompt/代码/截图/场景数据）——需在对话里让代理
调用 `disable_telemetry` 工具（一次性、只能关不能开），或去 Blender 偏好设置取消勾选。
隐私敏感者两个都做，并用 `get_addon_status` 复验 `telemetry_consent: false`。

**五大资产集成默认全关**（PolyHaven / Poly Pizza / Sketchfab / Hyper3D Rodin / Hunyuan3D）——
这是设计行为，不是故障。需要哪个在 Blender N 面板 → "Brickfly MCP for Blender" → 勾选即可，
**改完立刻生效，无需重启**（提示文案里的"Restart the connection"是错的）。开关是
Scene 级属性，**换 .blend 或新开场景就回到全关**，每次任务开头探一遍。

**evals 工具的解释器要求**：包内 `evals/` 的 runner / check-version 是 Python 脚本，需要真实
CPython——**推荐 `py` 启动器**（Windows 官方 launcher）；若 `python` 命令报 exit 9009 或
"不是内部或外部命令"，是 Store 占位程序/别名问题，见 regression-checks.md 的解释器注记。
Blender 自带解释器（`…\Blender 5.2\5.2\python\bin\python.exe`）亦可跑纯文档类工具。
Claude Code / Cursor 用各自的 MCP 配置入口，`command/env` 内容相同。

### DSH（DeepSeek Harness）单独一节【实测·BMCP-V161 审计 F-22】：注册机制与上面完全不同

DSH 的 MCP **不走配置文件键**（`settings.yaml` 里配了也没用），而是 **Cordis overlay 补丁**：
`@deepseek-ai/dsh-mcp-client` 插件条目，落在 profile 级用户补丁层
`~/.dsh/profiles/web/cordis.patch.yml`（profile 对应启动方式，本机=web / `pnpm dsh web`）。追加：

```yaml
- insert:
    - id: blender-mcp
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: blender
        transport: stdio
        command: 'C:\Users\<你>\.local\bin\brickfly-mcp.exe'
        cwd: !!js process.cwd()
        env:
          BLENDER_MCP_SAFE_MODE: '1'
          DISABLE_TELEMETRY: 'true'
          BLENDER_HOST: localhost
          BLENDER_PORT: '9876'
```

要点：① **写前先备份原文件**（备份→写→js-yaml 校验，顺序不能反——备份晚于写入等于没有回滚点）；
② **补丁在 harness 启动时生效，需重启 `dsh web`**；③ 生效判据=工具表新增 31 个
`mcp__blender__*`（2.0.0 工具全量），`get_addon_status` 复验通过。
④ **旧命令名兼容**：2.0.0 的 CLI 入口只有 `mcp-for-blender`——若客户端配置仍指向
`blender-mcp.exe`，用 `mcp-for-blender.exe` 复制覆盖该路径即可（本机已这样做并实测可用）。

### 发行签名与验签（v2.6.0 起，B1）

发行 zip 附 SSH 签名（`*.zip.sig`，命名空间 `blender-mcp`，签名公钥与 allowed_signers
在 `assets/release-signing/`）。**哈希只防损坏、不防投毒**（分发页可同时换掉件与哈希），
签名才能锚定"这份包出自作者密钥"。验签（任一台有 ssh-keygen 的机器）：

```bash
ssh-keygen -Y verify -f assets/release-signing/allowed_signers   -I blender-mcp-releases -n blender-mcp -s <发行包>.zip.sig < <发行包>.zip
# 输出 "Good "blender-mcp" signature" 即通过
```

服务端离线安装（默认通道）：`pip install assets/brickfly-mcp-bundle/brickfly_mcp-2.0.0-py3-none-any.whl`
（回退上游通道：`assets/blender-mcp-bundle/mcp_for_blender-2.0.0-py3-none-any.whl`；
注意其 `mcp` 等运行依赖需另备，见各包 ATTRIBUTION.md）。

## 3. 验证安装

1. 重启客户端 → 对话里说"检查 Blender 场景"——代理应调用 `get_scene_info`；
2. 健康判据：`netstat -ano | findstr 9876` 只见**一条** `127.0.0.1:9876 LISTENING`；
3. 热身样例：SKILL.md §8（建方块→材质→三点光→出图回读，全程 <30s/步）。

## 4. 升级与回滚（重要：备份不要落在 skill 发现根内）

**升级**：新版本 zip 解压后整目录替换上表中的 `blender-mcp/`；替换前把旧目录
**移出 skills 根**归档（如 `<审计或备份目录>/blender-mcp.bak.<日期>/`）。

> ⚠️ **不要把备份留在 skills 根内部**（如 `blender-mcp.bak.20260912/`）——skill 发现规则是
> `<根>/<名字>/SKILL.md`（深度 1），备份目录里有完整 SKILL.md，会被注册成**第二份同名
> skill**：子代理的 skill 调用会报 `ambiguous`，触发评测也会被污染（v1.3~v1.5 三轮实测）。

**同名自查**（每个根下同名 bundle 只应有一份）：

```powershell
Get-ChildItem "$env:USERPROFILE\.zcode\skills" | Where-Object Name -like 'blender-mcp*'
# 输出多于 1 行 = 有污染，把非当前版本的目录移出根外
```

**回滚**：把归档的旧版目录移回原位即可（先移走当前版，别让两份并存）。
升级备份若含 zip 里没有的文件（如评测结果），先另存再清理——备份是证据。

## 5. 包内容地图

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 入口：连接自检 / 七条铁律 / 任务路由 / 恢复 SOP / 协议摘要 |
| `references/00~14` | **14 册**：00 需求澄清（PRD 反问循环）、01 场景物体、02 材质、03 灯光相机渲染（含渲染隔离）、04 动画物理、05 几何节点、06 导入导出与资产库、07 网格体检、08 参数化生成、09 安全模式与错误、10 无头 CI、11 部署安全、12 力大砖飞执行契约、13 建模工艺、**14 视觉工作流（多模态深度融合）** |
| `scripts/` | 骨架模板 brickfly_skeleton.py + 场景审计 / 三点布光 / 渲染校验三件套 |
| `fragments/` + `nodes/` | 代码积木库与节点组库（复用阶梯，随用随长） |
| `assets/brickfly-mcp-bundle/` | **默认通道**：Brickfly MCP for Blender 离线包（skill 自有 fork=上游 2.0.0 vendor+身份改写，MIT，SHA256SUMS 校验；addon v1.7 + server 2.0.0 wheel；溯源见包内 ATTRIBUTION.md） |
| `assets/blender-mcp-bundle/` | （回退）上游 MCP for Blender 离线安装包（作者 Siddharth Ahuja @sidahuj，MIT，SHA256SUMS 校验；addon v1.7 + server 2.0.0 wheel） |
| `evals/` | 20 条触发评测集（should-trigger 正负例） |
| `docs/` | 架构设计书（力大砖飞 v3.0）、决策模型映射报告与工单档案 |

## 6. 兼容性与许可

- 所有结论按【实测】（Blender 5.2.1 LTS + brickfly-mcp 2.0.0 fork 通道 + Windows 中文 UI 真机验证）与
  【文献】（官方文档/社区，未复验）分级标注；升级 Blender 大版本后请重跑分册中的实测样例；
- blender-mcp 本体：MIT License（作者 Siddharth Ahuja），本包为其离线再分发，保留原版权声明；
- 本 skill 打包物：作者 misdeep，随包分发即用，无需署名。

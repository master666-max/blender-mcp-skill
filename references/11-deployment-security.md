# 11 部署与安全（安装 / 威胁模型 / 五层防御 / 维护）

> 来源：本机 2026-09-12《blender-mcp 安装测试与安全加固方案》会话文档
> （`<本机工作区>\blender-mcp-安全方案.md`）+ 本 skill 会话调研交叉验证。
> 【实测】= 该会话真机验证；【文献】= 官方文档/社区，未复验。

## 1. 安装部署（Windows 实测路径）

### 1.1 服务端（MCP host 侧）
```bash
# 默认通道（U-05 fork；未上 PyPI，必须从包内离线 wheel 装）：
uv tool install ./assets/brickfly-mcp-bundle/brickfly_mcp-2.0.0-py3-none-any.whl
# 回退上游通道（已上 PyPI，按名可装）：
uv tool install mcp-for-blender      # 旧名 blender-mcp 同版兼容（均为 2.0.0）
```
- 版本澄清【实测】：**brickfly-mcp 2.0.0（fork）与 mcp-for-blender 2.0.0（上游）均为
  协议 7 ↔ addon v1.7**；依赖包 `mcp` 是 1.30.0——**别把依赖版本当项目版本**（曾有误读）。
- ZCode 注册（`~/.zcode/cli/config.json` → `mcp.servers.blender`）：
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
四个环境变量缺一不可：Safe Mode 开、遥测关、回环绑定、端口对齐。
回退通道把 `command` 换回 `mcp-for-blender.exe` 即可；历史配置里的
`blender-mcp.exe`（上游 shim 副本）仍可用（F-134 勘误，v2.5.1 同步）。

### 1.2 Blender 侧 addon
- **默认通道**：`brickfly-mcp install-addon`（**须先按 §1.1 装好 server**；fork 未上
  PyPI，`uvx brickfly-mcp` 按名解析必失败——F-141），或本 skill
  `assets/brickfly-mcp-bundle/brickfly_mcp.py`（**离线兜底**，装前 `sha256sum -c SHA256SUMS.txt`，
  溯源与改写清单见同目录 ATTRIBUTION.md）；
- 位置（实测）：`%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\brickfly_mcp.py`；
- （回退上游通道：`uvx mcp-for-blender install-addon` / `assets/blender-mcp-bundle/addon.py`
  → `blender_mcp.py`）；
- 装后在 Preferences → Add-ons 启用；日常启动：视口 `N` → "Brickfly MCP for Blender"
  → Start MCP Server（插件默认 `auto_start_server=True`，随 Blender 自启）；
- **U-05 互斥纪律：fork addon 与上游 addon 不可同时启用**（操作符命名空间
  `blendermcp.*` 同源 + 9876 端口同占——先启者得，后者拒启）；文件共存无害（模块名不同）。

### 1.3 离线安装（无网络机器）
1. 服务端：`pip install ./brickfly_mcp-2.0.0-py3-none-any.whl`（wheel 在 skill assets/ 内；
   回退上游通道用 `mcp_for_blender-2.0.0-py3-none-any.whl`）；
2. addon：Blender Preferences → Add-ons → Install from Disk 选 `brickfly_mcp.py`
   （文件名即模块名，fork 离线包已按正确模块名命名）；
3. 依赖：wheel 不含 `mcp`/`fastmcp` 等运行依赖，离线机器需一并准备（`pip download brickfly-mcp==2.0.0`
   在联网机拉全依赖轮子——注意 brickfly-mcp 未上 PyPI，依赖以 mcp-for-blender==2.0.0 的
   依赖清单为准拉取）。

### 1.4 双通道与供应链（U-05）
- **默认通道 brickfly-mcp = 本 skill 自有 fork**（上游 2.0.0 vendor + 仅身份字段改写，
  行为 parity diff 可证，见 `assets/brickfly-mcp-bundle/ATTRIBUTION.md`）：发布闸由本
  skill 四查把守，**不随上游 latest 漂移**——这是对 2026-08-10 上游账号入侵类事件
  （【文献】）的结构性防御：哈希校验只能事后发现，收编+自建发布闸才能事前防御；
- 上游通道保留为回退与对照；**切回上游 = 客户端 command 改回上游 shim + 启用上游 addon**，
  行为契约（分册事实）在 2.0.0 版本点上对两通道同样成立；
- 上游发布监测进 HANDOFF §九触发条件：上游 release/协议变更 → 评估吸收（cherry-pick
  或重 vendor），**不自动跟随**。

## 2. 威胁模型：这套组合在防什么

`execute_blender_code` = 在 Blender 进程内执行任意 Python。五条风险通道：
1. **文件系统**（最大攻击面）：Blender 天生是文件处理器——保存/导入导出/贴图读写可触达任意路径；
2. **进程逃逸**：subprocess/外部程序；
3. **网络**：脚本直连外网（外传数据、下载执行）；
4. **持久化驻留**：handler/timer/driver/addon 注册——"一次中招，长期潜伏"；
5. **提示注入**：场景数据/资产站元数据藏指令诱导 AI（Safe Mode 只能兜底代码侧，兜不了"AI 被骗"侧）。

两个前置事实【实测】：socket 只绑 `127.0.0.1:9876`（局域网连不进来，netstat 确认）；
遥测默认开启（含代码/截图上传），`DISABLE_TELEMETRY=true` 已关并验证日志。

## 3. 五层防御

### 第 1 层 Safe Mode（已启用，防解释器逃逸）
AST 级静态校验（详见 09 分册白名单速查）。**关键认知：它不是沙箱**——封死
eval/exec/open/dunder 逃逸链，但 Blender 算子天生能碰文件：Safe Mode 下 AI 依然可以
`bpy.ops.wm.save_as_mainfile()` 覆盖你的 .blend、把导出写到任意路径。第 4 层不可省略。

### 第 2 层 Docker 隔离（可选加固，防服务端被攻破后摸到宿主机）
容器只跑 MCP 服务端，Blender 留宿主机，容器经 `host.docker.internal` 连回：
```json
"args": ["run", "-i", "--rm",
         "-e", "BLENDER_MCP_SAFE_MODE=1",
         "-e", "BLENDER_HOST=host.docker.internal",
         "-e", "DISABLE_TELEMETRY=true",
         "blender-mcp"]
```
【文献】Windows **不要加 `--network=host`**（那是 Linux 写法）。适用：跑不可信自动化/给别人演示。
代价：首次构建麻烦、镜像内不能 `uv tool upgrade`。单人日常用 1+4 层已够。

### 第 3 层 遥测与外部数据源（已关/默认关）
遥测已通过环境变量关闭（认 `DISABLE_TELEMETRY`/`BLENDER_MCP_DISABLE_TELEMETRY`/`MCP_DISABLE_TELEMETRY`）。
五大资产集成（PolyHaven/PolyPizza/Sketchfab/Hyper3D/Hunyuan3D）默认全关——要用再在面板勾选，
少一条"AI 从外网拉东西进来"的通道；Sketchfab token 属额外凭据暴露面，非必要不开。

### 第 4 层 操作兜底（Safe Mode 管不住的部分，靠流程）
1. **保存权在自己手里**（最值钱的一条）：给 AI 的指令明确"不要保存/不要导出"；
   Ctrl+Z 能救场景内操作，但"删了又保存过"就真没了；
2. 动手前手动存盘【文献】（官方 README 原话 ALWAYS save your work before using it）；
3. 开自动保存 + Save Versions 5~10：崩了去同目录 `.blend1/.blend2` 找历史；
4. 重要项目进 Git + LFS【文献】：`git lfs track "*.blend" "*.fbx" "*.png" "*.hdr"`，改坏直接 checkout；
5. 素材库与作业文件分离：资产单独 .blend，作业文件 Link/Append 引用，防 AI"顺手"删全局资产；
6. 用完即停：面板 Stop MCP Server 或关 Blender——减少暴露窗口。

### 第 5 层 监控
- `netstat -ano | findstr 9876`：应**只见一条** `127.0.0.1:9876 LISTENING`；多条=僵尸进程（见 09）；
  出现 `0.0.0.0:9876` 说明 addon 被改动过，立即停用排查；
- Blender 主控台窗口打印每条 MCP 命令日志，敏感操作盯一眼；
- 【文献】可选：防火墙出站规则限制 blender-mcp 进程联网（纵深防御）。

## 4. 维护速查

| 操作 | 命令 |
|---|---|
| 升级服务端 | `uv tool upgrade blender-mcp`（升级后重跑 install-addon 同步 addon） |
| 查协议兼容 | 服务端启动日志打印 `protocol N`/`addon [x,y]`，不匹配会告警 |
| 9876 被占 | 关多余 Blender 实例/僵尸进程（09 分册），或面板改端口并同步 `BLENDER_PORT` |
| 回归测试 | 重跑 skill evals 或该会话的 `blender_mcp_test.py`（需 Blender 侧服务已启动） |
| 临时关 Safe Mode | 不建议。确需时改配置 `BLENDER_MCP_SAFE_MODE` 为 "0"，用完改回；**只有用户能改**——且注意 09 分册"通道真相"：这只对正式注册通道成立 |
| 离线重装 | 用 skill assets/blender-mcp-bundle/（先 `sha256sum -c SHA256SUMS.txt`） |

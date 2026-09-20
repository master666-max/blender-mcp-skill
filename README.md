# blender-mcp skill

AI 驱动的 Blender 实时操控技能包（Agent Skills 标准格式）：让编码代理（ZCode / Claude Code / Cursor / Codex / DSH 等）通过 MCP 直连真实运行的 Blender——建模、材质、几何节点、灯光相机、渲染出图、动画、场景审计、五大资产库（PolyHaven / Poly Pizza / Sketchfab / Hyper3D Rodin / Hunyuan3D）直连，内置 PRD 反问循环与「力大砖飞」执行契约。

## 仓库布局

```
SKILL.md                 入口：连接自检 / 七条铁律 / 任务路由表 / 恢复 SOP
INSTALL.md               三步安装（多客户端路径表 / 默认通道与回退通道 / DSH 专属节）
references/00~14         14 分册：需求澄清 → 场景/材质/灯光渲染/动画/GN → 资产库 →
                         网格体检/参数化/安全错误/无头 CI/部署安全/执行契约/建模工艺/视觉工作流
scripts/                 骨架模板 + 场景审计 / 三点布光 / 渲染校验
fragments/ nodes/        代码积木与节点组（复用阶梯）
assets/                  两套离线安装包（默认通道 brickfly-mcp fork / 回退上游，SHA256SUMS 校验）
evals/                   86 条指纹回归 runner + M13 反向探针随包自检（9/9）+ 条款集/台账集登记断言
docs/                    架构设计书、工单与调研档案
```

## 安装（30 秒版）

1. 把本仓库的 `blender-mcp/` 目录复制到你的客户端 skills 根（如 `~/.zcode/skills/`）；
2. Blender 侧装 addon：Preferences → Add-ons → Install from Disk →
   `assets/brickfly-mcp-bundle/brickfly_mcp.py`（先 `sha256sum -c SHA256SUMS.txt`）；
3. 客户端 MCP 配置指向 `brickfly-mcp`（离线 wheel 在 bundle 内；详见 INSTALL.md）。

完整步骤、多客户端注意、DSH 专属节、升级与回滚见 [INSTALL.md](blender-mcp/INSTALL.md)。

## 治理层（这个包怎么保证自己没说谎）

- **四查发布门**：86 条条款指纹回归 / 版本三处同步 / 五根部署逐字节一致 / 台账断言（④a 登记 + ④b 严格递增 + ④c 指名文件存在 + 条款集/台账集登记常数 + 恒真正则 lint）；
- **M13 反向探针随包自检**：`py evals/run-negative-probes.py` → 9/9（对指纹/围栏施加破坏，断言必须报警）；
- **台账**：F-01 ~ F-164 全部历史发现与整改状态（`evals/regression-checks.md`），63 轮审计/整改闭环。

## 版本

- `main` 分支 = 最新发行负载（与 Release 资产 zip 内容逐字节一致）；
- 当前发行：**v2.5.9**（见 Releases）。

## 许可

- 上游 MCP for Blender（bundle 内 addon/wheel）：MIT，作者 Siddharth Ahuja（见 `assets/brickfly-mcp-bundle/ATTRIBUTION.md`）；
- 本 skill 打包物：作者 misdeep，随包分发即用。

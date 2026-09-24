---
name: blender-mcp
description: >
  通过 Blender MCP 工具实时驱动 Blender：建模、修改器、材质、几何节点、灯光、相机、
  渲染出图、动画关键帧、场景审计、模型文件的格式转换与交付（导出/导入 glTF/GLB、FBX、
  OBJ、USD 到 Unity/Unreal 等引擎或 DCC 流程），以及在 Blender 内执行
  任意 bpy Python。每当用户提到 Blender、3D 场景/建模/渲染/材质/贴图/动画/关键帧/
  几何节点/布光/出图、bpy 脚本、PolyHaven/Sketchfab 资产、场景审计或面数检查时使用本
  skill——即使用户没有明说"Blender"（例如"把这个场景渲染一下"、"给模型上个金属材质"、
  "做个低多边形小岛"、"做个椅子"、"把这个导出成 glb"）。需求一句话说不清时（建模/
  场景/出图类），先走
  PRD 反问循环澄清再动手（references/00，每问带默认值不盘问）。需要本机运行着 Blender
  且已连接 blender-mcp 插件
  （mcp__blender__* 工具）。无头批处理场景参见
  references/10-headless-ci.md。
metadata:
  author: misdeep
  version: "2.9.3"
  verified_on: "Blender 5.2.1 LTS + brickfly-mcp 2.0.0 (skill fork, 31 tools) + addon v1.7 (protocol 7), Windows, 中文UI"
---

# Blender MCP 驱动手册

通过 `mcp__blender__*` 工具操控真实运行的 Blender。本手册所有【实测】标记的结论都在
Blender 5.2.1 LTS + 插件 v1.6 + Windows 中文 UI 上真机验证过；【文献】标记来自官方文档
与社区调研、未在本机复验。版本差异处均标注。

## 0. 连接自检（每次会话必做，按序执行）

1. `get_scene_info` —— 通了就拿到场景概况（注意：**只返回前 10 个物体**，物体多不代表列表全）。
   此工具**必填** `user_prompt`（遥测/轨迹用途）：传**用户原话逐字**，多步任务全程传同一个
   目标——裸调会报 `Field required`，那是参数问题不是连接故障，别走 §6。该要求**与自报
   版本号无关**（内附的 mcp-for-blender 2.0.0 即如此，V-01 修正；serverInfo 自报的
   "1.30.0" 是 mcp 依赖版本，非本体版本）。
2. `get_addon_status` — 看版本兼容 + **五大资产集成开关状态**（PolyHaven/PolyPizza/
   Sketchfab/Hyper3D/Hunyuan3D）。**五个全 False 是正常的**——默认关闭设计，不是故障；
   需要哪个在 Blender N 面板勾选即可，**改完立刻生效无需重启**（提示文案里的"Restart
   the connection"是错的）；**开关是 Scene 属性，换 .blend 或新开场景就回到全关，每次
   任务开头必须探一遍**。改完记得存 .blend，否则开关不落盘。
   **版本期望值（U-05 解耦围栏；v2.5.3 改三态判据表）**：默认通道=brickfly-mcp（本
   skill 自有 fork，行为对齐上游 2.0.0 + F-147 行为修正）；期望 `addon_version [1,7]`、
   `protocol_version 7`。按返回的**三态判据（F-148 表）**逐行对号——**勿用 `warning`
   是否非空作判据**（除 `up_to_date:true` 外所有态都带非空 warning，F-148 教训）：
   **核心判据：只有 `up_to_date:null`（source:error）才是握手瞬断——重试一次再判，
   勿判过期**；`up_to_date:false` 的两种形态都是确认过期，直接重装：

   | `up_to_date` | `source` | 含义 | 处置 |
   |---|---|---|---|
   | `true` | `native` | 正常 | 继续 |
   | `false` | `native` | 协议落后（确认过期） | 按提示重装 addon（INSTALL §2） |
   | `false` | `missing` | 旧 addon 无 get_addon_info（确认过期） | 同上重装 |
   | `null` | `error` | 握手瞬断/环境问题 | **重试一次**；仍失败走 §6 排障——**勿判过期** |

   表外异形：**字段缺失/协议非整数值** → 上游可能已变更，开场如实告知用户"上游行为
   可能已漂移，本包结论按 2.0.0 版本书写"，勿假称兼容；完全连不上（纯报错字符串、
   无 JSON）直接走 §6。
   **自检结果不得静默消费（v2.1.7）**：五库开/关状态须**报给用户**——随开档消息或档位
   选择项一并说明（如"集成库：全关（默认态）；本任务建议启用 PolyHaven（免密钥）"）；
   进入档位问答时，资产库需求按问题池（A/B/C 型已含）作为常规问项；用户要用的库未开启
   时，指引导勾选而非代勾。
3. **感知自检（U-04，多模态前提）**：固化视角截图一次并**实看**——确认视觉通道可用 +
   获得场景第一印象（所见要点随首次汇报告知用户）。**本 skill 的设计前提是模型具备原生
   多模态能力，视觉通道默认开启**；通道不可用 = 环境降级：开场即告知用户"质量保障降级"、
   后续宣告行标 △、高视觉依赖工序与用户协商（权威定义：14 分册 §1/§6）。
4. `get_scene_info` 报错/超时 → 走 §6 恢复 SOP，**不要盲目重试**。
5. **开工前扫经验区（U-09，每次任务必做）**：跑 `py -X utf8 scripts/exp_hint.py <任务关键词>`
   （**在 skill 包根执行**；多个关键词空格分隔；无参数=列全部条目）——**命中条目先读其"规避法"再动手**；
   没有命中就照常开工（工具会照实说"无命中"，不虚构相关）。全量索引与晋升去向见
   `experience/INDEX.md`；教训回填与读取纪律见 [12 分册 §7](references/12-brickfly-protocol.md)。

## 0.5 需求澄清（PRD 反问循环——模糊建模任务的入口）

一句话建模/场景/渲染任务先分档（判据与分型问题池见 references/00-prd-intake.md）：
- **直通档不问**：查询/体检、单步修改、规格已足（有参考图/明确数值/明确风格）——
  AI 声明"按直通档直接执行"，用户随时可说"多问我几轮"升级；
- **非直通任务的第一交互 = 档位选择项**：先亮四档让用户选（每项一句话说明，AI 推荐档
  附理由），用户选档后进入对应流程——**档位是用户的选项，不是 AI 暗自决定**；
- **快速档**（默认推荐）：1 轮 ≤4 问（每问带推荐默认值，可回"按默认"整体跳过）→ PRD 卡片
  → 用户确认 → 骨架参数区实例化（12 分册 §6 映射表）→ 执行；
- **完整档**：2~3 轮（硬上限 3），后续轮只问矛盾与新依赖；
- **无限循环挡**：轮次无上限、退出权在用户；收敛按**五域清单+部件双覆盖**（细则见 references/00）；
  每轮 ≤4 问、深挖一层不算重问，卡片草稿逐轮演进展示，说"开工"立即冻结进入执行。
提问前先 get_scene_info 扫场景（已能推断的字段不问）；卡片确认即方案批准硬闸——
**确认后先输出开工提示（00 分册「开工提示」：问答结束 + 静默执行预告 + 中断权）再进执行环**。

**档位 = 交互强度 × 出品契约**（细则见 references/00「执行契约与质量门」）：选定档后，
执行侧绑死**必读册 + 过程门 + 出品门**——**走建模管线的任务（快速/完整/无限档的建模与
场景搭建）进入执行环前必读 13 分册**（快速档 §1~§2；完整档/无限挡全文+12 分册），
不许跳过工艺层直接堆代码；直通档单步修改按路由表即可。交付时最后一条消息必须含
**验收宣告行**（G 门 + R 门逐项打勾，不适用项标 N/A、禁止静默省略），其中渲染回读/
R2 实测/R3 隔离对账/R4 跳过留痕四项底线**永不静默省略**（允许 N/A，但 N/A 须附理由、
不得省略整行）；门可经用户明示降档省略（R4 留痕），但判据标准不可降格、
G1 铁门禁不可省略，静默跳过 = 任务未完成。

## 1. 七条铁律（每条都踩过真实的坑）

1. **30 秒硬超时**：MCP 工具约 30s 必超时返回（桥 socket 上限 180s，但客户端 30s 就放弃）。
   单次 `execute_blender_code` 的工作量控制在 **~20 秒**以内；超时后代码**可能已在 Blender
   里执行过**——重试前必须先查状态，否则重复执行。计时只能由 MCP **客户端侧**做
   （白名单禁 `import time`，脚本无法自测耗时），把每次调用的墙钟耗时记下来。
2. **安全模式（BLENDER_MCP_SAFE_MODE，实测开启）**：代码经 AST 白名单校验。
   - 只准 import：`bpy, bmesh, mathutils` + 标准库 27 个（math/json/random/re/itertools/
     collections/…）。**不准**：`sys/os/time/open/eval/exec/numpy/bpy_extras`。
   - 不准：lambda、class 定义、装饰器、驱动器、`bpy.app.handlers/timers`、类注册、
     `wm.append/link`、`dir()`、任何 dunder（`type(x).__name__`）、把方法赋给短变量再调用
     （`L = tree.links.new` 违规）、**动态 `setattr`/`getattr`（属性名必须是字面量）**、
     裸 `next()`（见铁律 5）。
   - 放行：渲染、保存/打开 .blend、**全部导入导出算子**、动画/物理 bake。
   - 拒绝是**秒回**且带行号的，改写重试即可，不伤队列。注意：Safe Mode 只拦**本通道**——
     其他进程可自带 SAFE_MODE=0 另起连接（09 分册 §4B 通道真相）。
3. **无事务回滚**：脚本中途报错，前面的语句已生效。每个脚本**开头幂等清理**本脚本会建的
   名字（get-or-create / 先删后建），失败重跑不留残骸。
4. **输出只走 `print(json.dumps(res))`**：print 内容会回传在 result 里。用默认 `ensure_ascii`
   （ASCII 转义），别传中文裸字符给 Windows 控制台编码。
5. **禁裸 `next()`**：`StopIteration` 的字符串是**空串**，MCP 会回传"空错误信息"，极难排查。
   要么 `next(iterable, default)`，要么先 `get()`/循环查找。
6. **导出必回读**：glTF/OBJ/USD 导出后必须重新导入（或 load 图片）验证；导出器会静默省略
   几何（GN 实例不 Realize 就进不了 glTF）。
7. **批量命名单一前缀 + 身份差集清理 + 快照先行**（爱弥斯 10 万面实战教训 BMCP-ERR-001）：
   生成器统一加前缀、report 回传**实际物体名**；清理外部导入物只用 before/after 身份差集
   ——**任何名字模式匹配都可能有同名碰撞**（实战误删自建 353 物体）；破坏性批量操作前先
   `save_as_mainfile(copy=True)` 落快照；对账用名单 diff 不用计数。（03/06/08 分册、12 分册 §7）

## 2. 中文 UI 大坑（本机默认状态）

新建 datablock 的**名字会被本地化**：新建材质的节点叫 `原理化 BSDF`/`材质输出`，
`nodes.get("Principled BSDF")` 返回 None。查找节点**永远用**：
- `node.type`（如 `'BSDF_PRINCIPLED'`、`'BACKGROUND'`）——注意这**不是** bl_idname；
- 或 `node.bl_idname`（如 `'ShaderNodeBsdfPrincipled'`）——注意这**不是** node.type。
自己建的节点随手 `node.name = "BSDF"` 固定英文名，后续按名取。

## 3. 任务路由表（按用户意图读对应分册）

| 用户想要 | 先读 | 关键事实速记 |
|---|---|---|
| **任何实作任务（开工前，先于本表其余行）** | `py -X utf8 scripts/exp_hint.py <任务关键词>`（在包根执行）→ 命中条目先读（全量索引 `experience/INDEX.md`） | 实战教训先读再做（U-09）；回填/晋升规则见 12 分册 §7 |
| 建物体/集合/变换/修改器 | [01-scene-objects.md](references/01-scene-objects.md) | ops 建物落活动集合；data API 免上下文；布尔用 `FLOAT` 求解器 |
| 材质/贴图/程序化材质 | [02-materials.md](references/02-materials.md) | 5.2 Principled = 32 输入（含 `Weight`/`Thin Wall`）；Mix 节点 RGBA 用 inputs[6]/[7] |
| 灯光/相机/构图/渲染出图 | [03-light-camera-render.md](references/03-light-camera-render.md) | 三点光 Area 150/40/100W；50mm+f/2.8 DOF+TRACK_TO；EEVEE 引擎 ID 5.x 是 `BLENDER_EEVEE`；渲染隔离见 §6 |
| 动画/关键帧/物理模拟 | [04-animation-physics.md](references/04-animation-physics.md) | `action.fcurves` 5.0 已删，走 channelbag；刚体先设帧范围再 bake |
| 几何节点 | [05-geometry-nodes.md](references/05-geometry-nodes.md) | 接口用 `tree.interface.new_socket`；5.2 输入写法 `mod.properties.inputs[ident] = 值` |
| 导入导出/外部资产 | [06-io-assets.md](references/06-io-assets.md) | glTF 是 `import_scene.gltf`/`export_scene.gltf`（没有 wm.gltf2_*！）；PolyHaven 全 CC0 免密钥 |
| 网格体检/面数/UV/烘焙 | [07-mesh-audit.md](references/07-mesh-audit.md) | `is_manifold` 只在 bmesh 上；`validate()` 返回 True=改过数据 |
| 参数化批量生成 | [08-parametric-generators.md](references/08-parametric-generators.md) | 单一前缀+幂等重置+参数钳制+固定种子+快照先行（§5） |
| 报错看不懂/连接卡死/安全模式 | [09-safety-errors.md](references/09-safety-errors.md) | 三形态+isError 陷阱对照表 + 卡死恢复 SOP |
| 无头批处理/CI/不走 GUI | [10-headless-ci.md](references/10-headless-ci.md) | `--factory-startup --python-exit-code 1`；bpy wheel 5.2 配 Python 3.13 |
| 需求不清/一句话任务先规格化 | [00-prd-intake.md](references/00-prd-intake.md) | 四档反问 + PRD 卡片 + 防盘问规则 |
| 部署安装/威胁模型/离线重装 | [11-deployment-security.md](references/11-deployment-security.md) | 五层防御；离线包在 assets/blender-mcp-bundle/ |
| 系统化建模/多阶段流水线 | [12-brickfly-protocol.md](references/12-brickfly-protocol.md) | 五段式骨架/四阶段隔离（单向依赖）/三级反馈/复用阶梯 |
| 建模顺序/工艺流程/精细模型怎么做 | [13-modeling-craft.md](references/13-modeling-craft.md) | **一切建模执行必读**（见 §0.5 出品契约）；七阶段管线（blockout→…→细节，G0~G4 质量门）+ 三级分层 + 停手判据 |
| 视觉工作流/多模态感知/场景盘点/成品展示 | [14-vision-workflow.md](references/14-vision-workflow.md) | **多模态深度融合权威册**：感知自检/开场识别（场景盘点+参考规格提取）/过程实时闭环/成品展示义务/知识库视觉检索/降级定位 |

## 4. 标准工作循环（每轮都走）

```
读（get_scene_info / get_object_info）
→ 改（execute_blender_code，≤20s 工作量，开头幂等清理，结尾 print(json)）
→ 看（固化截图/渲染出图 → 实看 → 不满意则定位问题再改——"看"是每轮修正的输入，
   不是交付前的单次验收；修正指令必须引用所见）
→ 汇报（列出动了哪些对象/参数；渲染**内嵌展示**并附视觉描述）
```

- **视觉核验（U-03，多模态模型必做）**：渲染/截图落盘后，用文件读取工具（名称随客户端：
  ZCode/Claude Code 为 Read，DSH 为 read_image）
  **实际打开 PNG 查看内容**再做质量判断——`bpy.data.images.load` 回读只证明文件存在；
  **禁止在没看过像素的情况下宣称"效果合格"**（预设模型不看图=瞎）。视觉通道不可达时
  按 00 分册 R1 降级条款处理（标 △ 并注明原因，不得假称合格）。
- **视觉全流程编排（U-04）**：开场识别（场景视觉盘点+参考规格提取+意图确认闭环）、
  过程实时闭环、成品展示义务、知识库视觉检索——权威定义见
  [14-vision-workflow.md](references/14-vision-workflow.md)，每轮循环的"看"是其过程段。

- **视口截图 ≠ 渲染图**：`get_viewport_screenshot` 截用户当前视口视角（会跟着用户的视图走）；
  要确定性的图就设 `scene.camera` 后 `bpy.ops.render.render(write_still=True)`。
- **渲染文件验证**：安全模式禁 `open()`，用 `bpy.data.images.load(path)` 回读成功即证明文件存在。
- **别保存用户的文件**：除非用户明确要求，绝不 `save_mainfile`。测试物体放隔离集合。

## 5. 隔离与清理（对用户场景零污染）

- 所有试验物体建进 `MCP_SKILL_TEST` 集合并设为活动集合；命名**分层** `TUT_<阶段>_<语义>`
  （几何 `TUT_GEO_*`、渲染装置 `TUT_RIG_*`——**装置别混进几何前缀**，否则几何阶段重跑
  会把灯光相机一起删掉）；`reset_prefix` 传**最具体**的那个前缀。
- 收尾时：删除该集合内 `TUT_*` 物体 → 删空集合 → 确认 `scene.world`/`scene.camera` 已还原为
  用户原值（**隔离窗口内禁 purge**——BMCP-ERR-005，见 03 分册 §6.3；骨架备有
  `assert_safe_to_purge()` 机器守卫）→
  `bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)` →
  再 `get_scene_info` 核对物体数回到初始值。
- 清理外部导入物只用**身份差集**（导入前名单 → 差集 → 逐个删），禁模式匹配；破坏性批量
  操作前先 `save_as_mainfile(copy=True)` 快照（爱弥斯事故教训，08 分册 §5、12 分册 §7）。
- 用户场景里的既有物体（哪怕看起来像垃圾）**一律不碰**。

## 6. 连接卡死恢复 SOP（实测有效）

症状：连 `print("alive")` 都 30s 超时，但 Blender 窗口本身活着。
0. 先查僵尸：`netstat -ano | findstr 9876` 应只见一条 `127.0.0.1:9876 LISTENING`；
   多条 = 僵尸 blender-mcp.exe，清理多余进程（09 分册 §4A）后再判断。
1. 别再重试 MCP 调用（队列堵死，重试无用）。
2. 最稳恢复：**重启 Blender**（若用户文件有未保存修改，先让用户保存；磁盘文件永远别替用户动）。
   重启后插件 `auto_start_server`（默认 True）自动起服，桥在下一条命令时自动重连——
   直接 `get_scene_info` 验证即可。
3. 不方便重启时的界面恢复：视口按 `N` → 侧栏标签（默认通道 **"Brickfly MCP for
   Blender"**；回退上游通道为 "MCP for Blender"）→ 断开/重连。
   （该插件**没有**注册进 F3 运算符搜索的启停算子，别浪费时间搜。）
4. 预防：单次脚本 ≤20s 工作量；布尔慎用 `EXACT` 求解器（优先 `FLOAT`）；禁写死循环。

## 7. 资产集成（五大库）速记

| 库 | 密钥 | 模式 |
|---|---|---|
| PolyHaven | 免密钥，全 CC0 | search → download(asset_id, asset_type, resolution) → set_texture |
| PolyPizza | poly.pizza/settings/api 免费 | **必须** `normalize_size=True` + 米制 `target_size`（Google Poly 遗产尺度混乱） |
| Sketchfab | sketchfab.com 免费档 API token | search → preview → download |
| Hyper3D Rodin | hyper3d.ai（面板有免费试用键按钮） | 文生 3D / 图生 3D → poll → import |
| Hunyuan3D | 本地服务或腾讯云 | 同上三步 |

集成在 Blender 侧栏面板勾选开启，**改动即时生效、无需重连**；工具由 server 静态全量
注册（开关不影响注册数），禁用态直调其检索工具会得到 `Unknown command type`（形似链路
故障，先看五库开关位再排障），引导开启的提示文本只在 get_*_status 上返回。生成式三件套
（Rodin/Hunyuan）只用来做"库里没有的单体道具"，不要生成
整个场景。详细参数与坑见 references/06-io-assets.md；部署安装/威胁模型/五层防御/维护速查
见 references/11-deployment-security.md；离线安装包在 assets/blender-mcp-bundle/
（装前 `sha256sum -c SHA256SUMS.txt`，作者与许可见 ATTRIBUTION.md）。

## 8. 端到端验收样例（新会话可先跑这个热身）

⚠️ 下面是**路线图不是完整脚本**——集合创建的 API 写法在 01 分册，灯位/色温/DOF/
`media_type` 细节在 03 分册（独立 agent 只抄这 5 行，RUN1 即崩在"设活动集合"）。
照路线走、细节按路由表读册：

1. 建 `MCP_SKILL_TEST` 集合并设为活动集合 + 立方体（scale 后 `transform_apply`）；
2. 挂 Principled 材质（按 `node.type` 找，设 Base Color/Metallic/Roughness）；
3. 三点光 + 相机（TRACK_TO 空物体 + f/2.8 DOF）+ `scene.camera` 赋值；
4. EEVEE 640×360、`taa_render_samples=16`、`render(write_still=True)` 到 %TEMP%；
5. `bpy.data.images.load` 回读验证（先取 size 后 remove）→ 向用户报路径。
全套在 30s 超时内完成（分 4~5 次调用跑）。

## 9. 已实测可用的最小代码骨架

```python
import bpy, json
res = {}
# ...幂等清理 + 操作 + 收集 res...
print(json.dumps(res))
```

场景自检（只读，随时可跑）：

```python
import bpy, json
print(json.dumps({
    "blender": ".".join(str(v) for v in bpy.app.version),
    "engine": bpy.context.scene.render.engine,
    "objects": len(bpy.data.objects),
    "active_collection": bpy.context.view_layer.active_layer_collection.name,
    "camera": bpy.context.scene.camera.name if bpy.context.scene.camera else None,
}))
```

## 10. 建模任务协议（力大砖飞，详见 references/12-brickfly-protocol.md）

- 写场景数据的代码一律五段式骨架（参数区→幂等清理→helper→建模→report），
  模板 `scripts/brickfly_skeleton.py`；report JSON 是场景唯一可信投影，禁止凭记忆描述场景；
- 多阶段任务按 几何→材质→构图→灯光 隔离推进，阶段 checkpoint 用 EEVEE 快渲判据；
- 看图三级：固化视角截图（每轮）/ EEVEE 快渲（checkpoint）/ Cycles 精渲（验收，本机先冒烟）；
- 复用阶梯：nodes/ 节点组 → fragments/ 积木 → 记忆指针（先验证存在）→ 从基元写起。

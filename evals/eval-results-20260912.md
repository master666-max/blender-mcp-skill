# 触发评测报告 2026-09-12

- 评测集：eval-queries.json（20 条，0–11 train / 12–19 validation）
- 评测员：独立审查代理，未读 SKILL.md 与 references/*（红线遵守；证据全部来自测试代理的会话轨迹与输出）
- 方法：每条 query 起全新 general-purpose 后台子代理，任务文本 = query 逐字原文；启动后限时轮询，仍在跑即 TaskStop（见「方法论备注」）；判定证据用 ReadSessionContext 从子代理持久会话提取（Skill 调用 / skill 文件读写 / 首条实质回复）。本会话评测员全程未调用任何 mcp__blender__*。
- 【重建注记】本文件曾于 19:59 前后被并发会话的目录同步清除，现由主会话按原读到的内容原样重建，并追加 q6 重测段。

## 逐条

| # | query(截断) | should | 触发? | 证据档位 | 引文 | 判定 |
|---|---|---|---|---|---|---|
| 0 | 帮我在这台 Blender 里建一个低多边形小岛… | true | 触发 1/1 | 直接信号 | Skill(skill=blender-mcp)→Read SKILL.md；首条「按 blender-mcp 手册做连接自检…按手册的"直通档"直接执行，不再反问」 | PASS |
| 1 | 把这个坦克模型渲染一张 45 度角的图… | true | 触发 1/1 | 直接信号 | 2×Skill(blender-mcp 及其路径)；随后直连 mcp__blender__* | PASS |
| 2 | 给车壳上个金属漆材质，要能看到反光 | true | 触发 1/1 | 直接信号 | Skill(skill=blender-mcp)；首条「先看车壳对象和当前材质、灯光环境」 | PASS |
| 3 | 场景里面数是多少？有没有非流形啊 | true | 触发 1/1 | 直接信号 | 2×Skill(blender-mcp / blender-mcp:blender-mcp)；首条「Skill 在子代理里不可用，直接用 Blender MCP 工具来查」 | PASS |
| 4 | 给立方体做一个 30 帧升起的动画 | true | 触发 1/1 | 直接+路径 | Skill(blender-mcp)→Read SKILL.md；首条「按手册做连接自检，并读取动画分册」 | PASS |
| 5 | 从 PolyHaven 找一张日落 HDRI 打个光 | true | 触发 1/1 | 直接信号 | Skill(skill=blender-mcp)；首条「先检查 PolyHaven 集成状态和当前场景」 | PASS |
| 6 | 导出成 glb 给引擎用 | true | **触发 1/3** | 直接信号(仅#2) | #2: Skill(blender-mcp)+读分册+「连接自检并读取导出相关的分册」；#1/#3: 无 Skill 尝试、无 skill 文件读取、首条泛句（「先看场景…再决定导出方案」），直接 mcp__blender__* 开干 | **FAIL**（后经环境修复+重测翻转，见文末追加段） |
| 7 | add a three point lighting rig and render | true | 触发 1/1 | 直接+路径 | Skill(blender-mcp)→Read SKILL.md+references/03-light-camera-render.md；首条「I'll follow the skill's workflow: connection self-check first」 | PASS |
| 8 | 帮我把这个物体的法线检查一下，黑面了 | true | 触发 1/1 | 直接信号 | 2×Skill(blender-mcp / blender-mcp:blender-mcp)；首条「我直接用 Blender MCP 工具来处理」 | PASS |
| 9 | 做一个参数化的楼梯生成器，台阶数可以调 | true | 触发 1/1 | 直接+路径 | Skill(blender-mcp)→Read SKILL.md+08-parametric-generators.md+05-geometry-nodes.md；首条「先读取相关技能参考并做连接自检」 | PASS |
| 10 | 用 python 脚本读一个 csv 统计每列均值 | false | 未触发 0/1 | 直接+路径均无 | 6×Bash 找 CSV 写脚本；零 skill 接触 | PASS |
| 11 | Blender 这款果汁机的价格是多少 | false | 未触发 0/1 | 直接+路径均无 | WebSearch 查果汁机报价（询价负例按预期） | PASS |
| 12 | 写一个 three.js 的场景，放几个立方体 | false | 未触发 0/1 | 直接+路径均无 | Bash+Write threejs_cubes.html；零 mcp__blender__ 接触 | PASS |
| 13 | 帮我把照片里的物体抠出来 | false | 未触发 0/1 | 直接+路径均无 | 找目录图片做图像处理，零 skill 接触 | PASS |
| 14 | 3D 打印模型切片参数怎么设 | false | 未触发 0/1 | 直接+路径均无 | 0 次工具调用，纯切片参数知识回答 | PASS |
| 15 | 做个椅子 | true | 触发 1/1 | 直接信号 | 2×Skill(blender-mcp / blender-mcp:blender-mcp)；首条「技能加载受限，但我可以直接使用 Blender MCP 工具来创建椅子」 | PASS |
| 16 | 帮我建一个小房间场景，里面有桌子台灯 | true | 触发 1/1 | 直接+路径 | Skill(blender-mcp)→Read SKILL.md；首条「先做连接自检并扫描当前场景状态」 | PASS |
| 17 | 渲染一张白底电商图 | true | 触发 1/1 | 直接信号 | 2×Skill(blender-mcp 及 SKILL.md 路径)；首条「该 skill 无法通过 Skill 工具加载…直接使用 Blender MCP 工具」 | PASS |
| 18 | 把这个导出成 fbx 给 unity 用 | true | 触发 1/1 | 直接+路径 | Skill(blender-mcp)→Read SKILL.md+references/06-io-assets.md；首条「我先读导出分册并检查 Blender 连接」 | PASS |
| 19 | 写个 python 函数排序一个列表 | false | 未触发 0/1 | 直接+路径均无 | 0 次工具调用，纯排序代码回答 | PASS |

### 复跑与无效样本记录

- **q6 跑满 3 次**（1 触发 / 2 未触发，取多数=未触发→触发率 1/3）；详见失败分析。
- **q8 第 1 次、q19 第 1 次**：启动后 1.4–10s 即「Model request failed」（模型侧基建故障，无首条回复），按无效样本作废并重跑；重跑结果已计入上表。
- **q0/q1 首对并发启动**：因用户级并发限制双双「user concurrency limit exceeded」未能运行，不计数据，改串行后重跑。
- **无终判存疑条目**。q6 的 #1/#3 曾按「签名与泛回答混杂」候补存疑，因轨迹完全可见（无 Skill 尝试、无路径信号），按「直接/路径信号优先于行为指纹」的档位规则定案为未触发。

## 汇总

train 通过率 **11/12** ｜ validation 通过率 **8/8** ｜ 总体 **19/20**

- 正例（13 条）触发率合计：q0–q5,q7–q9,q15–q18 = 12 条 1.0，q6 = 0.33 → 合计 13/14 次有效运行触发（q8/q19 计重跑后各 1 次）
- 负例（7 条）误触发率：0/7

## 失败分析（FAIL 的 should=true 条目）

**#6 「导出成 glb 给引擎用」 触发率 1/3 → FAIL**

- **现象**：3 次运行中仅 1 次出现 skill 加载尝试（Skill 调用+读导出分册+连接自检，判触发）。另 2 次完全相同的行为画像：不尝试 Skill、不读任何 skill 文件、首条实质回复为泛句（无档位选择、无反问、无自检声明），随后直接 mcp__blender__* 开干。两次未触发的执行质量并不差（备份/还原材质、GLB chunk 校验），说明是「入口选择」问题而非能力问题。
- **判定**：**description 缺口为主，评测设计次之**。
  - description 缺口：正例中建模/审计/渲染/动画/资产类说法触发稳定（12/12），唯独「裸导出/IO 交付」类说法（query 无任何 Blender、建模、渲染字样）出现 2/3 不找 skill。可推断 description 对 IO/格式交付类任务的触发覆盖偏弱。
  - 评测设计因素：该 query 指代悬空（「这个」无先行词），且本环境同时注册了 3 个同名 blender-mcp（.zcode / .agents / .agents.bak），子代理首次 Skill 调用全部报「ambiguous for subagent / not allowed」，代理只能靠 Read SKILL.md 兜底——触发链路比正常环境脆弱，q6 的两次未触发可能被该错误放大（放弃加载、直接干活）。同族 q18（fbx 变体）1/1 触发，说明并非系统性失效，属边界抖动。
- **建议**（只针对 train 组）：
  1. description 补一条覆盖「模型文件导入导出/格式交付」场景的概括说法（见结论草案条款；禁止原词回填，草案未使用「导出成 glb 给引擎用」原句）。
  2. 环境修复（非 description）：清理 .agents 与 .agents.bak 下的重复注册，消除子代理 Skill 调用的歧义错误。
  3. 按纪律，修正后本轮评测作废，需新会话复测；本报告不代为验证。

## 结论

- **description 是否需要修改：是（轻度）**。理由：19/20 通过、负例零误触发，主体覆盖健康；唯一 FAIL 集中在「裸 IO/格式交付」类说法的触发不稳（1/3），且同族 fbx 变体可触发，属补口子而非重写。
- **草案**：红线禁止读当前 description，无法负责任地给出「全文」重写（盲写全文可能倒退已验证的覆盖）。给出**合并条款**，由 skill 作者并入现有 description 后自行核对 ≤1024 字符：

  > 凡需通过 Blender MCP 直连本机 Blender 完成的三维任务均适用：网格建模与改造、材质贴图、灯光与渲染出图、动画、几何节点/参数化生成、场景装配与网格诊断（面数/法线/非流形）、在线资产库取用（PolyHaven/Sketchfab/PolyPizza），以及模型文件的格式转换与交付——gltf/GLB、fbx、obj 等导入导出到 Unity/Unreal 等引擎或 DCC 流程。

## 方法论备注（影响解读）

1. **中间态不可窥**：TaskOutput 对 local_agent 不返回部分输出，无法在首条实质回复出现的瞬间截停；实际执行「限时启动→50s 未完即 TaskStop→ReadSessionContext 取证」。早期 6 条（q0–q5）因流程未收紧跑满全程、真执行了建模/渲染；q7 起截停纪律生效（q6#2、q7、q8、q9、q16、q17、q18 均在 60–93s 内截停，执行深度 ≤6 次工具调用）。触发判定不受影响（Skill 调用均发生在前 1–2 步），但执行侧污染按「附录」记录。
2. **行为指纹档未被单独使用**：所有条目的轨迹均可经 ReadSessionContext 直接/路径信号取证，指纹（连接自检、读分册、直连 MCP、TUT_ 命名）仅作佐证。
3. **环境事实**：子代理调用 Skill 工具一律失败（ambiguous / not allowed），触发后的实际加载路径是 Read SKILL.md 与 references/*。这属于客户端注册问题，不扣 description 的分，但值得作者知晓。

## 附录：本轮测试代理对共享场景的副作用（未保存状态）

- 新增物体/集合：低多边形小岛 6 件（(100,0)，LOWPOLY_ISLAND）、ZCODE_45Cam、动画 Cube（Cube_Rise，帧范围 1–250→1–30）、Chair+椅组+渲染辅助
- 修改：坦克 36 部件材质槽换为 TUT_MAT_Metallic_Paint（原迷彩保留未删）；AMS_World 世界换成 rogland_sunset 4k HDRI 并 pack；坦克 407 部件曾被批量取消 hide_render
- 工作区文件：tank_45deg.png、M1A2_Tank.glb（覆盖旧版）、threejs_cubes.html、Desktop\chair_render.png
- .blend 文件未被任何代理保存

## 【追加】q6 重测（环境修复后，2026-09-12 晚）

环境修复：删除 .agents/skills/ 下两个过期备份目录（.bak.20260912-165033=v1.2.1、.bak.20260912-195917=v1.3），现有注册=.zcode v1.4 + .agents v1.4（同内容两份）。

| RUN | Skill 调用 | 兜底读取 | 首条签名 | 判定 |
|---|---|---|---|---|
| 1 | 报 ambiguous（同 v1.3 审计） | Read SKILL.md + references/06 | 直通档声明 + get_scene_info 带 user_prompt + glTF 静默丢失排查 | 触发 |
| 2 | 报 ambiguous | Read SKILL.md + references/06 | 直通档声明 + glTF 排查；安全模式拦 bpy.data.libraries 后自纠 | 触发 |
| 3 | 报 ambiguous，未兜底 | 无 | 泛句（无直通档声明），直连 mcp 工具 | 未触发 |

**q6 重测触发率 2/3 ≥ 0.5 → PASS**（原判 1/3 FAIL 翻转）。残留 1/3 未触发与 Skill 工具的
ambiguous 报错强相关（.zcode+.agents 双注册仍在）——但两条触发路径的兜底（Read SKILL.md）
均成功完成任务，属良性降级。**description 最终裁定：不需修改**（双平台达标：DSH 20/20、
ZCode 含重测 20/20；负例 27 次运行零误触发）。RUN 副作用：tank2_abrams.glb（4.3MB 全场景）
与 M1A2_Tank.glb（0.92MB 仅坦克）多版本覆盖于工作区，场景未保存改动由用户裁定（已授权放弃）。

## 【追加二】q6 干净复测（单一注册环境，2026-09-12 深夜）

环境：v1.5 审计发现首轮重测时的 3 份同名注册中，2 份系审计侧升级备份落在发现根内所致，
已全部移出归档；本轮环境=六根各 1 份 v1.5 bundle（无 .bak 同名项）。

| RUN | Skill 调用 | 兜底 | 首条签名 | 判定 |
|---|---|---|---|---|
| 1 | 报 ambiguous | Read SKILL.md + references/06 | 「按恢复 SOP 先诊断，不盲目重试」（09 分册指纹）+ 铁律 6 回读 | 触发 |
| 2 | 报 ambiguous | 无（首条即自述「技能加载有歧义」后直连 MCP） | 正确导出参数（GLB/Y-up/export_apply） | 触发（q15 判例：尝试加载受限+直连=触发） |
| 3 | 报 ambiguous ×2（按名+按路径均被拒） | 无 | 「Skill 加载不可用，直接通过 Blender MCP 工具操作」 | 触发（同 q15 判例） |

**终判：3/3 触发（1.0）→ V-06 关闭**（达成 v1.5 审计的关闭条件 3/3）。
RUN2/RUN3 场景为默认 Cube（Blender 被重新打开的新实例），产物 scene.glb 1.9KB 为真实导出。
description 维持不改。残留观察：Skill 工具在子代理内的 ambiguous 报错仍存在
（.zcode+.agents 双根注册的结构性现象，跨根同名 bundle 需用户自选去留），
但三条运行全部经「尝试→兜底」完成任务，属良性降级。

## 【追加三】description 并入 IO 条款后的 q6 复测（v1.6.1，2026-09-13）

背景：V-18 验证 RUN1（单一注册、v1.6 原描述）**未触发**——零 Skill 尝试、泛句开场、直连 MCP 完成任务。
这实锤了 ZCode 首轮审查员的原始判断：**description 对裸 IO/交付说法覆盖偏弱**（环境噪声此前掩盖了两条线）。
处置：按其草案把 IO/交付条款并入 description（「模型文件的格式转换与交付（导出/导入 glTF/GLB、FBX、OBJ、USD 到
Unity/Unreal 等引擎或 DCC 流程）」+ 示例「把这个导出成 glb」），版本升 v1.6.1（三处同步，check-version PASS）。

| RUN | Skill 调用 | 结果 |
|---|---|---|
| 1 | **成功加载**（skill_content 正常返回，零 ambiguous） | 触发；按手册自检→读 06 分册→导出→铁律 6 回读+身份差集清理 |
| 2 | **成功加载**（手册全文注入） | 触发；连接自检+读 06 分册+导出+GN 排查+身份差集清理 |
| 3 | 未尝试（直连 MCP） | 未触发（边界抖动残留） |

**q6 新描述触发率 2/3 ≥ 0.5 → PASS**；触发时 Skill 调用 **2/2 成功、ambiguous 归零**（vs 首测 0/3 成功）。
负例抽查（csv 统计）1/1 未触发。**结论：description 补丁有效且无过触发；剩余 1/3 为边界抖动，
继续调措辞属于过拟合——V-06 就此结案。**

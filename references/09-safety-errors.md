# 09 安全模式 / 错误处理 / 卡死恢复

## 1. 错误回传三形态（全部实测）

| 形态 | 长相 | 含义 | 对策 |
|---|---|---|---|
| 安全模式拒绝 | `Rejected by safe mode - line N: <原因>` + 完整规则文本 | AST 白名单拦截，**秒回**，队列无伤 | 按行号改写重试 |
| 运行时异常 | `Error executing code: Communication error with Blender: Code execution error: <消息>` | 脚本真报错了（前面的语句已生效！） | 先查残骸再修 |
| **空错误** | `Code execution error: `（冒号后什么都没有） | 八成是裸 `next()` 的 StopIteration（str 为空串） | 用 `next(x, default)` / `.get()` / for 循环 |

**协议层陷阱【实测·DSH 审计】**：以上三形态在 MCP 协议层的 `isError` **恒为 false**——
Safe Mode 拒绝也装在正常 content 里返回。**判据只用 result 文本前缀**：
`Code executed successfully:`（成功）/ `Rejected by safe mode`（被拒）/ `Error executing code:`（异常）；
绝不要用 `isError` 判断成败（审计桥 15 条调用 10 条被拒全部显示"成功"）。

常见错误消息对照：
- `bpy_prop_collection[key]: key "X" not found` → 物体/材质名不存在（中文键名可正常往返）
- `Unknown command type: X` → **该命令/工具未注册**【实测·坦克建模更正】：资产集成未勾选
  时调其工具返回的是这个，**不是**引导开启的文案（06 分册 §5A 已更正）——先让用户启用集成
- `ReferenceError: StructRNA of type X has been removed` → **数据块 remove 之后还在访问其属性**
  （先取值后删除；按名单清理时先收集引用、删完不再回读——skill 未写时独立 agent 与审计者
  都踩过，立此存照）
- `'NoneType' object has no attribute ...` → 按英文名 `nodes.get()` 找本地化节点扑空（见 02 分册）
- `id properties not supported for this type` → GN 修改器旧式 `mod["Socket_N"]` 直写（5.2 已移除）
- `bpy_struct[key] = val: ...` → 同上
- `dunder attribute '__name__' is not accessible` → `type(x).__name__` 之类被安全模式封
- `'L' is not a known callable` → 方法赋短变量再调用被安全模式封
- `import of 'X' is not allowed` / `import from 'bpy_extras' is not allowed` → 白名单外模块

## 2. 安全模式白名单速查（实测汇总）

**整脚本闸门【实测·DSH 审计】**：AST 校验在执行**前**跑——只要有一处违禁，
**整个脚本零执行（含它前面合法的语句）**。这与铁律 3"报错前语句已生效"方向**相反**，
两者并列记忆：**被拒 = 全无生效；运行时报错 = 前面已生效**。恢复/探测类语句不要和
白名单外的调用写在同一个脚本里。

- **可 import**：`bpy, bmesh, mathutils` + `math, cmath, random, colorsys, json, itertools,
  functools, collections, statistics, string, re, enum, dataclasses, typing, decimal,
  fractions, textwrap, unicodedata, uuid, copy, heapq, bisect, array`
- **不可**：`sys, os, time, subprocess, socket, numpy, bpy_extras, bpy.utils`（注册类）,
  `bpy.app.handlers/timers/driver_namespace`, `bpy.data.libraries`, `bpy.data.texts`
- **不可**：`open/eval/exec/compile/dir/globals/vars/super/object/memoryview/getattr/setattr动态名`,
  lambda, class, 装饰器, global/nonlocal, 海象, match, import 别名, `from bpy import ops`。
  【实测·坦克建模】动态 `setattr(obj, computed_name, val)` **秒拒**
  （"attribute name must be a literal string"）——属性名一律写字面量。
- **禁注册**：Operator/Panel/PropertyGroup、`bpy.props`、驱动器（`driver_add`）、handlers、timers
- **放行**：`bpy.ops.render.render`、`save_mainfile/open_mainfile/recover_auto_save`、
  全部导入导出算子、`ptcache/rigidbody/nla/fluid` 的 bake、`.filepath` 赋值、`bpy.path`
- 语法规模上限【文献】：≤200KB、≤2 万 AST 节点、嵌套 ≤24 层
- 关闭方式：环境变量 `BLENDER_MCP_SAFE_MODE`——**只有用户能关**，AI 别劝着关，按规则写代码。

## 3. 免驱动的替代方案（安全模式封驱动器）

| 想做的事 | 替代 |
|---|---|
| 参数随帧变化 | `keyframe_insert`（物体属性或节点 socket 都行，见 02 分册 §7） |
| 循环动画 | F-Curve 的 CYCLES 修饰器 `fc.modifiers.new('CYCLES')` |
| 追踪目标 | TRACK_TO / COPY_LOCATION 约束（纯 RNA 赋值） |
| 逐帧逻辑 | 先 bake 再 `frame_set` 循环读取 |

## 4. 卡死恢复 SOP（SKILL.md §6 的完整版）

**症状分级**：
1. 单条调用超时，下一条正常 → 30s 客户端超时正常现象；**先查上一步是否已生效**。
2. 所有调用全部超时（连 `print("alive")` 都不行）+ **Blender 窗口本身活着** → 插件执行队列堵死。
3. Blender 窗口都卡死 → Blender 本体问题（重负载/模态框），让用户看窗口。

**队列堵死恢复（实测有效，按优先级）**：
1. **重启 Blender**：数据安全性判断——标题栏有 `*` 前缀=有未保存修改，先请用户保存；
   重启后插件 auto_start_server 自动起服，MCP 桥下一条命令自动重连，`get_scene_info` 验证。
2. **界面重启插件**：视口 `N` 面板 → "MCP for Blender" 标签 → 断开/重连。
   （没有注册 F3 可搜的启停算子，实测搜不到。）
3. **别做**：反复重试 MCP 调用（排队无用）；杀 uvx 桥进程（可能永久断连）；
   替用户决定保存/丢弃。

**窗口最小化注意**【实测教训】：Blender 窗口最小化时 timer 可能得不到调度，MCP 调用变慢/超时；
长任务前提醒用户保持窗口还原（不必前台）。

## 4A. 故障模式：僵尸 blender-mcp.exe 进程【实测·隔壁会话实战案例】

**症状**：莫名弹窗、连接行为诡异、命令队列时好时坏、"明明没连却又有响应"。

**排查**（确定性判定）：
```bash
netstat -ano | findstr 9876
```
- 健康 = **只见一条** `127.0.0.1:9876 LISTENING`；
- 多条 LISTENING = 存在僵尸 blender-mcp.exe 实例（早期会话残留、uvx 重复拉起等）；
- 出现 `0.0.0.0:9876` = addon 被改动过，立即停用排查（见 11 分册第 5 层）。

**处置**：任务管理器按映像名清点 `blender-mcp.exe`，保留正在服务的那条连接对应的进程
（按 netstat 的 PID 对应），结束其余；Blender 侧 Stop→Start MCP Server 重置。

**预防**：用完即 Stop / 关 Blender；多个会话共用一台 Blender 时先对齐"谁在连"
（官方明确单实例：docs/capabilities "Only one MCP server instance can connect at a time"）。

## 4B. Safe Mode 通道真相（重要修正）【实测】

**修正表述**："只有用户能关 Safe Mode" 仅对 **ZCode 正式注册的那条 MCP 通道**成立
（配置里 `BLENDER_MCP_SAFE_MODE=1` 只作用于该通道的 stdio 环境）。

**真相**：任何本地进程都能以 `BLENDER_MCP_SAFE_MODE=0` 自起一条独立 stdio 连接——
实测案例：隔壁建模会话的 `tank_preview_inproc.py` 为 `import gpu` 离屏渲染
（gpu 模块不在白名单），另起了 SAFE_MODE=0 子进程通道。

**高级模式纪律**（确需白名单外能力时，如 gpu 离屏预览）：
1. 只用独立子进程（python + mcp ClientSession 自建连接），绝不改正式通道配置；
2. 代码先审核再跑：只用必要模块，无文件/网络/子进程操作，用完即弃；
3. 绝不触碰用户文件与场景持久化；
4. **警示**：这条通道同样是任何本地攻击者的同等通道——它存在的事实正是第 4 层
   操作兜底（保存权在用户）不可省略的原因（11 分册）。

## 5. 大 payload / 长任务纪律

- 单脚本 ≤ ~20s 工作量（30s 超时留余量）；渲染/bake/大型布料**单独成调用**。

## 5A. 驱动侧纪律：别堵死 Blender 主线程（F-144 实录）

addon 的 TCP 服务收到命令后**交给主线程的 timer 队列执行**——用 `--python`
脚本驱动 Blender 做验证/自动化时，**主线程一旦进入 `while + time.sleep()` 轮询，
timer 永不触发，所有命令（含 get_addon_status）静默无响应**，表象与"工具卡死"完全
相同。正确姿态：脚本只做布置（启服/注册），随后**立即把主线程还给事件循环**——
延时动作用 `bpy.app.timers.register(回调, first_interval=N)` 挂到 timer 上
（回调里 `bpy.ops.wm.quit_blender()` 可安全自退）。【实测】U-05 端到端验证
两次假失败均由此起。
- 返回值别 dump 整个场景：`get_scene_info` 只回前 10 物体是有意的，自写的 print 也要克制
  （几百个键的 JSON 会撑爆回传）。
- 需要长时间跑的任务：告诉用户预期时长，让其在 Blender GUI 里手动点（如大流体 bake），
  或者拆成多段带中间落盘。

## 6. 对用户场景的保护红线

- 用户的既有物体：不删、不改名、不移；演示一律 `MCP_SKILL_TEST` 集合 + `TUT_` 前缀。
- 不 `save_mainfile`，除非用户明说；改了用户物体属性要逐条汇报。
- 清理自己的实验后 `orphans_purge` + `get_scene_info` 物体数对账。

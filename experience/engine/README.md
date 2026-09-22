# 演化引擎（evo-seat 微型内核）— 经验区的对接层

> **来源**：审计区设计并实现（`D:/zcode-workspace-audit/`），
> `evo_seat.py` **v0.2.1**（**framework_sha 判别力修复版**：横幅定位 + 长度断言 +
> 判别力测试；SPEC 对齐 / 版本纪律 / 老库拒读语义承前），vendored **逐字节未改**。
> sha256 = `096077ce061c185016398f8e0d94f92d5b588593db95ddda48cc12329af05ba6`
> （升级时替换此文件并更新本行哈希 + 指纹 #92；配套映射见下，桥接脚本 `exp_bridge.py`）。
> 上一版 = `403d79a4…`（v2.8.2 换装版本纪律版 v0.2.0；更早 `43f8db8f…` / `61a808be…`，
> 见 CHANGELOG）。
>
> **v2.8.3 换装（上游 v0.2.1，判别力修复）**：原 `framework_sha()` 用 `src.find("§1 core")`
> 取**首个命中**，落在文件头 docstring 的区段名清单上（只哈希 66 字节）——对框架码偏离
> 零判别力（本包 v2.8.2 轮实测发现并报出，审计区独立复现后修复）；现改为**横幅行正则
> 定位**（`^# ═+ §1 core` → `^# ═+ §7 cli`）+ **<5000B fail-closed 抛错**；内嵌
> `test_framework_sha_discriminates`（selftest 10 → 11 测）；审计区 **conformance §F
> 从「字段在位」升级为判别力测试**（破坏副本对跑，两侧同值即 FAIL——本包实测：真件
> 14/14 PASS、回退件 13/14 FAIL）。
> **新基线：`framework_sha = a98f559753d7cbe0`（框架段长 13,297 B，独立复算一致）**。
> 对账口径（采纳上游回执 §四）：**段哈希为主**（区分「框架升级」与「宿主段改动」）
> + **整文件 sha256 为投递校验**（本 README 首部登记值 + 指纹 #92）。
>
> **残留守卫洞（本包回执核对实测；已回报上游，待 v0.2.2）**：① 内嵌判别力测试为
> **本地复算**、不调用 `framework_sha()` 本体——把函数回退成旧实现后该测试仍 11 测
> 全过（隔离目录实测），**真守卫是 conformance §F**；② `selftest` 用目录发现
> （`pattern="evo_seat.py"`），**重命名副本会静默测到邻文件**（实测：污染目录里回退件
> 跑出「9 测 OK」，实为另一旧文件的测试）；③ `selftest` 失败时**退出码仍 0**
> （fail-closed 违背，脚本化判定须读输出文本）。三处修法各约一行，见研究仓
> `研究/回执核对-framework_sha修复_20260923.md`。
>
> **既有（v2.8.1 SPEC 对齐，保留）**：`SPEC = SPEC-内核接口与宿主契约-v1` 符合性声明 +
> **治理位边界**（验收/裁决/修宪**不入内核**——执行无权自宣验收，治理位永远外置）；
> `audit` 增 [符合]/[边界] 行；`verify`/`audit` 顺带输出 `framework_sha`。

## 它是什么

单文件微型内核：**治理框架 × 演化内核融合**（分区即边界：cli→gates/decide→rank/
lifecycle→store→core）。经验区（`experience/`）是它的**轻宿主**——按架构书条款
"blender-kb 类轻宿主：evo-seat 是它们的默认形态"。

六档审查精细度（`evo level <库> G3` 单调升档、降级留痕）：

| 档 | 装什么 |
|---|---|
| G0 观察位 | 账本（触发器物理 append-only）+ 检索 + 三态 |
| G1 标准位 | + 链重放验证 + 墓碑 + 开库即验（fail-closed） |
| G2 类型位 | + 条目构造校验 + 类型差异化衰减 |
| G3 门位 | + 质量门五道（可对任意 .py 自食） |
| G4 决策位 | + 决策留痕 + 金标挣得接口 + defer 监控 |
| G5 锚定位 | + 入库锚 + 出站扫描三态 + 周巡检 |

**建议默认档：G3**（经验区需要的治理全在位：账本/链验/构造校验/质量门），
需要决策留痕与锚时升 G4/G5。

## 用法（快速验证——新工具先拿自己跑一遍）

```bash
cd experience/engine
py -X utf8 evo_seat.py selftest                 # 内嵌测试（11 测）
py -X utf8 evo_seat.py init ../state/evo.db --level G3
py -X utf8 evo_seat.py verify ../state/evo.db
py -X utf8 evo_seat.py gate ../state/evo.db evo_seat.py   # 质量门自食
py -X utf8 exp_bridge.py import ../state/evo.db           # 把 EXP 条目灌入账本
```

> 账本文件（`experience/state/`）是**运行态**，不入发行 zip、不入 git。

## 字段映射表（EXP 条目 ↔ 引擎条目）

| EXP frontmatter | 引擎字段 | 映射规则 |
|---|---|---|
| `id`（EXP-NNN） | `entry_id` | 直接 |
| `claims` + 「现象与根因」「规避法」正文 | `content` | claims 逐条 + 正文拼接（检索主文本） |
| （由 content 分词派生） | `keywords` | `exp_bridge` 自动分词（bigram 口径与引擎 §3 同族） |
| `status` | `importance` | draft=3 / pending=3 / verified=6 / **promoted=8** / rejected=1 |
| （恒定） | `type` | **procedural**——教训类知识**零衰减**（引擎 DECAY[procedural]=0），语义正当 |
| `date` | `created_at` | ISO 直用 |
| `status == promoted` | `state` | `longterm`（引擎 promotion 事件）；其余 `intermediate` |
| `evidence` / `promotion` | 随 payload 一并入账 | 只增不改，原位留档 |

## 双路径（经验区 ↔ 引擎）

1. **入账（本仓已接）**：`exp_bridge.py import` —— 读 `experience/EXP-*.md` → 灌入
   引擎 events 账本（actor=`engine:bridge`）。账本只增不改，投影按 entry_id 取
   **最新** → 重复 import 是幂等投影（每次追加，后写覆盖投影）。
2. **提议（预留）**：引擎侧决策/聚类产出 → 以 `status: draft` + `source: engine:<id>`
   的 **新 EXP 条目**回流（写入权：只允许 draft；**晋升进分册必须过人 + 发版门**——
   免疫通道不因引擎嵌入而放宽）。

## 边界（为什么桥不过引擎质量门）

引擎的 import 白名单（G3 门）服务于**引擎自身的单文件自包含契约**；`exp_bridge.py`
是**宿主侧适配器**，按设计依赖 `evo_seat`——因此对桥跑 `gate` 会报
`evo_seat 不在白名单`，这是契约的正常边界，不是缺陷。引擎自身的自食门以
`gate evo_seat.py` 为准（已通过）；桥的正确性由功能冒烟（import→verify→retrieve）保证。

## 不变量（嵌入不放宽）

触发器物理 append-only · 出处三件套 · fail-closed · 墓碑不删 · 决策留痕 ·
构造时校验 · 内嵌测试——**小的是体积，不是纪律**（逐字承自架构书 §四）。

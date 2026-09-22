# 演化引擎（evo-seat 微型内核）— 经验区的对接层

> **来源**：审计区设计并实现（`D:/zcode-workspace-audit/`），
> `evo_seat.py` **v0.2.0**（**版本纪律版**：SPEC 对齐 + 哈希算法声明 + 老库拒读语义），
> vendored **逐字节未改**。
> sha256 = `403d79a4e2fc9233451d78acec1a539534ccd524cd71d1e609cad5e27cea0fbb`
> （升级时替换此文件并更新本行哈希 + 指纹 #92；配套映射见下，桥接脚本 `exp_bridge.py`）。
> 上一版 = `43f8db8f…`（v2.8.1 换装 SPEC 对齐版；首发 `61a808be…`，见 CHANGELOG）。
>
> **v2.8.2 换装（上游 v0.2.0，版本纪律版）**：`VERSION`/`HASH_ALGO` 常量与**变更记录**
> 入档（0.1.0=v1 哈希只覆盖 payload；0.2.0=**v2 哈希把 actor/kind 并入输入**——老算法库
> open **拒绝并要求按事件流重建**，破坏性变更升版本+声明算法）；SCHEMA 增 `meta.hash_algo`
> 键；缺键的在途 v2 库按「首行试算」自动识别补键放行（不误杀不静默）；新增内嵌断言
> `test_version_and_algo_declared`（selftest 9 → 10 测）。本包账本为 v2 算法，
> **换装后旧账本向下兼容复验过**（28 事件链完整）。
>
> **既有（v2.8.1 SPEC 对齐，保留）**：`SPEC = SPEC-内核接口与宿主契约-v1` 符合性声明 +
> **治理位边界**（验收/裁决/修宪**不入内核**——执行无权自宣验收，治理位永远外置）；
> `audit` 增 [符合]/[边界] 行；`verify`/`audit` 顺带输出 `framework_sha`
> （实跑值 `89adf037485b4148`）。
>
> **上游已知边界（本包实测；不在本包修——vendor 逐字节原则）**：`framework_sha()` 的
> 切片是 `src.find("§1 core")` 的**首个命中**——落在文件头 docstring 的区段名清单上
> （实测 66 字节），**框架代码改动不改变该值**（改动-对照实测：破坏 §2 store 内代码后
> 仍输出 `89adf037485b4148`）。即该字段**在位但判别力近零**，SPEC §F 的 T-E 副本对账
> 目前请改用**整文件 sha256**（＝本 README 首部登记值 + 指纹 #92，锚定逐字节）。
> 已报出，待上游按修宪程序处置。

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
py -X utf8 evo_seat.py selftest                 # 内嵌测试（10 测）
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

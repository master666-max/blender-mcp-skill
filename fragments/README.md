# fragments/ — 代码积木库（L3b，M9 复用阶梯第 2 级）

**用法与约束**（先读）：
- 积木是**粘贴进 execute_blender_code 的代码块**，不是可 import 的模块——安全模式禁
  `open()` 与非白名单 import，文件加载这条路不存在；
- 每块积木一个 `.py` 文件，头部元数据六行（用途/依赖/实测状态/引用教训/参数/来源）；
- 积木内部自带 PREFIX 纪律与幂等清理；调用方负责把积木输出并入自己的 report JSON；
- 新积木入库前必须实跑验证并把头部"实测状态"写实际值（未实测的标 UNTESTED，不许标 PASS）；
- **视觉预览约定（U-04，14 分册 §5）**：新增积木**必须附渲染预览图**（同目录
  `preview_<名>.png`，展示积木产出的视觉结果）；存量积木在下一次触碰时补；
  使用积木前实看预览判断视觉适用性——复用阶梯每一级都要"看得到长什么样"；
- 复用阶梯（M9）：nodes/ 节点组 → 本目录积木 → 记忆组件指针 → 从基元写起。

## 现有积木

| 文件 | 用途 | 实测状态 |
|---|---|---|
| `three_point_rig.py` | 三点布光 + 相机（TRACK_TO+DOF）rig 函数 | PASS（skill v1.0 E2E） |
| `mesh_audit.py` | 几何体检 + 三角面统计（bmesh 路径） | PASS（skill v1.0 E2E） |
| `bake_essentials.py` | 高模→低模 selected-to-active 烘焙要点（法线/AO/漫透色+落盘回读；ERR-014 心智模型内建） | PASS（v2.2.0 入库：无头 factory-startup 幂等双跑，四通道两轮全 ok） |
| `lod_chain.py` | LOD 链（DECIMATE 比例链+apply+旧网格回收）+ GLB 导出回读 | PASS（v2.2.0 入库：无头幂等双跑，两轮面数一致、对象零漂移） |

## 未收录说明

- **图集贴花**（tank s15/s20 实测）：核心拼图逻辑依赖 numpy（`img.pixels.foreach_get`
  到 ndarray 再重排），**安全模式禁 numpy**——无法作为通道内积木。实战时以
  `BLENDER_MCP_SAFE_MODE=0` 独立子进程通道跑（09 分册 §4B），源码见
  工作区 `tank/scripts/s15_atlas.py`、`s20_decal_atlas.py`。

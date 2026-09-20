# nodes/ — 参数化节点组库（L3b，M9 复用阶梯第 1 级）

**形态约束（先读，这是安全模式决定的硬约束）**：
- 安全模式**禁** `wm.append/link` 与 `bpy.data.libraries`——模型**无法**从 .blend 文件
  加载节点组（05 分册 §6）。因此本目录以 **`.py` 重建脚本**为主体：代码即节点组的
  唯一事实来源，接口用 `tree.interface.new_socket`（4.0+ 唯一 API）；
- 用户手动通过 GUI 添加的重资产节点组不受此限——登记进记忆组件指针（M10）并写明
  "需用户 GUI 添加"，模型只调用不创建；
- 节点组脚本同样遵守 fragments/README 的元数据头部与实测纪律。

## 现有节点组

| 文件 | 组名 | 说明 | 实测状态 |
|---|---|---|---|
| `WD_wood.py` | `WD_wood_base` | 木纹基础组：Wave+Noise 扰动 → Mix(光/暗色) → Principled + Bump；接口 Scale/Color Light/Color Dark/Shader | PASS（WO-R2 P3 实测） |

（下一个建议：砖墙组 BR_brick，配方见 02 分册 §6；入库时同步登记记忆组件指针。）

## 入库检查单

1. 脚本能从空 `GeometryNodeTree`/`ShaderNodeTree` 完整重建（幂等：先删同名组）；
2. 接口 socket 全部 `interface.new_socket` 定义并给默认值；
3. 修改器输入写入用 `mod.properties.inputs[ident] = 值`（5.2 实机写法，05 分册 §2）；
4. 实跑验证 + 头部"实测状态"如实标注。

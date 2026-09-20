# 05 几何节点（Geometry Nodes）

## 1. 建树 + 挂修改器（【实测】5.2.1 全流程通过）

```python
import bpy

tree = bpy.data.node_groups.new("TUT_Scatter", 'GeometryNodeTree')
tree.is_modifier = True
# 4.0+ 唯一接口 API（旧 tree.inputs.new()/outputs.new() 已删除）
tree.interface.new_socket(name="Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
sock = tree.interface.new_socket(name="Count", in_out='INPUT', socket_type='NodeSocketInt')
sock.default_value = 30

n_in  = tree.nodes.new('NodeGroupInput');   n_in.location  = (-400, 0)
n_out = tree.nodes.new('NodeGroupOutput');  n_out.location = (400, 0)
dist  = tree.nodes.new('GeometryNodeDistributePointsOnFaces')
inst  = tree.nodes.new('GeometryNodeInstanceOnPoints')
cube  = tree.nodes.new('GeometryNodeMeshCube')
cube.inputs["Size"].default_value = (0.05, 0.05, 0.05)

tree.links.new(n_in.outputs["Geometry"],  dist.inputs["Mesh"])
tree.links.new(dist.outputs["Points"],    inst.inputs["Points"])
tree.links.new(cube.outputs["Mesh"],      inst.inputs["Instance"])
tree.links.new(inst.outputs["Instances"], n_out.inputs["Geometry"])
```
注意：`L = tree.links.new` 再 `L(...)` 会被**安全模式拒绝**（方法赋短变量再调用违规），
每条写全路径 `tree.links.new(...)`。

## 2. 设置修改器输入（5.2 实机唯一可用写法【实测】）

```python
mod = obj.modifiers.new("TUT_GN", 'NODES')
mod.node_group = tree

ident = next((i.identifier for i in tree.interface.items_tree
              if i.item_type == 'SOCKET' and i.in_out == 'INPUT' and i.name == "Count"),
             "Socket_2")   # identifier 形如 Socket_2；给 default 防裸 next()

mod.properties.inputs[ident] = 50            # ✅ 5.2.1 实测可用（经 properties 的 ID 属性组）
readback = mod.properties.inputs.get(ident)  # ✅ 50
```
**三种写法生死簿**（都在 5.2.1 实机测过）：
| 写法 | 结果 |
|---|---|
| `mod.properties.inputs[ident] = 50` | ✅ 可用 |
| `mod.properties.inputs[ident].value = 50` | ❌ 'IDPropertyGroup' object has no attribute 'value' |
| `mod["Socket_2"] = 50` | ❌ id properties not supported for this type（旧写法已移除） |

`mod.properties.inputs.keys()` 返回输入 socket 的全部 identifier（如 `["Socket_0","Socket_2"]`）。
【文献】称 5.2 已 RNA 化为 `.value`——与本机 5.2.1 实测不符，**以实机为准**，升级后需重测。

## 3. 常用节点 bl_idname（【文献】）

| 用途 | bl_idname |
|---|---|
| 面分布 | `GeometryNodeDistributePointsOnFaces`（Poisson 模式更均匀；Density 单位 点/m²，草地 50-200） |
| 点上实例 | `GeometryNodeInstanceOnPoints` |
| 立方体/球网格 | `GeometryNodeMeshCube` / `GeometryNodeMeshUVSphere` |
| 随机值 | `GeometryNodeRandomValue`（5.2 socket identifier 有变，按名取前先打印确认） |
| 实例旋转/缩放 | `GeometryNodeRotateInstances` / `GeometryNodeScaleInstances` |
| 实体化实例 | `GeometryNodeRealizeInstances`（**导出 glTF 前必须 Realize**，见 06 分册） |

## 4. 求值 / 验证

- 设完值 `bpy.context.view_layer.update()` 强制刷新。
- GN 的实例化结果不在基网格里：`evaluated_get(dg).to_mesh()` 拿到的是基网格求值，
  实例要数数量得靠 Realize 后的评估或直接读 modifier 输入值确认（【实测】导出回读更直接）。

## 5. 何时用 GN vs 直接代码

- 海量重复（草、碎石、螺钉）：GN 实例化，C 端求值比 Python 循环快 2~3 个数量级。
- 一次性少量物体：直接 bpy 循环更直观。
- 散布配方：Distribute(Poisson, seed) → Instance on Points → Random rotate/scale → Realize（要导出时）。

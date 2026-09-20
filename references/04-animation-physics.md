# 04 动画 / 关键帧 / 物理 / Shape Keys

## 1. 关键帧基础（【实测】跨版本最稳入口）

```python
import bpy
obj = bpy.data.objects["TUT_Cube"]
obj.location = (0, 0, 1)
obj.keyframe_insert(data_path="location", frame=1)
obj.location = (0, 0, 3)
obj.keyframe_insert(data_path="location", frame=30)
bpy.context.scene.frame_set(15)             # 推进时间线（同时步进模拟）
```
- 5.2 起新关键帧默认 **Bezier** 插值【文献】；要线性就显式设（见 §2）。
- `keyframe_insert` 在 4.4 slotted actions 改造后**完全不变**，一步自动建齐
  Action/layer/strip/slot——永远从这里进。

## 2. 读 F-Curve（5.x 必走 channelbag；【实测】手动遍历版）

`bpy_extras` **不在安全模式白名单**（实测拒绝），`anim_utils` 用不了，手动遍历：

```python
import bpy
ad = bpy.data.objects["TUT_Cube"].animation_data
slot = ad.action_slot                        # slot.identifier 形如 "OBTUT_Cube"（没有 .name 属性！）
bag = None
for layer in ad.action.layers:
    for strip in layer.strips:
        bag = strip.channelbag(slot)
fcurves = [(fc.data_path, len(fc.keyframe_points)) for fc in bag.fcurves]
# 【实测】返回 [["location",2],["location",2],["location",2]]
```
- **`action.fcurves` 在 5.0 已删除**（【实测】`hasattr` 为 False）；4.4 里是兼容垫片。
- 批量写关键帧【文献】（上千帧必备，别一个个 insert）：
```python
fc = bag.fcurves[0]
n = 120
fc.keyframe_points.add(n)
co = [0.0] * (n * 2)
for i in range(n):
    co[2*i] = float(i + 1)
    co[2*i + 1] = i / n
fc.keyframe_points.foreach_set("co", co)     # numpy 被禁，foreach_set 是正道
fc.update()
# 单点：kp = fc.keyframe_points[-1]; kp.co=(30.0, 2.5); kp.interpolation='LINEAR'
```
- F-Curve 循环修饰器【文献】：`m = fc.modifiers.new('CYCLES'); m.mode_after='REPEAT'`。

## 3. 约束与父级（纯 RNA 赋值，安全模式无碍）

```python
c = obj.constraints.new('TRACK_TO')
c.target = target; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'

child.parent = parent
child.matrix_parent_inverse = parent.matrix_world.inverted()   # 先 parent 再 inverse，防跳位
```

## 4. 相机切换动画（【文献】marker 绑定）

```python
scene.camera = cam_a
m1 = scene.timeline_markers.new("CAM_A", frame=1);  m1.camera = cam_a
m2 = scene.timeline_markers.new("CAM_B", frame=50); m2.camera = cam_b
```

## 5. 刚体（【文献】流程 + 版本改名）

```python
import bpy
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 120          # ① 先设帧范围！默认 1..250
if scene.rigidbody_world is None:
    bpy.ops.rigidbody.world_add()
rbw = scene.rigidbody_world
rbw.substeps_per_frame = 10                          # 5.2 改名（旧名 steps_per_second）
rbw.solver_iterations = 10
bpy.ops.object.select_all(action='DESELECT')
for name in ("Cube", "Floor"):
    bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["Cube"]
bpy.ops.rigidbody.objects_add(type='ACTIVE')         # 需要 3D 视口上下文，报错就 temp_override(area=视口)
bpy.data.objects["Floor"].rigid_body.type = 'PASSIVE'
bpy.ops.ptcache.bake_all(bake=True)                  # ② 同步阻塞，单独一次调用跑！
```
- **先 bake 再 frame_set**（读缓存又快又稳）；`ptcache.free_bake_all()` 重置。
- bake 放在**独立的 execute_blender_code 调用**里，简单场景 ≤300 帧一次能完。

## 6. 布料 / 流体（【文献】最小配置）

```python
mod = obj.modifiers.new("Cloth", 'CLOTH')
mod.settings.quality = 8; mod.settings.mass = 0.3
mod.point_cache.frame_start, mod.point_cache.frame_end = 1, 120   # 必须显式设
bpy.ops.ptcache.bake_all(bake=True)
```
流体（Mantaflow）：域 `fluid_type='DOMAIN'; domain_settings.domain_type='LIQUID';
resolution_max=32`（MCP 会话上限！），流 `flow_type='INFLOW'`，`bpy.ops.fluid.bake_all()`
极慢，只做 ≤60 帧演示，大模拟让用户 GUI 手动烘。
- 5.2 新的 XPBD 几何节点物理【文献】：**无 Python API** 且安全模式禁 append 资产——
  明确告诉用户"这个请在 GUI 里点"，不要硬写代码。

## 7. Shape Keys（【文献】）

```python
obj.shape_key_add(name="Basis", from_mix=False)
sk = obj.shape_key_add(name="Wave", from_mix=False)
sk.slider_min, sk.slider_max = -1.0, 2.0
# 搬顶点：for i, v in enumerate(obj.data.vertices): sk.data[i].co = ...
# 动画宿主是 obj.data.shape_keys（不是 obj）：
obj.data.shape_keys.key_blocks["Wave"].keyframe_insert("value", frame=1)
```

## 8. 性能护栏（单次 execute_blender_code ≤20s 的量级参考）

| 操作 | 安全量 |
|---|---|
| keyframe_insert 逐个 | ≤1000 个；更多用 foreach_set 批量（可 10k+） |
| 新建简单物体 | ≤500~1000 个；海量重复用 GN 实例化 |
| Python 顶点循环 | ≤100k 次；网格批量读写一律 foreach_get/foreach_set |
| frame_set 循环 | 先 bake（未 bake 的模拟每帧都在步进！）；纯变换 300-500 帧/次 |

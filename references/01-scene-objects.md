# 01 场景 / 集合 / 物体 / 变换 / 修改器

## 1. 两种建物路径（【实测】5.2.1 均可用）

### 方式 A：bpy.ops（落到活动集合，GUI 上下文在时最省事）
```python
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
cube = bpy.context.active_object
cube.name = "TUT_Cube"
```
常用 primitive 专属参数（【文献】5.2 文档）：cylinder `vertices=32, radius=1, depth=2,
end_fill_type='NGON'`；uv_sphere `segments=32, ring_count=16, radius=1`；ico_sphere
`subdivisions=2`；cone `radius1/radius2/depth`；circle `fill_type='NOTHING'|'NGON'|'TRIFAN'`；
torus `major_segments=48, minor_segments=12`（torus **没有** scale/calc_uvs 参数）；
grid 的 x/y_subdivisions 是"格数"，顶点数 = (n+1)²。

### 方式 B：data API + bmesh（不依赖选中/活动状态，最稳）
```python
import bpy, bmesh
mesh = bpy.data.meshes.new("TUT_SphereMesh")
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1)
bm.to_mesh(mesh)
bm.free()
ball = bpy.data.objects.new("TUT_Sphere", mesh)
target_collection.objects.link(ball)   # 物体必须 link 到至少一个集合
```

## 2. 集合管理（【实测】）

```python
col = bpy.data.collections.get("MCP_SKILL_TEST") or bpy.data.collections.new("MCP_SKILL_TEST")
if not col.users:
    bpy.context.scene.collection.children.link(col)
# 设为活动集合：ops 建物都会落进来
bpy.context.view_layer.active_layer_collection = \
    bpy.context.view_layer.layer_collection.children["MCP_SKILL_TEST"]
```
- 物体在同一 scene 只能属于一个集合；挪动 = 旧集合 unlink + 新集合 link。
- 删空集合：`bpy.data.collections.remove(col)`（先确认 users==0 或先 unlink）。

## 3. 变换

```python
import math
obj.location = (1, 2, 3)                    # 米
obj.rotation_euler = (0, 0, math.radians(30))  # 弧度！
obj.scale = (1, 1, 1.5)
loc, rot, scl = obj.matrix_world.decompose()   # 世界矩阵分解
```

### 应用变换（【实测】temp_override 写法 + 5.2 新参数）
```python
with bpy.context.temp_override(active_object=obj, object=obj,
                               selected_objects=[obj], selected_editable_objects=[obj]):
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True,
                                   properties=True, isolate_users=False)  # 返回 {'FINISHED'}
```
- 多用户 mesh 会报 "multi user data"：`isolate_users=True` 自动拷贝，或先 `obj.data = obj.data.copy()`。
- 程序化检测未应用缩放（【文献】）：`matrix_world.decompose()` 的 scale != 1；
  `matrix_world.determinant() < 0` = 负缩放（会翻法线，导出前必须处理）。

## 4. 修改器（【实测】全通过）

```python
bev = obj.modifiers.new("Edge", 'BEVEL')
bev.width = 0.05; bev.segments = 3; bev.limit_method = 'ANGLE'; bev.affect = 'EDGES'

ss = obj.modifiers.new("Smooth", 'SUBSURF')
ss.levels = 1; ss.render_levels = 2; ss.subdivision_type = 'CATMULL_CLARK'

arr = obj.modifiers.new("Line", 'ARRAY')
arr.count = 3; arr.use_relative_offset = True; arr.relative_offset_displace = (1.5, 0, 0)

sol = obj.modifiers.new("Shell", 'SOLIDIFY')
sol.thickness = 0.1; sol.offset = -1

b = obj.modifiers.new("Cut", 'BOOLEAN')
b.object = cutter_obj; b.operation = 'DIFFERENCE'; b.operand_type = 'OBJECT'
b.solver = 'FLOAT'   # 5.x：FAST 改名 FLOAT；另有 EXACT / MANIFOLD。慎用 EXACT（本环境曾疑似卡死）
```
- 应用单个修改器（需 override）：
```python
with bpy.context.temp_override(active_object=obj, object=obj,
                               selected_editable_objects=[obj]):
    bpy.ops.object.modifier_apply(modifier=mod.name)
```
- 免算子取修改器结果（安全模式最稳）：
```python
dg = bpy.context.evaluated_depsgraph_get()
me = obj.evaluated_get(dg).to_mesh()
tri = sum(len(p.vertices) - 2 for p in me.polygons)   # 【实测】布尔后 1648 三角面
obj.evaluated_get(dg).to_mesh_clear()                  # 必须清，防内存泄漏
```

## 5. 复制 / 删除 / 孤儿清理

```python
dup = obj.copy(); dup.data = obj.data.copy()   # data 不 copy 则共用网格
bpy.context.collection.objects.link(dup)
bpy.data.objects.remove(obj, do_unlink=True)
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)  # 收尾必做
```
- 【实测】删除集合不会自动删物体——先逐个 remove 物体再删集合。

## 6. 父化矩阵三定律 + 同名重建碰撞（BMCP-ERR-010【实测·坦克建模，炮塔悬空实锤】）

1. **定律一**：新设 location 后立即读 `matrix_world` 得旧值（depsgraph 未刷新，与 03 分册
   §6.5 同源）——多级父化时以此算 `matrix_parent_inverse` 会整链偏移；
2. **终版规范**：子物体顶点**直接建在父级局部坐标系**，`matrix_parent_inverse` 与
   `matrix_basis` 保持单位阵（world = parent.matrix_world 的唯一可靠路径）；
3. **定律二**：同一脚本内改完父化立即读 matrix_world / bbox 仍可能滞后一拍（连渲染都取
   中间态）——**数值验收放到下一个调用**；
4. **定律三（假象警示）**："矩阵振荡"追三轮不如先验几何本体——真根因可能是顶点没建在
   轴线高度，父化修正只是换了偶然偏移。先验几何，再怀疑依赖图；
5. **同名重建碰撞**：删除失败（名字打错）后再建同名物体 → 新物体**静默带 .001 后缀**，
   后续按名删除永远删不到原件。规范：删除后必须断言
   `bpy.data.objects.get(name) is None`，重建统一走幂等 KILL 前置。

## 7. 集合实例化（重复元素省内存）

```python
emp = bpy.data.objects.new("TUT_instancer", None)
bpy.context.collection.objects.link(emp)
emp.instance_type = 'COLLECTION'
emp.instance_collection = src_collection
# 源集合不重复显示：view_layer.layer_collection.children[src.name].exclude = True
```

# 08 参数化生成器（JSON 驱动批量建物）

## 1. 健壮生成器骨架（安全模式兼容，可直接粘贴进 execute_blender_code）

设计四原则：幂等重置（同前缀先删）、参数钳制（clamp 不崩）、固定种子（同配置同结果）、
前缀命名（批量删除/识别）。

```python
import bpy, json, math, random

PREFIX = "CFG_"
rng = random.Random(42)   # 固定种子 = 幂等

def reset(prefix=PREFIX):
    # 先删物体（快照列表，避免边遍历边改）
    for ob in [o for o in bpy.data.objects if o.name.startswith(prefix)]:
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)

def clamp(cfg, key, default, lo, hi):
    v = cfg.get(key, default)
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = float(default)
    return max(lo, min(hi, v))

def build_part(name, spec, coll):
    t = spec.get("type", "cube")
    loc = spec.get("location", [0, 0, 0])
    rot = [math.radians(a) for a in spec.get("rotation", [0, 0, 0])]  # 配置用角度制
    if t == "cube":
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
        ob = bpy.context.active_object
        s = spec.get("scale", [1, 1, 1])
        ob.scale = (s[0], s[1], s[2])
    elif t == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=int(clamp(spec, "vertices", 32, 3, 256)),
            radius=clamp(spec, "radius", 0.5, 0.001, 10000.0),
            depth=clamp(spec, "depth", 2.0, 0.001, 10000.0),
            location=loc, rotation=rot)
        ob = bpy.context.active_object
    else:
        raise ValueError("unsupported part type: " + str(t))
    ob.name = name
    ob.data.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob

def build_from_config(cfg):
    reset()
    coll = bpy.data.collections.get(PREFIX + "build") or \
        bpy.data.collections.new(PREFIX + "build")
    if not coll.users:
        bpy.context.scene.collection.children.link(coll)
    made = []
    for i, part in enumerate(cfg.get("parts", [])):
        name = PREFIX + part.get("name", "part_%03d" % i)
        made.append(build_part(name, part, coll).name)
    return made

# 用法：
# config = {"parts":[{"name":"leg1","type":"cylinder","location":[0,0,0.5],"depth":1.0}]}
# print(json.dumps(build_from_config(config)))
```

## 2. 复合形状套路

- **椅子**：4×cylinder 腿 + cube 坐面 + 倾斜 cube 靠背 → bevel → (可选) subsurf。
- **楼梯**：循环 cube（`for i in range(n): location=(0, i*w, i*h)`）或 ARRAY 修改器。
- **管道/电线**：曲线 + bevel_depth 成管：
```python
cu = bpy.data.curves.new("CFG_wire", type='CURVE')
cu.dimensions = '3D'; cu.bevel_depth = 0.02; cu.fill_mode = 'FULL'
sp = cu.splines.new('BEZIER')
sp.bezier_points.add(3)                      # 新建自带 1 点，add(3)=4 点
for bp, p in zip(sp.bezier_points, pts):
    bp.co = p
    bp.handle_left_type = bp.handle_right_type = 'AUTO'
```
- **文字**：`bpy.data.curves.new(name, type='FONT')`：body/size/extrude/bevel_depth/
  align_x='CENTER'；要网格就 `bpy.ops.object.convert(target='MESH')`（需选中激活）。
- **散布**：集合实例化 + 空物体载体（见 01 分册 §6）；N 个实例用 `rng.uniform` 撒位置。

## 3. 确定性 random 的边界

安全模式白名单里有 `random`，但**每次 execute 是独立脚本**——同配置要同结果，
必须 `random.Random(固定种子)`，不能用全局 random 状态。

## 4. 与 30s 超时配合

- 单次调用建 ≤200 个部件没问题；上千部件拆多次调用（每次幂等：只建自己的部分）。
- 或改用 GN 实例化（05 分册）：一颗种子撒几万实例是 C 端求值，毫秒级。

## 5. 批量生成器命名纪律（【实测】爱弥斯 10 万面案例，教训 BMCP-ERR-001）

来源：`Blender技能审计_爱弥斯建模_20260912/`——批量发束脚本把 `"AMS_TailStrand000"`
（已带前缀）传入 `objects.new("AMS_" + name)`，自建物体实际名为 `AMS_AMS_*`；
日志记录的却是传入名。后续模式匹配清理导入残留时与自建物体全碰撞，**误删 353 物体**。

### 5.1 单一前缀 + 回传实际名
- `objects.new(name)` 的 name 由**生成器统一加前缀**，调用方只传裸名：
```python
def make_strands(bare_names, coll, prefix="AMS_"):
    made = []
    for bare in bare_names:
        ob = bpy.data.objects.new(prefix + bare, mesh)   # 前缀只在这一处加
        coll.objects.link(ob)
        made.append(ob.name)                             # 回传【实际物体名】，不是传入名
    return made
```
- print/report **必须回传实际物体名**（`ob.name`），日志与场景真值一致才有对账意义。

### 5.2 清理外部导入物只用身份差集
```python
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=glb_path)
imported = set(bpy.data.objects.keys()) - before          # 差集=导入物名单
for name in sorted(imported):
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
```
**任何模式匹配（通配符/前缀字符串过滤）都可能有同名碰撞**——外部导入物的名字不受你控制。

### 5.3 破坏性批量操作前先落快照
清理、布尔、大规模删除之前：
```python
bpy.ops.wm.save_as_mainfile(filepath="D:/proj/快照.blend", copy=True)  # 不动原文件，秒级
```
成本秒级，退路无价——爱弥斯事故当时"以为只是删几十个导入物"，没落快照，353 物体只能全量重建。

### 5.4 对账用名单 diff，不用计数
计数吻合可能掩盖错名物体（爱弥斯重建后计数达标，diff 却抓出 268 个双前缀错名）。
程序化对账：期望名单（生成器 made 列表）vs 实际名单（场景扫描）逐名比对。

## 6. 自愈前导 + 集合持久性异常（BMCP-ERR-009【实测·坦克建模】）

- 【实测】隔离集合（MCP_SKILL_TEST）会在**下一个调用里消失**，而同一脚本内的其他
  mutation（物体隐藏、场景自定义属性）都持久——集合操作有跨调用持久性异常；
  半途报错的脚本还会留下孤儿数据块（铁律 3 的集合版）。
- **规范：每个脚本开头放"自愈前导"**（幂等三连）：
```python
col = bpy.data.collections.get("MCP_SKILL_TEST") or bpy.data.collections.new("MCP_SKILL_TEST")
if not col.users:
    bpy.context.scene.collection.children.link(col)
bpy.context.view_layer.active_layer_collection = \
    bpy.context.view_layer.layer_collection.children["MCP_SKILL_TEST"]
```
- 半途报错的孤儿块：随下一次同前缀脚本的 reset 清理，或按身份差集手动删。

# 03 灯光 / 相机 / 渲染

## 1. 灯光四型（【实测】data API 全通过）

```python
import bpy

def make_light(name, ltype, energy, loc, col=None):
    ld = bpy.data.lights.new(name, type=ltype)
    ld.energy = energy
    if col: ld.color = col
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = loc
    return lo, ld

key,  kd = make_light("TUT_LampKey",  'AREA', 150.0, ( 4, -4, 5), (1.0, 0.95, 0.88))
fill, fd = make_light("TUT_LampFill", 'AREA',  40.0, (-4, -3, 3), (0.85, 0.9, 1.0))
rim,  rd = make_light("TUT_LampRim",  'AREA', 100.0, ( 0,  5, 4))
kd.shape = 'SQUARE'; kd.size = 2.0          # 尺寸越大影子越软
```
- 能量单位【文献】：POINT/SPOT/AREA = W（新建默认 100W）；SUN = W/m²（默认 1.0），
  SUN 柔影用 `sun.angle`（弧度）。
- SPOT 专属：`spot_size`（弧度）`spot_blend`。
- 三点光比例【文献】：Fill = Key 的 1/4~1/2；Rim = 0.7~1.5×Key；冷暖对比 3200K vs 6500K。

## 2. 相机 + 对焦 + 景深（【实测】）

```python
import bpy
cam_data = bpy.data.cameras.new("TUT_Camera")
cam_data.lens = 50.0                        # 35 环境 / 50 通用 / 85 人像特写
cam = bpy.data.objects.new("TUT_Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (7, -7, 4)

aim = bpy.data.objects.new("TUT_Aim", None) # 瞄准空物体
bpy.context.collection.objects.link(aim)
aim.location = (0.3, 0, 1.0)

tc = cam.constraints.new('TRACK_TO')        # 相机 -Z 对准目标 +Y 朝上
tc.target = aim
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'

cam_data.dof.use_dof = True                 # 景深：f/2.8 起步
cam_data.dof.focus_object = aim
cam_data.dof.aperture_fstop = 2.8

bpy.context.scene.camera = cam              # 必须赋值，否则渲染报 No camera found
```

## 3. 渲染（【实测】端到端 640×360 EEVEE 出图验证）

```python
import bpy
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'       # 5.x 就叫这个！4.2~4.5 才是 BLENDER_EEVEE_NEXT
scene.eevee.taa_render_samples = 16         # 测试 16，出图 64+（Cycles 产品图 1024+）
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = "%TEMP%/out.png"   # 正斜杠最稳
bpy.ops.render.render(write_still=True)

# 回读验证（安全模式禁 open()，这是唯一可靠的落盘校验）
img = bpy.data.images.load(scene.render.filepath)
size = list(img.size)                       # [640, 360]
bpy.data.images.remove(img)
```
- **引擎 ID 兼容写法【文献】**：`for eng in ('CYCLES','BLENDER_EEVEE','BLENDER_EEVEE_NEXT'): try: scene.render.engine = eng; break; except TypeError: continue`
- **Cycles GPU**【文献】：本机 GPU 未配置（devices 空）。启用：`prefs = bpy.context.preferences.
  addons['cycles'].preferences; prefs.compute_device_type='OPTIX'|'CUDA'|'HIP'|'ONEAPI';
  prefs.get_devices(); [d.use for d in prefs.devices...]` + `scene.cycles.device='GPU'`。
  ⚠️ **该配方在 Safe Mode 下不可执行**【实测】：`preferences` 链式导航被拒
  （"reached through an unresolvable receiver"）——需按 09 分册 §4B 独立子进程通道，
  或由用户在 GUI 偏好里手动勾选。
  低采样冒烟：`scene.cycles.samples=32; scene.cycles.use_denoising=True`。
- **色彩管理**：4.0+ 默认 AgX（颜色偏灰是特性不是 bug）。要鲜艳：
  `scene.view_settings.look = 'AgX - Medium High Contrast'` 或 `view_settings.exposure += 0.3`。
  需要精确色值（UI 稿比对）才用 `view_transform='Standard'`。本机用户文件当前是 Standard。
- Cycles 渲染是否超 30s：**以首次冒烟实测为准**【实测判据】三角面 <5 万且 ≤720p/64spp 时
  CPU Cycles 通常 <30s（1280×720/16spp/672 tris = 3.96s）；先 640×360/32 samples 试水，
  把实测耗时记进 report，再决定出大图前是否要给用户预告时长。
- 5.0+ 输出格式新规【文献】：先设 `scene.render.image_settings.media_type='IMAGE'`
  再设 `file_format`。

## 4. 世界与 HDRI

```python
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
bg = next((n for n in world.node_tree.nodes if n.type == 'BACKGROUND'), None)
if bg is None:                               # 兜底（4.x 需要；5.2 会抛 DeprecationWarning，6.0 移除）
    world.use_nodes = True                   # 【文献】5.x 已废弃恒 True——新代码勿写，仅 4.x 兼容保留
    bg = next((n for n in world.node_tree.nodes if n.type == 'BACKGROUND'), None)
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
bg.inputs["Strength"].default_value = 1.0
```
HDRI（【文献】）：
```python
env = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load("C:/hdris/kloppenheim_02_1k.hdr")
tc = world.node_tree.nodes.new('ShaderNodeTexCoord')
mp = world.node_tree.nodes.new('ShaderNodeMapping')
mp.inputs["Rotation"].default_value[2] = 1.5708          # Z 旋转 HDRI
world.node_tree.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
world.node_tree.links.new(mp.outputs["Vector"], env.inputs["Vector"])
world.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"])
# Strength 1.0 是物理正确曝光；嫌暗调曝光，别猛拉 Strength
```
- **程序化天空的 5.2 枚举变更（BMCP-ERR-012【实测·坦克建模】）**：Sky Texture 的
  `'NISHITA'` 已删除，现值 `SINGLE_SCATTERING / MULTIPLE_SCATTERING / PREETHAM / HOSEK_WILKIE`；
  Nishita 的 sun_elevation/rotation/intensity 参数迁移到 SINGLE_SCATTERING。
- **GPU 配置状态是会话可变的**【实测】：本会话 devices 空 ≠ 下个会话仍空（用户可随时在
  GUI 偏好开启；坦克建模实战实测 GPU 可用并**单调用完成 1280×720@64 Cycles**）——耗时
  判断永远以"首次冒烟实测"为准（见 §3 精渲行）。
- PolyHaven 直链（集成未开启时也可走 headless 下载）【文献】：
  `https://api.polyhaven.com/files/<asset_id>` 返回的 hdr 直链形如
  `https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/<id>_1k.hdr`。

## 5. 构图速查（【文献】社区共识）

- 三分法：`cam_data` 无直接属性，是 Viewport Display 的 Thirds 勾选（辅助线）；交点放主体。
- 焦段：24-35 环境（建筑垂直线用 `shift_x/y` 而非倾斜）/ 50 通用 / 85+ 特写压缩。
- 透视只由**机位**决定：换焦距=裁切，压缩感=拉远+长焦。
- DOF：产品/人像 f/1.4–f/4；全景 f/8+。

## 6. 渲染隔离与用户场景保护（【实测】爱弥斯 10 万面建模案例）

来源：`D:\...\迷深清洗工作2\Blender技能审计_爱弥斯建模_20260912\`（45 次 MCP 调用实战）。
教训编号归属见 12 分册 §7（BMCP-ERR-002/003/004）。

### 6.1 hide_set ≠ 渲染可见性（BMCP-ERR-002）
- `hide_set`（视口眼标）**不影响 F12 渲染**；渲染只认 `hide_render`（相机标）。
  【实测】自检图拍到用户物体，就是只做了 hide_set。
- 隔离用户物体做自方渲染时：`obj.hide_render = True`（数量大时先存快照再改，见 6.3）。

### 6.2 渲染顺序纪律（BMCP-ERR-002 同源）
**恢复用户场景（可见性/World/相机/分辨率）必须放在所有渲染全部完成之后**。
【实测】两次失误：①恢复可见性后渲染 → 用户坦克入镜；②恢复用户 World 后渲染 → 天光过曝。
正确顺序：隔离 → 全部渲染（含返工重渲）→ 恢复 → （如需）重新隔离再渲。

### 6.3 World 背景被贴图驱动时改 default_value 无效（BMCP-ERR-003）
- 场景已有 World 且 Background 颜色输入被贴图节点驱动时，改
  `bg.inputs["Color"].default_value` **不生效**（被驱动端口，改了也被覆盖）。
- 正确做法：自建 world 挂到 scene（`bpy.data.worlds.new` + 赋 `scene.world`），
  渲染完把用户原 world 赋回去。
- 同类坑：改分辨率/采样数也属"借用的场景设置"，渲染完按快照还原。
- **隔离期间禁止任何 `orphans_purge`**【BMCP-ERR-005，DSH 实测真事故】：换 world 后用户的
  world 变成 users==0，purge 会把它当孤儿清掉（AMS_World 曾被静默删除，靠快照重建）；
  先还原用户 world/camera，再做任何清理。骨架备有 `assert_safe_to_purge()` 机器守卫
  （v1.4，V-02）。

### 6.4 用户场景快照/恢复模式（长任务标配）
建模期需要动用户可见性/World/相机时，先存快照再改、渲染完全量还原：
```python
import json
# 存（挂 scene 自定义属性；存取格式必须一致——实测踩过 list/dict 不一致的坑）
scene["AMS_hiderender_json"] = json.dumps(
    {o.name: [o.hide_get(), o.hide_render] for o in bpy.context.scene.objects})
# 还原（还原脚本开头先做幂等解析，格式不对报错重来）
snap = json.loads(scene["AMS_hiderender_json"])
for name, (hv, hr) in snap.items():
    o = bpy.data.objects.get(name)
    if o:
        o.hide_set(hv); o.hide_render = hr
```
还原清单：hide_get/hide_render、`scene.world`、`scene.camera`、分辨率与采样、
自建的自定义属性（还原后删除）。

### 6.5 matrix_world 延迟求值（BMCP-ERR-004）
- 变换后立即读 `obj.matrix_world` 可能拿到**旧矩阵**——先 `bpy.context.view_layer.update()`。
- 【实测】场景级包围盒勘误被 ±60m 地面板撑大：算"真·车体"包围盒前先按名单过滤物体集，
  别拿整个场景的 bbox 做位置判断。

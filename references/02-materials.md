# 02 材质 / 节点树 / 程序化配方

## 1. 新建材质（【实测】5.2 行为）

- `bpy.data.materials.new("X")` **自带节点树**（Principled + Output 两个节点）；
  `use_nodes` 已废弃（恒 True，赋值无效），为兼容 3.x/4.x 可以写但别指望它。
- **中文名坑**：默认节点名是 `原理化 BSDF` / `材质输出`（中文 UI 本地化）。
  找节点按 `node.type == 'BSDF_PRINCIPLED'`（type）或 `bl_idname == 'ShaderNodeBsdfPrincipled'`
  （bl_idname），两者不是一回事；自己建的节点随手改名固化。

```python
import bpy, json
mat = bpy.data.materials.get("TUT_Metal") or bpy.data.materials.new("TUT_Metal")
bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)  # 带默认——裸 next 的空错误见 09 分册
bsdf.inputs["Base Color"].default_value = (0.75, 0.3, 0.1, 1.0)
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.3
obj.data.materials.append(mat)          # 或 obj.active_material = mat
print(json.dumps([i.name for i in bsdf.inputs]))
```

## 2. Principled BSDF 5.2 全部 32 个输入（【实测】逐个抓取）

```
Base Color, Metallic, Roughness, IOR, Alpha, Thin Wall, Normal, Weight,
Diffuse Roughness, Subsurface Weight, Subsurface Radius, Subsurface Scale,
Subsurface IOR, Subsurface Anisotropy, Specular IOR Level, Specular Tint,
Anisotropic, Anisotropic Rotation, Tangent, Transmission Weight,
Coat Weight, Coat Roughness, Coat IOR, Coat Tint, Coat Normal,
Sheen Weight, Sheen Roughness, Sheen Tint, Emission Color, Emission Strength,
Thin Film Thickness, Thin Film IOR
```
- 版本改名史【文献】：4.0 起 `Specular→Specular IOR Level`、`Emission→Emission Color`、
  `Clearcoat→Coat Weight`、`Transmission→Transmission Weight`、`Subsurface→Subsurface Weight`。
  跨版本防御：`sock = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")`。
- **永远按名字取**，不要按索引（4.0 索引位移过）。
- 5.2 新增 `Weight`/`Thin Wall`；本机实测**没有**色散插槽（文献说法与实机不符处，以实测为准）。

## 3. 贴图节点标准接线（【文献】+ 实测接线 API）

```python
nt = mat.node_tree
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(r"C:/path/albedo.png", check_existing=True)
uv = nt.nodes.new('ShaderNodeUVMap')
nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])   # sRGB 保持默认

nrm_tex = nt.nodes.new('ShaderNodeTexImage')
nrm_tex.image = bpy.data.images.load(r"C:/path/normal_gl.png")
nrm_tex.image.colorspace_settings.name = 'Non-Color'            # 数据图必须 Non-Color！
nrm = nt.nodes.new('ShaderNodeNormalMap'); nrm.strength = 1.0
nt.links.new(nrm_tex.outputs["Color"], nrm.inputs["Color"])
nt.links.new(nrm.outputs["Normal"], bsdf.inputs["Normal"])
```
- PolyHaven 贴图后缀约定【文献】：`diff`(sRGB) / `nor_gl`(Non-Color, Blender/glTF 通用的
  OpenGL 法线) / `rough` / `ao` / `metal`(均 Non-Color) / `arm` = 打包图 R=AO G=Rough B=Metal。

## 4. 程序化节点速查（【文献】版本红线）

| 需求 | bl_idname | 红线 |
|---|---|---|
| 噪声 | `ShaderNodeTexNoise` | **Musgrave 4.1 已删**，功能并入 Noise 的 noise_type |
| 砖墙 | `ShaderNodeTexBrick` | 稳定；属性 offset/squash，输入 Color1/Color2/Mortar/Scale/Mortar Size/Brick Width/Row Height |
| 波纹(木纹) | `ShaderNodeTexWave` | wave_type='BANDS'，Distortion 是灵魂 |
| ColorRamp | `ShaderNodeValToRGB` | 名字怪但没变过；操作 color_ramp.elements |
| 混色 | `ShaderNodeMix` + data_type='RGBA' | **MixRGB 已淘汰别再建**；RGBA 的 A/B 是 **inputs[6]/[7]**（同名 socket 多份，靠 index/identifier 区分），Factor 是 inputs[0]，输出 outputs[2] |

**Mix 方向陷阱（BMCP-ERR-011【实测·坦克建模】）**：`Factor=0` 输出 **A（inputs[6]）**、
`Factor=1` 输出 **B（inputs[7]）**——把主色放 A、磨损色放 B 再把 Factor 接到"磨损程度"，
方向就反了（全车呈磨损色的实锤）；排查时还容易误疑 Pointiness。接线前默念：
**0=第一个口（A），1=第二个口（B）**。
| 凹凸 | `ShaderNodeBump` | Height 入 / Normal 出 |
| 坐标/映射 | `ShaderNodeTexCoord` / `ShaderNodeMapping` | Generated/UV/Object → Mapping → 纹理 Vector |
| 边缘磨损 | `ShaderNodeNewGeometry` | Pointiness 输出——**Cycles 专属**，EEVEE 恒 0.5 |

## 5. 配方：磨损边金属（【文献】节点图，可在 Cycles 出效果）

```
Geometry.Pointiness → ColorRamp(0.50/0.60 收窄) → Mix.Factor
Mix.A_Color=底色(0.08,0.10,0.14)  B_Color=磨损色(0.85,0.87,0.90) → Principled.Base Color
Noise(12,6) → ColorRamp(0.35/0.65) → Principled.Roughness + Bump.Height → Normal
Metallic = 1.0
```
EEVEE 替代 Pointiness：用 Bevel 节点或 AO 节点近似边缘。

## 6. 节点组（【文献】4.0+ 接口 API）

```python
grp = bpy.data.node_groups.new("WD_wood", 'ShaderNodeTree')
grp.interface.new_socket("Scale", in_out='INPUT', socket_type='NodeSocketFloat')
grp.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
gin = grp.nodes.new('NodeGroupInput'); gout = grp.nodes.new('NodeGroupOutput')
# 旧 grp.inputs.new()/outputs.new() 已删除，别用
```
- 材质里实例化：`gnode = nt.nodes.new('NodeGroup'); gnode.node_tree = grp`。
- 安全模式**禁** `wm.append/link`——外部 .blend 里的节点组资产导不进来，只能代码重建。

## 7. 材质参数动画（免驱动器；安全模式封驱动器，这是唯一路径）

```python
sock = nt.nodes["Mix"].inputs[0]           # Factor
for f, v in [(1, 0.0), (48, 1.0), (96, 0.0)]:
    sock.default_value = v
    sock.keyframe_insert("default_value", frame=f)
```
注意 fcurve 挂在 `nt.animation_data` 上；data_path 里节点名是字符串，**建节点时固定名字**。

## 8. 材质槽

```python
obj.data.materials.append(mat)             # 常规
slot = obj.material_slots[0]
slot.link = 'DATA'                          # 'OBJECT'=物体级覆盖（同 mesh 换装）
obj.data.materials.clear()                  # 全清
```

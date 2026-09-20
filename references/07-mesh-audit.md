# 07 网格体检 / 清理 / 面数 / UV / 烘焙

## 1. 几何体检（无算子路径，安全模式友好）

【文献·关键事实】`is_manifold/is_boundary/is_wire/is_contiguous` **只在 bmesh 上**，
`mesh.edges` 的 MeshEdge 没有这些属性。

```python
import bpy, bmesh, json

def geometry_report(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    r = {"non_manifold_edges": 0, "boundary_edges": 0, "wire_edges": 0,
         "flipped_winding_edges": 0, "zero_area_faces": 0}
    for e in bm.edges:
        if e.is_boundary:            r["boundary_edges"] += 1          # 洞
        elif not e.is_manifold:
            if e.is_wire:            r["wire_edges"] += 1
            else:                    r["non_manifold_edges"] += 1      # >2 面
        elif not e.is_contiguous:    r["flipped_winding_edges"] += 1   # 绕向不一致
    for f in bm.faces:
        if f.calc_area() <= 1e-12:   r["zero_area_faces"] += 1
    r["tris"] = sum(len(p.vertices) - 2 for p in me.polygons)
    bm.free()
    return r

print(json.dumps(geometry_report(bpy.data.objects["TUT_Cube"])))
```
完整闭包法线检测（signed volume）【文献】：封闭网格对原点求有向体积，负值=法线朝内。

## 2. 清理（bmesh 路径免上下文，优先用）

```python
import bmesh
def merge_by_distance(obj, dist=0.001):
    me = obj.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)   # verts 必传
    bm.to_mesh(me); bm.free(); me.update()
```
- 法线重算：`bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])`
- 补洞：`bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=4)`（**名字是 holes_fill** 不是 fill_holes）
- 三角化：`bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')`
- 非破坏焊接：`mod = obj.modifiers.new("Weld", 'WELD'); mod.merge_threshold = 0.001`
- `mesh.validate(verbose=False)`【文献】：返回 **True = 它改了数据**（本来的好网格返回 False，
  反直觉！）；修索引越界/重复面/零长边，**不修**洞和翻转法线。
- `me.update()`：from_pydata / bmesh 写回后的标准收尾。

## 3. 面数统计与平台预算

```python
tri = sum(len(p.vertices) - 2 for p in mesh.polygons)     # 最快
# 含修改器（评测真面数）：
dg = bpy.context.evaluated_depsgraph_get()
me = obj.evaluated_get(dg).to_mesh()
tri_eval = sum(len(p.vertices) - 2 for p in me.polygons)
obj.evaluated_get(dg).to_mesh_clear()
```
平台预算参考【文献】（三角形）：手机道具 100–2000；手机角色 ~1500；PC 环境件 1k–10k；
PC 主角 15k–50k；低多边形 <5000；VR 每帧 30–50 万（Quest 实践）；LOD 梯度 25k/8k/2k。

## 4. UV 自动化

```python
# Smart UV Project（编辑模式+全选；角度是弧度！66°≈1.15192）
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')
```
- 标记接缝（免算子）：`me.edges[idx].use_seam = True`
- 5.x 写 UV 层数据【文献】：`layer.uv[loop_index].uv = (u, v)`——`layer.data` 已弃用！
- UV 打包/重叠检测需 UV 编辑器上下文，MCP 会话里能跑（有 GUI）但要用
  `temp_override(area=IMAGE_EDITOR_area)`。

## 5. 纹理烘焙（只有 Cycles 能烘【文献】）

```python
import bpy
scene = bpy.context.scene
scene.render.engine = 'CYCLES'

# ① 造目标图 + 挂到材质里"活动且选中"的 Image Texture 节点
img = bpy.data.images.new("bake_normal", 2048, 2048, alpha=False)
img.colorspace_settings.name = 'Non-Color'          # 法线/粗糙/AO 必须 Non-Color
mat = obj.data.materials[0]
node = mat.node_tree.nodes.new('ShaderNodeTexImage')
node.image = img
for n in mat.node_tree.nodes: n.select = False
node.select = True
mat.node_tree.nodes.active = node                    # 不激活 = 烘了个寂寞

# ② 烘
bpy.ops.object.bake(type='NORMAL', margin=8, margin_type='EXTEND')

# ③ 落盘（不 save = 数据只活在 .blend 内）
img.filepath_raw = "%TEMP%/bake_normal.png"
img.file_format = 'PNG'
img.save()
```
- type 全集【文献】：COMBINED/AO/SHADOW/POSITION/NORMAL/UV/ROUGHNESS/EMIT/ENVIRONMENT/
  DIFFUSE/GLOSSY/TRANSMISSION；只烘漫反射颜色：`type='DIFFUSE', pass_filter={'COLOR'}`。
- 失败清单：无 UV / 无活动选中图像节点 / 引擎不是 Cycles / 忘 img.save() /
  **方向反（不报错，产出平图）**——见下节第 5 条。
- Selected-to-Active：`use_selected_to_active=True` + `cage_extrusion`/`max_ray_distance`；
  高模先 join 再烘（内存）。

### 7.2A Selected-to-Active 的方向与语义（BMCP-ERR-014【实测·DSH 坦克】：方向反了**不报错**，只产出平图）

- **心智模型：取色看源（选中），落图看目标（active）**——active 必须是**低模（目标）**，
  高模只被选中；把高模设成 active = 往没有 UV 的高模上烘，法线图全平（实测整套交付作废）；
- **EMIT/曲率烘的是"源物体"的着色**：Pointiness 等 Emission 链要接在**高模**材质上，
  接低模 = 全黑平图（同一条数据流，换张图又踩一次——只记操作步骤、没理解数据流向的下场）；
- 高模需有 UV 层（**占位空层即可**，报错会点名目标物体）；
- 高模物体多时射线极慢：先减面合并成单一网格再烘（实测 840 件 → 3.2M 单网格后分钟级完成）；
- **烘焙目标节点不要复用**（换 image 会让旧图变零用户、保存时被回收）——跨脚本传递产出
  靠磁盘文件回读；
- **静默失败机验**（对照第 5 类失败）：平贴图体积必然**小一个量级**——相对判据即可，
  无需记绝对数（配对实测：1024² 13.7KB→507KB=37×、2048² 53.9KB→647KB=12×、
  4096² 215KB→7156KB=33×，均为同资产修复前后）；法线均值应 ≈ [0.5, 0.5, 1.0]——
  把这两条写进验收脚本。

## 5A. 图集合并与独立贴花（BMCP-ERR-014 同批【实测·DSH 坦克资产】；13 分册七阶段未覆盖的"资产化管线"）

- **图集合并**：多张贴图 → 4096² 图集 + UV 重映射；**图块间做中性填充**（防边界采样渗色）；
- **贴花两路**：① 独立面片（定位见下）保持可动；② "擦除烘死"——把贴花烘进图集并改材质槽指派；
- **矢量渲贴花**：点阵/矢量数据 → 渲染成贴花图集再贴；
- **同型件复用 UV 必须连材质/贴图指向一起复用**（M-04：只复用 UV 是半套，负重轮其余组渲染发暗实锤）；
- 建立显式 key → 代表组映射，勿按名字猜测。

**装饰面片定位手段（F-26 整改，安全模式友好）**：`obj.ray_cast(origin, direction)`
取命中点 `loc + normal×offset` 定位面片——纯 bmesh/ray_cast，**实测 20+ 件命中率 100%**；
命中失败即跳过该件（容错写法）。**定位必须依据外表面实测值**（M-05：按主体标称尺寸放 = 面片埋进装甲）。

## 6. 游戏导出就绪清单（glTF）

1. 变换已应用（scale 全 1、无负缩放）——程序化检测 `matrix_world.decompose()`。
2. 面数达标（§3 评测口径，含修改器）。
3. UV 一套、无重叠；法线/数据贴图 Non-Color。
4. 材质用 Principled；无空材质槽；材质名规范（引擎按名匹配）。
5. LOD：`DECIMATE` 修改器 `ratio` 0.5/0.25 + `use_collapse_triangulate=True`，
   命名 `Name_LOD1/LOD2`（内置 glTF 导出器不带 LOD 功能【文献】）。

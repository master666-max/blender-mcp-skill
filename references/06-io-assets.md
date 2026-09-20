# 06 导入导出 / 外部资产 / 保存

## 1. 算子名对照表（【文献】4.x→5.x 全核对；AI 最容易写错的地方）

| 格式 | 导入 | 导出 |
|---|---|---|
| OBJ | `bpy.ops.wm.obj_import` | `bpy.ops.wm.obj_export` |
| glTF | `bpy.ops.import_scene.gltf` | `bpy.ops.export_scene.gltf` |
| FBX | `bpy.ops.wm.fbx_import`（4.5+） | `bpy.ops.export_scene.fbx` |
| USD | `bpy.ops.wm.usd_import` | `bpy.ops.wm.usd_export` |
| STL | `bpy.ops.wm.stl_import` | `bpy.ops.wm.stl_export` |
| PLY | `bpy.ops.wm.ply_import` | `bpy.ops.wm.ply_export` |
| Alembic | `bpy.ops.wm.alembic_import` | `bpy.ops.wm.alembic_export` |

- **没有** `wm.gltf2_*`（常见 AI 幻觉）；FBX 导出没有 `wm.fbx_export`；Collada 5.0 已移除。
- 全部导入导出算子**安全模式放行**（【实测】glTF/OBJ 闭环通过）。

## 2. glTF 导出（【实测】+ 踩坑实录）

```python
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.ops.export_scene.gltf(filepath="D:/out/model.glb",
                          export_format='GLB',      # GLB | GLTF_SEPARATE | GLTF_EMBEDDED
                          export_apply=True,        # 应用修改器（默认 False，务必显式！）
                          use_selection=True,
                          export_yup=True)          # Blender Z-up 自动转 glTF Y-up
```
【实测】三大坑（第三个来自爱弥斯实战事故，教训编号 BMCP-ERR-001）：
- **GN 实例化几何会被静默省略**：日志出现 `no primitives and will be omitted`，导出的 glb 是空壳。
  修法：GN 树末尾接 `GeometryNodeRealizeInstances`，或改用集合实例化。
- **修改器求值结果会爆开**：带 ARRAY/GN 的物体导 OBJ 后重导入得到 689 个分离对象。
  导出前想清楚：要"烘死"修改器就先 duplicate + modifier_apply；要干净几何就用原始网格。
- **重导入名高碰撞**：glTF 导出器把 **mesh 数据名当作 primitive 名**，重导入后的
  物体名/网格名与原场景高度同碰撞（爱弥斯案例两次导入各产生数百同名/近似名物体）。
- **导出必回读 + 身份差集清理（禁模式匹配）**：回读验证后清理导入残留，**只用
  before/after 身份差集**——导入前记下 `set(bpy.data.objects.keys())`，导入后差集
  即导入物名单，逐个按名删除；**任何名字模式匹配都可能与自有物体碰撞**
  （爱弥斯事故：`AMS_AMS_*` 模式清理误删自建 353 物体，见 08 分册 §5 与 12 分册 §7
  BMCP-ERR-001）。对账用"期望名单 vs 实际名单"程序化 diff，不靠计数推断。
- 材质映射【文献】：必须用 Principled BSDF（其他节点 PBR 属性不导出）；rough/metal 打包进
  metallicRoughness（G=rough, B=metal）；法线是 OpenGL 约定（PolyHaven 的 nor_gl 直接用）。

## 3. OBJ / USD 关键参数（【文献】5.2 签名）

```python
bpy.ops.wm.obj_export(filepath="D:/out/m.obj", export_selected_objects=False,
                      apply_modifiers=True, export_uv=True, export_normals=True,
                      forward_axis='NEGATIVE_Z', up_axis='Y')
bpy.ops.wm.obj_import(filepath="D:/in/m.obj", validate_meshes=True,
                      forward_axis='NEGATIVE_Z', up_axis='Y')
bpy.ops.wm.usd_export(filepath="D:/out/shot.usda", selected_objects_only=True,   # 参数名不叫 export_selected_objects
                      evaluation_mode='RENDER')
```

## 4. 保存 / 打开（安全模式放行，但对用户文件要克制）

```python
bpy.ops.wm.save_as_mainfile(filepath="D:/proj/out.blend", compress=False, copy=False)
bpy.ops.wm.save_mainfile()                        # 原地保存
bpy.ops.wm.open_mainfile(filepath="D:/proj/out.blend")
```
- filepath 必须**绝对路径**；Windows 路径用正斜杠 `"D:/x/y.blend"` 或 raw string
  `r"D:\x\y.blend"`——`"D:\temp"` 的 `\t` 是 TAB。
- 自动备份【文献】：同目录 `.blend1/.blend2`（越旧编号越大），`wm.open_mainfile` 可直接打开；
  崩溃恢复 `bpy.ops.wm.recover_auto_save`。
- **铁律重申**：没经用户明确同意绝不保存用户的文件；自己的实验产物存 %TEMP%。

## 5A. 被墙环境的资产获取通路（BMCP-ERR-008【实测·坦克建模】）

直连 Wikimedia/Commons 全链路 000（含真实 IP 直连，疑 SNI 阻断）时的实测解法：
1. 图像经 **wsrv.nl 图像代理**抓取；
2. curl 加 **`--ssl-no-revoke`**（本机 schannel CRL 检查离线时必需）；
3. 文件页用 **Special:FilePath 直链**先解析出真实文件 URL——重定向不被 wsrv 跟随；
4. webReader 类服务端可绕墙抓 Commons **页面**，但**拒绝带查询参数的 URL**（api.php 报
   "Please Enter the Correct URL Format"）——别把带参 API 塞给它。

**PolyHaven 集成未启用时的真实错误形态**【实测更正；机制按 F-132 真机再确证】：调用返回
`Unknown command type: search_polyhaven_assets`——这是 **addon 侧拒识命令**（server 侧
工具静态全量注册，开关不影响注册数；v1.x 曾误注"工具未注册"），**形似链路故障，勿误走
SKILL §6 恢复排障**；先让用户在侧栏勾选启用即可，**即时生效，无需重连**；引导开启的
提示文案只在 `get_polyhaven_status` 等状态类工具上返回（详见下文"集成使用规则"）。

## 6. 资产库五件套（MCP 工具直连）

### PolyHaven（免密钥，全 CC0）
`search_polyhaven_assets(asset_type='hdris'|'textures'|'models', categories=...)` →
`download_polyhaven_asset(asset_id, asset_type, resolution='1k'|'2k'|'4k', file_format=...)` →
HDRI 自动接 World；贴图用 `set_texture(object_name, texture_id)` 一键接 PBR。
贴图分辨率 jpg/png，模型 gltf/fbx【文献】。

### PolyPizza（免费 API key：poly.pizza/settings/api）
`search_polypizza_models(query, category, licence='CC0'|'CC-BY', animated=False)` →
`download_polypizza_model(model_id, normalize_size=True, target_size=1.0)`
**必须** normalize_size=True + 米制 target_size（Google Poly 遗产尺度混乱）。
CC-BY 的署名串写在对象自定义属性 `polypizza_attribution` 里，交付时带上。

### Sketchfab（免费 API token）
`search_sketchfab_models(query, downloadable=True)` → `get_sketchfab_model_preview(uid)` 看图 →
`download_sketchfab_model(uid)`。写实模型优先在这里找。

### Hyper3D Rodin（hyper3d.ai；面板有免费试用键）
`generate_hyper3d_model_via_text(text_prompt=...)` 或 `_via_images(...)` →
`poll_rodin_job_status(...)`（轮询）→ `import_generated_asset(name, ...)`。
免费试用键每日限量。

### Hunyuan3D（本地服务 localhost:8081 或腾讯云）
`generate_hunyuan3d_model(...)` → `poll_hunyuan_job_status(job_id)` →
`import_generated_asset_hunyuan(name, zip_file_url)`（优先 .glb）。

### 集成使用规则
- 集成开关在 Blender 侧栏面板（默认通道 **"Brickfly MCP for Blender"**，回退上游通道为
  "MCP for Blender"；两通道行为对齐——U-05）。**禁用态实测行为（F-132 勘误，v2.4.0）**：
  工具在 server 侧**静态全量注册**，开关不影响注册数；禁用时直接调用其检索/下载工具得到
  `Unknown command type: …`——**形似链路故障，勿误走 SKILL §6 恢复排障**；引导文本（告诉
  用户去勾选）只在 `get_polyhaven_status` / `get_polypizza_status` / `get_sketchfab_status` /
  `get_hyper3d_status` 上返回。正确处置 = SKILL §0 第 2 步先看 `get_addon_status` 的五库
  开关位。开关改动**即时生效，无需重连**（面板上"Restart the connection to Claude"字样
  已过时，见 SKILL §6）。
- 选型策略【文献】：写实模型 Sketchfab → PolyHaven；风格化 low-poly Poly Pizza → Sketchfab；
  环境光 PolyHaven HDRI；库里没有的自定义单体才用 Rodin/Hunyuan 生成；
  **不要**用生成式做整场景/地面/规则建筑。
- **检索实看义务（U-04，视觉工作流 14 分册 §5；F-113 补出路；F-133 按真机实测改写）**：
  search 结果的**缩略图/预览必须实看后再选择**——外观匹配是选择依据，名称/标签只是初筛。
  **通道事实（v2.4.0 真机实测，与上游 2.0.0 源码同构）**：五库中仅 Sketchfab 有回图工具
  （`get_sketchfab_model_preview`，需 API Key）；**PolyHaven search 返回的文本只含
  名称/ID/类型/分类/下载数，不含任何 URL**（server 格式化时丢弃 thumbnail_url，URL 从未
  到达模型），因此"把缩略图 URL 落盘后实看"**在 MCP 通道内不成立**（Blender 内 safe mode
  亦封网络与文件读取）。**可行路径**：先下载低分辨率资产、进场景渲染后实看再决定取舍；
  该路径也不可用时如实告知用户"当前无法实看资产外观"，按 △ 降级口径处理，
  **不得按名称/标签选完就声称已实看**（那正是"只是初筛"禁令所禁止的）。文本检索给出候选，
  视觉实看做出决策；多候选时并列对比后向用户说明选择理由。
- 所有下载/生成工具都可能超 30s：生成类务必用 poll 轮询拆步，不要一次等死。

### server 2.0（mcp-for-blender，v2.4.0 适配）
上游 server 于 2026-09-16 发布 2.0.0 并改名 `mcp-for-blender`（PyPI 旧名 `blender-mcp`
同版兼容）。与本册相关的事实：**工具 28 → 31**（计数口径=server.py `@mcp.tool(` 静态计数
或客户端 tools/list；F-135 勘误），新增 `describe_node_type`（节点类型
socket/属性 schema 查询）、`bpy_api_lookup`（RNA/API 签名查询）、`export_scene`（场景/
选中/命名对象导出 GLB/FBX）、`disable_telemetry`、`record_trajectory_feedback`；
**协议 5 → 7、内置 addon (1,6) → (1,7)**——旧 addon 在 2.0 server 下会报过期，须重装
（见 INSTALL）。**节点 schema/操作符参数/枚举值不确定时，先查 `describe_node_type` /
`bpy_api_lookup`，不要用 execute_blender_code 试错或凭记忆猜**——这两个工具是官方化的
"知识库查询"，回答的正是本 skill 知识库分册要人工沉淀的问题。Poly Pizza 检索行新增
licence 与三角形数（低模选型可一次完成）；~69% 素材为 CC-BY，导入时 server 会在对象上
写 `polypizza_attribution` 自定义属性，**交付引用素材时保留署名**。safe mode 为
**env 选入**（`BLENDER_MCP_SAFE_MODE=1` 开启；1.9.1 与 2.0.0 的 safe_mode.py 逐字节
相同——"自 2.0 起默认关闭"系归类失准，F-136 勘误；本部署与 11 分册示例均显式开启，
开启后 execute_blender_code 先过
校验器：禁 os/subprocess/网络/open 等）；server 默认开启匿名遥测，`DISABLE_TELEMETRY=true`
可关（或调 `disable_telemetry` 工具）。

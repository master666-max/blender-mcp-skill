# -*- coding: utf-8 -*-
"""brickfly_skeleton.py — 力大砖飞五段式骨架模板（安全模式兼容）

【适用范围·已裁定】凡新建/修改/删除场景数据的 execute_blender_code 一律走本骨架；
纯只读检查脚本豁免（仅要求第 5 段 report）。

五段式：①参数区 → ②幂等清理 → ③helper → ④建模 → ⑤report
安全模式合规要点：只 import bpy/bmesh/mathutils/json/math；无 lambda/class/别名 import；
无动态 getattr/dunder；无"方法赋短变量再调用"；无裸 next()；print 只输出 json（默认 ASCII 转义）。

用法：把本文件全文粘贴进 execute_blender_code，改 ①参数区 与 ④建模段。
本模板自带一个最小示例（PREFIX 隔离的斜角立方体+材质），可直接连跑验证幂等。
"""
import bpy
import bmesh
import json
import math

# ============ ① 参数区（改这里；PRD 卡片确认后由此实例化） ============
PREFIX = "BF_"                 # 本任务命名前缀：清理/识别只动 PREFIX_*
STAGE = "GEO"                  # 当前阶段：GEO/MAT/CAM/LIT（12 分册 §2 单向依赖）
UPSTREAM_DIGEST = ""           # 上游 report digest；GEO 阶段留空。重跑上游后必须重跑下游（BMCP-ERR-006）
DETAIL_LEVEL = "standard"      # 13 分册 §1（v2.1）：细节深度上限——draft 细节止于阶段2 / standard 到阶段4 / fine 全阶段+加密；阶段5清理与阶段6交付恒走
USER_WORLD_NAME = ""           # 隔离前记录的用户原 world 名；本任务没动过 world 就留空（BMCP-ERR-005）
USER_CAMERA_NAME = ""          # 隔离前记录的用户原相机名；同上
PARAMS = {
    "cube_size": 1.0,          # 米
    "bevel_width": 0.03,
    "base_color": (0.65, 0.3, 0.1, 1.0),
    "metallic": 0.0,
    "roughness": 0.45,
    "location": (0.0, 0.0, 0.5),
}
# 教训引用区：本段代码规避了哪些历史坑（无则留空）。例：# BMCP-ERR-001 ...
LESSONS = []


# ============ ② 幂等清理（只动 PREFIX_*，跑十遍状态一致） ============
def reset_prefix(prefix):
    doomed = [o for o in bpy.data.objects if o.name.startswith(prefix)]
    removed = len(doomed)
    for ob in doomed:
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)
    for mname in [m.name for m in bpy.data.materials if m.name.startswith(prefix)]:
        bpy.data.materials.remove(bpy.data.materials[mname])
    return removed


# ============ ③ helper（跨版本/跨语言 安全查找与赋值） ============
def find_node(nodes, node_type):
    """按 node.type 查找节点——中文 UI 下默认名是本地化的（原理化 BSDF），禁止按英文名 get。"""
    for n in nodes:
        if n.type == node_type:
            return n
    return None


def set_input(node, candidates, value):
    """跨版本 socket 赋值：候选名列表依序探测（对抗 4.0/5.0 大规模改名）。
    返回实际命中的 socket 名；全不中返回 None（调用方记入 report 的 warnings）。"""
    for name in candidates:
        sock = node.inputs.get(name)
        if sock is not None:
            sock.default_value = value
            return name
    return None


def count_tris(mesh):
    """基网格三角面数（导出统计口径）。"""
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def stage_digest():
    """本阶段参数指纹（白名单无 hashlib，用排序 JSON 串当 digest）。"""
    return STAGE + ":" + json.dumps(PARAMS, sort_keys=True)


def check_stage_stamps(objects):
    """BMCP-ERR-006：下游阶段启动时校验上游依赖戳——不一致=上游已变，必须重跑下游。"""
    if STAGE == "GEO":
        return []
    out = []
    for ob in objects:
        if ob.get("bf_stage_digest", "") != UPSTREAM_DIGEST:
            out.append("stale_stage_stamp:" + ob.name)
    return out


def assert_safe_to_purge():
    """BMCP-ERR-005 机器守卫（V-02）：调 orphans_purge 前必须先过这一关。
    隔离窗口内（scene.world/camera 仍是自建物、没还原成 USER_* 记录的用户原值）会抛错拦截。
    本任务没动过 world/camera 时（USER_* 留空）直接放行。"""
    problems = []
    if USER_WORLD_NAME:
        w = bpy.context.scene.world
        got = w.name if w is not None else "None"
        if got != USER_WORLD_NAME:
            problems.append("scene.world=" + got + " != 用户原值 " + USER_WORLD_NAME)
    if USER_CAMERA_NAME:
        c = bpy.context.scene.camera
        got = c.name if c is not None else "None"
        if got != USER_CAMERA_NAME:
            problems.append("scene.camera=" + got + " != 用户原值 " + USER_CAMERA_NAME)
    if problems:
        raise RuntimeError(
            "PURGE_BLOCKED（BMCP-ERR-005）：" + "; ".join(problems)
            + "——先还原用户 world/camera 再 orphans_purge（03 分册 §6.3）")


def make_report(objects, warnings, err=None):
    """⑤ report 组装：场景向模型世界的只读投影（C5）。字段精简，float 保留 4 位。"""
    items = []
    for ob in objects:
        items.append({
            "name": ob.name,
            "loc": [round(v, 4) for v in ob.location],
            "dims": [round(v, 4) for v in ob.dimensions],
            "tris": count_tris(ob.data) if ob.type == 'MESH' else 0,
        })
    return {"objects": items, "warnings": warnings, "err": err}


# ============ ④ 建模段（示例：斜角立方体 + Principled 材质） ============
def build(params):
    warnings = []
    reset_prefix(PREFIX)

    bpy.ops.mesh.primitive_cube_add(size=params["cube_size"], location=params["location"])
    cube = bpy.context.active_object
    cube.name = PREFIX + "Cube"

    bev = cube.modifiers.new("Bevel", 'BEVEL')
    bev.width = params["bevel_width"]
    bev.segments = 3
    bev.limit_method = 'ANGLE'

    mat = bpy.data.materials.new(PREFIX + "Mat")
    bsdf = find_node(mat.node_tree.nodes, 'BSDF_PRINCIPLED')
    if bsdf is None:
        warnings.append("no principled node in new material")
    else:
        hit = set_input(bsdf, ["Base Color"], params["base_color"])
        if hit is None:
            warnings.append("Base Color socket missing")
        set_input(bsdf, ["Metallic"], params["metallic"])
        set_input(bsdf, ["Roughness"], params["roughness"])
    cube.data.materials.append(mat)
    return [cube], warnings


# ============ ⑤ 执行与 report（唯一出口） ============
objects, warnings = build(PARAMS)
for ob in objects:
    ob["bf_stage_digest"] = stage_digest()   # 阶段依赖戳：下游按 UPSTREAM_DIGEST 校验
warnings = warnings + check_stage_stamps(objects)
report = make_report(objects, warnings)
report["stage"] = STAGE
if LESSONS:
    report["lessons_applied"] = LESSONS
print(json.dumps(report))

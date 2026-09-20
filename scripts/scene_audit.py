"""scene_audit.py — 网格体检/面数统计（安全模式兼容，MCP 与无头双用）

用法A（MCP）: 读出全文粘贴进 execute_blender_code，改 TARGET 列表。
用法B（无头）: blender -b file.blend --python scene_audit.py
输出: 每物体几何体检 + 全场景三角面合计（JSON）。
"""
import bpy
import bmesh
import json

TARGET_PREFIX = ""   # 空 = 全场景；或填前缀如 "TUT_"
INCLUDE_HIDDEN = False


def audit_object(obj, depsgraph):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    r = {
        "name": obj.name,
        "tris": sum(len(p.vertices) - 2 for p in me.polygons),
        "verts": len(me.vertices),
        "non_manifold_edges": 0,
        "boundary_edges": 0,
        "wire_edges": 0,
        "flipped_winding_edges": 0,
        "zero_area_faces": 0,
        "modified": len(obj.modifiers) > 0,
    }
    for e in bm.edges:
        if e.is_boundary:
            r["boundary_edges"] += 1
        elif not e.is_manifold:
            if e.is_wire:
                r["wire_edges"] += 1
            else:
                r["non_manifold_edges"] += 1
        elif not e.is_contiguous:
            r["flipped_winding_edges"] += 1
    for f in bm.faces:
        if f.calc_area() <= 1e-12:
            r["zero_area_faces"] += 1
    bm.free()

    loc, rot, scl = obj.matrix_world.decompose()
    r["scale_not_applied"] = any(abs(s - 1.0) > 1e-6 for s in scl)
    r["negative_scale"] = obj.matrix_world.determinant() < 0.0

    # 含修改器的求值面数（只在有修改器时算，省时间）
    if r["modified"]:
        ev = obj.evaluated_get(depsgraph).to_mesh()
        r["tris_evaluated"] = sum(len(p.vertices) - 2 for p in ev.polygons)
        obj.evaluated_get(depsgraph).to_mesh_clear()
    return r


def main():
    dg = bpy.context.evaluated_depsgraph_get()
    report = {"objects": [], "total_tris": 0, "problems": [], "skipped_hidden": 0}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if not INCLUDE_HIDDEN and obj.hide_render:
            report["skipped_hidden"] += 1   # 渲染隔离窗口内的静默盲区要显式可见（BMCP-ERR-005 同源）
            continue
        if TARGET_PREFIX and not obj.name.startswith(TARGET_PREFIX):
            continue
        row = audit_object(obj, dg)
        report["objects"].append(row)
        report["total_tris"] += row.get("tris_evaluated", row["tris"])
        if row["non_manifold_edges"] or row["flipped_winding_edges"]:
            report["problems"].append({"name": row["name"],
                                       "non_manifold": row["non_manifold_edges"],
                                       "flipped": row["flipped_winding_edges"]})
        if row["negative_scale"]:
            report["problems"].append({"name": row["name"], "negative_scale": True})
    report["object_count"] = len(report["objects"])
    print(json.dumps(report))


main()

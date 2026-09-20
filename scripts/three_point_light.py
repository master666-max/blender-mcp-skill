"""three_point_light.py — 三点布光 + 相机 + 渲染设置一条龙（安全模式兼容双用）

用法A（MCP）: 粘贴进 execute_blender_code，改 TARGET 与 CAM_POS。
用法B（无头）: blender -b scene.blend --python three_point_light.py -- --render out.png
              （透传参数以 "--" 开头的原始 argv 处理，兼容无 sys 环境）
输出: JSON（灯/相机/渲染配置回执）。
"""
import bpy
import json
import mathutils

TARGET_NAME = ""                 # 空 = 用场景原点；填物体名则自动取其包围盒中心
CAM_POS = (7.0, -7.0, 4.0)       # 50mm 常规机位
KEY_E = 150.0                    # Area 主光 W
FILL_E = 40.0                    # 补光 = 主光 1/4 左右
RIM_E = 100.0                    # 轮廓光 0.7~1.5x 主光
RENDER_STILL = ""                # 非空则渲染落盘到该路径（如 C:/tmp/out.png）
PREFIX = "RIG_"


def aim_location():
    if TARGET_NAME:
        obj = bpy.data.objects[TARGET_NAME]
        bb = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        cx = sum(v.x for v in bb) / 8.0
        cy = sum(v.y for v in bb) / 8.0
        cz = sum(v.z for v in bb) / 8.0
        return cx, cy, cz
    return 0.0, 0.0, 1.0


def clear_old():
    for n in (PREFIX + "Key", PREFIX + "Fill", PREFIX + "Rim", PREFIX + "Cam", PREFIX + "Aim"):
        o = bpy.data.objects.get(n)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)


def make_light(name, ltype, energy, loc, size, color):
    ld = bpy.data.lights.new(name, type=ltype)
    ld.energy = energy
    ld.shape = 'SQUARE'
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    return lo


def main():
    import mathutils
    clear_old()
    aim_at = aim_location()

    make_light(PREFIX + "Key", 'AREA', KEY_E, (aim_at[0] + 4, aim_at[1] - 4, aim_at[2] + 4), 2.0, (1.0, 0.95, 0.88))
    make_light(PREFIX + "Fill", 'AREA', FILL_E, (aim_at[0] - 4, aim_at[1] - 3, aim_at[2] + 2), 3.0, (0.85, 0.9, 1.0))
    make_light(PREFIX + "Rim", 'AREA', RIM_E, (aim_at[0], aim_at[1] + 5, aim_at[2] + 3), 1.0, (1.0, 1.0, 1.0))

    aim = bpy.data.objects.new(PREFIX + "Aim", None)
    bpy.context.scene.collection.objects.link(aim)
    aim.location = aim_at

    cam_data = bpy.data.cameras.new(PREFIX + "Cam")
    cam_data.lens = 50.0
    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = aim
    cam_data.dof.aperture_fstop = 2.8
    cam = bpy.data.objects.new(PREFIX + "Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = CAM_POS
    ctc = cam.constraints.new('TRACK_TO')
    ctc.target = aim
    ctc.track_axis = 'TRACK_NEGATIVE_Z'
    ctc.up_axis = 'UP_Y'
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    engines = ('CYCLES', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT')
    engine_used = scene.render.engine
    for eng in engines:
        try:
            scene.render.engine = eng
            engine_used = eng
            break
        except TypeError:
            continue

    result = {
        "lights": [PREFIX + "Key", PREFIX + "Fill", PREFIX + "Rim"],
        "camera": PREFIX + "Cam",
        "aim": list(aim_at),
        "engine": engine_used,
    }

    if RENDER_STILL:
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = RENDER_STILL
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(RENDER_STILL)   # 回读验证落盘
        result["rendered_size"] = list(img.size)
        bpy.data.images.remove(img)
        result["rendered_file"] = RENDER_STILL

    print(json.dumps(result))


main()

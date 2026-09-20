"""render_check.py — 渲染出图 + 回读验证（安全模式兼容双用）

用法A（MCP）: 粘贴进 execute_blender_code，改 OUT_PATH / SAMPLES。
用法B（无头）: blender -b scene.blend --python render_check.py
输出: JSON（引擎/分辨率/落盘尺寸回执）。load 失败会抛异常 = 文件没写出来。
"""
import bpy
import json
import tempfile

OUT_PATH = tempfile.gettempdir() + "/blender_mcp_render.png"
WIDTH = 1280
HEIGHT = 720
SAMPLES = 16          # EEVEE: taa_render_samples；Cycles: samples（冒烟 16~32，出图 256+）
ENGINE = ""           # 空 = 保持当前；'BLENDER_EEVEE' / 'CYCLES'


def main():
    scene = bpy.context.scene
    engine_used = scene.render.engine
    if ENGINE:
        for eng in (ENGINE, 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'CYCLES'):
            try:
                scene.render.engine = eng
                engine_used = eng
                break
            except TypeError:
                continue

    if engine_used == 'CYCLES':
        scene.cycles.samples = SAMPLES
        scene.cycles.use_denoising = True
    else:
        try:
            scene.eevee.taa_render_samples = SAMPLES   # 5.x 属性名（4.2~4.5 为 _NEXT 同名）
        except AttributeError:
            pass

    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = OUT_PATH

    if scene.camera is None:
        raise RuntimeError("scene.camera is None — 先建相机并赋值，否则渲染报 No camera found")

    bpy.ops.render.render(write_still=True)

    img = bpy.data.images.load(OUT_PATH)               # 回读 = 落盘验证（安全模式禁 open()）
    size = list(img.size)
    bpy.data.images.remove(img)

    print(json.dumps({
        "engine": engine_used,
        "resolution": [WIDTH, HEIGHT],
        "file": OUT_PATH,
        "file_size_px": size,
    }))


main()

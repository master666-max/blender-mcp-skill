# 10 无头批处理 / CLI / CI（不走 MCP 的另一条腿）

适用：批量转换、渲染农场、回归测试、没有 GUI 的服务器。MCP 实时操控见其他分册。

## 1. CLI 速查（【文献】5.2 LTS 手册）

```bash
# 黄金模板（可复现 + 异常非零退出 + 参数透传）
blender --background --factory-startup --disable-crash-handler \
        --python-exit-code 1 --python build.py -- --input model.glb --quality high

# 渲染
blender -b scene.blend -o //renders/frame_#### -F PNG -f 1        # 单帧
blender -b scene.blend -s 1 -e 240 -j 2 -a                        # 动画 1..240 步长2
blender -b scene.blend -E CYCLES -f 1                             # 指定引擎
```
- `--factory-startup`：跳过用户 startup.blend/偏好/插件——**可复现性的关键**，CI 必加；
  要插件用 `--addons id1,id2` 显式声明。
- `--python-exit-code 1`：**默认脚本抛异常退出码是 0**！CI 必设。
- `--` 之后的参数透传给脚本：`sys.argv[sys.argv.index("--")+1:]`。
- 单行内联：`--python-expr "import bpy; print(bpy.app.version_string)"`。
- 日志：`--log "*render*" --log-level 2`；`--debug-python`；`--debug-cycles`。
- `--disable-autoexec` 是默认（安全），带内嵌脚本的 .blend 需显式 `--enable-autoexec`。

## 2. pip 的 bpy 模块（进程内 Blender）

```bash
pip install bpy==5.2.1     # 严格绑定 CPython 3.13！（4.x 全系绑 3.11）
```
```python
import bpy                 # 即进程内完整 bpy
bpy.ops.wm.read_factory_settings(use_empty=True)   # 每个任务的隔离沙盒
bpy.ops.mesh.primitive_monkey_add()
```
- 平台轮【文献】：win_amd64 / win_arm64 / manylinux / macos arm64（**macOS Intel 已停发**）。
- 与 `blender -b` 差异：venv 里的 Python（可与 numpy/requests 共存）、启动快、但数据文件
  （OCIO 配置等）需按 wheel 内路径补齐。
- 已知坑【文献】：Windows+RTX 下模块模式 GPU 设备选择可能被忽略回退 CPU；
  `read_factory_settings(use_empty=True)` 做测试隔离是标准姿势。

## 3. 无头渲染引擎行为

| 引擎 | 无 GPU 时 | 说明 |
|---|---|---|
| Cycles CPU | ✅ 开箱即用 | CI 冒烟首选 |
| Cycles GPU | ✅ 纯计算无需显示器 | 需在脚本里显式启用设备（headless 不读用户偏好） |
| EEVEE | 分两档【实测修正】：**有 GPU 的桌面机 `--background` 直接可用**（Windows 实测 EEVEE 640×360 6.5~33.7s 一次成功非黑图）；**真·无 GPU 的 CI 容器**才黑图/失败（解法 Mesa llvmpipe/lavapipe 软渲） | 4.2+ 起完全 GPU 化；判断依据=机器有没有可用 GPU 驱动，不是"无头"本身 |
| Workbench | ❌ 同 EEVEE | 同待遇 |

软渲配方【文献】：`LIBGL_ALWAYS_SOFTWARE=1 blender -b ... -E BLENDER_EEVEE ...` 或
`xvfb-run -a blender -b ...`；4.5+ Vulkan 路线 `--gpu-backend vulkan` + lavapipe。慢是预期，
只当正确性信号，不当性能信号。

## 4. CI 断言样例（pytest + bpy wheel）

```python
import bpy, pathlib

def test_cube_and_render(tmp_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add()
    assert any(o.type == "MESH" for o in bpy.data.objects)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"          # CPU 无头可渲
    sc.cycles.samples = 16
    sc.render.filepath = str(tmp_path / "out.png")
    bpy.ops.render.render(write_still=True)
    assert (tmp_path / "out.png").stat().st_size > 10_000   # 存在且非全黑截断
```
- 测试框架是 **pytest-blender**（mondeja）；PyPI 上**不存在** pytest-bpy，别装。
- 渲染回归用 imagehash 感知哈希（average_hash/phash + 汉明距离阈值）对比。

## 5. Docker 骨架【文献】

```dockerfile
# CPU 冒烟镜像（与 bpy 5.2 绑定 Python 3.13）
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgl1 libegl1 libxrender1 libxi6 libxkbcommon0 libxfixes3 libxxf86vm1 \
      libgomp1 libgl1-mesa-dri libegl-mesa0 mesa-vulkan-drivers xvfb \
    && rm -rf /var/lib/apt/lists/*
ENV LIBGL_ALWAYS_SOFTWARE=1
RUN pip install --no-cache-dir bpy==5.2.1
WORKDIR /work
```
GPU 渲染镜像：官方 tarball（download.blender.org）+ nvidia/cuda 基础镜像 +
`docker run --gpus all`；Cycles kernel 用缓存目录做镜像层避免首渲编译超时。
**不要用 snap/flatpak 版**跑 CI（沙箱干扰环境变量与路径）。

## 6. 看门狗包装【文献】

```bash
timeout --kill-after=10s 600 \
  blender --background --factory-startup --disable-crash-handler \
          --python-exit-code 1 --python build.py 2>&1 | tee -a run.log
# 退出码 124/137 = 超时被杀（模态操作挂起的典型表现）
```
常驻 agent 进程模式：`bpy` wheel 常驻 + 每任务 `read_factory_settings(use_empty=True)`
复位 + psutil 监控 RSS 回收，避免每步 1~2s 冷启动。

## 7. 两条路径怎么选

| 场景 | 用哪条 |
|---|---|
| 交互式建模/看效果/用户在场 | MCP（mcp__blender__*） |
| 批量转换/回归测试/服务器/无人值守 | CLI 或 bpy wheel |
| 同一段代码 | 保持安全模式兼容（只 import 白名单模块），两条路都能跑 |

## 8. `--python` 脚本路径纪律（F-144 实录）

**路径含全角字符（！、「」等非 ASCII 标点）时 Blender 解析 `--python` 参数会报
"could not be opened: No such file or directory"**——文件明明存在。中文 Windows 的
目录名（含「！」类全角标点）极易踩中。**规避：把脚本与日志放到纯 ASCII 路径**
（如 `C:\temp_verify\`）再传给 `--python`；bpy wheel 路线不受此限——路径由
Python 自己解析，不经过 Blender 的参数层。

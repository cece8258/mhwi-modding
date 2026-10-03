# -*- coding: utf-8 -*-
"""X8_面料亮度定标.py（第4版）—— 配方定标：用 **UV 实际覆盖区** 口径量贴图亮度，并算过曝占比。
判据（沿用 第3版 已验收的做法）：
  等效发光 = fEmissiveMapFactor × 面料区亮度 ；目标 ≈ 2.08~2.19（用户认可过的两档）
  "面料区" = 该贴图**被 UV 三角形真正覆盖**的像素（不是全图均值、也不是非黑像素）
用法: blender -b _p_work.blend --python X8_面料亮度定标.py -- <输出txt>
"""

# ============================================================================
# 【公开版】所有**路径**都集中在同目录的 `_config.py`（先改那一个文件就行）。
# 本仓库**只含代码**，不含任何游戏文件 / 素材文件 / 他人模组文件 —— 见 NOTICE.md。
# ============================================================================
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
try:
    from _config import *          # noqa: F401,F403
except ImportError as _e:
    raise SystemExit("缺 _config.py（应与本脚本同目录）：%s" % _e)
# ============================================================================


import bpy, os, sys
import numpy as np

OUT = sys.argv[sys.argv.index("--") + 1]
PK = BAKED_DIR
L = []


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


# (材质名, 显示名, 烘焙png, 允许的部位关键字)
# ★ 本版的坑：**同一个材质名在不同部位指向不同贴图** ——
#   `__5` 在 body=UV1、在 arm=UV1（同图）；`__6` 在 body=UV2、在 leg=UV2（同图）；
#   `__9` 在 body=FUR、在 wst=FUR；`__10` 在 body/arm/leg 都是 METAL。
#   若不带部位过滤，掩码会把两套不相干的 UV 并起来 ⇒ 读数无意义。
JOBS = [
    ("Ch_Standard_Mt__5",  "UV1",   "UV1.png",   ("body", "arm")),
    ("Ch_Standard_Mt__6",  "UV2",   "UV2.png",   ("body", "leg")),
    ("Ch_Standard_Mt__7",  "BAG",   "BAG.png",   ("body",)),
    ("Ch_Standard_Mt__8",  "STOCK", "STOCK.png", ("leg",)),
    ("Ch_Standard_Mt__9",  "FUR",   "FUR.png",   ("body", "wst")),
    ("Ch_Standard_Mt__10", "METAL", "METAL.png", ("body", "arm", "leg")),
    ("Ch_Standard_Mt__11", "GLOVE", "GLOVE.png", ("arm",)),
    ("Ch_Standard_Mt__12", "HAIR",  "HAIR.png",  ("body",)),
    ("Ch_Standard_Mt__13", "ACC",   "ACC.png",   ("body",)),
]
# ★ 定标用的 fEmissiveMapFactor（与 `Y3_材质指向.py` 的 CB_FIX 保持一致；命令行 emi= 可覆盖）
EMI = 2.00
for _a in sys.argv:
    if isinstance(_a, str) and _a.startswith("emi="):
        EMI = float(_a.split("=", 1)[1])
RES = 1024
PARTS = ("body", "arm", "wst", "leg")


def mask_of(matname, parts=None):
    parts = parts or PARTS
    m = np.zeros((RES, RES), bool)
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        mats = [x.name if x else None for x in o.data.materials]
        if matname not in mats:
            continue
        if not any(pp in c.name.lower() for pp in parts for c in o.users_collection):
            continue
        uvl = o.data.uv_layers
        if not uvl:
            continue
        uvd = uvl[0].data
        lo = 0
        for p in o.data.polygons:
            n = len(p.vertices)
            if n < 3:
                lo += n
                continue
            p0 = np.array([(float(uvd[lo + k].uv[0]), float(uvd[lo + k].uv[1]))
                           for k in range(n)], float)
            lo += n
            x0 = np.floor(p0[:, 0] * RES).astype(int)
            y0 = np.floor(p0[:, 1] * RES).astype(int)
            xmin, xmax = max(0, x0.min()), min(RES - 1, x0.max())
            ymin, ymax = max(0, y0.min()), min(RES - 1, y0.max())
            if xmax < xmin or ymax < ymin:
                continue
            xs = (np.arange(xmin, xmax + 1) + 0.5) / RES
            ys = (np.arange(ymin, ymax + 1) + 0.5) / RES
            X, Y = np.meshgrid(xs, ys)
            d = np.zeros_like(X)
            for k in range(n):
                a, b = p0[k], p0[(k + 1) % n]
                d = d + (X - a[0]) * (b[1] - a[1]) - (Y - a[1]) * (b[0] - a[0])
            # ★ 按**每个三角形自己的有符号面积**决定判定方向 —— UV 岛有镜像的，
            #   用固定符号会整片漏掉镜像岛（skill 实测：blond 74%、Body_Base 26% 负面积）
            s2 = 0.0
            for k in range(n):
                a, b = p0[k], p0[(k + 1) % n]
                s2 += a[0] * b[1] - a[1] * b[0]
            inside = (d * s2) < 0
            m[ymin:ymax + 1, xmin:xmax + 1] |= inside
    return m


w("### 覆盖区亮度定标（UV 光栅化 %d² 掩码；口径 = 掩码内像素）" % RES)
w("    目标：等效发光 ≈ 2.08~2.19（用户认可过 v1 军装 4.0×0.52 / 花瓣裙 0.93×2.35）")
w("")
w("    %-24s %-14s %8s %9s %9s %9s %11s %11s" %
  ("材质", "贴图", "覆盖px", "覆盖率", "均值", "p90", "×%.2f过曝" % EMI, "等效发光"))
for mat, tex, png, pf in JOBS:
    p = os.path.join(PK, png)
    if not os.path.exists(p):
        w("   !! 缺 %s" % p)
        continue
    img = bpy.data.images.load(p)
    img.colorspace_settings.name = "Non-Color"     # 读原始字节，不做色彩管理
    px = np.array(img.pixels[:], float).reshape(img.size[1], img.size[0], 4)
    bpy.data.images.remove(img)
    rgb = px[..., :3][::-1]                        # Blender 行序上下翻转
    m = mask_of(mat, pf)
    n = int(m.sum())
    if n == 0:
        w("   %-24s %-14s 掩码为空" % (mat, tex))
        continue
    # 掩码是 RES²，贴图可能更大（4096²）或更小（纯色 64²）⇒ 统一到贴图尺寸
    H, W = rgb.shape[0], rgb.shape[1]
    k = max(1, H // RES)
    if k > 1:
        m = np.repeat(np.repeat(m, k, axis=0), k, axis=1)
        m = m[:H, :W]
    if H < RES:
        # ★ 贴图比掩码小（纯色 64²）⇒ 按块 OR 把掩码缩到贴图尺寸（一个贴图像素被任何 UV 覆盖即算覆盖）
        f = max(1, RES // H)
        m = m[:H * f, :W * f].reshape(H, f, W, f).any(axis=(1, 3))
    while m.shape[0] < H or m.shape[1] < W:
        m = np.pad(m, ((0, max(0, H - m.shape[0])), (0, max(0, W - m.shape[1]))), mode="edge")
    bright = rgb[m].mean(axis=1)
    w("   %-24s %-14s %8d %8.1f%% %9.4f %9.4f %10.1f%% %11.3f" %
      (mat + ("[%s]" % ",".join(pf) if pf else ""), tex, n, 100.0 * n / (RES * RES),
       bright.mean(), np.percentile(bright, 90),
       100.0 * float(np.mean(bright * EMI >= 1.0)), bright.mean() * EMI))
w("")
w("### 说明")
w("  · 等效发光 = fEmissiveMapFactor(%.2f) × 覆盖区均值亮度；过曝 = 乘 %.2f 后 >=1.0 的像素占比" %
  (EMI, EMI))
w("  · 过曝占比高 ⇒ 花纹会被乘法压平；低 ⇒ 花纹保留")
w("WROTE " + OUT)
print("DONE")

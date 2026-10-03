# -*- coding: utf-8 -*-
"""Y2b_渔网投影UV.py —— 给丝袜做「腿皮投影」用：算出 Stocking 每个**面角(loop)** 在
`Body_base` 表面上对应的 **UV**（供 `Y2_贴图烘焙与生成.py` 采 `Body_Base.png`）。

为什么要这一步（用户 2026-10-03 实机反馈："图一是本套_有描边，图二是…_白渔网，显然整体变白了"）：
  第一版把渔网的**网眼**填成"身体贴图不透明区的**中位色** (252,228,222)"——那是接近纯白的肤色，
  而实际腿在游戏里被光照与贴图明暗压暗 ⇒ 拿一块平的亮色盖上去，**整条腿看起来发白**。
  ⇒ 改成**按位置投影**：网眼里放"这条腿在那一处的真实颜色"，腿的观感就不会变。
  ★ 因为丝袜的法线 ≈ 腿皮的法线、光照也一致 ⇒ 只要底色对，观感就与"真透明"几乎一样。

做法（与 skill 的"逐骨/逐面签对拍"同一路数：最近面 + 重心插值）：
  · 用 `_X3_preview.json` 里 `Stocking` 的**世界坐标**（预览坐标）在 `Body_base` 的 BVH 上找最近面；
  · 该面的三个面角 UV 按重心坐标插值 ⇒ 得到"投影后的 UV"；
  · 写成 `_texwork/STOCK_proj_uv.npy`（(n_loops, 2)，float32），Y2 侧再光栅化 + 采样。

★ 必须在**预览坐标**里做（两个网格都在 `_X3_preview.json` 里，同空间、免配准）。
用法: blender -b --python Y2b_渔网投影UV.py -- <_X3_preview.json> <输出.npy>
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


import bpy, os, sys, json
import numpy as np
from mathutils.bvhtree import BVHTree

argv = sys.argv
args = argv[argv.index("--") + 1:]
J, OUT = args[0], args[1]
LOG = OUT.replace(".npy", ".txt")
L = []


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(LOG, "w", encoding="utf-8").write("\n".join(L))


pre = json.load(open(J, encoding="utf-8"))
objs = pre["objs"]
src = objs["Stocking"]
body = objs["Body_base"]
w("### 源：Stocking %d 顶点 / %d 面（%d 个面角）；Body_base %d 顶点 / %d 面" %
  (src["verts"], len(src["polys"]), len(src["uv"]), body["verts"], len(body["polys"])))

SW = np.array(src["world"], float)
BW = np.array(body["world"], float)
BP = [tuple(p) for p in body["polys"]]
BU = body["uv"]
# 面角起始索引（面按顺序排列）
BSTART = np.zeros(len(BP), int)
_acc = 0
for i, p in enumerate(BP):
    BSTART[i] = _acc
    _acc += len(p)
w("    Body_base 面角 %d（JSON 里的 uv 条数 %d ⇒ %s）" %
  (_acc, len(BU), "一致 ✓" if _acc == len(BU) else "!! 不一致"))

bt = BVHTree.FromPolygons([tuple(q) for q in BW], BP)

n_loop = len(src["uv"])
proj = np.zeros((n_loop, 2), np.float32)
ok = 0
miss = 0
dists = []
li = 0
for pi, p in enumerate(src["polys"]):
    for k, vi in enumerate(p):
        q = SW[vi]
        loc, nrm, fi, dist = bt.find_nearest(tuple(q))
        if fi is None or fi >= len(BP):
            miss += 1
            proj[li] = (0.0, 0.0)
            li += 1
            continue
        tri = BP[fi]
        A = BW[tri[0]]; B = BW[tri[1]]; C = BW[tri[2]]
        v0, v1, v2 = B - A, C - A, np.array(q) - A
        d00 = float(v0 @ v0); d01 = float(v0 @ v1); d11 = float(v1 @ v1)
        d20 = float(v2 @ v0); d21 = float(v2 @ v1)
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-20:
            bc = (1.0, 0.0, 0.0)
        else:
            vv = (d11 * d20 - d01 * d21) / den
            ww = (d00 * d21 - d01 * d20) / den
            vv = min(max(vv, 0.0), 1.0); ww = min(max(ww, 0.0), 1.0)
            if vv + ww > 1.0:
                s = vv + ww; vv /= s; ww /= s
            bc = (1.0 - vv - ww, vv, ww)
        bs = BSTART[fi]
        u0 = BU[bs]; u1 = BU[bs + 1]; u2 = BU[bs + 2]
        proj[li] = (bc[0] * u0[0] + bc[1] * u1[0] + bc[2] * u2[0],
                    bc[0] * u0[1] + bc[1] * u1[1] + bc[2] * u2[1])
        ok += 1
        dists.append(float(dist))
        li += 1

d = np.array(dists, float) if dists else np.zeros(1)
w("   投影成功 %d / 失败 %d；到身体表面的距离：中位 %.4f m，p95 %.4f m，max %.4f m" %
  (ok, miss, float(np.median(d)), float(np.percentile(d, 95)), float(d.max())))
w("   （距离 = 丝袜顶点到最近腿皮的远近，正常应是 mm~cm 级；最近面 ⇒ 不会跨到另一条腿）")
np.save(OUT, proj)
w("WROTE " + OUT)
print("DONE")

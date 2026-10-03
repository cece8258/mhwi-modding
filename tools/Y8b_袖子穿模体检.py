# -*- coding: utf-8 -*-
"""Y8b_袖子穿模体检.py —— 只读（不保存）。**v4 专项**（用户点名的风险）：
去手套之后，袖子 `BH_Arm` 本身就是"最后一道"—— 它沿手指轴伸到 x=0.5286（工作坐标 ≈0.729），
而 `Hand.L` 在 0.4411、`Little Distal.L` 在 0.5287 ⇒ 几乎包到指尖。

量三件事：
 ① **静止**：袖子每个顶点到身体(`Body_base`)的**有符号距离**（正=在体外）—— 按主导骨分组
 ② **逐指**："袖子 ↔ 指皮"的距离分布（判据：min < −2mm 才需要处理）
 ③ **摆姿势**：把每根指的 Proximal/Intermediate 各弯 45°，用**求值网格**复量 ①②
    —— 这是 skill 反复强调的"判据必须能覆盖争议区域 + 摆姿势复量"。
  ★ 预期（写在判据里，用来区分假设）：`Z32` 已把袖子逐顶点对齐到皮肤权重
    （L1 差 中位/p90 **0.494/1.544 → 0.000/0.000**）⇒ 袖子与皮肤**同权重、同形变**
    ⇒ 弯曲时**相对错动应 ≈ 0** ⇒ 穿入数不该明显变差。若明显变差 ⇒ 说明"逐顶点对齐"没覆盖到指尖。

用法: blender -b _p_work.blend --python Y8b_袖子穿模体检.py -- <输出txt>
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
from mathutils.bvhtree import BVHTree

OUT = sys.argv[sys.argv.index("--") + 1]
L = []


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


SLEEVE = "BH_Arm"
SKIN = "Body_base"
ARMS = {"arm": "f_arm040_0010 Armature", "body": "f_body040_0010 Armature",
        "leg": "f_leg040_0010 Armature", "wst": "f_wst040_0010 Armature"}
FING = [(31, 34, 41, 44), (48, 51, 58, 61)]        # 每侧的 Thumb/Index/Ring/Little Proximal 号
FING_MID = [(32, 35, 42, 45), (49, 52, 59, 62)]


def ev_co(o):
    """求值网格的世界坐标（吃骨架形变）。"""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = np.array(o.matrix_world)
    co = np.array([list(v.co) for v in me.vertices], float)
    ev.to_mesh_clear()
    return (mw[:3, :3] @ co.T).T + mw[:3, 3]


def bvh_of(P, polys):
    return BVHTree.FromPolygons([tuple(q) for q in P], [tuple(p) for p in polys])


def report(tag):
    so = bpy.data.objects.get(SLEEVE)
    sk = bpy.data.objects.get(SKIN)
    if so is None or sk is None:
        w("!! 找不到 %s / %s" % (SLEEVE, SKIN))
        return
    SP = ev_co(so)
    BP = ev_co(sk)
    bt = bvh_of(BP, [list(p.vertices) for p in sk.data.polygons])
    gi2n = {g.index: g.name for g in so.vertex_groups}
    per = {}
    for i, v in enumerate(so.data.vertices):
        r = bt.find_nearest(tuple(SP[i]))
        if r[0] is None:
            continue
        sd = float(np.dot(SP[i] - np.array(r[0]), np.array(r[1])))
        nm = gi2n[max(v.groups, key=lambda g: g.weight).group] if v.groups else "<无组>"
        per.setdefault(nm, []).append(sd)
    allsd = np.array([x for v in per.values() for x in v])
    w("   [%s] 袖子 %d 顶点：sgn 最小 %+.4f 中位 %+.4f  p1 %+.4f  陷入(<0) %d (%.2f%%)" %
      (tag, len(allsd), allsd.min(), float(np.median(allsd)),
       float(np.percentile(allsd, 1)), int((allsd < 0).sum()), 100.0 * (allsd < 0).mean()))
    bad = [(k, float(np.array(v).min())) for k, v in per.items() if min(v) < -0.002]
    for k, mn in sorted(bad, key=lambda kv: kv[1]):
        a = np.array(per[k])
        w("        !! %-24s 顶点%4d  min %+.4f 陷入 %d" % (k, len(a), mn, int((a < 0).sum())))
    return allsd


def pair_delta(tag, SP_rest, BP_rest, SP_now, BP_now, skin_polys):
    """★ 免疫"最近特征跳变"的判据（skill：别用有符号最近距离下结论）——
    静止时给每个袖子顶点配**最近的那个皮肤顶点**，之后一直用这一对，
    量 `配对距离(姿态) − 配对距离(静止)`。min < 0 才是真的"相对靠近/穿入"。
    静止时传 SP_now=SP_rest / BP_now=BP_rest ⇒ Δ 恒为 0（**零点自检**）。"""
    n = len(SP_rest)
    idx = np.zeros(n, int)
    dr = np.zeros(n)
    for i in range(n):
        k = int(np.argmin(((BP_rest - SP_rest[i]) ** 2).sum(axis=1)))
        idx[i] = k
        dr[i] = float(np.linalg.norm(SP_rest[i] - BP_rest[k]))
    dn = np.linalg.norm(SP_now - BP_now[idx], axis=1)
    dd = dn - dr
    w("   [配对法] %-8s 配对 %d 对：Δ 中位 %+.3fmm  p1 %+.2fmm  **min %+.2fmm**  变近>1mm 的 %d 个" %
      (tag, n, float(np.median(dd)) * 1000, float(np.percentile(dd, 1)) * 1000,
       float(dd.min()) * 1000, int((dd < -0.001).sum())))
    return dd


w("=" * 96)
w("### Y8b · v4 袖子专项穿模体检（%s）" % bpy.data.filepath)
w("=" * 96)
w("")
w("### ① 静止姿态")
so = bpy.data.objects[SLEEVE]
sk = bpy.data.objects[SKIN]
SP_rest = ev_co(so)
BP_rest = ev_co(sk)
base = report("静止")
pair_delta("静止（零点自检，应全 0）", SP_rest, BP_rest, SP_rest, BP_rest, None)

# ---- 摆姿势：每根指 Proximal/Intermediate 各弯 45° ----
armA = bpy.data.objects[ARMS["arm"]]
for o in bpy.context.view_layer.objects:
    o.select_set(False)
armA.select_set(True)
bpy.context.view_layer.objects.active = armA
bpy.ops.object.mode_set(mode="POSE")
moved = 0
for _side in (0, 1):
    for fn in list(FING[_side]) + list(FING_MID[_side]):
        b = armA.pose.bones.get("MhBone_%03d" % fn)
        if b is None:
            continue
        b.rotation_mode = "XYZ"
        b.rotation_euler = (np.radians(45.0), 0.0, 0.0)
        moved += 1
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()
w("")
w("### ② 摆姿势：%d 根指骨各弯 45°（绕局部 X）" % moved)
bpy.context.view_layer.update()
posed = report("屈指45°")
SP_now = ev_co(so)
BP_now = ev_co(sk)
dd = pair_delta("屈指45°", SP_rest, BP_rest, SP_now, BP_now, None)
if base is not None and posed is not None:
    w("")
    w("   ★ 两个判据并排看：")
    w("     · 有符号最近距离（**会被最近特征跳变污染**）：陷入 %d → %d；min %+.4f → %+.4f" %
      (int((base < 0).sum()), int((posed < 0).sum()), base.min(), posed.min()))
    w("     · 配对法（免疫跳变）：min Δ %+.2fmm ⇒ %s" %
      (float(dd.min()) * 1000,
       "**袖子与皮肤同步**，没有新增相对穿入 ⇒ 上面那个更深的负数多半是最近点跳了"
       if float(dd.min()) > -0.001 else "确有新增相对靠近，需要处理"))
w("WROTE " + OUT)
print("DONE")

# -*- coding: utf-8 -*-
"""Z32_衣物权重对齐身体.py —— 把**贴身衣物**的权重换成"正下方那块皮肤"的权重（BVH 最近面 + 重心坐标）。

★ 为什么需要这一步（用户 2026-09-24 实机反馈）：
  "紧身衣 站立时稳定穿模、小腹露出来；足リング 靠近大腿内侧的一半会陷进腿里"。
  用户点明了机理：**MHW 里角色站立会自然往前挺胯、双腿自然岔开** —— 也就是**姿态驱动**的穿模。
  实测（`_X3_preview.json`）紧身衣 与最近皮肤的权重 L1 差：中位 0.029、**p90 0.114、max 0.345**，
  最差点正好在**胯/下腹**（皮肤 `Upper_leg` 0.46 vs 衣物只有 0.16）。
  ⇒ 腿骨转 20° 时胯部相对错动可达 **1 cm 量级** ⇒ 1~2 mm 的几何余量根本挡不住。
  ⇒ **只有让衣物"与皮肤逐顶点同一套权重"才能从根上消除相对运动**（skill：贴身衣物的权重
     从身体转移永远优于照抄原骨架的权重）。

★ 顺序铁律：**必须在"所有改身体权重的步骤"之后**（Y11 手指 → Z26 臀部 → Z27 裆部 → Z31 脚踝），
  否则采到的皮肤权重是旧的。本脚本排在 Z28 之后、Y4 之前。

★ 描边壳：壳的顶点是同位置外扩 1mm 出来的 ⇒ 用"最近源顶点"把源件**转移后**的权重抄给壳，
  否则壳与被壳的本体会以不同权重形变（黑边会错位/穿出）。

用法: blender -b <工作副本.blend> --python Z32_衣物权重对齐身体.py -- [报告txt]
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

P = PROJ
OUT = (sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv
       else os.path.join(P, "_Z32_权重对齐.txt"))
L = []
KMAX = 4


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


# 要对齐的"贴身衣物"（精确名或"名_"前缀匹配）。
# ★★ 本版的取舍：**带物理链的件一律不列进来** —— Z32 会把每个顶点的权重整个换成皮肤权重，
#   链骨的权重会被抹掉（物理形同虚设）。第5版 也是这样把 腰部褶边 排除在外的。
#   本版带链的件（列出来备查，**不要**加进 TARGETS）：
#     BH_Suit（SuitFrill_L/R_F/B 共 4 条链）｜ BH_Headband（BunnyEar_L/R）
#     BH_Bag（Bag 2 节点）｜ BH_Choker（ChokerBand/ChokerDrop）｜ BH_Tail（BunnyTail）
#   ⇒ 这 5 件靠 `Y1` 的 `PUSHOUT`（静态单调外推）处理贴身度；
#      若实机发现它们**姿态驱动**的穿模明显，就 `nosuitchain` / `nochokerchain` / … 关掉对应链，
#      再把这几个名字加进 TARGETS 重出（代价 = 那条链不动了）。
#   ★ 本版最关键的是 **BH_Arm（袖子）**：v4 去掉手套后它是"最后一道"，且它的 34 个顶点组
#     含全部手指骨 ⇒ 对齐后袖子会**逐顶点跟着手指**（第6版 的配方）。
#   ★ 手套 **BH_Gloves 不列进来**：用户 2026-10-03 明确"手套非常大，手指不管怎么动都不可能
#     穿出手套 ⇒ 只需要跟着手腕就行了" ⇒ 保留源权重（Hand.L/R + Wrist_support→Hand + Lower_arm
#     = 4 根骨，刚性跟手），对齐到皮肤反而会让它跟着手指扭。
TARGETS = ["BH_Arm", "BH_Stocking", "BH_Shoes", "BH_LegBelt", "BH_ACC"]

bb = bpy.data.objects["Body_base"]
bmw = np.array(bb.matrix_world)
BVS = [tuple(bmw[:3, :3] @ np.array(v.co) + bmw[:3, 3]) for v in bb.data.vertices]
BPS = [tuple(p.vertices) for p in bb.data.polygons]
bgi2n = {g.index: g.name for g in bb.vertex_groups}
BW = [{bgi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0.0}
      for v in bb.data.vertices]
BT = BVHTree.FromPolygons(BVS, BPS)


def skin_weights(q):
    """最近面的三个顶点权重按重心坐标混合。"""
    loc, nrm, fi, dist = BT.find_nearest(tuple(q))
    if fi is None or fi >= len(BPS):
        return None
    tri = BPS[fi]
    A = np.array(BVS[tri[0]]); B = np.array(BVS[tri[1]]); C = np.array(BVS[tri[2]])
    v0, v1, v2 = B - A, C - A, np.array(q) - A
    d00 = v0 @ v0; d01 = v0 @ v1; d11 = v1 @ v1
    d20 = v2 @ v0; d21 = v2 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-20:
        bc = (1.0, 0.0, 0.0)
    else:
        v = (d11 * d20 - d01 * d21) / den
        ww = (d00 * d21 - d01 * d20) / den
        v = min(max(v, 0.0), 1.0); ww = min(max(ww, 0.0), 1.0)
        if v + ww > 1.0:
            s = v + ww; v /= s; ww /= s
        bc = (1.0 - v - ww, v, ww)
    out = {}
    for k in range(3):
        c = bc[k]
        if c <= 1e-6:
            continue
        for b, x in BW[tri[k]].items():
            out[b] = out.get(b, 0.0) + c * x
    return out


def apply_weights(o, W):
    """把权重写回对象（删掉旧的组、按需建组；≤KMAX 影响 + 归一化）。"""
    for g in list(o.vertex_groups):
        o.vertex_groups.remove(g)
    made = {}
    n4 = 0
    for vi in range(len(o.data.vertices)):
        it = sorted(W[vi].items(), key=lambda kv: -kv[1])[:KMAX]
        it = [(b, x) for b, x in it if x > 1e-6]
        tot = sum(x for _, x in it)
        if tot <= 0:
            it, tot = [("MhBone_002", 1.0)], 1.0
        if len(it) == KMAX:
            n4 += 1
        for b, x in it:
            if b not in made:
                made[b] = o.vertex_groups.new(name=b)
            made[b].add([vi], float(x / tot), "REPLACE")
    return len(made), n4


def mismatch(o):
    """本件与最近皮肤顶点的权重 L1 差（中位/p90/max）。"""
    gi2n = {g.index: g.name for g in o.vertex_groups}
    ds = []
    for vi, v in enumerate(o.data.vertices):
        gw = {gi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0}
        q = o.matrix_world @ v.co
        sw = skin_weights(tuple(q))
        if sw is None:
            continue
        bones = set(gw) | set(sw)
        ds.append(sum(abs(gw.get(b, 0.0) - sw.get(b, 0.0)) for b in bones))
    if not ds:
        return 0.0, 0.0, 0.0
    a = np.array(ds)
    return float(np.median(a)), float(np.percentile(a, 90)), float(a.max())


w("=" * 100)
w("### Z32 · 贴身衣物权重对齐身体（BVH 最近面 + 重心坐标）")
w("=" * 100)
objs = [o for o in bpy.data.objects if o.type == "MESH"]
main = {n: [] for n in TARGETS}
for o in objs:
    for n in TARGETS:
        if o.name == n or o.name.startswith(n + "_"):
            if "__Outline" not in o.name:
                main[n].append(o)
for n in TARGETS:
    for o in main[n]:
        if not o.data.vertices:
            continue
        gi2n = {g.index: g.name for g in o.vertex_groups}
        Wold = [{gi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0.0}
                for v in o.data.vertices]
        m0 = mismatch(o)
        Wnew = []
        for vi, v in enumerate(o.data.vertices):
            q = o.matrix_world @ v.co
            sw = skin_weights(tuple(q))
            Wnew.append(sw if sw else Wold[vi])
        ng, n4 = apply_weights(o, Wnew)
        m1 = mismatch(o)
        w("   %-24s 顶点%5d  与皮肤 L1 差 中位 %.3f→%.3f  p90 %.3f→%.3f  max %.3f→%.3f  用骨%2d（4影响 %d）" %
          (o.name, len(o.data.vertices), m0[0], m1[0], m0[1], m1[1], m0[2], m1[2], ng, n4))
        # 描边壳：抄源件转移后的权重（按最近源顶点）
        sh = bpy.data.objects.get(o.name + "__Outline_Black")
        if sh is not None and len(sh.data.vertices):
            src = np.array([list(q.co) for q in o.data.vertices], float)
            Wsh = []
            for v in sh.data.vertices:
                p = np.array(list(v.co), float)
                j = int(np.argmin(((src - p) ** 2).sum(axis=1)))
                Wsh.append(Wnew[j])
            ng2, n42 = apply_weights(sh, Wsh)
            w("        └ 壳 %-30s 抄源件权重：用骨%2d（4影响 %d）" % (sh.name, ng2, n42))

w("")
w("WROTE " + OUT)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("SAVED %s" % bpy.data.filepath)
print("DONE")

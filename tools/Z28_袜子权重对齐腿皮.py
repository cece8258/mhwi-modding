# -*- coding: utf-8 -*-
"""Z28_袜子权重对齐腿皮.py —— 把 `ID_socks` 的权重**按腿皮（Body_base）逐点对齐**。

实测（`Z27_量裆部与袜子权重.py`，用户反馈"走动时膝盖前后袜子与腿穿模、皮肤漏出"）：
  袜子的"小腿→大腿"过渡带比腿皮**高约 6 cm**：
    z −0.46~−0.40 ：袜（大腿 0.891 / 小腿 0.109）  vs  腿皮（大腿 0.621 / 小腿 0.379）
    z −0.16~−0.10 ：袜（大腿 1.000）              vs  腿皮（大腿 0.736）
  ⇒ 膝一弯两边错开 ⇒ 皮肤从袜子里顶出来。**这正是 skill 里"袜子穿模"的标准根因。**

做法（照抄 skill 的"最近面插值"口径，比最近顶点稳）：
  ① 给 `Body_base` 建 BVH；
  ② 每个袜子顶点 `find_nearest` 取最近点所在**面**，按重心坐标把该面 3 个顶点的权重混合；
  ③ 只保留**本部位（leg）骨架里存在**的骨；top-4 归一化；
  ④ 与旧权重做**逐点替换**（袜子贴腿 ⇒ 跟腿皮走才是对的）。
判据：改完再量一遍"袜 vs 腿皮 逐高度平均权重"，两边的差应显著变小。

★ 必须跑在所有改 `Body_base` 权重的步骤**之后**（Y11 手指 / Z26 臀部 / Z27 裆部），否则会拿到旧权重。
用法: blender -b <工作blend> --python Z28_袜子权重对齐腿皮.py -- <报告txt>
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


import bpy, sys
import numpy as np
from mathutils.bvhtree import BVHTree

OUT = sys.argv[sys.argv.index("--") + 1]
L = []


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


try:
    bpy.ops.object.mode_set(mode="OBJECT")
except RuntimeError:
    pass

LEG = {"MhBone_014", "MhBone_015", "MhBone_016", "MhBone_017",
       "MhBone_018", "MhBone_019", "MhBone_020", "MhBone_021"}
KMAX = 4

sock = bpy.data.objects.get("ID_socks")
if sock is None:
    # 无丝袜版（nosock）没有这个网格 ⇒ 跳过
    w("### 本版没有 ID_socks（nosock 无丝袜版）⇒ 跳过袜子权重对齐")
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    w("")
    w("SAVED %s" % bpy.data.filepath)
    w("WROTE " + OUT)
    raise SystemExit
bb = bpy.data.objects["Body_base"]
arm = bpy.data.objects["f_leg040_0010 Armature"]
OK_BONES = set(b.name for b in arm.data.bones)
w("本部位骨架骨数 %d；袜子顶点 %d；腿皮顶点 %d" % (len(OK_BONES), len(sock.data.vertices),
                                              len(bb.data.vertices)))

bmw = np.array(bb.matrix_world)
BVS = [tuple(bmw[:3, :3] @ np.array(v.co) + bmw[:3, 3]) for v in bb.data.vertices]
BPS = [tuple(p.vertices) for p in bb.data.polygons]
BVF = [list(p.vertices) for p in bb.data.polygons]
bt = BVHTree.FromPolygons(BVS, BPS)
bgi2n = {g.index: g.name for g in bb.vertex_groups}
BW = [{bgi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0.0}
      for v in bb.data.vertices]

# ---- 统计用：改前的逐高度剖面 ----
def profile(co, weight_list, tag):
    out = []
    for zlo in np.arange(-1.00, 0.10, 0.06):
        rows = []
        for i, p in enumerate(co):
            if not (zlo <= p[2] < zlo + 0.06 and p[0] > 0.0):
                continue
            wd = weight_list[i]
            rows.append((sum(t for b, t in wd.items() if b in ("MhBone_014",)),
                         sum(t for b, t in wd.items() if b in ("MhBone_015",)),
                         sum(t for b, t in wd.items() if b in ("MhBone_016", "MhBone_017"))))
        out.append((zlo, np.array(rows) if rows else None))
    return out


sc = np.array([list(v.co) for v in sock.data.vertices], float)
smw = np.array(sock.matrix_world)
sc = (smw[:3, :3] @ sc.T).T + smw[:3, 3]
sgi2n = {g.index: g.name for g in sock.vertex_groups}
SW = [{sgi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0.0}
      for v in sock.data.vertices]

w("")
w("### 改前：袜 vs 腿皮 逐高度平均权重（大腿/小腿/脚趾）")
pw0 = profile(sc, SW, "sock")
pb = profile(np.array(BVS), BW, "skin")
for (z1, a), (z2, b) in zip(pw0, pb):
    if a is None or b is None:
        continue
    w("   z %+.3f 袜(%.3f %.3f %.3f)  腿皮(%.3f %.3f %.3f)" %
      (z1, a[:, 0].mean(), a[:, 1].mean(), a[:, 2].mean(),
       b[:, 0].mean(), b[:, 1].mean(), b[:, 2].mean()))

# ---- ★ 按**高度**取权重剖面（替代"最近面插值"）----
#   为什么改：最近面插值在**脚踝前面这种凹面**处会失效 —— 袜子在踝前"跨"过去，
#   最近皮肤点会跳到小腿或脚背 ⇒ 袜子的"脚→小腿"过渡比腿皮低 2cm（试验 实测：
#   z −0.88~−0.86 袜子 脚0.887 / 腿皮 小腿0.875），脚一勾两边就错开顶穿。
#   按高度取剖面能保证：**同一高度上袜子的权重 == 腿皮的权重**。
# ★★ 最终做法：**同侧 + z±3cm 窗口内**取最近 K=4 个皮肤顶点，按 1/d^3 混合权重。
#   为什么不用前面两种：
#   · "最近面插值"在**脚踝前的凹面**处会跳到别的部位（袜子跨过踝前，最近点跑到小腿/脚背）
#     ⇒ 袜子的"脚→小腿"过渡比腿皮低 2cm；
#   · "按 z 分箱建表"会把**稀疏环状的身体网格**变成阶梯函数（实测腿在 z∈[−0.89,−0.867]
#     一个顶点都没有，空箱被邻近箱填成"脚1.0"，而腿皮的真实权重是上下两环插值出的 ≈50/50）。
#   窗口限制住"不会跳到别的部位"，KNN 1/d^3 保留真实插值 —— 这也是 skill 里验证过的口径。
KWIN = 0.030          # z 窗口：只在这个高度范围内找"最近面"（避免跳到别的部位）
_BCO = np.array(BVS, float)
SCO = sc
_BCOz = _BCO[:, 2]
_BCOx = _BCO[:, 0]
# 预先算好每个面的质心（z 窗口筛选用）与顶点表
_FACE = []
for _p in bb.data.polygons:
    _vs = list(_p.vertices)
    _FACE.append((_BCO[_vs].mean(0), _vs))
_FC = np.array([f[0] for f in _FACE])
w("   判据：**同侧 + z±%.0fmm 窗口内的最近面 + 重心插值**（K=面 3 顶点）" % (KWIN * 1000))


def _bary(q, A, B, C):
    v0, v1, v2 = B - A, C - A, q - A
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-14:
        return (1.0, 0.0, 0.0)
    b1 = (d11 * d20 - d01 * d21) / den
    b2 = (d00 * d21 - d01 * d20) / den
    return (1.0 - b1 - b2, b1, b2)


newW = []
n_miss = 0
for i, q in enumerate(SCO):
    sgn = 1 if q[0] >= 0 else -1
    m = ((_FC[:, 0] >= 0) == (sgn > 0)) & (np.abs(_FC[:, 2] - q[2]) <= KWIN)
    idx = np.nonzero(m)[0]
    if len(idx) == 0:
        newW.append(SW[i])
        n_miss += 1
        continue
    k = int(idx[np.argmin(np.linalg.norm(_FC[idx] - np.array(q, float), axis=1))])
    _cen, vs = _FACE[k]
    if len(vs) < 3:
        newW.append(SW[i])
        n_miss += 1
        continue
    A, B, C = _BCO[vs[0]], _BCO[vs[1]], _BCO[vs[2]]
    bc = _bary(np.array(q, float), A, B, C)
    acc = {}
    for _k2, vi in enumerate(vs[:3]):
        c = max(0.0, float(bc[_k2]))
        if c <= 0:
            continue
        for b, t in BW[vi].items():
            acc[b] = acc.get(b, 0.0) + c * t
    acc = {b: t for b, t in acc.items() if b in OK_BONES and t > 1e-6}
    if not acc:
        newW.append(SW[i])
        n_miss += 1
        continue
    items = sorted(acc.items(), key=lambda kv: -kv[1])[:KMAX]
    tot = sum(t for _, t in items)
    newW.append({b: t / tot for b, t in items})
chg = [max([abs(newW[i].get(b, 0.0) - SW[i].get(b, 0.0)) for b in
            set(newW[i]) | set(SW[i])] or [0.0]) for i in range(len(SW))]
chg = np.array(chg)
w("   逐顶点最大权重变化：中位 %.3f p90 %.3f max %.3f" %
  (np.median(chg), np.percentile(chg, 90), chg.max()))

# ---- 写回（先清后建，幂等）----
allb = set(b for d in newW for b in d) | set(sgi2n.values())
for b in allb:
    if b not in sock.vertex_groups and b in OK_BONES:
        sock.vertex_groups.new(name=b)
gs = {g.name: g for g in sock.vertex_groups}
for i, d in enumerate(newW):
    for b in list(gs.keys()):
        if b in LEG:
            try:
                gs[b].remove([i])
            except Exception:
                pass
    for b, t in d.items():
        gs[b].add([int(i)], float(t), "REPLACE")

# ---- 复核 ----
sgi2n2 = {g.index: g.name for g in sock.vertex_groups}
SW2 = [{sgi2n2[g.group]: float(g.weight) for g in v.groups if g.weight > 0.0}
       for v in sock.data.vertices]
w("")
w("### 改后：袜 vs 腿皮 逐高度平均权重")
pw1 = profile(sc, SW2, "sock")
tot_before = tot_after = 0.0
for (z1, a), (z2, b) in zip(pw1, pb):
    if a is None or b is None:
        continue
    w("   z %+.3f 袜(%.3f %.3f %.3f)  腿皮(%.3f %.3f %.3f)  大腿差 %+.3f" %
      (z1, a[:, 0].mean(), a[:, 1].mean(), a[:, 2].mean(),
       b[:, 0].mean(), b[:, 1].mean(), b[:, 2].mean(), a[:, 0].mean() - b[:, 0].mean()))
# 总差（大腿通道）
for tag, prof in (("改前", pw0), ("改后", pw1)):
    s = 0.0
    n = 0
    for (z1, a), (z2, b) in zip(prof, pb):
        if a is None or b is None:
            continue
        s += abs(a[:, 0].mean() - b[:, 0].mean())
        n += 1
    w("   [%s] 大腿通道逐层平均绝对差 = %.4f（%d 层）" % (tag, s / max(n, 1), n))
rs = [sum(d.values()) for d in newW]
w("   行和 min=%.6f max=%.6f ；影响数 max=%d" %
  (min(rs), max(rs), max(len(d) for d in newW)))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("")
w("SAVED %s" % bpy.data.filepath)
w("WROTE " + OUT)

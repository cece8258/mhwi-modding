# -*- coding: utf-8 -*-
"""Y11_施加54权重.py —— 把 `试验` 的**目标态**权重写进 Body_base（绝对写，幂等）。
为什么不用 A9：A9 有"基态必须 == W0"的前置断言，而本工程主 blend 的基态**既不是 W0 也不是 W54**
（实测：vs W0 差 1192 顶点 / vs W54 差 3024 顶点）——所以先**量清差异落在哪**，再写。
判据：W54 是**实机验收过**的目标态（用户原话"不管做什么动作都不会出现皮肤拉长"），
非手部列在 W54 里 == W0；只要"blend 与 W0 的差异全部落在手部"，绝对写 W54 就是安全的。

报告：① 差异顶点的空间分布（是否全在手区）② 写前/写后 vs W0/W54 ③ 拇指 6 列冻结 ④ 行和
用法: blender -b <工作副本.blend> --python Y11_施加54权重.py
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


import bpy, os, json
import numpy as np

P = PROJ
OUT = os.path.join(P, "_Y11_施加54.txt")
L = []


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


js = json.load(open(os.path.join(P, "_T1_master.json"), encoding="utf-8"))
BONES = sorted(set(b for wd in js["W"] for b in wd))
BI = {b: i for i, b in enumerate(BONES)}
NB = len(BONES)
W0 = np.zeros((len(js["co"]), NB))
for i, wd in enumerate(js["W"]):
    for b, x in wd.items():
        W0[i, BI[b]] = x
W54 = np.load(os.path.join(P, "_S55_W_cap6.npy")).astype(np.float64)

ob = bpy.data.objects["Body_base"]
gi2n = {g.index: g.name for g in ob.vertex_groups}
N = len(ob.data.vertices)
CO = np.array([list(v.co) for v in ob.data.vertices], float)
Wc = np.zeros((N, NB))
for v in ob.data.vertices:
    for g in v.groups:
        n = gi2n.get(g.group)
        if n in BI:
            Wc[v.index, BI[n]] = g.weight

w("### ① 差异落在哪（按空间分区统计 差值>1e-6 的顶点数）")
regions = [("手区 |x|>0.55", np.abs(CO[:, 0]) > 0.55),
           ("前臂 0.35<|x|<=0.55", (np.abs(CO[:, 0]) > 0.35) & (np.abs(CO[:, 0]) <= 0.55)),
           ("躯干/其余 |x|<=0.35", np.abs(CO[:, 0]) <= 0.35)]
for lab, m in regions:
    d0 = np.abs(Wc - W0).max(axis=1) > 1e-6
    w("   %-22s 顶点 %6d ；与 W0 有差 %5d（%.2f%%）" %
      (lab, int(m.sum()), int((d0 & m).sum()), 100.0 * (d0 & m).sum() / max(m.sum(), 1)))
d0 = np.abs(Wc - W0).max(axis=1) > 1e-6
w("   ⇒ 与 W0 有差的顶点里，落在**手区之外**的 = %d 个" %
  int((d0 & (np.abs(CO[:, 0]) <= 0.55)).sum()))
if (d0 & (np.abs(CO[:, 0]) <= 0.55)).sum():
    idx = np.where(d0 & (np.abs(CO[:, 0]) <= 0.55))[0][:10]
    for i in idx:
        w("        顶点%d  局部(%+.4f,%+.4f,%+.4f) vs W0 max|Δ|=%.4f  vs W54=%.4f" %
          (i, CO[i][0], CO[i][1], CO[i][2], np.abs(Wc[i] - W0[i]).max(), np.abs(Wc[i] - W54[i]).max()))

w("")
w("### ② 写 W54（绝对写，REPLACE）")
w("   写前：vs W0 max|Δ|=%.4e ；vs W54 max|Δ|=%.4e" %
  (np.abs(Wc - W0).max(), np.abs(Wc - W54).max()))
n_ch = 0
gs = {}
for b in BONES:
    if b in ob.vertex_groups:
        gs[b] = ob.vertex_groups[b]
    else:
        gs[b] = ob.vertex_groups.new(name=b)
moved = 0
for i in range(N):
    for j, b in enumerate(BONES):
        v = float(W54[i, j])
        cur = Wc[i, j]
        if abs(cur - v) > 1e-7:
            moved += 1
        if v <= 0.0:
            try:
                gs[b].remove([i])
            except Exception:
                pass
        else:
            gs[b].add([int(i)], v, "REPLACE")
w("   被执行 REPLACE 的（顶点,骨）对 = %d ；涉及顶点 %d / %d" %
  (moved, int((np.abs(Wc - W54).max(axis=1) > 1e-7).sum()), N))

# 复核
Wc2 = np.zeros((N, NB))
gi2n2 = {g.index: g.name for g in ob.vertex_groups}
for v in ob.data.vertices:
    for g in v.groups:
        n = gi2n2.get(g.group)
        if n in BI:
            Wc2[v.index, BI[n]] = g.weight
w("   写后：vs W54 max|Δ|=%.4e （应≈0，量化到 1/1024 以内）" % np.abs(Wc2 - W54).max())
TH = ["MhBone_031", "MhBone_032", "MhBone_033", "MhBone_048", "MhBone_049", "MhBone_050"]
cols = [BI[b] for b in TH if b in BI]
w("   拇指 6 列 写后 vs W0 逐位相同 = %s（应 True）" %
  np.allclose(Wc2[:, cols], W0[:, cols], atol=0.0))
rs = Wc2.sum(axis=1)
w("   行和 min=%.6f max=%.6f ｜ 每顶点影响数 max=%d（应 ≤6）" %
  (rs.min(), rs.max(), max(int((Wc2[i] > 0).sum()) for i in range(N))))
# 手部以外是否被改动
out_hand = np.abs(Wc2 - Wc).max(axis=1) > 1e-7
w("   手区以外被改动的顶点 = %d（应 0 或极少）" %
  int((out_hand & (np.abs(CO[:, 0]) <= 0.55)).sum()))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("")
w("SAVED %s" % bpy.data.filepath)
w("WROTE " + OUT)

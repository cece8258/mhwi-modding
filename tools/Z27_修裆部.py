# -*- coding: utf-8 -*-
"""Z27_修裆部.py —— 把 `Body_base` **裆部**（左右大腿同时拉的区域）的腿骨权重让给骨盆。

实测（`Z27_量裆部与袜子权重.py`，用户反馈"裆部被拉向两条大腿、近似正方形"）：
  工作坐标 z∈(-0.30,0.06)、|x|<0.12 的**正面与中间**：
    |x| 0.01~0.02  腿总和 0.971  **左腿 0.486 / 右腿 0.486**（几乎完美对半）
    |x| 0.02~0.04  腿总和 1.000  **左腿 0.500 / 右腿 0.500**
  ⇒ 这些顶点被**两条大腿同时**拉，两腿分开时它们被拉成一片"方形的蹼"。
  （上一版 `Z26` 只修了**背面** y>0.04，正面/中间从没修过。）

判据（本脚本用的作用域，比"直角边界"准）：
  **只按 |x| 圈中缝**：|x| < XIN 全额、到 XMAX 淡出；配合 z 范围与 Laplacian 平滑。
  ★ 为什么不用"两腿比"：那条判据**看着成立、实测是假的** —— 镜像对称的网格上
    "左腿均值 == 右腿均值"必然成立（本轮实测 |x| 0.01~0.04 两腿各 0.486/0.486），
    但**逐顶点**是"非左即右的单侧"（同区域逐顶点两腿比均值只有 **0.084**），
    ⇒ 用两腿比筛出来的顶点数是 **0**。判据必须先证明它能区分假设。

做法（照抄 Z26 已验证的形态）：
  目标腿权重 = min(腿总和, **0.35**)，让出量 = 腿总和 − 目标；让出量再乘空间权重
  （对半分程度 × |x| 淡出），**沿网格 Laplacian 平滑 8 轮（α=0.5）**后施加，让出的给 `MhBone_013`。
用法: blender -b <工作blend> --python Z27_修裆部.py -- <报告txt>
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

TARGET = 0.35           # 裆部腿权重上限
YZ = (-0.22, 0.06)
XMAX = 0.075            # |x| 淡出到 0
XIN = 0.045             # |x| < XIN 全额（裆中缝）
YMAX = 0.05             # 只管正面与中间（背面交给 Z26）
LEG = {"MhBone_014", "MhBone_015", "MhBone_016", "MhBone_017",
       "MhBone_018", "MhBone_019", "MhBone_020", "MhBone_021"}
PEL = "MhBone_013"
KMAX = 6

ob = bpy.data.objects["Body_base"]
gi2n = {g.index: g.name for g in ob.vertex_groups}
CO = np.array([list(v.co) for v in ob.data.vertices], float)

give_of = {}
sel = 0
for v in ob.data.vertices:
    x, y, z = CO[v.index]
    if not (YZ[0] < z < YZ[1] and y < YMAX and abs(x) < XMAX):
        continue
    wd = {gi2n[g.group]: g.weight for g in v.groups if g.weight > 0.0}
    leg = sum(t for b, t in wd.items() if b in LEG)
    if leg <= TARGET:
        continue
    ax = abs(x)
    if ax >= XMAX:
        continue
    xf = 1.0 if ax <= XIN else max(0.0, (XMAX - ax) / (XMAX - XIN))
    give = max(0.0, leg - TARGET) * xf
    if give <= 1e-6:
        continue
    give_of[v.index] = give
    sel += 1
w("### Z27 修裆部：作用域内顶点 %d 个（判据：|x|<0.045 全额、0.075 淡出，腿权重让到 ≤0.35）" % sel)

# Laplacian 平滑"让出量"
SMOOTH_ROUNDS, SMOOTH_A = 8, 0.5
adj = {i: set() for i in give_of}
for _p in ob.data.polygons:
    _vs = list(_p.vertices)
    for _a in _vs:
        if _a in adj:
            for _b in _vs:
                if _b != _a:
                    adj[_a].add(_b)
        for _b in _vs:
            if _b in adj and _a != _b:
                adj[_b].add(_a)
_g = {i: float(x) for i, x in give_of.items()}
for _ in range(SMOOTH_ROUNDS):
    _ng = dict(_g)
    for _i, _nb in adj.items():
        if not _nb:
            continue
        _av = sum(_g.get(_j, 0.0) for _j in _nb) / len(_nb)
        _ng[_i] = (1 - SMOOTH_A) * _g.get(_i, 0.0) + SMOOTH_A * _av
    _g = _ng
moves = {}
for _i, _gi in _g.items():
    if _gi <= 1e-6:
        continue
    _wd = {gi2n[_gg.group]: _gg.weight for _gg in ob.data.vertices[_i].groups if _gg.weight > 0.0}
    _leg0 = sum(t for b, t in _wd.items() if b in LEG)
    if _leg0 <= 1e-9:
        continue
    _take = min(_gi / _leg0, 0.95)
    _nw = {}
    for b, t in _wd.items():
        _nw[b] = t * (1.0 - _take) if b in LEG else t
    _nw[PEL] = _nw.get(PEL, 0.0) + _gi
    _items = sorted(_nw.items(), key=lambda kv: -kv[1])[:KMAX]
    _tot = sum(t for _, t in _items)
    moves[_i] = [(b, t / _tot) for b, t in _items]
w("   平滑 %d 轮后实际施加 %d 个顶点" % (SMOOTH_ROUNDS, len(moves)))

for b in set(b for q in moves.values() for b, _ in q) | LEG | {PEL}:
    if b not in ob.vertex_groups:
        ob.vertex_groups.new(name=b)
gs = {g.name: g for g in ob.vertex_groups}
for i, q in moves.items():
    for b in list(gs.keys()):
        if b in LEG or b == PEL:
            try:
                gs[b].remove([i])
            except Exception:
                pass
    for b, t in q:
        gs[b].add([int(i)], float(t), "REPLACE")

# 复核（同判据）
gi2n2 = {g.index: g.name for g in ob.vertex_groups}
rows = []
for v in ob.data.vertices:
    x, y, z = CO[v.index]
    if not (YZ[0] < z < YZ[1] and y < YMAX and abs(x) < XMAX):
        continue
    wd = {gi2n2[g.group]: g.weight for g in v.groups if g.weight > 0.0}
    leg = sum(t for b, t in wd.items() if b in LEG)
    rows.append((leg, wd.get(PEL, 0.0), sum(wd.values()), len(wd)))
A = np.array(rows)
w("   复核（同区域 %d 顶点）：腿总和均值 %.3f ；骨盆均值 %.3f" % (len(A), A[:, 0].mean(), A[:, 1].mean()))
for _lo, _hi in ((0.0, 0.015), (0.015, 0.03), (0.03, 0.045), (0.045, 0.06), (0.06, 0.075)):
    m2 = []
    for v in ob.data.vertices:
        x2, y2, z2 = CO[v.index]
        if not (YZ[0] < z2 < YZ[1] and y2 < YMAX and _lo <= abs(x2) < _hi):
            continue
        wd2 = {gi2n2[g.group]: g.weight for g in v.groups if g.weight > 0.0}
        m2.append((sum(t for b, t in wd2.items() if b in LEG), wd2.get(PEL, 0.0)))
    if m2:
        B2 = np.array(m2)
        w("      |x| %.3f~%.3f ：%4d 顶点 腿%.3f 骨盆%.3f ；腿主导(>0.5) %.1f%%" %
          (_lo, _hi, len(B2), B2[:, 0].mean(), B2[:, 1].mean(), 100.0 * (B2[:, 0] > 0.5).mean()))
w("   行和 min=%.6f max=%.6f ；影响数 max=%d（应 ≤%d）" %
  (A[:, 2].min(), A[:, 2].max(), int(A[:, 3].max()), KMAX))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("")
w("SAVED %s" % bpy.data.filepath)
w("WROTE " + OUT)

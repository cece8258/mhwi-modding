# -*- coding: utf-8 -*-
"""Z26_修臀部左右甩.py —— 把 `Body_base` **臀部**（背面 y>0.02）的腿骨权重按比例让给骨盆骨。
实测根因（`Z25_量屁股权重.py`）：臀部顶点被腿骨绑了 **68.7%**，只有 |x|<0.02 的窄条是骨盆主导(74%)。
来源：原 角色 骨架给屁股专门的 `Butt.L/.001`、`Butt.R/.001` 抖动骨，MHW 没有对应骨，
上一版做权重转移时落到了最近的大腿骨上 ⇒ 腿一动整个屁股大幅摆动、内裤背面像分左右两半。
做法（照抄上一版治"裆部左右甩"的同一招）：臀部区域腿权重 ×0.45，让出的给 `MhBone_013`(骨盆)；
**只动背面(y>0.02)、只动 z∈(-0.25,0.05)、|x|<0.20**；不碰手部（手指修复目标态不受影响，因为
本脚本在 Y11 之后运行、且手区 |x|>0.55 完全在作用域外）。
★ 必须跑在 Y11（施加54手指权重）**之后**，否则会被 W54 的绝对写覆盖。
用法: blender -b <工作blend> --python Z26_修臀部左右甩.py -- <报告txt>
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


K = 0.45                     # 臀部腿权重的保留比例
YZ = (-0.25, 0.05)
XMAX = 0.20
# ★ 用户实测：YMIN=0.02 时**裆部中心/下缘的顶点也会落进作用域**（它们紧挨着背面），
#   被一起改成骨盆主导 ⇒ 不跟腿 ⇒ 大腿正面顶穿内裤。提到 0.04 只保留外后侧。
YMIN = 0.04
LEG = {"MhBone_014", "MhBone_015", "MhBone_016", "MhBone_017",
       "MhBone_018", "MhBone_019", "MhBone_020", "MhBone_021"}
PEL = "MhBone_013"
KMAX = 6

ob = bpy.data.objects["Body_base"]
gi2n = {g.index: g.name for g in ob.vertex_groups}
CO = np.array([list(v.co) for v in ob.data.vertices], float)
moves = {}                   # 顶点 -> {骨名: 新权重}
give_of = {}                 # 顶点 -> 让给骨盆的权重量（用于平滑）
n_sel = 0
for v in ob.data.vertices:
    x, y, z = CO[v.index]
    if not (y > YMIN and YZ[0] < z < YZ[1] and abs(x) < XMAX):
        continue
    wd = {gi2n[g.group]: g.weight for g in v.groups if g.weight > 0.0}
    leg = sum(x2 for b, x2 in wd.items() if b in LEG)
    if leg <= 1e-6:
        continue
    give = leg * (1.0 - K)
    nw = {}
    for b, x2 in wd.items():
        nw[b] = x2 * K if b in LEG else x2
    nw[PEL] = nw.get(PEL, 0.0) + give
    items = sorted(nw.items(), key=lambda kv: -kv[1])[:KMAX]
    tot = sum(x2 for _, x2 in items)
    moves[v.index] = [(b, x2 / tot) for b, x2 in items]
    give_of[v.index] = give
    n_sel += 1
# ★ 平滑过渡：把"让出的权重"沿网格 Laplacian 平滑，消除硬边界造成的折痕/凹坑
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
    _leg0 = sum(x2 for b, x2 in _wd.items() if b in LEG)
    if _leg0 <= 1e-9:
        continue
    _take = min(_gi / _leg0, 0.95)
    _nw = {}
    for b, x2 in _wd.items():
        _nw[b] = x2 * (1.0 - _take) if b in LEG else x2
    _nw[PEL] = _nw.get(PEL, 0.0) + _gi
    _items = sorted(_nw.items(), key=lambda kv: -kv[1])[:KMAX]
    _tot = sum(x2 for _, x2 in _items)
    moves[_i] = [(b, x2 / _tot) for b, x2 in _items]
w("### 臀部腿权重让给骨盆（让出量已 Laplacian 平滑 %d 轮）：作用域内顶点 %d 个，K=%.2f" %
  (SMOOTH_ROUNDS, len(moves), K))
# 写回（先清后建，幂等）
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
    for b, x2 in q:
        gs[b].add([int(i)], float(x2), "REPLACE")
# 复核
gi2n2 = {g.index: g.name for g in ob.vertex_groups}
rows = []
for v in ob.data.vertices:
    x, y, z = CO[v.index]
    if not (y > YMIN and YZ[0] < z < YZ[1] and abs(x) < XMAX):
        continue
    wd = {gi2n2[g.group]: g.weight for g in v.groups if g.weight > 0.0}
    rows.append((abs(x), sum(x2 for b, x2 in wd.items() if b in LEG),
                 sum(x2 for b, x2 in wd.items() if b == PEL),
                 sum(wd.values()), len(wd)))
a = np.array(rows)
w("   复核（同作用域）：腿骨均值 %.3f -> 应为约 %.3f ；骨盆均值 %.3f" %
  (a[:, 1].mean(), 0, a[:, 2].mean()))
w("   行和 min=%.6f max=%.6f ；影响数 max=%d（应 ≤%d）" %
  (a[:, 3].min(), a[:, 3].max(), int(a[:, 4].max()), KMAX))
w("   腿骨均值 修后 = %.3f（修前 0.687 × 0.45 ≈ 0.309）" % a[:, 1].mean())
# 手部未被触碰的自检（手指修复目标态在 |x|>0.55）
w("   作用域与手区(|x|>0.55)无交集 = %s" % (XMAX < 0.55))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("")
w("SAVED %s" % bpy.data.filepath)
w("WROTE " + OUT)

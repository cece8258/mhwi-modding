# -*- coding: utf-8 -*-
"""Z31_修脚踝权重.py —— **身体侧**的根修：把 `Body_base` 腿部的权重按**高度**抹成光滑剖面。

实测（`K30_量脚踝.py` / `K31_对拍脚踝顶点.py`）：
  身体在脚踝那一圈（z≈−0.8667）的权重是**混的** —— 30 个顶点里 26 个是"小腿 MhBone_015 = 1.0"、
  4 个是"脚 MhBone_016 = 1.0"。这是上一版从供体转移权重留下的噪声。
  ⇒ 身体自己的脚踝形变就是错的 ⇒ 袜子无论怎么对齐都是**抄这个乱摊子**
    （三轮对齐口径都试过：最近面 / 按 z 分箱 / 同侧 z 窗口 KNN，结果都一样）。

做法：**腿是圆柱面 ⇒ 权重应当只随高度变化**。
  ① 按 z 分 1cm 箱，取每箱的平均权重（左右分开）；
  ② 沿 z 做 3 格滑动平均 ×2 轮（把混圈的噪声抹平）；
  ③ 每个顶点取自己高度的插值剖面写回（腿部 z∈(−1.02,−0.20)，不碰裆部）。
★ 必须跑在 Z28（袜子对齐腿皮）**之前**。
用法: blender -b <工作blend> --python Z31_修脚踝权重.py -- <报告txt>
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

BIN = 0.010
ZFLO, ZFHI = -1.02, -0.20      # 只处理腿（在裆部以下）
KMAX = 4
SMOOTH_R = 2                   # 沿 z 的滑动平均轮数

ob = bpy.data.objects["Body_base"]
gi2n = {g.index: g.name for g in ob.vertex_groups}
CO = np.array([list(v.co) for v in ob.data.vertices], float)
WD = [{gi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0.0} for v in ob.data.vertices]

nb = int((ZFHI - ZFLO) / BIN) + 1
prof = {}
for sgn in (1, -1):
    acc = [dict() for _ in range(nb)]
    cnt = [0] * nb
    for i in range(len(CO)):
        if (CO[i, 0] >= 0) != (sgn > 0):
            continue
        if not (ZFLO <= CO[i, 2] < ZFHI):
            continue
        k = int((CO[i, 2] - ZFLO) / BIN)
        if not (0 <= k < nb):
            continue
        cnt[k] += 1
        for b, t in WD[i].items():
            acc[k][b] = acc[k].get(b, 0.0) + t
    tab = []
    for k in range(nb):
        tab.append({b: t / cnt[k] for b, t in acc[k].items()} if cnt[k] else None)
    # 空箱：用相邻非空箱插值
    for k in range(nb):
        if tab[k] is not None:
            continue
        lo = next((j for j in range(k - 1, -1, -1) if tab[j] is not None), None)
        hi = next((j for j in range(k + 1, nb) if tab[j] is not None), None)
        if lo is None and hi is None:
            tab[k] = {}
        elif lo is None:
            tab[k] = dict(tab[hi])
        elif hi is None:
            tab[k] = dict(tab[lo])
        else:
            f = (k - lo) / (hi - lo)
            tab[k] = {b: tab[lo].get(b, 0.0) * (1 - f) + tab[hi].get(b, 0.0) * f
                      for b in set(tab[lo]) | set(tab[hi])}
    # 沿 z 滑动平均
    for _ in range(SMOOTH_R):
        for k in range(nb):
            lo = tab[max(0, k - 1)]
            ce = tab[k]
            hi = tab[min(nb - 1, k + 1)]
            keys = set(lo) | set(ce) | set(hi)
            tab[k] = {b: (lo.get(b, 0.0) + 2 * ce.get(b, 0.0) + hi.get(b, 0.0)) / 4.0
                      for b in keys}
    prof[sgn] = tab
w("### 按高度建腿部权重剖面：%d 箱 × %0.fmm，左右各一张，沿 z 平滑 %d 轮" % (nb, BIN * 1000, SMOOTH_R))

moves = {}
for i in range(len(CO)):
    if not (ZFLO <= CO[i, 2] < ZFHI):
        continue
    sgn = 1 if CO[i, 0] >= 0 else -1
    x0 = (CO[i, 2] - ZFLO) / BIN
    k0 = int(np.clip(np.floor(x0), 0, nb - 1))
    k1 = int(np.clip(k0 + 1, 0, nb - 1))
    f = float(np.clip(x0 - k0, 0.0, 1.0))
    d0, d1 = prof[sgn][k0], prof[sgn][k1]
    acc = {b: d0.get(b, 0.0) * (1 - f) + d1.get(b, 0.0) * f for b in set(d0) | set(d1)}
    if not acc:
        continue
    items = sorted(acc.items(), key=lambda kv: -kv[1])[:KMAX]
    tot = sum(t for _, t in items)
    if tot <= 0:
        continue
    moves[i] = [(b, t / tot) for b, t in items]
w("   作用顶点 %d（腿部 z∈(%.2f,%.2f)）" % (len(moves), ZFLO, ZFHI))

allb = set(b for q in moves.values() for b, _ in q)
for b in allb:
    if b not in ob.vertex_groups:
        ob.vertex_groups.new(name=b)
gs = {g.name: g for g in ob.vertex_groups}
for i, q in moves.items():
    for b in list(gs.keys()):
        try:
            gs[b].remove([i])
        except Exception:
            pass
    for b, t in q:
        gs[b].add([int(i)], float(t), "REPLACE")

# 复核：脚踝的逐 1cm 剖面
gi2n2 = {g.index: g.name for g in ob.vertex_groups}
w("")
w("### 复核：身体腿部逐 1cm 的（小腿 MhBone_015 / 脚 MhBone_016+017）平均权重（左侧）")
for zl in np.arange(-1.02, -0.70, 0.02):
    rows = []
    for i in range(len(CO)):
        if not (zl <= CO[i, 2] < zl + 0.02 and CO[i, 0] > 0):
            continue
        wd = {gi2n2[g.group]: g.weight for g in ob.data.vertices[i].groups if g.weight > 0}
        rows.append((sum(t for b, t in wd.items() if b == "MhBone_015"),
                     sum(t for b, t in wd.items() if b in ("MhBone_016", "MhBone_017"))))
    if rows:
        A = np.array(rows)
        w("   z %+.4f~%+.4f ：%4d 点  小腿 %.3f  脚 %.3f" %
          (zl, zl + 0.02, len(A), A[:, 0].mean(), A[:, 1].mean()))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("")
w("SAVED %s" % bpy.data.filepath)
w("WROTE " + OUT)

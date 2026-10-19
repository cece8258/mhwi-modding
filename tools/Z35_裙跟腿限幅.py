# -*- coding: utf-8 -*-
"""Z35_裙跟腿限幅.py（原名 Z35_裙中缝归骨盆.py）—— 给裙子的**"跟腿"量设上限**。

为什么（用户 2026-10-09 实机，三轮反馈归到一条）：
  · `Z32` 把裙子逐顶点对齐皮肤后，**裙摆两侧 ≈100% 跟大腿** ⇒ 一岔腿，两侧被带走 15cm 量级，
    与"定住的中缝"之间就被**拉扯**（"岔开腿时裙子中间被拉伸得很长"）；
  · 但完全不跟腿又回到"腿穿裙子"（碰撞在本工程实测**不生效**）。
⇒ 正确口径 = **限定跟腿的量**：中缝（|x|<XE）**0%**、越往外线性升到 `CAP`（默认 30%），
   到 |x|≥XF 就不再涨。这样：中缝挂骨盆（不被两腿拉）、外侧最多跟 30%（不会再拉裂）。

做法：逐顶点按 `capv = CAP × clamp((|x|−XE)/(XF−XE), 0, 1)` 求允许的腿权重上限；
      超出的部分按比例搬给 `MhBone_013`（骨盆），其余骨不动；≤4 影响 + 归一化。
★ 同时处理描边壳（壳权重抄源件，必须一起改，否则壳与本体会错开）。
★ 幂等（只做"腿 → 骨盆"的搬运；跑第二遍时已在上限内 ⇒ 不动）。
用法: blender -b <工作副本.blend> --python Z35_裙跟腿限幅.py -- <报告txt> [cap=0.30] [xe=0.02] [xf=0.10]
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

P = PROJ
argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
OUT = args[0] if args else os.path.join(P, "_Z35_裙中缝.txt")

CAP = 0.30         # ★ 跟腿上限：任何顶点最多 30% 权重落在腿骨上
XE = 0.020         # 中缝内（|x|<2cm）完全不给腿
XF = 0.100         # 到 |x|≥10cm 才给满 CAP
Z0 = 0.060         # 腰头以上不管（本来就是 Hips/Spine）
LEG = {"MhBone_014", "MhBone_018", "MhBone_015", "MhBone_019"}    # Upper_leg.L/R、Lower_leg.L/R
HIPS = "MhBone_013"
TARGET = "CR_Pleated_skirt"
KMAX = 4
for _a in args[1:]:
    if _a.startswith("cap="):
        CAP = float(_a.split("=", 1)[1])
    if _a.startswith("xe="):
        XE = float(_a.split("=", 1)[1])
    if _a.startswith("xf="):
        XF = float(_a.split("=", 1)[1])
L = []


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


try:
    bpy.ops.object.mode_set(mode="OBJECT")
except RuntimeError:
    pass

objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(TARGET)]
w("### Z35 · 裙跟腿限幅（cap=%.2f xe=%.3f xf=%.3f；对象 %s）" % (CAP, XE, XF, [o.name for o in objs]))
for o in objs:
    mw = np.array(o.matrix_world)
    co = (mw[:3, :3] @ np.array([list(v.co) for v in o.data.vertices], float).T).T + mw[:3, 3]
    gi2n = {g.index: g.name for g in o.vertex_groups}
    if HIPS not in [g.name for g in o.vertex_groups]:
        o.vertex_groups.new(name=HIPS)
    moves, n_ch, leg_before, leg_after = [], 0, 0.0, 0.0
    for vi, v in enumerate(o.data.vertices):
        x, z = float(co[vi][0]), float(co[vi][2])
        if z > Z0:
            continue
        ramp = max(0.0, min(1.0, (abs(x) - XE) / max(XF - XE, 1e-6)))
        capv = CAP * ramp
        wd = {gi2n[g.group]: float(g.weight) for g in o.data.vertices[vi].groups if g.weight > 0}
        lb = sum(v2 for k, v2 in wd.items() if k in LEG)
        if lb <= capv + 1e-6:
            continue
        t = (lb - capv) / lb
        give = lb - capv
        leg_before += lb
        new = {}
        for k, v2 in wd.items():
            new[k] = v2 * (1.0 - t) if k in LEG else v2
        new[HIPS] = new.get(HIPS, 0.0) + give
        items = sorted([(k, v2) for k, v2 in new.items() if v2 > 1e-4],
                       key=lambda kv: -kv[1])[:KMAX]
        tot = sum(v2 for _, v2 in items) or 1.0
        items = [(k, v2 / tot) for k, v2 in items]
        moves.append((vi, items))
        leg_after += sum(v2 for k, v2 in items if k in LEG)
        n_ch += 1
    # 先收集后执行
    for vi, items in moves:
        keep = [k for k, _ in items]
        for g in list(o.vertex_groups):
            if g.name not in keep:
                try:
                    g.remove([vi])
                except Exception:
                    pass
        have = {g.name for g in o.vertex_groups}
        for k, x2 in items:
            if k not in have:
                o.vertex_groups.new(name=k)
            o.vertex_groups[k].add([vi], float(x2), "REPLACE")
    w("   %-30s 顶点%6d ｜ 动过 %5d ｜ 腿权重之和 %.1f -> %.1f（%+.1f%%）" %
      (o.name, len(o.data.vertices), n_ch, leg_before, leg_after,
       100.0 * (leg_after - leg_before) / max(leg_before, 1e-9)))
w("SAVED")

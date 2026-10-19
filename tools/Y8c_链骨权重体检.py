# -*- coding: utf-8 -*-
"""Y8c_链骨权重体检.py —— 只读。确认新件的**链骨权重是沿链渐变的**（否则布料不会弯）。
判据：对每个链（root/tip 两根骨），统计该链相关网格上"链骨权重之和"沿**链的真实轴** u 的分档均值；
      u≈0 应偏 root、u≈1 应偏 tip（单调）。
★★ 链轴取自 `_Y4_链骨位置.json` 的**链节点折线**（弧长参数）。**不要**用 `末骨.tail − 首骨.head`：
   本流水线的链骨统一是 +Z、长 0.05 ⇒ 那个向量不是链的方向（第一版就是这么量出**空读数**的）。
用法: blender -b _p_work.blend --python Y8c_链骨权重体检.py -- <输出txt>
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

OUT = sys.argv[sys.argv.index("--") + 1]
L = []


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


def co_of(o):
    mw = np.array(o.matrix_world)
    co = np.array([list(v.co) for v in o.data.vertices], float)
    return (mw[:3, :3] @ co.T).T + mw[:3, 3]


PART_ARM = {"body": "f_body040_0010 Armature", "arm": "f_arm040_0010 Armature",
            "leg": "f_leg040_0010 Armature", "wst": "f_wst040_0010 Armature"}
# ---------- === 本工程 === ----------
# 链：名字 -> (部位, 骨号列表, 关联网格)；号与 `_Y1_链清单.json` 一致（单一数据源）。
# ★★ 本版**只有 2 条链**（body 的 盘发 侧发，140~143）；wst/arm/leg **无链**。
_TBFS = ["HAIR_FrontSide"]          # 侧发（`emit` 只按材质拆件，本件单槽 ⇒ 就是一个对象）
CHAINS = [("HAIR_Side_L", "body", [140, 141], _TBFS),
          ("HAIR_Side_R", "body", [142, 143], _TBFS)]
# ★★ 链轴：**必须用链自己的节点位置**（`_Y4_链骨位置.json`，= `Y4` 从 `_Y1_链清单.json`
#   取的、`Y4b` 写进 ctc 的那套节点）。
#   ★ 本版修正的坑（第一版量出的是**空读数**）：原来用 `末骨.tail − 首骨.head` 当链轴，
#   而本流水线的链骨**统一是 +Z、长 0.05**（照抄导入器留下的形态，skill 里记过）
#     ⇒ 那个向量**不是链的方向**（实测 2 节点链的 dv=(0.003,0.015,0.008) —— 被 y 主导）
#     ⇒ u 分档全是噪声。早期几版报告里的 u 表**也是这么来的**，同样无效。
try:
    _NODES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(OUT)),
                                         "_Y4_链骨位置.json"), encoding="utf-8"))
except Exception as _e:
    _NODES = {}
    w("!! 读不到 _Y4_链骨位置.json（%s）⇒ 链轴退化为「末骨tail−首骨head」，**读数不可信**" % _e)


def chain_axis(part, fns):
    """返回 (节点折线 P[N,3], 弧长累计 cum[N], 总长) —— 缺数据则返回 None。"""
    d = _NODES.get(part) or {}
    pts = []
    for f in fns:
        v = d.get("%03d" % f)
        if v is None:
            return None
        pts.append(np.array(v, float))
    if len(pts) < 2:
        return None
    P = np.array(pts, float)
    cum = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    return P, cum, max(float(cum[-1]), 1e-9)


def u_of(q, ax):
    """顶点 -> 折线上的**弧长参数** u（贴根 0、尖 1）。"""
    P, cum, tot = ax
    seg = P[1:] - P[:-1]
    L2 = np.maximum((seg ** 2).sum(1), 1e-18)
    t = np.clip(((q - P[:-1]) * seg).sum(1) / L2, 0.0, 1.0)
    proj = P[:-1] + seg * t[:, None]
    k = int(np.argmin(((q - proj) ** 2).sum(1)))
    return float(np.clip((cum[k] + t[k] * float(np.linalg.norm(seg[k]))) / tot, 0.0, 1.0))


for cname, part, fns, meshes in CHAINS:
    names = ["MhBone_%03d" % f for f in fns]
    ax = chain_axis(part, fns)
    if ax is None:
        w("   %-11s !! 取不到链节点位置 ⇒ 跳过（别用骨 tail 当轴）" % cname)
        continue
    rows = []
    for nm in meshes:
        o = bpy.data.objects.get(nm)
        if o is None:
            continue
        gi2n = {g.index: g.name for g in o.vertex_groups}
        CO = co_of(o)
        for v in o.data.vertices:
            wd = {gi2n[g.group]: g.weight for g in v.groups if g.weight > 0}
            sw = sum(x for b, x in wd.items() if b in names)
            if sw <= 1e-6:
                continue
            u = u_of(CO[v.index], ax)
            root = sum(x for b, x in wd.items() if b == names[0])
            rows.append((u, root / sw, sw))
    if not rows:
        w("   %-11s 没有任何顶点带该链的权重  !!" % cname)
        continue
    A = np.array(rows)
    w("   %-11s 骨号%-16s 带权顶点 %4d ；链骨权重和 中位 %.3f ；root 占比按 u 分档：" %
      (cname, str(fns), len(A), np.median(A[:, 2])))
    for lo in (0.0, 0.25, 0.5, 0.75):
        # ★ 末档必须用 <=（u 会被 clip 到恰好 1.0；用 < 会把它整批漏掉 —— 实测尾巴少报 549 个顶点）
        m = (A[:, 0] >= lo) & ((A[:, 0] <= lo + 0.25) if lo == 0.75 else (A[:, 0] < lo + 0.25))
        if m.sum() == 0:
            w("        u %.2f~%.2f ：无顶点" % (lo, lo + 0.25))
            continue
        w("        u %.2f~%.2f ：%5d 顶点  root 占比均值 %.3f  tip 占比 %.3f  链权重和均值 %.3f" %
          (lo, lo + 0.25, int(m.sum()), A[m, 1].mean(), 1 - A[m, 1].mean(), A[m, 2].mean()))
w("")
w("WROTE " + OUT)

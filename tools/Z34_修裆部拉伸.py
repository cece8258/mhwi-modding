# -*- coding: utf-8 -*-
"""Z34_修裆部拉伸.py —— 身体侧：把**裆（会阴那一小块）**的腿权重让给骨盆，压掉"腿一动就扯"，
而**不动大腿段**（大腿是圆柱 ⇒ 权重只该随高度变化）。

★ 用户实机反馈两轮（2026-09-23）：
  第一轮："当角色扭腰时，裆部不该被扭成这样 …… 裆部的紧身衣会拉长到腿部"
  第二轮："裆部确实不怎么扭了，**但是大腿的扭曲非常严重**"  ← 第一版修过头了

★ 判据（两个一起看，缺一个就会翻车）：
  ① **摆姿势下的边长拉伸率** `|L/L0−1|`（skill §11.4：症状是视觉的 ⇒ 判据必须是可见量）：
     姿势 = 抬腿 25°（绕 Upper_leg.L 的 head 转 x）/ 扭腰 20°（绕 Spine 的 head 转 z）。
     实测：**扭腰 20° 只把裆部拉 17%（>10% 的边仅 2/2690）；抬腿 25° 拉 178%**
     ⇒ 罪魁是"腿动"不是"腰动"。
  ② ★★ **同一高度环内 w_leg 的 sd**（Z33 的老口径）：圆柱部位（腿）的权重本该**只随高度变化**。
     **第一版只盯①，把 |x| 半宽开到 0.14、一路管到裆底以下 10cm ⇒ 同一高度上"内侧跟骨盆、
     外侧跟腿" ⇒ ①变好了、②从 0.148 涨到 0.256 ⇒ 实机就是"大腿扭曲严重"。**
     ⇒ 影响区必须是**以裆底为中心的椭圆**（越往腿的深处 |x| 越窄），而且②不许比现状变差。

★ 做法：`t = K · (1 − smoothstep(0.55, 1.0, sqrt((x/XR)² + ((z−ZC)/ZR)²)))`，
  把这根顶点的 `t × 腿权重` 从 `Upper_leg.L/R`（按原比例）挪给 `Hips`。
  pool（Hips+两腿）守恒、其余骨一个都不动、椭圆边缘 smoothstep 到 0（无硬边界）。

★ 顺序：**Z33 之后、Z32 之前** —— Z32 会把贴身衣物对齐到"最终的皮肤"，于是紧身衣自动继承同一套权重
  （逐顶点一致 ⇒ 任何姿态下衣物与皮肤都不会相对错动）。

用法: blender -b <工作副本.blend> --python Z34_修裆部拉伸.py -- [报告txt] [crotchx=../crotchz=../crotchk=../crotchzc=..]
  加 dry=1 ⇒ **只在真实权重场上扫参数、不写盘**
  （第一版拿预览 JSON 离线调参跑偏了：预览与工作 blend 的裆部权重场不一样，区域内 Hips 均值 0.616 vs 0.279）
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
OUT = os.path.join(P, "_Z34_裆部拉伸.txt")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for _a in ARGS:
    if _a.endswith(".txt"):
        OUT = _a
S_XF, TZ_XF = 1.379583, -1.026176      # 预览 -> 工作
# ★★ 默认档 = 在"真实权重场 + 双判据"下扫出来的**最保守且有效**的一档（见 `_Z34_扫4.txt`）：
#   XR=0.040 ZR=0.035 K=0.6 → **大腿段(预览 z 0.44~0.62)的环内 sd 与基线 0.0118 分毫不动**
#   （= 不会再造成"大腿扭曲"），髋部带 0.241（Z33 当年实测 0.217 且用户认可，同量级），
#   而拉伸率 p99 2.340→1.606（−31%）。想更狠就 `crotchk=0.9` 或 `crotchz=0.048`，但**必须复核腿段 sd**。
ZC = 0.648        # 椭圆中心 z（预览）= 裆底
XR = 0.040        # |x| 半宽（预览）
ZR = 0.035        # z 半高（预览）
K = 0.60          # 让出强度
for _a in ARGS:
    if _a.startswith("crotchx="):
        XR = float(_a.split("=", 1)[1])
    if _a.startswith("crotchz="):
        ZR = float(_a.split("=", 1)[1])
    if _a.startswith("crotchzc="):
        ZC = float(_a.split("=", 1)[1])
    if _a.startswith("crotchk="):
        K = float(_a.split("=", 1)[1])
B_HIPS, B_ULL, B_ULR = "MhBone_013", "MhBone_014", "MhBone_018"
L = []


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


def pz2w(z):
    return z * S_XF + TZ_XF


def smoothstep(a, b, x):
    t = np.clip((x - a) / max(b - a, 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


bb = bpy.data.objects.get("Body_base")
if bb is None:
    w("!! 找不到 Body_base")
    raise SystemExit(1)
me = bb.data
NV = len(me.vertices)
gi2n = {g.index: g.name for g in bb.vertex_groups}
WORK = np.array([list(v.co) for v in me.vertices], float)
Wd = [{gi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0} for v in me.vertices]
w("### Z34 · 裆部拉伸修正（身体侧，椭圆影响区）")
w("   椭圆：中心 z=%.3f ｜ XR=%.3f ZR=%.3f K=%.2f（预览坐标）" % (ZC, XR, ZR, K))

# ---- 骨架 head（做姿势用）----
AB = None
for o in bpy.data.objects:
    if o.type == "ARMATURE" and "f_body040_0010" in o.name:
        AB = o
bones = {}
if AB is not None:
    _mw = np.array(AB.matrix_world)
    for nm in (B_HIPS, B_ULL, B_ULR, "MhBone_001"):
        b = AB.data.bones.get(nm)
        if b:
            bones[nm] = _mw[:3, :3] @ np.array(b.head_local) + _mw[:3, 3]
    w("   骨架 %s：Hips head %s ／ Upper_leg.L head %s" %
      (AB.name, np.round(bones.get(B_HIPS, [0, 0, 0]), 4).tolist(),
       np.round(bones.get(B_ULL, [0, 0, 0]), 4).tolist()))

# ---- 判据 ①：摆姿势拉伸率（体检区 = 椭圆放大一圈）----
ZC_W = pz2w(ZC)
XR_W, ZR_W = XR * S_XF, ZR * S_XF
D2 = (WORK[:, 0] / XR_W) ** 2 + ((WORK[:, 2] - ZC_W) / ZR_W) ** 2
REG = D2 < 1.0      # 只测**椭圆本身**内的边（第一版放大 √2 后 max 被区外的退化边主导 = 假信号）
EDGES = []
for p in me.polygons:
    vs = list(p.vertices)
    for k in range(len(vs)):
        a, b = vs[k], vs[(k + 1) % len(vs)]
        if REG[a] and REG[b]:
            EDGES.append((a, b))
EDGES = np.array(sorted(set((min(a, b), max(a, b)) for a, b in EDGES))) if EDGES else np.zeros((0, 2), int)
# ---- 判据 ②：大腿各高度环内 w_leg 的 sd（圆柱口径；z 0.44~0.70 预览）----
Z_LO_W, Z_HI_W = pz2w(0.44), pz2w(0.70)


def ring_sd(Wlist, z_lo=0.44, z_hi=0.70):
    leg = np.array([d.get(B_ULL, 0.0) + d.get(B_ULR, 0.0) for d in Wlist])
    sds = []
    # ★★ 环 = **整条大腿的一圈**（不限椭圆！第一版把环限制在椭圆内 ⇒ 那里腿权重本就≈0
    #    ⇒ 现状读数恰好 0.0000（skill：恰好 0 一律当 bug），于是所有候选都被判"变差"）。
    #   只排除中线那一窄条（|x|<0.03，会阴本来就不该跟腿）。
    for lo in np.arange(pz2w(z_lo), pz2w(z_hi), 0.014):
        sel = ((WORK[:, 2] >= lo) & (WORK[:, 2] < lo + 0.014)
               & (np.abs(WORK[:, 0]) > 0.03) & (np.abs(WORK[:, 0]) < 0.35))
        if sel.sum() > 12:
            sds.append(float(leg[sel].std()))
    return (float(np.median(sds)), float(np.max(sds)), len(sds)) if sds else (-1.0, -1.0, 0)


def stretch(Wlist):
    if not len(EDGES) or B_ULL not in bones:
        return None
    h = bones[B_ULL]
    a = np.radians(25.0)
    R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    disp = ((R @ (WORK - h).T).T + h) - WORK
    Pw = WORK + disp * np.array([d.get(B_ULL, 0.0) for d in Wlist])[:, None]
    L0 = np.linalg.norm(WORK[EDGES[:, 0]] - WORK[EDGES[:, 1]], axis=1)
    L1 = np.linalg.norm(Pw[EDGES[:, 0]] - Pw[EDGES[:, 1]], axis=1)
    ok = L0 > 0.003          # 3mm 以下当退化边（1mm 门限会被 1.2mm 的缝边刷出 16x 假信号）
    return np.abs(L1[ok] / L0[ok] - 1.0) if ok.sum() > 10 else None


def apply_bias(Wlist, xr, zr, k, zc=ZC):
    xw, zw, zcw = xr * S_XF, zr * S_XF, pz2w(zc)
    d2 = (WORK[:, 0] / max(xw, 1e-9)) ** 2 + ((WORK[:, 2] - zcw) / max(zw, 1e-9)) ** 2
    tb = k * (1.0 - smoothstep(0.55, 1.0, np.sqrt(d2)))
    Wn = [dict(d) for d in Wlist]
    n = 0
    for vi in range(NV):
        if tb[vi] <= 1e-6:
            continue
        ln = Wn[vi].get(B_ULL, 0.0) + Wn[vi].get(B_ULR, 0.0)
        if ln <= 1e-6:
            continue
        cut = min(tb[vi] * ln, ln)
        sl = Wn[vi].get(B_ULL, 0.0) / ln
        Wn[vi][B_ULL] = Wn[vi].get(B_ULL, 0.0) - cut * sl
        Wn[vi][B_ULR] = Wn[vi].get(B_ULR, 0.0) - cut * (1 - sl)
        Wn[vi][B_HIPS] = Wn[vi].get(B_HIPS, 0.0) + cut
        n += 1
    return Wn, n


w("   体检区（椭圆 x sqrt(2)）：%d 顶点 / %d 边 ；环 sd 统计 %d 环" %
  (int(REG.sum()), len(EDGES), ring_sd(Wd)[2]))
r0, m0 = stretch(Wd), ring_sd(Wd)

# ---- dry：在真实权重场上扫椭圆参数 ----
if any(_a.startswith("dry=") for _a in ARGS):
    w("")
    w("### [dry] 椭圆参数扫描（★ 两个判据一起看）")
    w("   判据① 拉伸率（抬腿 25°）：max/p95/p99 与 >10% 条数 —— 越小越好")
    w("   判据② 大腿环内 w_leg 的 sd：中位/max —— **不许比现状变差**（变差 = 大腿扭曲）")
    w("   %-24s %7s %7s %7s %6s ｜ %9s %9s" %
      ("参数", "max", "p95", "p99", ">10%", "环sd中位", "环sdMax"))
    w("   %-24s %7.3f %7.3f %7.3f %6d ｜ %9.4f %9.4f" %
      ("现状（K=0）", r0.max(), float(np.percentile(r0, 95)), float(np.percentile(r0, 99)),
       int((r0 > 0.10).sum()), m0[0], m0[1]))
    _THIGH = (0.44, 0.62)      # ★ 大腿段：基线 sd 只有 0.0118 ⇒ 任何 |x| 依赖都是凹痕（护栏）
    _HIPBAND = (0.63, 0.70)    # 髋部带：Z33 自己就管这里（它实测 max 0.217 且用户认可）⇒ 只报不判
    m0t = ring_sd(Wd, *_THIGH)
    w("   [护栏] 大腿段(预览 z %.2f~%.2f) 环内 w_leg 的 sd：中位 %.4f max %.4f（%d 环）" %
      (_THIGH[0], _THIGH[1], m0t[0], m0t[1], m0t[2]))
    w("   [参考] 髋部带(z %.2f~%.2f) 现状 max %.4f（Z33 实测过的水平）" %
      (_HIPBAND[0], _HIPBAND[1], ring_sd(Wd, *_HIPBAND)[1]))
    rows = []
    for _xr in (0.040, 0.055):
        for _zr in (0.025, 0.035, 0.048):
            for _k in (0.6, 0.9):
                Wn, _n = apply_bias(Wd, _xr, _zr, _k)
                rr = stretch(Wn)
                if rr is None:
                    continue
                mt = ring_sd(Wn, *_THIGH)
                mh = ring_sd(Wn, *_HIPBAND)
                bad = mt[1] > max(m0t[1] * 1.5, 0.05)
                w("   XR=%.3f ZR=%.3f K=%.1f    %7.3f %7.3f %7.3f %6d ｜ 腿段 %7.4f 髋带 %7.4f%s" %
                  (_xr, _zr, _k, rr.max(), float(np.percentile(rr, 95)),
                   float(np.percentile(rr, 99)), int((rr > 0.10).sum()), mt[1], mh[1],
                   "  << 腿段变差" if bad else "  OK"))
                if not bad:
                    rows.append((float(np.percentile(rr, 99)) + 0.002 * int((rr > 0.10).sum()),
                                 _xr, _zr, _k, mt[1]))
    if rows:
        b = min(rows)
        w("   => 在 腿段环sd 不变差 的候选里最优（p99+0.002 x 条数）：XR=%.3f ZR=%.3f K=%.1f（腿段max %.4f）" %
          (b[1], b[2], b[3], b[4]))
    else:
        w("   !! 所有候选的大腿段环 sd 都变差 => 椭圆还要更小/更靠上")
    w("WROTE " + OUT)
    raise SystemExit(0)

w("   [判据① 修前] 抬腿 25° 拉伸率：max %.3f  p95 %.3f  p99 %.3f  >10%% 的边 %d/%d" %
  (r0.max(), float(np.percentile(r0, 95)), float(np.percentile(r0, 99)),
   int((r0 > 0.10).sum()), len(r0)))
w("   [判据② 修前] 大腿段环内 w_leg 的 sd：中位 %.4f  max %.4f（%d 环）【护栏：基线极低，不许变差】" %
  (ring_sd(Wd, 0.44, 0.62)[0], ring_sd(Wd, 0.44, 0.62)[1], ring_sd(Wd, 0.44, 0.62)[2]))
_leg0 = np.array([d.get(B_ULL, 0.0) + d.get(B_ULR, 0.0) for d in Wd])
for lo in np.arange(Z_LO_W, Z_HI_W, 0.028):
    sel = ((WORK[:, 2] >= lo) & (WORK[:, 2] < lo + 0.028) & (np.abs(WORK[:, 0]) > 0.03)
           & (np.abs(WORK[:, 0]) < 0.35))
    if sel.sum() > 12:
        w("        z(预览) %.3f~%.3f ：%4d 点  腿均值 %.3f  sd %.4f" %
          ((lo - TZ_XF) / S_XF, (lo + 0.028 - TZ_XF) / S_XF, int(sel.sum()),
           float(_leg0[sel].mean()), float(_leg0[sel].std())))

# ---- 施加 ----
Wd_new, n_chg = apply_bias(Wd, XR, ZR, K)
w("   改动顶点 %d（%.1f%% 全网格）" % (n_chg, 100.0 * n_chg / NV))
for g in list(bb.vertex_groups):
    bb.vertex_groups.remove(g)
made = {}
n4 = 0
for vi in range(NV):
    it = sorted(Wd_new[vi].items(), key=lambda kv: -kv[1])
    it = [(b, x) for b, x in it if x > 1e-6][:4]
    tot = sum(x for _, x in it) or 1.0
    if len(it) == 4:
        n4 += 1
    for b, x in it:
        if b not in made:
            made[b] = bb.vertex_groups.new(name=b)
        made[b].add([vi], float(x / tot), "REPLACE")
w("   写回：用骨 %d 个；4 影响的顶点 %d；行和已归一化" % (len(made), n4))

# ---- 复核（★ 删过顶点组 ⇒ 索引变了，必须重建映射）----
gi2n2 = {g.index: g.name for g in bb.vertex_groups}
Wd2 = [{gi2n2[g.group]: float(g.weight) for g in v.groups if g.weight > 0} for v in me.vertices]
m1 = ring_sd(Wd2)
r1 = stretch(Wd2)
w("   [判据① 修后] 抬腿 25° 拉伸率：max %.3f  p95 %.3f  p99 %.3f  >10%% 的边 %d/%d" %
  (r1.max(), float(np.percentile(r1, 95)), float(np.percentile(r1, 99)),
   int((r1 > 0.10).sum()), len(r1)))
w("        => max %.3f->%.3f（%+.0f%%）｜p99 %.3f->%.3f（%+.0f%%）｜>10%% 的边 %d->%d" %
  (r0.max(), r1.max(), 100 * (r1.max() / r0.max() - 1),
   float(np.percentile(r0, 99)), float(np.percentile(r1, 99)),
   100 * (float(np.percentile(r1, 99)) / float(np.percentile(r0, 99)) - 1),
   int((r0 > 0.10).sum()), int((r1 > 0.10).sum())))
_t0, _t1 = ring_sd(Wd, 0.44, 0.62), ring_sd(Wd2, 0.44, 0.62)
w("   [判据② 修后] 大腿段环内 sd：中位 %.4f->%.4f  max %.4f->%.4f  髋带 max %.4f->%.4f  %s" %
  (_t0[0], _t1[0], _t0[1], _t1[1], ring_sd(Wd, 0.63, 0.70)[1], ring_sd(Wd2, 0.63, 0.70)[1],
   "OK 大腿段未变差" if _t1[1] <= max(_t0[1] * 1.5, 0.05) else "!! 大腿段变差（会扭曲）"))
sel = np.where(REG)[0]
w("   区域内 Hips 均值 %.4f->%.4f ／ 腿均值 %.4f->%.4f" %
  (np.mean([Wd[i].get(B_HIPS, 0.0) for i in sel]),
   np.mean([Wd2[i].get(B_HIPS, 0.0) for i in sel]),
   np.mean([Wd[i].get(B_ULL, 0.0) + Wd[i].get(B_ULR, 0.0) for i in sel]),
   np.mean([Wd2[i].get(B_ULL, 0.0) + Wd2[i].get(B_ULR, 0.0) for i in sel])))
w("")
w("WROTE " + OUT)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("SAVED %s" % bpy.data.filepath)
print("DONE")

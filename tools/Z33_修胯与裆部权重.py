# -*- coding: utf-8 -*-
"""Z33_修胯与裆部权重.py —— 把身体（Body_base）在**胯 / 大腿上部 / 裆底**的
`Hips ↔ Upper_leg` 分配改成"**只随高度变化**"的平滑函数，跨过裆底那条硬边界连续。

★ 依据（用户 2026-09-24 实机反馈 + 本脚本的实测，`_m_crotch.py` / `_m_hip.py`）：
  ① **待机"左右切换重心、提胯"时，另一条腿的大腿上部被明显拉扯**：
     实测同一条腿、同一 2cm 高度环内 `Hips` 的 **sd = 0.16~0.23、极差 0.59~0.71**
     ⇒ 一圈里有的顶点跟骨盆、有的跟腿 ⇒ 骨盆一动就在同一圈内错开 = 撕扯。
     （skill 的老规矩：**圆柱部位（腿）的权重本就该只随高度变化**。）
  ② **直立时裆底最下面被"拉向两侧敞开"**：
     实测在 |x|<0.02 的裆底中心有一条 **1~2mm 的硬边界** —— `z=0.639` 处 `Hips=0.46`、
     下一圈 `z=0.641` 处 `Hips=1.00`（下面 100% 跟腿、上面 100% 跟骨盆）
     ⇒ 腿一动，表面正好从这条线撕开。
     （同族教训：skill「改权重的作用域不要用'直角边界'」。）
  另实测确认：**全网格没有任何顶点"被两条腿同时拉"**（UL.L 与 UL.R 同时 >0.2 的顶点 = 0）
  ⇒ 左右分派本身是干净的，问题只在"同一侧内的 Hips/腿 分配有噪声与硬跳"。

★ 做法：对 z ∈ [z0, z1] 的顶点，把 `pool = Hips + Upper_leg.L + Upper_leg.R` 按
  `t = smoothstep((z − z0)/(z1 − z0))` 重新分配：`Hips = pool·t`、腿 = `pool·(1−t)`
  （腿内部按原本 own:other 比例分，实测 other 基本为 0）。
  **其余骨骼（Butt.L/R 的臀部抖动、Lower_leg、Spine…）一个都不动**；
  pool 守恒 ⇒ 总权重不变（无重新归一化带来的副作用）。
  ★ 对"越靠上腿权重越小"的顶点是**恒等变换**（pool≈Hips、t=1 ⇒ 不变）⇒ 只影响真正被腿带的顶点。

★ 目标曲线与原均值的吻合（用实测的均值核对，说明只去噪声、不改整体姿态）：
    z 0.64~0.66 → 目标 0.06 ／ 实测均值 0.17
    z 0.68~0.70 → 目标 0.44 ／ 实测均值 0.41
    z 0.70~0.72 → 目标 0.67 ／ 实测均值 0.60
    z 0.72~0.74 → 目标 0.86 ／ 实测均值 0.79

★ 顺序：必须在 **Z31（脚踝）之后、Z28 / Z32（衣物对齐）之前** —— 衣物要从"最终的皮肤"取权重。

用法: blender -b <工作副本.blend> --python Z33_修胯与裆部权重.py -- [报告txt]
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

P = PROJ
OUT = (sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv
       else os.path.join(P, "_Z33_胯部权重.txt"))
L = []
S_XF, TZ_XF = 1.379583, -1.026176     # 预览 -> 工作（按 z 换算参数用）
# ★★ 分界高度**随 |x| 变化** —— 骨盆下缘是一条曲线：**中线最低（裆底 ≈0.655）、两侧最高（髋 ≈0.705）**。
#   实测（`_m_crotch.py`）：中线 z=0.639 处 Hips 0.46 → z=0.641 处 Hips 1.00（**2mm 的硬跳**，
#   这正是"裆底被拉向两侧敞开"的来源）；两侧在 z 0.67~0.71 间从 0 跳到 0.92（且带内 sd 0.354）。
#   ⚠ 若照"只随高度"一刀切，会把本该跟骨盆的**会阴**拉到腿上（本脚本第一版就犯了这个错）。
ZC_MID, ZC_SIDE = 0.655, 0.705        # 预览 z：分界中心（中线 / 两侧）
ZC_W = 0.05                           # 分界中心随 |x| 过渡的宽度（预览单位）
HW = 0.035                            # 平滑带半宽（全带宽 7cm）⇒ 没有硬边界
KMAX_SAFE = 4
# ★★ 注意：**工作 blend 里 `Body_base` 的顶点组名是 `MhBone_NNN`**（不是预览里的 `Hips`/`Upper_leg.L`）
#    —— 照预览的组名找会全读到 0（本脚本第一版就踩了这个，报告里表现为"改动顶点 0"）。
B_HIPS = "MhBone_013"
B_ULL = "MhBone_014"
B_ULR = "MhBone_018"


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


def smoothstep(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


ob = bpy.data.objects["Body_base"]
mw = np.array(ob.matrix_world)
gi2n = {g.index: g.name for g in ob.vertex_groups}
N = len(ob.data.vertices)
CO = np.array([list(v.co) for v in ob.data.vertices], float)
WP = (mw[:3, :3] @ CO.T).T + mw[:3, 3]
PREZ = (WP[:, 2] - TZ_XF) / S_XF
W0 = [{gi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0.0}
      for v in ob.data.vertices]

w("=" * 100)
w("### Z33 · 修胯 / 大腿上部 / 裆底的 Hips ↔ Upper_leg 分配")
w("=" * 100)
w("   分界中心：中线 z=%.3f（预览）→ 两侧 z=%.3f，随 |x| 在 %.2f 内过渡；平滑带半宽 %.3f（全宽 %.0fmm）"
  % (ZC_MID, ZC_SIDE, ZC_W, HW, 2000 * HW))


def zc_of(x):
    return ZC_MID + (ZC_SIDE - ZC_MID) * smoothstep(abs(x) / ZC_W)


def t_of(x, zp):
    return smoothstep((zp - (zc_of(x) - HW)) / (2.0 * HW))

# ---- 改动前：分侧分带的 sd（用于前后对比）----
def stats(W, lab):
    rows = []
    for tag, xlo, xhi in (("L", 0.03, 0.30), ("R", -0.30, -0.03), ("M", -0.03, 0.03)):
        for lo in np.arange(0.63, 0.77, 0.02):
            hi = lo + 0.02
            m = (PREZ >= lo) & (PREZ < hi) & (WP[:, 0] >= xlo) & (WP[:, 0] < xhi)
            idx = np.where(m)[0]
            if len(idx) < 4:
                continue
            h = np.array([W[i].get(B_HIPS, 0.0) for i in idx])
            rows.append((tag, lo, len(idx), h.mean(), h.std(), h.max() - h.min()))
    w("   [%s] 侧 z档 点数 Hips均值 sd 极差" % lab)
    for tag, lo, n, mu, sd, rng in rows:
        w("      %s z%.2f %3d  %.2f  %.3f  %.2f" % (tag, lo, n, mu, sd, rng))
    sds = np.array([r[4] for r in rows])
    rngs = np.array([r[5] for r in rows])
    w("      ⇒ 带内 sd：中位 %.3f 最大 %.3f ；极差：中位 %.3f 最大 %.3f" %
      (np.median(sds), sds.max(), np.median(rngs), rngs.max()))
    return float(np.median(sds))


sd0 = stats(W0, "改前")

# ---- 改 ----
W1 = []
n_ch = 0
pool_ch = []
for vi in range(N):
    wd = dict(W0[vi])
    pool = wd.get(B_HIPS, 0.0) + wd.get(B_ULL, 0.0) + wd.get(B_ULR, 0.0)
    if pool <= 1e-6:
        W1.append(wd)
        continue
    t = t_of(WP[vi, 0], PREZ[vi])
    hip_new = pool * t
    leg_new = pool * (1.0 - t)
    own = B_ULL if WP[vi, 0] > 0 else B_ULR
    oth = B_ULR if own == B_ULL else B_ULL
    a, b = wd.get(own, 0.0), wd.get(oth, 0.0)
    s = a + b
    if s > 1e-9:
        wn, wo = leg_new * a / s, leg_new * b / s
    else:
        wn, wo = leg_new, 0.0
    for k in (B_HIPS, B_ULL, B_ULR):
        wd.pop(k, None)
    for k, val in ((B_HIPS, hip_new), (own, wn), (oth, wo)):
        if val > 1e-6:
            wd[k] = wd.get(k, 0.0) + val
    if abs((wd.get(B_HIPS, 0.0) + wd.get(own, 0.0) + wd.get(oth, 0.0)) - pool) > 1e-6:
        n_ch += 1
    pool_ch.append(abs(wd.get(B_HIPS, 0.0) - W0[vi].get(B_HIPS, 0.0)))
    W1.append(wd)

# ---- 写回（保留原有影响数：不截断、只重排）----
for g in list(ob.vertex_groups):
    ob.vertex_groups.remove(g)
made = {}
n4 = 0
for vi in range(N):
    it = sorted(W1[vi].items(), key=lambda kv: -kv[1])
    it = [(b, x) for b, x in it if x > 1e-6]
    if not it:
        it = [(B_HIPS, 1.0)]
    if len(it) > KMAX_SAFE:
        n4 += 1
    tot = sum(x for _, x in it)
    for b, x in it:
        if b not in made:
            made[b] = ob.vertex_groups.new(name=b)
        made[b].add([vi], float(x / tot), "REPLACE")

w("")
w("   改动顶点 %d / %d ；pool 守护失败 %d ；影响数 >%d 的顶点 %d ；用组 %d" %
  (int(sum(1 for x in pool_ch if x > 1e-6)), N, n_ch, KMAX_SAFE, n4, len(made)))
w("   Hips 权重变化：|Δ| 中位 %.3f 最大 %.3f（0 表示该顶点本来就没被腿带）" %
  (float(np.median(pool_ch)), float(np.max(pool_ch))))
w("")
gi2n = {g.index: g.name for g in ob.vertex_groups}     # ★ 重建组表（上面全删重建过）
sd1 = stats([{gi2n[g.group]: float(g.weight) for g in v.groups if g.weight > 0.0}
             for v in ob.data.vertices], "改后")
w("")
w("★ 带内 sd 中位：%.3f -> %.3f（越小 ⇒ 同一高度环内越一致 ⇒ 不再撕扯）" % (sd0, sd1))
w("")
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("WROTE " + OUT)
w("SAVED %s" % bpy.data.filepath)
print("DONE")

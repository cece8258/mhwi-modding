# -*- coding: utf-8 -*-
"""探针_素材对拍与小件贴合.py —— **只读**，两个模式（第16次实战用出来的）。

★ 用途 1「对拍」：两个 `blend` 逐件对拍 **父级 / matrix_world 的缩放与平移 / 世界 bbox**。
  典型场景：**用户手改过一版素材工程**（"用我改的那版"）⇒ 先量清楚他改了什么、
  以及**同一个文件里有没有别的东西被带坏**（实测踩过：MH 的 13 件 `mwScale` 0.01→1.0、
  世界坐标≈×100 且轴序被换、贴图目录还没拷过来）。
★ 用途 2「贴合」：量某个**小件**到某个**宿主件**（可多件）表面的最近距离，并可沿一个轴扫位移。
  典型场景："贴在头发上的符咒浮空了" ⇒ 判据是"到宿主表面的最近距离"，而不是靠眼看。
  实测：素材帧 2.44mm（贴着）／只挪主体后 **19.70mm**（= 用户报的浮空）／沿 Y 扫位移**最小就在 Δy=0**
  ⇒ 结论是"小件要**跟着主体一起挪**"，不是"往哪边挪"。

用法:
  # ① 单文件逐件对拍（对两个文件各跑一次，再 diff）
  blender -b <blend> --python 探针_素材对拍与小件贴合.py -- 对拍 <标签> <输出txt>
  # ② 小件贴合 + 扫位移（默认沿 Y，步长/范围可给）
  blender -b <blend> --python 探针_素材对拍与小件贴合.py -- 贴合 <小件名> <宿主件名,逗号分隔> <输出txt> [轴=x|y|z] [扫mm=-20:30:5]
"""
import bpy, sys
import numpy as np

A = sys.argv[sys.argv.index("--") + 1:]
MODE, OUT = A[0], A[-1] if len(A) > 2 else "probe_out.txt"
L = []


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


def wco(o):
    mw = np.array(o.matrix_world)
    co = np.array([list(v.co) for v in o.data.vertices], float)
    return ((mw[:3, :3] @ co.T).T + mw[:3, 3]) if len(co) else np.zeros((0, 3))


if MODE == "对拍":
    TAG = A[1]
    w("### [%s] %s" % (TAG, bpy.data.filepath))
    for c in sorted(bpy.data.collections, key=lambda x: x.name):
        ms = [o for o in c.objects if o.type == "MESH"]
        if not ms:
            continue
        w("")
        w("=== 集合 %s（%d 网格）===" % (c.name, len(ms)))
        for o in sorted(ms, key=lambda x: x.name):
            mw = np.array(o.matrix_world)
            sc = [round(float(np.linalg.norm(mw[:3, i])), 4) for i in range(3)]
            P = wco(o)
            zr = ("z %+.4f~%+.4f" % (P[:, 2].min(), P[:, 2].max())) if len(P) else "-"
            w("   %-22s parent=%-22s scale=%-20s T=(%+.3f,%+.3f,%+.3f) %s" %
              (o.name, (o.parent.name if o.parent else "-"), str(sc),
               mw[0, 3], mw[1, 3], mw[2, 3], zr))
    w("")
    w("★ 对拍要点：① `scale` 若从 0.01 变成 1.0 ⇒ 父级变换丢了；② 世界 bbox 差一个数量级 = 同一件事；")
    w("   ③ 贴图目录（`//Texture/`）不在旁边 ⇒ 图全断（几何仍可读，但别当数据源）。")

elif MODE == "贴合":
    from mathutils.bvhtree import BVHTree
    small = bpy.data.objects[A[1]]
    hosts = [bpy.data.objects[n] for n in A[2].split(",") if n in bpy.data.objects]
    axis, sweep = "y", np.arange(-20.0, 30.1, 5.0) * 0.001
    for a in A[3:-1]:
        if a.startswith("轴="):
            axis = a.split("=")[1]
        if a.startswith("扫mm="):
            lo, hi, st = (float(x) for x in a.split("=")[1].split(":"))
            sweep = np.arange(lo, hi + 1e-9, st) * 0.001
    HV, HP = [], []
    for o in hosts:
        v = wco(o)
        off = len(HV)
        HV.extend([tuple(q) for q in v])
        HP.extend([tuple(x + off for x in p.vertices) for p in o.data.polygons])
    BT = BVHTree.FromPolygons(HV, HP)
    PV = wco(small)
    ai = {"x": 0, "y": 1, "z": 2}[axis]
    w("### 小件 `%s`（%d 顶点）→ 宿主 %s ｜ 轴=%s ｜ 输出 %s" %
      (small.name, len(PV), [o.name for o in hosts], axis, OUT))

    def ds(Q):
        r = [BT.find_nearest(tuple(q))[3] for q in Q]
        return np.array([x for x in r if x is not None]) * 1000.0
    d = ds(PV)
    w("   [现状] 最近距离 中位 %6.2f mm  p10 %6.2f  p90 %6.2f  max %6.2f" %
      (np.median(d), np.percentile(d, 10), np.percentile(d, 90), d.max()))
    w("")
    w("   === 沿 %s 扫位移 ===" % axis)
    w("   %9s %9s %9s %9s" % ("Δ(mm)", "中位", "p10", "max"))
    best = None
    for dy in sweep:
        dv = np.zeros(3)
        dv[ai] = dy
        e = ds(PV + dv)
        w("   %9.1f %9.2f %9.2f %9.2f" % (dy * 1000, np.median(e), np.percentile(e, 10), e.max()))
        if best is None or abs(np.median(e) - 2.0) < abs(best[1] - 2.0):
            best = (dy, float(np.median(e)))
    w("")
    w("   ⇒ 中位最接近 2mm（贴住但不穿插）的一档：Δ%s = **%+.1f mm**（中位 %.2f mm）" %
      (axis, best[0] * 1000, best[1]))
    w("   ★ 若最小档就在 Δ=0 ⇒ 小件本来是对的，**要跟着「主体」一起挪**（别单独往某边挪）。")
else:
    w("!! 未知模式 %r（应为 对拍 / 贴合）" % MODE)
w("WROTE " + OUT)
print("DONE")

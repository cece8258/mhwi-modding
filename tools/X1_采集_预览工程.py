# -*- coding: utf-8 -*-
"""X1_采集_本套头发.py（第7版）—— 只读。采集「本套装 本套 12 件（13 件去掉 Carrot）
+ 头发_头发素材蓬蓬双马尾 7 件 + Body_base/Body」的全部数据。

★★ 本版与前六版最大的不同：**本套装 是"裸 FBX"**，从来没有进过 preview2.blend
   ⇒ 本脚本**自己 import_scene.fbx** 把它导进一个新集合（名字固定 `素材0_本套装`），
   **不保存任何工程**（preview2.blend 原样不动）。
   ★ 导入后对象名会因重名被改：`Tail` → `Tail.003`（preview2 里已有 `Tail`(身体) 与
     `Tail.002`(头发)）⇒ **清单一律按"导入前后对象差集 + 去掉尾部 .NNN"判定，绝不写死名字**。

★ 坐标（`_模组调研\\eku7\\_probe*.txt` 实测）：
  · 本套装 的 `Armature`（162 骨）与 角色 `Armature`（222 骨）逐位同源
    （Hips/Spine/Chest/Neck/Head/Upper_leg.L/…/Little Distal.L **差 0.000000 m**）
    ⇒ **SCALE = 1.0、不配准、不缩放**（比 第6版 的 3.5mm 还干净）。
  · 头发 与 角色 **0 个同名骨**（另一套 VRChat 骨名），但网格是世界尺度 1.0 ⇒ 同样 SCALE = 1.0。

★ 坑1（本版实测**成立**）：`Suit` 的形态键 **`Stocking_ON` 键值 = 1.0**，
  且该键块与 Basis 的**逐顶点最大差 = 14.303 mm** ⇒ **真有形状差**，预览里看到的是"开了丝袜模式"
  的紧身衣 ⇒ 采集端**必须**吃键值（走求值网格）。其余件的键值全 0（`Headband` 那些 44~98mm 的键
  全都是 0）⇒ 走 basis 即可。

★ 坑2：`Stocking` 在 FBX 里 **0 个材质槽**；`Gloves`/`Tail` **没有 UV 层** ⇒ 这三件不能靠 UV 贴图。

★ 坑7：`Suit` 的**槽 2（`NO.1-1`）是 0 面**（`_probe3.txt`）⇒ Y1 按材质拆件时要跳过 0 面槽。

★ 坑3：`Head_Root_Headband.*`（6 段）、`Hip_Root_Suit.*.L/R`（每侧 8 段有权重）、
  `Neck_Root_Choker.*`（11 段）**都可能不沿链** ⇒ 采脚本把**逐段主导组质心**打出来，
  供 Y1 的 `order_segs_geo()` + **兔耳按质心 x 符号分左右**。

输出：
  *_X3_preview.json  给 Y1_构建.py（world / 面 / 全部UV层 / 权重 / 材质 / 矩阵 / 骨架骨 head+tail）
  *_X3_preview.txt   给人看：集合清单 / 逐件 / 顶点组全表（Σw 排序）/ 材质->贴图 / 骨架对拍 /
                     贴合度 / 形态键 basis vs 求值 / 链候选几何 / 鞋底剖面

用法: blender -b "eku\\1\\preview2\\eku_preview2.blend" --python X1_采集_本套头发.py -- <out.json>
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


import bpy, os, re, sys, json
import numpy as np
from mathutils.bvhtree import BVHTree

argv = sys.argv
args = argv[argv.index("--") + 1:]
OUT = args[0]
TXT = OUT.replace(".json", ".txt")
L = []
SCALE = 1.0

FBX = CLOTH_FBX
COLL_NAME = "素材0_本套装"
SKIP_CLOTH = {"Carrot"}          # ★ 用户已确认：四版全删
SKIP_HAIR = set()                # 头发 一件都不删


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(TXT, "w", encoding="utf-8").write("\n".join(L))


def base_of(nm):
    """去掉 Blender 的重名后缀 `.001` / `.003`（★ 只吃纯数字后缀，`NO.1` 不受影响）。"""
    return re.sub(r"\.\d{3}$", "", nm)


def co_of(o, sc=1.0):
    mw = np.array(o.matrix_world)
    co = np.array([list(v.co) for v in o.data.vertices], float)
    if not len(co):
        return co
    return ((mw[:3, :3] @ co.T).T + mw[:3, 3]) * sc


# ================= ⓪ 导入 本套装 FBX =================
w("### 文件 %s" % bpy.data.filepath)
w("")
w("=== ⓪ 导入 本套装 FBX（原预览工程不保存） ===")
_before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=FBX)
NEW_OBJS = [o for o in bpy.data.objects if o not in _before]
w("   FBX = %s" % FBX)
w("   新导入对象 %d 个：%s" % (len(NEW_OBJS), sorted(o.name for o in NEW_OBJS)))

CS = bpy.data.collections.get(COLL_NAME)
if CS is None:
    CS = bpy.data.collections.new(COLL_NAME)
    bpy.context.scene.collection.children.link(CS)
for o in NEW_OBJS:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    CS.objects.link(o)
w("   已收进集合 [%s]" % CS.name)

ARM_NEW = [o for o in NEW_OBJS if o.type == "ARMATURE"]
if not ARM_NEW:
    raise SystemExit("导入里没有 ARMATURE")
CLOTH_ARM = ARM_NEW[0].name           # ★ 按**对象引用**判，绝不按名字
w("   本套装 骨架对象 = %r（骨 %d；★ 名字是导入器给的，按引用用）"
  % (CLOTH_ARM, len(ARM_NEW[0].data.bones)))

# 逐件：去掉尾部 .NNN 后匹配；Carrot 跳过
IMPORTED_MESH = {}
for o in NEW_OBJS:
    if o.type != "MESH":
        continue
    b = base_of(o.name)
    if b in IMPORTED_MESH:
        w("   !! 基准名重复：%s 与 %s 都叫 %s" % (IMPORTED_MESH[b].name, o.name, b))
    IMPORTED_MESH.setdefault(b, o)
w("   导入的网格基准名（%d）：%s" % (len(IMPORTED_MESH), sorted(IMPORTED_MESH)))
for k in sorted(SKIP_CLOTH):
    o = IMPORTED_MESH.pop(k, None)
    w("   ★ 跳过（四版全删）：%s → 实际对象 %s" % (k, o.name if o else "<未导入>"))

CLOTH_OBJ = {k: IMPORTED_MESH[k] for k in sorted(IMPORTED_MESH)}

# ================= ① 集合全表 =================
w("")
w("=== ① 集合与对象 ===")
CH = None
for c in bpy.data.collections:
    if "头发" in c.name:
        CH = c
    if c.objects or c.children:
        w("  [%s] 子集合=%s" % (c.name, [x.name for x in c.children]))
        w("        对象(%d)=%s" % (len(c.objects), [o.name for o in c.objects]))
w("   本套 = %s ；头发 = %s" % (CS.name, CH.name if CH else "!! 未找到"))
if CH is None:
    raise SystemExit("找不到头发 集合")

CLOTH = [o.name for o in CLOTH_OBJ.values()]
HAIR = sorted([o.name for o in CH.objects if o.type == "MESH" and o.name not in SKIP_HAIR])
w("   本套 保留 %d 件：%s" % (len(CLOTH), CLOTH))
w("   本套 跳过：%s" % sorted(SKIP_CLOTH))
w("   头发 保留 %d 件：%s" % (len(HAIR), HAIR))


def find(nm):
    for c in (CS, CH):
        for o in c.objects:
            if o.name == nm and o.type == "MESH":
                return o
    o = bpy.data.objects.get(nm)
    return o if (o and o.type == "MESH") else None


# ================= ★ 坑1：求值网格 =================
DG = bpy.context.evaluated_depsgraph_get()


def eval_mesh_co(o):
    """求值网格的**局部**顶点坐标（吃形态键与修改器）。返回 (co, polys) 或 (None, None)。"""
    try:
        ev = o.evaluated_get(DG)
        me = ev.to_mesh()
        co = np.array([list(v.co) for v in me.vertices], float)
        polys = [list(p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
        return co, polys
    except Exception as e:
        w("   !! 求值网格失败 %s：%s" % (o.name, e))
        return None, None


def info(o, sc, with_keys=True):
    mw = np.array(o.matrix_world)
    keys = []
    sk = o.data.shape_keys
    if sk and with_keys:
        for k in sk.key_blocks:
            keys.append(dict(name=k.name, value=round(float(k.value), 6)))
    co = np.array([list(v.co) for v in o.data.vertices], float)
    polys = [list(p.vertices) for p in o.data.polygons]
    n_basis = len(co)
    used_eval = False
    if sk and any(abs(k["value"]) > 1e-6 for k in keys):
        eco, epolys = eval_mesh_co(o)
        if eco is not None and len(eco) == n_basis:
            co, polys, used_eval = eco, epolys, True
        elif eco is not None:
            w("   !! %s 求值网格顶点数 %d != basis %d ⇒ 退回 basis" %
              (o.name, len(eco), n_basis))
    world = ((mw[:3, :3] @ co.T).T + mw[:3, 3]) * sc if len(co) else co
    uvs = {}
    for uvl in o.data.uv_layers:
        uvs[uvl.name] = [[round(float(d.uv[0]), 6), round(float(d.uv[1]), 6)] for d in uvl.data]
    act = o.data.uv_layers.active.name if o.data.uv_layers.active else (
        list(uvs.keys())[0] if uvs else None)
    first = uvs.get(act, list(uvs.values())[0] if uvs else [])
    gi2n = {g.index: g.name for g in o.vertex_groups}
    vgw = [dict((gi2n[g.group], round(float(g.weight), 6)) for g in v.groups if g.weight > 0.0)
           for v in o.data.vertices]
    return dict(name=o.name, scale=sc, verts=n_basis, used_eval=used_eval,
                polys=[list(q) for q in polys],
                co=[[round(float(x), 6) for x in q] for q in co],
                world=[[round(float(x), 6) for x in q] for q in world],
                uv=first, uv_layer_used=act, uv_all=uvs,
                vgw=vgw,
                mats=[(m.name if m else None) for m in o.data.materials],
                mat_index=[int(p.material_index) for p in o.data.polygons],
                shape_keys=keys,
                matrix_world=[float(x) for x in mw.reshape(-1)],
                parent=(o.parent.name if o.parent else None),
                vgroups=[g.name for g in o.vertex_groups],
                uv_layers=[u.name for u in o.data.uv_layers])


# ================= ③ 采集 =================
w("")
w("=== ③ 采集对象 ===")
out = dict(blend=bpy.data.filepath, scale_cloth=SCALE, scale_hair=SCALE,
           cloth_arm=CLOTH_ARM, hair_arm="Armature.004", objs={})
ALL = [(n, CS, "本套") for n in CLOTH] + [(n, CH, "头发") for n in HAIR]
for n, coll, lab in ALL:
    o = find(n)
    if o is None:
        w("   !! 找不到 %s" % n)
        continue
    d = info(o, SCALE)
    out["objs"][n] = d
    co = np.array(d["world"], float)
    w("   %-22s [%s] 顶点%6d 面%6d 三角%6d  世界 z %+.4f~%+.4f x %+.4f~%+.4f y %+.4f~%+.4f" %
      (n, lab, d["verts"], len(d["polys"]), sum(max(len(p) - 2, 0) for p in d["polys"]),
       co[:, 2].min(), co[:, 2].max(), co[:, 0].min(), co[:, 0].max(),
       co[:, 1].min(), co[:, 1].max()))
    w("        UV层=%s（用「%s」） 形态键=%s 顶点组%d 材质%s 父=%s%s" %
      (d["uv_layers"], d["uv_layer_used"], [(k["name"], k["value"]) for k in d["shape_keys"]],
       len(d["vgroups"]), d["mats"], d["parent"], "  ★吃求值网格" if d["used_eval"] else ""))
for n in ("Body_base", "Body"):
    o = bpy.data.objects.get(n)
    if o is None:
        w("   !! 找不到 %s" % n)
        continue
    d = info(o, 1.0, with_keys=False)
    out["objs"][n] = d
    co = np.array(d["world"], float)
    w("   %-22s [角色] 顶点%6d 面%6d  世界 z %.4f~%.4f  x %.4f~%.4f  材质%s 顶点组%d" %
      (n, d["verts"], len(d["polys"]), co[:, 2].min(), co[:, 2].max(),
       co[:, 0].min(), co[:, 0].max(), d["mats"], len(d["vgroups"])))

# ================= ★ 坑1 验收 =================
w("")
w("=== ③b ★坑1 验收：有形态键的对象，basis 与求值网格的包围盒对比 ===")
for n, coll, lab in ALL:
    o = find(n)
    if o is None or not o.data.shape_keys:
        continue
    keys = [(k.name, round(float(k.value), 4)) for k in o.data.shape_keys.key_blocks]
    if not any(abs(v) > 1e-6 for _k, v in keys):
        w("   %-22s 键值全 0 ⇒ 与 basis 相同（不逐点算）" % n)
        continue
    basis = co_of(o)
    eco, _ = eval_mesh_co(o)
    if eco is None or not len(eco):
        continue
    mw = np.array(o.matrix_world)
    ev = ((mw[:3, :3] @ eco.T).T + mw[:3, 3])
    dmax = float(np.linalg.norm(ev - basis, axis=1).max()) if len(ev) == len(basis) else float("nan")
    w("   %-22s 键值=%s" % (n, keys))
    w("        basis  z %+.4f~%+.4f  x %+.4f~%+.4f  y %+.4f~%+.4f" %
      (basis[:, 2].min(), basis[:, 2].max(), basis[:, 0].min(), basis[:, 0].max(),
       basis[:, 1].min(), basis[:, 1].max()))
    w("        求值   z %+.4f~%+.4f  x %+.4f~%+.4f  y %+.4f~%+.4f   逐顶点最大位移 %.4f m %s" %
      (ev[:, 2].min(), ev[:, 2].max(), ev[:, 0].min(), ev[:, 0].max(),
       ev[:, 1].min(), ev[:, 1].max(), dmax,
       "← ★ 有明显形状差，采集已吃键值" if (dmax == dmax and dmax > 1e-4) else "（与 basis 相同）"))

# ================= ④ 顶点组全表 =================
w("")
w("=== ④ 顶点组全表（★ 定 AUX / 链 的依据） ===")
AGG = {}
for n, coll, lab in ALL:
    if n not in out["objs"]:
        continue
    d = out["objs"][n]
    co = np.array(d["world"], float)
    cnt, sw, cs = {}, {}, {}
    for vi, wd in enumerate(d["vgw"]):
        for g, x in wd.items():
            cnt[g] = cnt.get(g, 0) + 1
            sw[g] = sw.get(g, 0.0) + x
            cs[g] = cs.get(g, np.zeros(3)) + co[vi] * x
    tot = sum(sw.values()) or 1.0
    w("   --- %s（%d 组，Σw=%.1f，顶点%d）---" % (n, len(cnt), tot, d["verts"]))
    for g in sorted(sw, key=lambda k: -sw[k]):
        cen = cs[g] / max(sw[g], 1e-12)
        d2 = AGG.setdefault(g, dict(sw=0.0, cnt=0, c=np.zeros(3), objs=[]))
        d2["sw"] += sw[g]
        d2["cnt"] += cnt[g]
        d2["c"] += cen * sw[g]
        d2["objs"].append((n, round(100.0 * sw[g] / max(tot, 1e-9), 2)))
        w("       %-30s 影响%6d Σw=%9.2f 占%5.2f%% 质心(%+.4f,%+.4f,%+.4f)" %
          (g, cnt[g], sw[g], 100.0 * sw[g] / max(tot, 1e-9), cen[0], cen[1], cen[2]))

w("")
w("=== ④b 跨件汇总（用于定 AUX 表 / 判真身骨） ===")
EKUB = set(bpy.data.objects["Armature"].data.bones.keys()) if bpy.data.objects.get("Armature") else set()
for g in sorted(AGG, key=lambda k: -AGG[k]["sw"]):
    d2 = AGG[g]
    cen = d2["c"] / max(d2["sw"], 1e-12)
    w("   %-30s %-4s Σw=%9.2f 影响%6d 质心(%+.4f,%+.4f,%+.4f)  %s" %
      (g, "真身" if g in EKUB else "辅骨", d2["sw"], d2["cnt"], cen[0], cen[1], cen[2],
       [x[0] for x in d2["objs"]]))

# ================= ⑤ 材质 -> 贴图 =================
w("")
w("=== ⑤ 材质（每网格：材质名 / 面数 / 贴图 / baseColor） ===")
from collections import Counter
for n, coll, lab in ALL:
    if n not in out["objs"]:
        continue
    d = out["objs"][n]
    c = Counter(d["mat_index"])
    w("   --- %s ---" % n)
    if not d["mats"]:
        w("       !! **没有任何材质槽**（FBX 里没给）⇒ 目标材质取 MAT_OF 的 mainkey")
        continue
    for mi, m in enumerate(d["mats"]):
        texs, col, met, rgh = [], None, None, None
        mo = bpy.data.materials.get(m) if m else None
        if mo and mo.use_nodes:
            for nd in mo.node_tree.nodes:
                if nd.type == "TEX_IMAGE" and nd.image:
                    texs.append((nd.image.name, getattr(nd, "uv_map", "")))
                if nd.type == "BSDF_PRINCIPLED":
                    col = [round(float(x), 3) for x in nd.inputs["Base Color"].default_value]
                    met = round(float(nd.inputs["Metallic"].default_value), 3)
                    rgh = round(float(nd.inputs["Roughness"].default_value), 3)
        w("       [%d] %-30s 面%6d tex=%s%s" %
          (mi, m, c.get(mi, 0), texs,
           ("  baseColor=%s Metallic=%s Roughness=%s" % (col, met, rgh)) if col else ""))

# ================= ⑥ 骨架对拍 =================
w("")
w("=== ⑥ 骨架（head/tail 按本版 SCALE；角色 与素材对拍） ===")
ARMS = [o for o in bpy.data.objects if o.type == "ARMATURE"]
out["arm_bones"] = {}
for a in ARMS:
    mw = np.array(a.matrix_world)
    w("   %-20s 骨=%3d loc=%s 轴模长=%s" %
      (a.name, len(a.data.bones), np.round(mw[:3, 3], 4).tolist(),
       np.round([np.linalg.norm(mw[:3, i]) for i in range(3)], 4).tolist()))
for a in ARMS:
    mw = np.array(a.matrix_world)
    rec = {}
    for b in a.data.bones:
        h = ((mw[:3, :3] @ np.array(b.head_local)) + mw[:3, 3]) * SCALE
        t = ((mw[:3, :3] @ np.array(b.tail_local)) + mw[:3, 3]) * SCALE
        rec[b.name] = dict(head=[round(float(x), 6) for x in h],
                           tail=[round(float(x), 6) for x in t],
                           parent=(b.parent.name if b.parent else None))
    out["arm_bones"][a.name] = rec

eku = out["arm_bones"].get("Armature")
for cname, lab in ((CLOTH_ARM, "本套"), ("Armature.004", "头发")):
    rec = out["arm_bones"].get(cname)
    if rec is None or eku is None:
        continue
    same = [k for k in rec if k in eku]
    dd = [np.linalg.norm(np.array(rec[k]["head"]) - np.array(eku[k]["head"])) for k in same]
    if not same:
        w("   [%s] %s：骨 %d，与 角色 **0 个同名骨** ⇒ 另一套骨名，网格直接按世界坐标用（SCALE=1.0）"
          % (lab, cname, len(rec)))
    else:
        dd.sort()
        w("   [%s] %s：骨 %d，与 角色 同名 %d 个；head 距离 max %.6f 中位 %.6f" %
          (lab, cname, len(rec), len(same), max(dd), float(np.median(dd))))
        bad = sorted([(np.linalg.norm(np.array(rec[k]["head"]) - np.array(eku[k]["head"])), k)
                      for k in same], reverse=True)[:8]
        w("        差最大的 8 根：%s" % ["%s %.4f" % (k, v) for v, k in bad])
        w("        ⇒ 判定：%s" % ("★ 逐位同源（差 0.000000 m 档）⇒ SCALE=1.0、不配准"
                                  if max(dd) < 1e-4 else
                                  ("基本同源" if max(dd) < 0.03 else "!! 需要配准，见 X4_对齐体检")))
only_c = sorted(set(out["arm_bones"].get(CLOTH_ARM, {})) - set(eku or {}))
w("   本套 独有骨（%d）：%s" % (len(only_c), only_c))
only_h = sorted(set(out["arm_bones"].get("Armature.004", {})) - set(eku or {}))
w("   头发 独有骨（%d）：%s" % (len(only_h), only_h))

# ================= ⑦ 贴合度 =================
w("")
w("=== ⑦ 贴合度（保留件 -> Body_base 的有符号距离；正=在外侧） ===")


def bvh_of(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    mw = np.array(o.matrix_world)
    vs = [tuple(((mw[:3, :3] @ np.array(v.co)) + mw[:3, 3])) for v in o.data.vertices]
    ps = [tuple(p.vertices) for p in o.data.polygons]
    return BVHTree.FromPolygons(vs, ps)


BT = bvh_of("Body_base")
if BT is not None:
    for n, coll, lab in ALL:
        if n not in out["objs"]:
            continue
        co = np.array(out["objs"][n]["world"], float)
        sg, ds = [], []
        for q in co:
            loc, nrm, idx, dist = BT.find_nearest(tuple(q))
            if loc is None:
                continue
            ds.append(float(dist))
            sg.append(float(np.dot(np.array(q) - np.array(loc), np.array(nrm))))
        sg, ds = np.array(sg), np.array(ds)
        w("   %-22s |d|中位%.4f p95 %.4f ；sgn min%+.4f 中位%+.4f 陷入(<0) %.2f%%" %
          (n, np.median(ds), np.percentile(ds, 95), np.nanmin(sg), np.nanmedian(sg),
           100.0 * np.mean(sg < 0)))

# ================= ⑧ 逐槽成分（判"哪一槽是布/金属/毛"，★ 坑7：0 面槽要跳过） =================
w("")
w("=== ⑧ 逐件逐材质槽：面数 + 包围盒（world） ===")
for n in CLOTH:
    d = out["objs"].get(n)
    if d is None:
        continue
    co = np.array(d["world"], float)
    mi = np.array(d["mat_index"], int)
    polys = d["polys"]
    w("   [%s]  面数=%d  槽数=%d" % (n, len(polys), len(d["mats"])))
    for k, mname in enumerate(d["mats"]):
        sel = [j for j, p in enumerate(polys) if mi[j] == k]
        if not sel:
            w("      slot%d %-12s 面=   0   ★ 0 面槽（拆件时必须跳过）" % (k, mname))
            continue
        vs = sorted({v for j in sel for v in polys[j]})
        P = co[vs]
        w("      slot%d %-12s 面=%6d 顶点=%6d bbox x[%+.4f,%+.4f] y[%+.4f,%+.4f] z[%+.4f,%+.4f]" %
          (k, mname, len(sel), len(vs),
           P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(),
           P[:, 2].min(), P[:, 2].max()))

# ================= ⑨ 链候选几何 =================
w("")
w("=== ⑨ 链候选几何（主导组质心 + 包围盒；★ 作者编号不沿链 ⇒ 必须按几何排序） ===")
KEYOBJ = ["Headband", "Choker", "Bag", "Tail", "Suit", "Arm warmers"]
for nm in KEYOBJ:
    o = CLOTH_OBJ.get(nm) if nm in CLOTH_OBJ else find(nm)
    if o is None:
        w("   !! 找不到 %s" % nm)
        continue
    co = co_of(o, SCALE)
    d0 = out["objs"].get(o.name)
    if d0 is None:
        w("   !! %s（对象 %s）不在采集表里" % (nm, o.name))
        continue
    gi2n = {g.index: g.name for g in o.vertex_groups}
    groups = {}
    for vi, v in enumerate(o.data.vertices):
        if not v.groups:
            continue
        best = max(v.groups, key=lambda g: g.weight)
        groups.setdefault(gi2n[best.group], []).append(vi)
    w("   --- %s（对象 %s，顶点 %d，%d 个主导组）---" % (nm, o.name, len(co), len(groups)))
    for g in sorted(groups, key=lambda k: -len(groups[k])):
        idx = groups[g]
        P = co[idx]
        if len(P) < 3:
            w("       %-30s 主导%5d 点太少" % (g, len(idx)))
            continue
        c = P.mean(0)
        sw = 0.0
        for vi in idx:
            for gg in o.data.vertices[vi].groups:
                if gi2n[gg.group] == g:
                    sw += gg.weight
        w("       %-30s 主导%5d Σw=%8.2f 质心(%+.4f,%+.4f,%+.4f) 盒 x%+.3f~%+.3f y%+.3f~%+.3f z%+.3f~%+.3f" %
          (g, len(idx), sw, c[0], c[1], c[2],
           P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(),
           P[:, 2].min(), P[:, 2].max()))
    w("       全部组名：%s" % sorted(o.vertex_groups.keys()))
    tot = {}
    for vi, wd in enumerate(d0["vgw"]):
        for g, x in wd.items():
            tot[g] = tot.get(g, 0.0) + x
    w("       Σw 排序前 14：%s" % sorted(tot.items(), key=lambda kv: -kv[1])[:14])

# ================= ⑩ ★ 坑3 前置：兔耳 6 段按质心 x 分左右 =================
w("")
w("=== ⑩ 兔耳：`Head_Root_Headband.*` 逐段质心（按 x 符号分左右耳；★ 不假设编号是 LLLRRR） ===")
d = out["objs"].get("Headband")
if d is not None:
    co = np.array(d["world"], float)
    seg = {}
    for vi, wd in enumerate(d["vgw"]):
        for g, x in wd.items():
            if g.startswith("Head_Root_Headband"):
                s = seg.setdefault(g, [0.0, np.zeros(3)])
                s[0] += x
                s[1] += co[vi] * x
    for g in sorted(seg):
        sw, c = seg[g]
        c = c / max(sw, 1e-12)
        w("   %-30s Σw=%8.2f 质心 x=%+.4f y=%+.4f z=%+.4f  ⇒ %s" %
          (g, sw, c[0], c[1], c[2], "左(+x)" if c[0] > 0 else "右(−x)"))

# ================= ⑪ ★ 鞋底剖面（Shoes / Stocking，沿脚长 y 分档取最低 z） =================
w("")
w("=== ⑪ 鞋底剖面（沿脚长 y 分档取最低 z；y 越小越靠脚尖） ===")


def sole(pts, lab):
    if not len(pts):
        w("   [%s] 无点" % lab)
        return
    edges = [-0.16, -0.12, -0.08, -0.04, 0.0, 0.04, 0.08]
    w("   [%s] n=%d  z范围 %.4f~%.4f  y范围 %.4f~%.4f" %
      (lab, len(pts), pts[:, 2].min(), pts[:, 2].max(), pts[:, 1].min(), pts[:, 1].max()))
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        sel = (pts[:, 1] >= lo) & (pts[:, 1] < hi)
        n = int(sel.sum())
        w("      y[%+.2f,%+.2f) n=%5d  最低z=%s" %
          (lo, hi, n, ("%.4f" % pts[sel, 2].min()) if n else "—"))


for nm in ("Shoes", "Stocking"):
    d = out["objs"].get(nm)
    if d is None:
        continue
    co = np.array(d["world"], float)
    sole(co[co[:, 0] > 0], "%s 左脚(+x)" % nm)
bb = out["objs"].get("Body_base")
if bb is not None:
    co = np.array(bb["world"], float)
    sole(co[co[:, 0] > 0], "Body_base 左脚(+x)")

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
w("")
w("WROTE %s  (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))
w("SAVED")
print("DONE")

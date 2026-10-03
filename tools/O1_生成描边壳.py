# -*- coding: utf-8 -*-

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


r"""O1_生成描边壳.py — 给 5 件头发 + 耳朵 + 尾巴生成「反法线外壳（外扩式 inverted hull）」

参考实现 = Alf 的描边（_模组调研\epv与描边_调研.md B 部分 + 本次 o1/o3/o4 复核）：
   · 沿本体顶点法线外扩 0.10 mod3 单位
   · 反转三角绕序
   · 顶点法线取反（导出后的表现 = 有符号体积为负、面法线指向本体内部）
   · 独立新材质名（不与本体共用）
   · 顶点权重与本体完全一致（不改权重、不改骨骼）

尺度换算依据（本次 o8 实测 + o6 dump）：
   · Alf body x 跨度 155.63 mod3 单位；我们 body x 跨度 155.05 mod3 单位（同尺度）
   · 我们 body 主网格 y 跨度 172.481 mod3 单位；Blender 里 body 集合世界 z 跨度 1.7248 m
   · ⇒ **1 Blender 单位 = 100 mod3 单位**，1 mod3 单位 = 1 cm
   · ⇒ 外扩 0.10 mod3 单位 = 0.001 Blender 单位（= 1 mm）

形态键陷阱：导出器读 obj.evaluated_get(dg)，改 mesh.vertices 会被形态键覆盖
⇒ 这里把每个顶点的位移 delta 同步加到**所有**形态键块（含 Basis）。

★ 第三轮（2026-09-18 实测反馈：蝴蝶结从白变黑）追加的「排除带」：
    实测（_outline\r2/r3/r4）：蝴蝶结 = 独立网格 `Acc_Ribbon`（材质 Ch_Pl_Standard_Mt__04，
    920 顶点 / 1776 三角，PCA 第三轴 ±0.993 ⇒ **双面薄片**），它**自己没有描边壳**。
    但它贴在头发卡片表面外侧只有 **0.0087 mod3 单位（≈0.09 mm）**，而头发的描边壳是
    从卡片往外 0.10 单位 ⇒ **壳正好糊在蝴蝶结外面那一层**，把白蝴蝶结整片盖成黑的
    （r4 实测：壳 mesh10 有 282 面、mesh12 有 75 面落在"蝴蝶结外扩 0.2 单位"这条带里）。
    修法（只改这一件事）：把壳上**离蝴蝶结表面 < EXCLUDE_M 的面整片丢掉**。
    r4 实测代价：31773 三角里丢 357 个 = **1.12%**，其余 98.88% 的头发轮廓线保留。

幂等：先删掉所有名字以 __Outline 结尾的旧壳，再从本体重建。

用法（后台）：blender -b <blend> --python O1_生成描边壳.py
"""
import bpy
import os
import json
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJ = PROJ
OUTDIR = os.path.join(PROJ, "_outline")
LOG = os.path.join(OUTDIR, "o15_shell_log.txt")
REPORT = os.path.join(OUTDIR, "o15_shell_report.json")

OFFSET_M = 0.001          # = 0.10 mod3 单位，见文件头尺度依据
MAT_NAME = "Outline_Black"
SUFFIX = "__Outline_Black"
TARGETS = ["Hair_Atama", "Hair_Center", "Hair_Tail_Back",
           "Hair_Tail_Front_L", "Hair_Tail_Front_R", "Animal_Ear", "Tail"]
# ★ 排除带：蝴蝶结（Acc_Ribbon）周围的壳面不要（原因见文件头）
BOW_OBJECT = "Acc_Ribbon"
EXCLUDE_M = 0.002         # = 0.20 mod3 单位；0 = 关掉这个排除

L = []
bow_bvh = None            # 排除带的 BVH（在 main 里建）


def P(s=""):
    L.append(str(s))
    print(s, flush=True)


def ensure_object_mode():
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except RuntimeError:
        pass


def get_material():
    m = bpy.data.materials.get(MAT_NAME)
    if m is None:
        m = bpy.data.materials.new(MAT_NAME)
    m.name = MAT_NAME
    # 观感无所谓（游戏用 mrl3），但设成不透明以免预览出问题
    try:
        m.blend_method = "OPAQUE"
    except Exception:
        pass
    return m


def remove_old_shells():
    gone = []
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o.name.endswith(SUFFIX):
            gone.append(o.name)
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me and me.users == 0:
                bpy.data.meshes.remove(me)
    return gone


def world_space_normal_dirs(obj):
    """返回每个顶点的「本体世界空间外法线」，方向取 mesh.vertices[i].normal（局部），
    再用 matrix_world 的法线矩阵转到世界。本项目 matrix_world 是单位矩阵，但保持一致。"""
    me = obj.data
    nm = obj.matrix_world.to_3x3().inverted().transposed()
    out = []
    for v in me.vertices:
        n = nm @ v.normal
        if n.length < 1e-9:
            out.append(Vector((0.0, 0.0, 0.0)))
        else:
            out.append(n.normalized())
    return out


def build_bow_bvh():
    """为排除带建蝴蝶结表面的 BVH（世界坐标；本项目各对象 matrix_world 都是单位阵）。"""
    if not BOW_OBJECT or EXCLUDE_M <= 0:
        return None, None
    o = bpy.data.objects.get(BOW_OBJECT)
    if o is None:
        P("!! 排除带：找不到对象 %s（跳过排除）" % BOW_OBJECT)
        return None, None
    mw = o.matrix_world
    verts = [mw @ v.co for v in o.data.vertices]
    tris = [tuple(p.vertices) for p in o.data.polygons if len(p.vertices) == 3]
    if not tris:
        P("!! 排除带：%s 没有三角面（跳过排除）" % BOW_OBJECT)
        return None, None
    bvh = BVHTree.FromPolygons(verts, tris, all_triangles=True)
    P("排除带基准 = %s：顶点 %d / 三角 %d（世界坐标 BVH 已建）" %
      (BOW_OBJECT, len(verts), len(tris)))
    return bvh, o


def make_shell(src_name):
    src = bpy.data.objects.get(src_name)
    if src is None:
        P("!! 找不到 %s" % src_name)
        return None
    if src.data.users > 1:
        src.data = src.data.copy()
    me0 = src.data
    nv = len(me0.vertices)

    # ---- 外扩位移（世界空间方向 × OFFSET_M，matrix_world 为单位阵时即局部空间）----
    dirs = world_space_normal_dirs(src)
    zero_n = sum(1 for d in dirs if d.length < 1e-9)

    # ---- 复制对象（含顶点组 / 修改器 / 父级 / 集合）----
    new = src.copy()                      # 复制对象（含修改器栈、顶点组、父级）
    new.data = src.data.copy()            # 独占网格数据（保留形态键）
    new.name = src.name + SUFFIX
    new.data.name = src.name + SUFFIX
    for c in list(src.users_collection):
        if new.name not in c.objects:
            c.objects.link(new)
    ensure_object_mode()
    bpy.context.view_layer.objects.active = new

    me = new.data
    assert len(me.vertices) == nv, "顶点数不一致"

    # ---- 1) 沿法线外扩（同时写进所有形态键块）----
    deltas = []
    for i, v in enumerate(me.vertices):
        d = dirs[i] * OFFSET_M
        deltas.append(d)
        v.co = v.co + d
    me.update()

    nk = 0
    # （形态键的位移同步挪到"排除带"之后做：删面会让顶点重排，见下面 ---- 3) ----）

    # ---- 2) 反转绕序 + 顶点法线取反（= 用 flip_normals，参考实现就是这么做的）----
    before = [v.normal.copy() for v in me.vertices]
    wind_before = [list(p.vertices) for p in me.polygons[:5]]
    n_poly_before = len(me.polygons)
    bpy.ops.object.select_all(action="DESELECT")
    new.select_set(True)
    bpy.context.view_layer.objects.active = new
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    after = [v.normal.copy() for v in me.vertices]
    me2 = new.data
    wind_after = [list(p.vertices) for p in me2.polygons[:5]]
    # 绕序是否真的反了：(a,b,c) -> (a,c,b)（循环等价形式也算反）
    def is_rev(a, b):
        if len(a) != 3 or len(b) != 3:
            return a != b
        same = (a == b) or (a == [b[1], b[2], b[0]]) or (a == [b[2], b[0], b[1]])
        return not same
    rev_ok = all(is_rev(wind_before[i], wind_after[i])
                 for i in range(min(len(wind_before), len(wind_after))))
    n_rev = sum(1 for i in range(min(len(wind_before), len(wind_after)))
                if is_rev(wind_before[i], wind_after[i]))

    # ---- 3) 排除带：丢掉"糊在蝴蝶结外面"的那批壳面（第三轮追加，见文件头）----
    nk = 0
    exc = dict(faces=0, verts_before=nv, polys_before=n_poly_before,
               dist_min=None, dist_med=None, shapekey_blocks_synced=0)
    if EXCLUDE_M > 0 and bow_bvh is not None:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me2)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        dd = []
        for v in bm.verts:
            res = bow_bvh.find_nearest(v.co)
            d = res[3] if res else None
            dd.append(d if d is not None else 1e9)
        if dd:
            dd_sorted = sorted(dd)
            exc["dist_min"] = dd_sorted[0]
            exc["dist_med"] = dd_sorted[len(dd_sorted) // 2]
        kill = [f for f in bm.faces if min(dd[v.index] for v in f.verts) < EXCLUDE_M]
        exc["faces"] = len(kill)
        survivor = None
        if kill:
            bmesh.ops.delete(bm, geom=kill, context="FACES")
            orphan = [v for v in bm.verts if not v.link_faces]
            if orphan:
                bmesh.ops.delete(bm, geom=orphan, context="VERTS")
            exc["orphan_verts"] = len(orphan)
            survivor = [v.index for v in bm.verts if v.link_faces]
        bm.to_mesh(me2)
        bm.free()
        me2.update()
        exc["verts_after"] = len(me2.vertices)
        exc["polys_after"] = len(me2.polygons)
        P("     [排除带] 离 %s 表面 < %.4f m 的壳面丢掉 %d 个；顶点 %d -> %d，面 %d -> %d"
          "（壳顶点到蝴蝶结的最小距离=%.4f m，中位=%.4f m）" %
          (BOW_OBJECT, EXCLUDE_M, exc["faces"], exc["verts_before"], exc["verts_after"],
           exc["polys_before"], exc["polys_after"],
           exc["dist_min"] if exc["dist_min"] is not None else -1.0,
           exc["dist_med"] if exc["dist_med"] is not None else -1.0))
        # 形态键：bm.to_mesh 会重排顶点顺序 ⇒ 用 survivor（保留顶点在**旧**索引里的顺序）
        # 把位移补到每个形态键块上
        if me2.shape_keys and survivor is not None:
            nkb = len(me2.shape_keys.key_blocks[0].data)
            if nkb != len(survivor):
                P("     !! 形态键块顶点数 %d != 保留顶点数 %d —— 跳过形态键同步" %
                  (nkb, len(survivor)))
            else:
                for kb in me2.shape_keys.key_blocks:
                    for j, orig in enumerate(survivor):
                        kb.data[j].co = kb.data[j].co + deltas[orig]
                    nk += 1
                me2.update()
        elif me2.shape_keys:
            for kb in me2.shape_keys.key_blocks:
                for i in range(len(me2.vertices)):
                    kb.data[i].co = kb.data[i].co + deltas[i]
                nk += 1
            me2.update()
    else:
        if me2.shape_keys:
            for kb in me2.shape_keys.key_blocks:
                for i in range(len(me2.vertices)):
                    kb.data[i].co = kb.data[i].co + deltas[i]
                nk += 1
            me2.update()
        P("     [排除带] 已关闭（EXCLUDE_M=0 或找不到 %s）" % BOW_OBJECT)
    exc["shapekey_blocks_synced"] = nk

    # ---- 3) 材质 ----
    mat = get_material()
    me2.materials.clear()
    me2.materials.append(mat)

    # ---- 4) 度量（只对"留下来的"顶点算；删过面的壳顶点数会变少）----
    keep = list(range(len(after)))
    if exc.get("verts_after") is not None and exc["verts_after"] < len(after):
        # 删过面：after/before/deltas 里只有 survivor 那些还有意义，
        # 这里退化成"按坐标就近匹配"太脆，直接跳过这两项度量并标注
        keep = None
    if keep is not None:
        dot = []
        for i in keep:
            b = before[i]
            a = after[i]
            if b.length > 1e-9 and a.length > 1e-9:
                dot.append(b.normalized().dot(a.normalized()))
        ndot_med = sorted(dot)[len(dot) // 2] if dot else float("nan")
        neg_frac = (sum(1 for d in dot if d < 0) / len(dot)) if dot else float("nan")
        align = []
        for i in keep:
            d = deltas[i]
            a = after[i]
            if d.length > 1e-9 and a.length > 1e-9:
                align.append(d.normalized().dot(a.normalized()))
        align_med = sorted(align)[len(align) // 2] if align else float("nan")
    else:
        ndot_med = neg_frac = align_med = float("nan")

    # 权重复核：只抽查前 300 个顶点（删面后索引对不上，改按"保留顶点"的坐标匹配太脆，
    # 这里只做"顶点组名字集合 + 前 300 点权重分布"的粗核）
    wmatch = True
    nchk = min(300, len(me2.vertices), len(src.data.vertices))
    for i in range(nchk):
        a = {g.group: round(g.weight, 6) for g in src.data.vertices[i].groups}
        b = {g.group: round(g.weight, 6) for g in me2.vertices[i].groups}
        if a != b:
            wmatch = False
            break

    info = dict(name=new.name, src=src_name, verts=nv,
                verts_after=len(me2.vertices),
                polys=len(me2.polygons), tris=sum(1 for p in me2.polygons if len(p.vertices) == 3),
                shapekeys=len(me2.shape_keys.key_blocks) if me2.shape_keys else 0,
                shapekey_blocks_synced=nk,
                exclude=exc,
                offset_m=OFFSET_M, zero_normal_verts=zero_n,
                normal_flip_ndot_med=ndot_med, normal_flip_neg_frac=neg_frac,
                offset_vs_newnormal_med=align_med,
                winding_reversed=rev_ok, winding_checked=min(len(wind_before), len(wind_after)),
                weights_identical_head300=wmatch,
                vgroups=len(new.vertex_groups),
                material=me2.materials[0].name if me2.materials else None,
                collections=[c.name for c in new.users_collection],
                modifiers=[(m.type, getattr(m, "object", None).name if getattr(m, "object", None) else None)
                           for m in new.modifiers],
                parent=new.parent.name if new.parent else None)
    P("  %-24s -> %-34s v=%5d->%5d tri=%5d keys=%2d/%2d | 排除面=%d | "
      "法线取反 ndot中位=%+.4f (<0 %.4f) | 绕序反转=%s | 权重粗核=%s" %
      (src_name, new.name, nv, info["verts_after"], info["tris"],
       info["shapekey_blocks_synced"], info["shapekeys"], exc.get("faces", 0),
       ndot_med, neg_frac, rev_ok, wmatch))
    return info


def main():
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except RuntimeError:
        pass
    P("=" * 110)
    P("### O1 · 生成描边壳（外扩 %.3f m = %.2f mod3 单位，材质名 %s）" %
      (OFFSET_M, OFFSET_M * 100, MAT_NAME))
    P("=" * 110)
    P("blend: %s" % bpy.data.filepath)

    gone = remove_old_shells()
    if gone:
        P("先删掉旧壳 %d 个: %s" % (len(gone), gone))

    global bow_bvh
    bow_bvh, _bowobj = build_bow_bvh()

    infos = []
    for t in TARGETS:
        r = make_shell(t)
        if r:
            infos.append(r)

    P("")
    P("汇总：新壳 %d 个，顶点 %d（本体合计 %d），三角 %d，"
      "排除带丢掉的面 %d 个，同步过的形态键块 %d 个" %
      (len(infos), sum(i["verts_after"] for i in infos), sum(i["verts"] for i in infos),
       sum(i["tris"] for i in infos),
       sum(i["exclude"].get("faces", 0) for i in infos),
       sum(i["shapekey_blocks_synced"] for i in infos)))
    all_w = all(i["weights_identical_head300"] for i in infos)
    all_r = all(i["winding_reversed"] for i in infos)
    P("  权重粗核（前 300 顶点）: %s" % all_w)
    P("  三角绕序反转: %s" % all_r)
    P("  排除带: %s = %s 周围 %.4f m" %
      ("开" if EXCLUDE_M > 0 else "关", BOW_OBJECT, EXCLUDE_M))

    json.dump(dict(offset_m=OFFSET_M, material=MAT_NAME, targets=TARGETS,
                   exclude_object=BOW_OBJECT, exclude_m=EXCLUDE_M, shells=infos),
              open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(LOG, "w", encoding="utf-8").write("\n".join(L))
    P("wrote %s / %s" % (LOG, REPORT))
    # ★ SAVE 开关：先跑 dry-run（False）确认数字；确认无误后改成 True 再跑一次。
    SAVE = True
    if SAVE:
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        P("已保存 blend: %s" % bpy.data.filepath)
    else:
        P("dry-run：未保存 blend")


main()

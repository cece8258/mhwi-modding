# -*- coding: utf-8 -*-
"""
阶段B · 步骤7：导出 4 个 mod3
================================
对 4 个 mod3 子集合各导出一次。每次会把目标集合写到插件的
`exportMod3Collection` 上（导出器就是读这个值的）。

输出目录：<本脚本所在目录>\_mod3\
    f_body040_0010.mod3
    f_arm040_0010.mod3
    f_wst040_0010.mod3
    f_leg040_0010.mod3

★ 导出前会先做一次完整预检（松散顶点/UV/三角面/权重/材质名/骨数），
  任何一项不过就报出来，避免导出器弹一堆错。

跑之前 Ctrl+S。本脚本**不改场景**（只导出），所以不自动保存。
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


import bpy
import os
import re
import shutil

OUT_DIR = MOD3_DIR
LOG_PATH = EXPORT_LOG


def P(*a):
    print(*a, flush=True)


def off_console():
    for k in list(bpy.context.preferences.addons.keys()):
        if "MHW" in k or "Mod3" in k:
            try:
                bpy.context.preferences.addons[k].preferences.showConsole = False
            except Exception:
                pass


def precheck(log, problems):
    """导出前预检，逐项对应导出器的报错"""
    try:
        import bmesh
    except Exception:
        bmesh = None
    pat = re.compile(r"^MhBone_\d{3}$")
    # 描边材质白名单：Outline 或 Outline_<颜色>（照抄 参考件 的命名；与 o12 的 mrl3 新建条目同名）
    OUTLINE_MAT = re.compile(r"^Outline(_[A-Za-z0-9]+)?$")
    targets = sorted([c for c in bpy.data.collections if c.name.endswith(".mod3")],
                     key=lambda x: x.name)
    if not targets:
        problems.append("找不到 .mod3 集合")
        return targets
    log.append("=" * 100)
    log.append("### 导出前预检 ###")
    log.append("=" * 100)
    for c in targets:
        meshes = [o for o in c.objects if o.type == "MESH"]
        arms = [o for o in c.objects if o.type == "ARMATURE"]
        log.append("[%s]  骨架 %d 副, 网格 %d 个" % (c.name, len(arms), len(meshes)))
        if len(arms) == 0:
            problems.append("%s: 没有骨架 (NoArmatureInCollection)" % c.name)
        if len(arms) > 1:
            problems.append("%s: %d 副骨架 (MoreThanOneArmature)" % (c.name, len(arms)))
        if not meshes:
            problems.append("%s: 没有网格 (NoMeshesInCollection)" % c.name)
        for a in arms:
            if len(a.data.bones) > 255:
                problems.append("%s: 骨数 %d > 255 (MaxBonesExceeded)" % (a.name, len(a.data.bones)))
            badb = [b.name for b in a.data.bones if not pat.match(b.name)]
            if badb:
                problems.append("%s: 骨骼名不合规 %s (IncorrectBoneNameFormat)" % (a.name, badb[:5]))
        for o in meshes:
            me = o.data
            if len(me.vertices) < 3:
                problems.append("%s: 顶点太少 (NoVerticesOnSubMesh)" % o.name)
            if len(me.polygons) == 0:
                problems.append("%s: 没有面 (NoFacesOnSubMesh)" % o.name)
            if not me.uv_layers:
                problems.append("%s: 缺 UV (NoUVMapOnSubMesh)" % o.name)
            ngon = sum(1 for p in me.polygons if len(p.vertices) != 3)
            if ngon:
                problems.append("%s: %d 个非三角面 (NonTriangulatedFace)" % (o.name, ngon))
            if not me.materials:
                problems.append("%s: 没材质 (NoMaterialOnSubMesh)" % (o.name,))
            elif not (pat.match(me.materials[0].name)
                      or me.materials[0].name.startswith("Ch_")
                      # ★ 描边材质是自定义名（不在游戏全局字典里，参考件 的 Outline_* 也一样），
                      #   白名单放行；见 _outline\o1/o12 与调研报告 §4.6
                      or OUTLINE_MAT.match(me.materials[0].name)):
                problems.append("%s: 材质名可疑 %s" % (o.name, me.materials[0].name))
            maxinf = 0
            badw = 0
            for v in me.vertices:
                cc = sum(1 for g in v.groups if g.weight > 1e-4)
                maxinf = max(maxinf, cc)
                if sum(g.weight for g in v.groups) < 0.5:
                    badw += 1
            if maxinf > 8:
                problems.append("%s: 最大影响数 %d > 8 (MaxWeightsPerVertexExceeded)" % (o.name, maxinf))
            if badw:
                problems.append("%s: %d 个顶点权重不足" % (o.name, badw))
            if bmesh:
                bm = bmesh.new(); bm.from_mesh(me)
                loose = sum(1 for v in bm.verts if not v.link_faces)
                bm.free()
                if loose:
                    problems.append("%s: %d 个松散顶点 (LooseVerticesOnSubMesh)" % (o.name, loose))
            if not o.vertex_groups:
                problems.append("%s: 没有顶点组 (NoWeightsOnMesh)" % o.name)
        # 每个网格的材质名
        for o in sorted(meshes, key=lambda x: x.name):
            log.append("      %-30s 材质=%s 顶点=%d" %
                       (o.name, o.data.materials[0].name if o.data.materials else "None",
                        len(o.data.vertices)))
    return targets


def main():
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except RuntimeError:
        pass
    off_console()
    log, problems = [], []
    P("=== 阶段B 步骤7：导出 mod3 ===")

    targets = precheck(log, problems)
    if problems:
        log.append("")
        log.append("!! 预检未通过，共 %d 个问题，已中止导出：" % len(problems))
        for p in problems:
            log.append("   " + p)
        return finish(log, problems, 0)

    # 清输出目录
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR, ignore_errors=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    log.append("")
    log.append("=" * 100)
    log.append("### 开始导出 ###")
    log.append("=" * 100)
    panel = bpy.context.scene.mhw_mod3_toolpanel
    n_ok = 0
    for c in targets:
        # 导出器读的是面板上的 exportMod3Collection
        panel.exportMod3Collection = c
        # 从集合名推文件名： f_body040_0010.mod3 -> f_body040_0010.mod3
        fname = c.name if c.name.lower().endswith(".mod3") else c.name + ".mod3"
        fpath = os.path.join(OUT_DIR, fname)
        try:
            r = bpy.ops.mhw_mod3.export_mhw_mod3(filepath=fpath)
        except Exception as e:
            problems.append("[%s] 导出异常: %s" % (c.name, e))
            P("  !! %s 导出异常: %s" % (c.name, e))
            continue
        exists = os.path.exists(fpath)
        size = os.path.getsize(fpath) if exists else 0
        log.append("  [%-24s] -> %-26s %s  %s" %
                   (c.name, fname, r, ("%.2f MB" % (size / 1048576.0)) if exists else "!! 文件没生成"))
        P("  [%s] -> %s  %s" % (c.name, fname, r))
        if exists and size > 0:
            n_ok += 1
        else:
            problems.append("[%s] 文件没生成" % c.name)

    log.append("")
    log.append("成功导出 %d / %d 个" % (n_ok, len(targets)))
    finish(log, problems, n_ok)


def finish(log, problems, n_ok):
    P("")
    P("\n".join(log))
    P("-" * 60)
    for p in problems:
        P("!! " + p)
    try:
        open(LOG_PATH, "w", encoding="utf-8").write("\n".join(log + ["", "-" * 60] + problems))
    except Exception as e:
        P("写日志失败:", e)
    if bpy.app.background:
        return

    def draw(self, context):
        self.layout.label(text="导出 %d 个 mod3" % n_ok, icon="ERROR" if problems else "CHECKMARK")
        for line in log[-8:]:
            self.layout.label(text=line[:112])
        for p in problems[:3]:
            self.layout.label(text=p[:112], icon="ERROR")

    try:
        bpy.context.window_manager.popup_menu(draw, title="阶段B·步骤7 导出", icon="INFO")
    except Exception as e:
        P("弹窗失败:", e)


main()

# -*- coding: utf-8 -*-
"""K1_出检视blend.py —— 把工作副本另存成"给用户自己看"的检视工程。
为什么需要：工作副本里的材质是**导出用占位材质**（全部无贴图、纯灰），用户在 Blender 里打开
看不到花色。本脚本把**源 PNG 重新挂回材质**，并把视口设成"能直接看到贴图"的状态。

照 skill「第七次实战 F」那张表逐条做（那几条每次都中招）：
  · Solid 模式默认不显示贴图 ⇒ 视口必须 `shading.type='MATERIAL'` + `color_type='TEXTURE'`
  · 从 Unity/FBX 转进来的 Principled 带自发光/镜面 ⇒ **Emission Color 涂黑、Strength=0、
    Metallic=0、Roughness≈0.85**，让贴图说了算
  · 集合的"眼睛"要用 `layer_collection.hide_viewport`（`collection.hide_viewport` 是那个小复选框，
    用户点眼睛没反应）
  · 灯光过曝（sun 3.0 + Standard）⇒ 降到 ~1.0
用法: blender -b <工作副本.blend> --python K1_出检视blend.py -- <输出blend> [版本名]
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

argv = sys.argv
args = argv[argv.index("--") + 1:]
OUT = args[0]
VER = args[1] if len(args) > 1 else ""

BH = CLOTH_TEX_DIR
HAIR1 = os.path.join(HAIR_SRC_DIR, "PNG")
EKU = BASE_TEX_DIR

# 部位 -> （材质名 -> 贴图文件 或 (R,G,B) 纯色）
# ★ 纯色给的是**线性**值（Blender 的 Base Color 是线性）⇒ 与 Y2 生成 .tex 时的
#   "sRGB(线性色)" 是同一组数（Y2 存的是 sRGB 字节，这里给回线性）。
PLAN = {
    "body": {"Ch_Standard_Mt__1": os.path.join(EKU, "Body_Base.png"),
             "Ch_Standard_Mt__2": os.path.join(EKU, "Face_Base_orange.png"),
             "Ch_Standard_Mt__3": os.path.join(EKU, "Hair.png"),
             "Ch_Standard_Mt__5": os.path.join(BH, "UV1", "Skyblue.png"),
             "Ch_Standard_Mt__6": os.path.join(BH, "UV2", "Skyblue.png"),
             "Ch_Standard_Mt__7": os.path.join(BH, "Bag", "Skyblue.png"),
             "Ch_Standard_Mt__9": (0.970, 0.970, 0.980),      # FUR 毛
             "Ch_Standard_Mt__10": (0.800, 0.820, 0.860),     # METAL 银灰（平涂）
             "Ch_Standard_Mt__12": os.path.join(HAIR1, "Yellow.png"),
             "Ch_Standard_Mt__13": os.path.join(HAIR1, "Accessories.png")},
    "arm": {"Ch_Standard_Mt__5": os.path.join(BH, "UV1", "Skyblue.png"),
            "Ch_Standard_Mt__6": os.path.join(BH, "UV2", "Skyblue.png"),
            "Ch_Standard_Mt__10": (0.800, 0.820, 0.860),
            "Ch_Standard_Mt__11": (0.6667, 0.859, 1.000)},    # GLOVE 淡蓝
    "wst": {"Ch_Standard_Mt__9": (0.970, 0.970, 0.980)},      # 兔尾
    "leg": {"Ch_Standard_Mt__6": os.path.join(BH, "UV2", "Skyblue.png"),
            # ★ 丝袜：指向 **Y2 烘焙后**的 RGBA 图（网眼=皮肤色、网线=黑色，且带 alpha）
            #   —— 这样在 Blender 里看到的就是游戏里的渔网效果，而不是源图那张"全白+alpha"
            "Ch_Standard_Mt__8": STOCK_SKIN_PNG,
            "Ch_Standard_Mt__10": (0.800, 0.820, 0.860)},
}
LOG = []


def w(s=""):
    print(s, flush=True)
    LOG.append(str(s))


# 默认一律给一套通用映射（同名材质在不同部位指向不同贴图 —— 只按 mesh 的所属部位定不了，
# 所以用"并集 + 先到先得"：__5 在 body=白上衣，arm=手套，wst=短裤，leg=袜 —— 名字相同、
# 贴图不同，这里按**集合**分别处理，避免串图）
def fresh_bsdf(m):
    """★ 基壳的"导出用占位材质"节点树是空的/没有 Principled ⇒ **整棵重建**（检视工程无所谓）。"""
    if not m.use_nodes:
        try:
            m.use_nodes = True
        except Exception:
            return None
    nt = m.node_tree
    if nt is None:
        return None
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (200, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (-100, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return bsdf


def norm_bsdf(bsdf):
    for key, val in (("Emission Color", (0, 0, 0, 1)), ("Emission Strength", 0.0),
                     ("Metallic", 0.0), ("Roughness", 0.85), ("Specular IOR Level", 0.2)):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = val


def set_tex(m, bsdf, path):
    nt = m.node_tree
    im = bpy.data.images.get(os.path.basename(path))
    if im is None or not im.filepath:
        im = bpy.data.images.load(path, check_existing=True)
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = im
    tn.location = (-460, 160)
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    return im.size[0]


w("### %s -> %s" % (bpy.data.filepath, OUT))
done = {}
for cname, plan in PLAN.items():
    c = bpy.data.collections.get("f_%s040_0010.mod3" % cname)
    if c is None:
        w("!! 缺集合 f_%s040_0010.mod3" % cname)
        continue
    for nm, src in plan.items():
        m = bpy.data.materials.get(nm)
        if m is None:
            continue
        bsdf = fresh_bsdf(m)
        if bsdf is None:
            w("   !! %s 建不出节点树" % nm)
            continue
        norm_bsdf(bsdf)
        if isinstance(src, tuple):
            bsdf.inputs["Base Color"].default_value = (src[0], src[1], src[2], 1.0)
            w("   %-6s %-22s 纯色 %s" % (cname, nm, src))
        else:
            if not os.path.exists(src):
                w("   !! 源图不存在 %s" % src)
                continue
            sz = set_tex(m, bsdf, src)
            w("   %-6s %-22s 贴图 %s (%d²)" % (cname, nm, os.path.basename(src), sz))
        done[(cname, nm)] = True

# 描边材质：纯黑
m = bpy.data.materials.get("Outline_Black")
if m is not None:
    bsdf = fresh_bsdf(m)
    if bsdf:
        norm_bsdf(bsdf)
        bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
    w("   Outline_Black -> 纯黑（描边壳）")

# ---- 视口 / 场景设置 ----
for sc in bpy.data.screens:
    for ar in sc.areas:
        if ar.type == "VIEW_3D":
            for sp in ar.spaces:
                if sp.type == "VIEW_3D":
                    try:
                        sp.shading.type = "MATERIAL"
                        sp.shading.color_type = "TEXTURE"
                        sp.shading.light = "STUDIO"
                        sp.shading.show_shadows = False
                        sp.shading.show_cavity = False
                    except Exception as _e:
                        w("   !! 视口设置部分失败：%s" % _e)
sc = bpy.context.scene
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.view_settings.exposure = 0.0
nsun = 0
for o in bpy.data.objects:
    if o.type == "LIGHT":
        nsun += 1
        if o.data.type == "SUN":
            o.data.energy = 1.0
        else:
            o.data.energy = min(o.data.energy, 30.0)
w("   灯光 %d 个（sun 降到 1.0）；视口 = MATERIAL/TEXTURE；view_transform = Standard" % nsun)
if nsun == 0:
    w("   ⚠ 场景里没有灯 ⇒ 视口用 Studio 光也能看清（MATERIAL 模式自带）")

# ---- 集合的"眼睛"（用 layer_collection.hide_viewport，不是 collection.hide_viewport）----
vlc = bpy.context.view_layer.layer_collection
for ch in vlc.children:
    w("   集合 %-26s hide_viewport=%s" % (ch.name, ch.hide_viewport))

bpy.ops.wm.save_as_mainfile(filepath=OUT)
w("")
w(">>> 检视工程已写出：%s" % OUT)
w(">>> 打开后：视口左上角确认是 Material Preview（球图标）；滚轮缩放看细节。")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)

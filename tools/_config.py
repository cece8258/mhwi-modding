# -*- coding: utf-8 -*-
"""_config.py —— **所有路径都集中在这里**。使用前请改这一个文件。
（脚本里 `from _config import *`，所以这里定义的每个名字都能直接用。）

★ 设计约定：
  · 只改 `PROJ` 一行，下面所有派生路径都会跟着走；
  · 其余常量（texconv / 模板 .tex / 素材目录）按你机器上的位置填；
  · 路径里有中文不要紧，但**texconv 只吃纯 ASCII 路径** ⇒ `WORK_ASCII` 必须是纯 ASCII。
"""
import os

# ============================================================================
# ① 你的工作工程目录（脚本运行时 cwd 建议就是这里；也可以直接用这个绝对路径）
# ============================================================================
PROJ = r"D:\your\mhwi-mod-project"          # ← ★ 改这一行

# ============================================================================
# ② 工程内的派生目录（一般不用改）
# ============================================================================
PKG_DIR     = os.path.join(PROJ, "05_导出成品", "nativePC", "pl", "f_equip", "pl040_0010")
MOD3_DIR    = os.path.join(PROJ, "_mod3")
BAKED_DIR   = os.path.join(PROJ, "_texwork", "烘焙_y2")
EXPORT_LOG  = os.path.join(PROJ, "_export_log.txt")
Y3_OUT      = os.path.join(PROJ, "_Y3_材质指向.txt")
STOCK_SKIN_PNG = os.path.join(BAKED_DIR, "STOCK.png")
MAIN_BLEND  = "主工程副本.blend"              # Z9 会 `cp "$MAIN_BLEND" _p_work.blend`
                                             # ★ 别让它等于 `_p_work.blend`（会 SameFileError）

# ============================================================================
# ③ 外部工具与模板（按你机器上的位置改）
# ============================================================================
TEXCONV      = r"D:\tools\texconv.exe"        # DirectXTex 的 texconv
TEX_TEMPLATE = r"D:\tools\dds\Body_Base.tex"  # 一个**能跑通**的现成 .tex，当 184 字节头的模板
WORK_ASCII   = r"D:\texwork"                  # texconv 的工作目录：**必须纯 ASCII**
BLENDER_CFG_DIR = r"C:\Users\<你>\AppData\Roaming\Blender Foundation\Blender\4.2"
ADDON_ROOT   = os.path.join(BLENDER_CFG_DIR, "extensions", "user_default", "MHW_Mod3_Editor")
#   ★ 官方字典（various_hash_dict / master_material_dict / property_dict）就在
#     ADDON_ROOT\addons\MHW_Model_Editor\modules\mrl3\dict\ 下。

# ============================================================================
# ④ 素材目录（**本仓库不包含任何素材文件**，请自备并自行确认授权）
# ============================================================================
CLOTH_FBX     = r"D:\assets\服装.fbx"          # 要移植的衣服 FBX
CLOTH_TEX_DIR = r"D:\assets\服装贴图"           # 它的贴图目录
HAIR_SRC_DIR  = r"D:\assets\头发素材"           # 头发素材目录（X1 会从里面找贴图）
HAIR_PACK_DIR = ""                             # 若头发贴图在更深的子目录里，填这里
BASE_TEX_DIR  = r"D:\assets\角色贴图"           # 角色本体贴图（身体/脸/头发）
BODY_PNG      = os.path.join(BASE_TEX_DIR, "Body.png")     # 身体 albedo（做"腿皮投影"要用）
BASE_HAIR_PNG = os.path.join(BASE_TEX_DIR, "Hair.png")
CAND_DIR      = r"D:\assets\候选套装"           # 可选：备用候选素材

__all__ = ["PROJ", "PKG_DIR", "MOD3_DIR", "BAKED_DIR", "EXPORT_LOG", "Y3_OUT",
           "STOCK_SKIN_PNG", "MAIN_BLEND", "TEXCONV", "TEX_TEMPLATE", "WORK_ASCII",
           "BLENDER_CFG_DIR", "ADDON_ROOT", "CLOTH_FBX", "CLOTH_TEX_DIR",
           "HAIR_SRC_DIR", "HAIR_PACK_DIR", "BASE_TEX_DIR", "BODY_PNG",
           "BASE_HAIR_PNG", "CAND_DIR"]

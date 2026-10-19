# -*- coding: utf-8 -*-
"""Y1_构建.py（第7版 · 本套装 本套天蓝配色 + 头发素材 蓬蓬双马尾 Yellow）——
把「本套装 12 件（13 件去掉 `Carrot`）+ 头发_头发素材 7 件」搬进 MHW 工作工程。
★ 先决条件：输入 blend 必须是主工程（`MAIN_BLEND`）的**副本**（本脚本会改写它）。
★ 本文所有"实测"读数来自 `本项目调研记录\\\_probe*.txt` 与本工程 `X1_采集_本套头发.py`
  产出的 `_X3_preview.txt`（★ X1 里**自己 import_scene.fbx** 导入裸 FBX）。

与 第6版 的 Y1 的差别（本版新增，全部有实测依据）：
 ① 坐标：本套 `Armature.007`（导入器给的名字，按 `pre["cloth_arm"]` 取，**不写死**）与 角色
    **65 个同名骨**、head 距离中位 **0.000001** / max **0.001083 m**（1.08mm，只来自**手指远节**：
    Ring/Little/Index Distal 那一档；躯干/四肢主骨逐位 0.000000）
    ⇒ **同源同尺度，SCALE = 1.0、不配准不缩放**。
    头发 的 `Armature.004` 与 角色 **0 个同名骨**（另一套 VRChat 骨名，与 第2·3·4版 同一套），
    但**网格是世界尺度 1.0** ⇒ 同样 SCALE = 1.0。
 ② NEW 表 = 本套 **12 件**（`Carrot` 四版全删，在 X1 就跳过）+ 头发 的 7 件（一件不删）。
 ③ 材质：★ 实测（`本项目调研记录\\\_槽位UV归属.py`）**同一件的各材质槽共享同一套 UV**
    （`NO.1`/`NO.1-1`/`NO.1-2` 的 UV 区间互相重叠）⇒ **按件归组**：
      UV1（Suit/Headband/Arm warmers）/ UV2（Choker/arm belt/Leg Belt/Shoes/ACC）/
      BAG / STOCK / FUR（毛）/ METAL（金属）/ GLOVE（纯色）/ HAIR / ACC —— 共 **9 个**目标材质键。
    ★ 导出器每网格只写**材质槽 0** ⇒ 必须**按材质拆件**（`emit` 里做）。★ `Suit` 的槽 2 是 **0 面**，
      拆件时被 `fgroups` 自然跳过（坑7）。
 ④ 顶点组是 角色 真身骨 + 素材辅骨混排 ⇒ AUX 表按**权重所在的位置**给辅骨定去处
    （`Elbow_support.L/R` 挂在**肘之前**、属 Upper_arm 一侧 ⇒ 给 6/10，不是按骨名给前臂）。
 ⑤ 链（本版 **31 根链骨**，全部**按链名固定分配**号）：
      body 206~234：双马尾 L/R 各 **5**（与 第2·3·4版 同一套、已验收）；
                    兔耳 **R 4 段→3 节点 / L 2 段→2 节点**（★ 实测不是 3+3，见 ⑧）；
                    包 `Bag` 2 节点（Σw 6173，全表最大）；`Suit` 髋部蕾丝褶 每侧 2 条 ×2 节点；
                    颈饰 `Choker` 2 条 ×2 节点
      wst  206~207：本套兔尾 `Tail` 2 节点（★ 与 第6版 不同：**它有真权重** Σw 2540）
      arm  无新链（袖子/手套/臂环都跟随身体）
    ★ 开关 `nochain` / `nohairchain` / `noearchain` / `nobagchain` / `nosuitchain` /
      `nochokerchain` / `notailchain` 可分别关掉（观感类，让用户一句话迭代）。
 ⑥ ★★ 段组**必须先按几何排序**再用 seg_nodes（作者编号不沿链，见 ② 的诊断打印）。
 ⑦ ★ 坑1（**本版成立**）：`Suit` 的形态键 **`Stocking_ON` 键值 = 1.0**，与 Basis 的逐顶点最大差
    **14.303 mm** ⇒ 预览里看到的是"开了丝袜模式"的紧身衣。X1 已按"键值非 0 就走求值网格"处理
    （其余件的键值全 0，`Headband` 那些 44~98mm 的键值都是 0）。
 ⑧ ★★ 提示词被实测修正的一条：`Head_Root_Headband.*` **不是"每耳 3 段"**，而是**右 4 段 / 左 2 段**
    （按质心 x 符号分完就是 4+2）⇒ 节点数按实际段数取（右 3 / 左 2）。
 ⑨ 原版 `Animal_Ear` / `Tail` **本版默认删除**（v1/v2；用户明确要求）—— 这套衣服自带兔耳/兔尾。
    它们的旧描边壳 `Animal_Ear__Outline_Black` / `Tail__Outline_Black` **一并删**（本体没了、壳留着
    会"有网格没材质"）。v3/v4 用 `origear` / `origtail` 保留。
 ⑩ 变体开关：`nostock`（v2）/ `nosuit`（v2）/ `noheadband`（v3）/ `nobunnytail`（v3）/
    `nogloves`（v4）/ **`nobag`（兜底，默认保留）** / `nooutline`。
 ⑪ ★ **本版不做**丝袜脚的"绕踝旋转"：实测 `Shoes` 鞋底全程 0.0019~0.0060（起伏 **4.1mm**）=
    平底、`Stocking` 袜底也是平的 ⇒ 与 第6版 那只"给高跟鞋做的鞋楦"（17.3mm 脚尖下沉）完全不同。
 ⑫ ★★ v4 的重点（用户点名）：`Arm warmers` 的几何沿手指轴伸到 **x=0.5286**（Hand.L 在 0.4411、
    `Little Distal.L` 在 0.5287）⇒ 去掉手套后**袖子本身就是手套**；且袖子在指尖段**缺
    `Index/Middle/Ring Distal` 权重**。本版先报数字（⑥e），`Y8_摆姿势穿模体检.py` 复量。
 ⑬ ★★ 用户 2026-10-03 纠正：**`Suit` 是无裙摆的紧身连衣体**（典型本套装扮）——
    `Hip_Root_Suit.*` 是**髋/腿洞的蕾丝褶边**（方位角上绕腿洞一圈、z 几乎不变），
    ⇒ 每侧拆成"前弧 / 后弧"两条 2 节点链，**不**硬拉成一条绕髋的折线。

用法: blender -b <工作副本.blend> --python Y1_构建.py -- <_X3_preview.json> <报告txt> [开关...]
  开关：nostock  nosuit  nogloves  noheadband  nobunnytail  nobag  nooutline
        origear  origtail  nochain  nohairchain  noearchain  nobagchain
        nosuitchain  nochokerchain  notailchain  nopushout  margin=<mm>
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

argv = sys.argv
args = argv[argv.index("--") + 1:]
J, OUT = args[0], args[1]
OPTS = set(args[2:])
# ---- 变体开关（用户 2026-10-03 拍板的四版成品）----
#   v1 = 有描边 + 无原版耳尾 + 本套全在（Headband/兔尾/Gloves）      ← 基准（本版先只出 v1）
#   v2 = v1 去掉 Stocking + Suit                                     ⇒ nostock nosuit
#   v3 = v1 把 Headband/兔尾 换回原版 Animal_Ear/Tail                ⇒ noheadband nobunnytail origear origtail
#   v4 = v3 再去掉 Gloves                                            ⇒ + nogloves
NO_STOCK = "nostock" in OPTS        # 不出 Stocking（v2）
NO_SUIT = "nosuit" in OPTS          # 不出 Suit（v2）
NO_GLOVES = "nogloves" in OPTS      # 不出 Gloves（v4）
NO_HEADBAND = "noheadband" in OPTS  # 不出 Headband（v3）
NO_BUNNYTAIL = "nobunnytail" in OPTS  # 不出本套兔尾 Tail（v3）
NO_BAG = "nobag" in OPTS            # ★ 兜底：不出 Bag（默认**保留**；只在"物理/穿模不好处理"时开）
NO_OUTLINE = "nooutline" in OPTS    # 不做描边（并删掉遗留的耳/尾描边壳）
# ★★ 本版与 第5版 **相反**：原版 Animal_Ear / Tail **默认删除**（这套衣服自带兔耳/兔尾）
ORIG_EAR = "origear" in OPTS        # 保留原版 Animal_Ear（v3/v4）
ORIG_TAIL = "origtail" in OPTS      # 保留原版 Tail（v3/v4）
NO_EAR = not ORIG_EAR
NO_TAIL = not ORIG_TAIL
# ---- 物理链开关（观感类 ⇒ 让用户一句话迭代，不要助手猜）----
NO_CHAIN = "nochain" in OPTS             # 全部链都不做
NO_HAIR_CHAIN = NO_CHAIN or ("nohairchain" in OPTS)     # 双马尾（头发）
NO_EAR_CHAIN = NO_CHAIN or ("noearchain" in OPTS)       # 兔耳 Headband
NO_BAG_CHAIN = NO_CHAIN or ("nobagchain" in OPTS)       # 包 Bag
NO_SUIT_CHAIN = NO_CHAIN or ("nosuitchain" in OPTS)     # Suit 髋部褶边（每侧 8 段）
NO_CHOKER_CHAIN = NO_CHAIN or ("nochokerchain" in OPTS)  # 颈饰飘带（11 段）
NO_TAIL_CHAIN = NO_CHAIN or ("notailchain" in OPTS)     # 本套兔尾（2 段，有真权重）
NO_PUSHOUT = "nopushout" in OPTS         # 全部不做"穿模外推"（对照用）
MARGIN = 0.0006          # 兜底外推的目标间隙（米）
for _o in OPTS:
    if _o.startswith("margin="):
        MARGIN = float(_o.split("=", 1)[1]) / 1000.0
# ★ 本版**没有**需要"跟腿"的裙片（Suit 是无裙摆的紧身连体衣），保留解析以兼容旧命令行。
FOLLOW = 0.0
T0 = 0.45
FOLLOW_OBJS = ()
for _o in OPTS:
    if _o.startswith("follow="):
        FOLLOW = float(_o.split("=", 1)[1])
    if _o.startswith("t0="):
        T0 = float(_o.split("=", 1)[1])

L = []


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


for _k in list(bpy.context.preferences.addons.keys()):
    if "MHW" in _k or "Mod3" in _k:
        try:
            bpy.context.preferences.addons[_k].preferences.showConsole = False
        except Exception:
            pass

pre = json.load(open(J, encoding="utf-8"))
OBJ = pre["objs"]
AB = pre["arm_bones"]
# ★ 本版链的根来自**两副素材骨架**：本套 `Armature.007`（兔耳/颈饰/包/兔尾/髋褶）
#   与头发 的 `Armature.004`（双马尾）；两副**没有同名骨**（0 个），且都与 角色 同世界尺度
#   ⇒ 直接合并（不缩放、不配准）。
#   ★★ 本套那副的名字是**导入器给的**（preview2 里已有 Armature.001~.006 ⇒ 新建的叫 .007）
#      ⇒ 一律按 `pre["cloth_arm"]` 取名字，**绝不写死**（skill「新服装包的导入与探针」⑧）。
_CLOTH_ARM = pre.get("cloth_arm") or "Armature.001"
_HAIR_ARM = pre.get("hair_arm") or "Armature.004"
w("### 骨架对象名（来自采集 JSON）：本套=%r 头发=%r" % (_CLOTH_ARM, _HAIR_ARM))
A3 = AB.get(_CLOTH_ARM, {})
A6 = AB.get(_HAIR_ARM, {})
assert A3, "采集结果里没有本套骨架 %r" % _CLOTH_ARM
_dup = set(A3) & set(A6)
A4 = dict(A6)
A4.update(A3)                        # 同名骨以素材 的为准（实测两者都没有同名骨）
_dd = [(np.linalg.norm(np.array(A3[k]["head"]) - np.array(A6[k]["head"])), k) for k in _dup] \
    if _dup else []
w("### 骨架：素材 Armature.001 骨 %d ；头发 Armature.004 骨 %d ；合并 %d（同名 %d 个，"
  "head 最大差 %.6f m ⇒ %s）" %
  (len(A3), len(A6), len(A4), len(_dup), (max(_dd)[0] if _dd else 0.0),
   "可直接合并 ✓" if (not _dd or max(_dd)[0] < 1e-3) else "!! 两副骨架同名骨位置不同，要逐名处理"))

# ---------- 真身骨名 -> MhBone 号（与 第3版 相同，已实测复核）----------
NAME2FN = {
    "Hips": 13, "Spine": 1, "Chest": 2, "Neck": 3, "Head": 4, "head": 4,
    "Shoulder.L": 5, "Shoulder.R": 9,
    "Upper_arm.L": 6, "Upper_arm.R": 10,
    "Lower_arm.L": 7, "Lower_arm.R": 11,
    "Hand.L": 8, "Hand.R": 12,
    "Breast.L": 197, "Breast.L.001": 198, "Breast.R": 194, "Breast.R.001": 195,
    "Upper_leg.L": 14, "Upper_leg.R": 18, "Lower_leg.L": 15, "Lower_leg.R": 19,
    "Foot.L": 16, "Foot.R": 20, "Toe.L": 17, "Toe.R": 21,
}
_FING = {
    "L": {"Thumb": (31, 32, 33), "Index": (34, 35, 36), "Middle": (37, 38, 39),
          "Ring": (41, 42, 43), "Little": (44, 45, 46)},
    "R": {"Thumb": (48, 49, 50), "Index": (51, 52, 53), "Middle": (54, 55, 56),
          "Ring": (58, 59, 60), "Little": (61, 62, 63)},
}
for _s in ("L", "R"):
    for _f, _tri in _FING[_s].items():
        for _k, _pos in enumerate(("Proximal", "Intermediate", "Distal")):
            NAME2FN["%s %s.%s" % (_f, _pos, _s)] = _tri[_k]

# ---------- 本套/头发 的辅骨 -> 固定骨号（依据 = 实测的**权重质心位置**，不是骨名）----------
#   ★ 注：`Butt.L/R`、`Wrist_support.L/R`、`Elbow_support.L/R` 是 **角色 真身骨**
#     （在 角色 的 Armature 里），但 MHW 没有它们的号 ⇒ 也要在这里给固定骨号。
#     （`Breast.L/R` / `Breast.*.001` 已在上面 NAME2FN 里，不重复。）
#   ★★ 下面**同时**列了所有"可能被链接管"的组 —— 因为 `nochain` / `no*chain` 关掉链之后，
#      那些组会走到 `resolve_group` ⇒ 必须有一个合理的兜底（否则会被并到 Chest(2)，
#      症状是"耳朵/颈饰/包被胸口拽着动"，skill「第八次实战 B」记过这个坑）。
AUX = {
    # ---- 角色 真身骨（MHW 无功能号；号按**权重所在位置**给，不按骨名，skill 第五次实战 M）----
    "Butt.L": 13, "Butt.R": 13,          # 质心 z≈0.74（Suit 髋褶 / Stocking 臀）-> 骨盆
    "Wrist_support.L": 8, "Wrist_support.R": 12,     # 质心 x±0.421（袖子/手套腕口）-> Hand
    "Elbow_support.L": 6, "Elbow_support.R": 10,     # 质心 x±0.244、盒 x0.219~0.261 在肘**之前**
                                                     # ⇒ 属 Upper_arm 一侧，挂 Upper_arm
    # ---- 本套作者辅骨（★ 只有关掉对应链时才会走到这里）----
    "Head_Root_Headband": 4, "Head_Root_Headband.001": 4, "Head_Root_Headband.002": 4,
    "Head_Root_Headband.003": 4, "Head_Root_Headband.004": 4,
    "Head_Root_Headband.005": 4, "Head_Root_Headband.006": 4,          # 兔耳 -> Head
    "Head_Root_Carrot": 4, "Head_Root_Carrot.001": 4, "Head_Root_Carrot.002": 4,
    "Head_Root_Carrot.003": 4,                     # Carrot 四版全删，骨仍在 ⇒ 兜底无害
    "Neck_Root_Choker": 3, "Neck_Root_Choker.001": 3, "Neck_Root_Choker.002": 3,
    "Neck_Root_Choker.003": 3, "Neck_Root_Choker.004": 3, "Neck_Root_Choker.005": 3,
    "Neck_Root_Choker.006": 3, "Neck_Root_Choker.007": 3, "Neck_Root_Choker.008": 3,
    "Neck_Root_Choker.009": 3, "Neck_Root_Choker.010": 3,
    "Neck_Root_Choker.011": 3,                                         # 颈饰 -> Neck
    "Chest_Root_Bag": 2, "Chest_Root_Bag.001": 2, "Chest_Root_Bag.002": 2,   # 包 -> Chest
    "Hip_Root_Tail": 13, "Hip_Root_Tail.001": 13, "Hip_Root_Tail.002": 13,   # 兔尾 -> 骨盆
    "Hip_Root_Suit": 13,                                               # Suit 髋部褶边 -> 骨盆
}
for _i in range(1, 10):
    for _sd in ("L", "R"):
        AUX["Hip_Root_Suit.%03d.%s" % (_i, _sd)] = 13
# 前缀规则：头发里**不摆动/不做链**的部分 -> Head(4)。（★ 顺序：长的前缀在前，避免被短前缀抢走）
#   ⚠ 链组在前缀之前由 CHAIN_GROUP 截走，不会误吃；这里列的是"万一不做链"的兜底。
AUX_PREFIX = [("Bun.", 4), ("Bun", 4), ("Front.", 4), ("Front", 4),
              ("Side2.", 4), ("Side2", 4), ("Side.", 4),
              ("ahoge.", 4), ("ahoge", 4),
              ("Tail.", 4), ("Tail.L", 4), ("Tail.R", 4)]

PART_ARM = {"body": "f_body040_0010 Armature", "arm": "f_arm040_0010 Armature",
            "leg": "f_leg040_0010 Armature", "wst": "f_wst040_0010 Armature"}
PART_COLL = {"body": "f_body040_0010.mod3", "arm": "f_arm040_0010.mod3",
             "leg": "f_leg040_0010.mod3", "wst": "f_wst040_0010.mod3"}
# ★ 无顶点组的孤立顶点兜底骨（部位 -> MhBone 号）：取该部位"居中"的真身骨
FB_FN = {"body": 2, "arm": 6, "wst": 13, "leg": 14}      # Chest / Upper_arm.L / Hips / Upper_leg.L
# ★ 按**件**覆盖兜底骨：头发/耳朵的落单顶点必须挂 Head(4)，不能按部位兜到 Chest(2)
#   （第4版 实测：`TD_Main` 有 160 个顶点没有任何顶点组（2405 里的 6.7%），挂 Chest 会被胸口拽着动）。
FB_OBJ = {"TD_Main": 4, "TD_Bun": 4, "TD_Front": 4, "TD_Side": 4, "TD_Side2": 4,
          "TD_Tail": 4, "TD_acc": 4,
          "BH_Headband": 4, "BH_Choker": 3}
# ★★ `FORCE_CHAIN`（整件 0 顶点组 ⇒ 按链投影白送权重）：**本版留着但空着** ——
#   实测本套 12 件**没有一件是 0 顶点组**（兔尾 `Tail` 有 4 组真权重，Hip_Root_Tail.001/.002
#   Σw 2540，见 `_probe2.txt` ①）⇒ 与 第6版 的 `Tail.001`（86 顶点 0 组）不同。
FORCE_CHAIN = {}
REBIND = {}          # 本版不需要"按高度重绑"

# ---------- ★ 本版**不做**丝袜脚的"绕踝旋转" ----------
#   实测（本工程 X1 ⑪，沿脚长分档取最低 z）：
#     `Shoes`    鞋底全程 0.0019~0.0060（起伏 **4.1mm**）= 平底，比身体脚底低 ~13mm（厚底，作者原样）
#     `Stocking` 袜底 0.0126~0.0161，比身体脚底（0.0151~0.0171）只低 1~2.5mm，也是平的
#   ⇒ 与 第6版 那只"给高跟鞋做的鞋楦"（17.3mm 脚尖下沉）**完全不同**，不需要旋转/切脚，
#     只做兜底"单调外推"（见 PUSHOUT）。
# ★ 可选功能：`foot_fix()` —— 给"为高跟鞋做的鞋楦"那种袜子做"绕踝旋转 + 抬到身体脚底"。
#   本版**不用**（鞋/袜都是平底），所以 `FOOT_FIX_OBJ = None`（下面的函数就成了死代码，
#   但它对"高跟袜"那类素材是有用的，留着）。要用就把 `FOOT_FIX_OBJ` 设成目标件的 **NEW 键名**，
#   并给下面三个参数；四个值一起给，函数才自洽。
FOOT_FIX_OBJ = None
FOOT_ROT = None        # None = 按鞋底剖面自动拟合角度；给度数（°）则用给定值
FOOT_CLEAR = 0.0015    # 袜底抬到"身体脚底 − 这个值"（米）
FOOT_FADE = 0.015      # 踝上下各 1.5cm 的平滑过渡带（米）

# ---------- 贴图 -> 材质名（名字取自各部位 mrl3 的材质条目；四个部位的 34 条**完全一致**）----------
# ★ 避开的：`__1`(身体) `__2`(脸) `__3`(耳/尾) = 基壳 角色 的材质，**一个字节都不动**；
#   以及死条目 hash 3425628335 = `Outline_Black`（描边专用，由 O2 就地打补丁）。
# ★ 本版 9 个目标材质键（`本项目调研记录\_槽位UV归属.py` 实测：**同一件的各槽共享同一套 UV**，
#   面数/UV 区间都重叠 ⇒ 决定用**按件归组**，而不是按槽名归组）：
#     UV1  <- 贴图/UV1/Skyblue.png          （Suit / Headband / Arm warmers）
#     UV2  <- 贴图/UV2/Skyblue.png          （Choker / arm belt / Leg Belt / Shoes / ACC）
#     BAG  <- 贴图/Bag/Skyblue.png          （Bag）
#     STOCK<- 贴图/Stockings/Stockings.png  （Stocking；★ 官方蓝系没有丝袜配色）
#     FUR  <- 纯色 (0.97,0.97,0.98)         （Suit 的毛边 / Headband 耳绒 / Tail 兔尾）
#     GLOVE<- 纯色 (0.667,0.859,1.000)      （Gloves；作者脚本就是这么定的）
#     METAL<- 纯色（源 Metal 材质的 baseColor；Y2 生成）
#     HAIR <- 头发素材 Yellow.png（4096²）
#     ACC  <- 头发素材 Accessories.png（4096²）
#   ★ 可用名：四个部位的 mrl3 里都有 `Ch_Standard_Mt__1..__20`（实测 `_mod3` 之外单独验过）
#     ⇒ 用 `__5`~`__13`（`__4` 是描边死条目、不用）。
MAT_OF = {
    "body": {"UV1": "Ch_Standard_Mt__5",      # Suit 主体 / Headband 耳本体
             "UV2": "Ch_Standard_Mt__6",      # Choker / Bag 备用
             "BAG": "Ch_Standard_Mt__7",      # Bag
             "FUR": "Ch_Standard_Mt__9",      # Suit 毛边 / Headband 耳绒
             "METAL": "Ch_Standard_Mt__10",   # 金属件（平涂）
             "HAIR": "Ch_Standard_Mt__12",    # 头发素材 Yellow
             "ACC": "Ch_Standard_Mt__13"},    # 头发素材 Accessories
    "arm":  {"UV1": "Ch_Standard_Mt__5",      # Arm warmers
             "UV2": "Ch_Standard_Mt__6",      # arm belt 的布面
             "GLOVE": "Ch_Standard_Mt__11",   # Gloves（纯色淡蓝）
             "METAL": "Ch_Standard_Mt__10"},  # arm belt 的金属
    "wst":  {"UV2": "Ch_Standard_Mt__6",      # （备用）
             "FUR": "Ch_Standard_Mt__9"},     # 兔尾（纯色白毛）
    "leg":  {"UV2": "Ch_Standard_Mt__6",      # Shoes / Leg Belt / ACC
             "STOCK": "Ch_Standard_Mt__8",    # Stocking
             "METAL": "Ch_Standard_Mt__10"},
}
# 源材质槽名 -> 目标键（★ FBX 槽名是**通用的**：`NO.1`/`NO.1-1`/`NO.1-2` 不代表"第几套 UV"，
#   同一件的三个 NO.* 槽 UV 区间重叠 ⇒ 都归该件的组；`Fur1*`=毛、`Metal*`=金属）
MMAP_C = {"NO.1": "__PIECE__", "NO.1-1": "__PIECE__", "NO.1-2": "__PIECE__",
          "Fur1": "FUR", "Fur1-1": "FUR",
          "Metal": "METAL", "Metal.001": "METAL"}
# ★ 本套的 `Gloves` 按作者脚本是**整件纯色**（`给衣服上蓝色材质.py`：Gloves → color(0.667,0.859,1.0)）
MMAP_G = {"Fur1": "GLOVE", "NO.1-1": "GLOVE"}
# 头发（与 第2·3·4·6版 同一套 头发素材）
MMAP_H = {"Ash Blonde": "HAIR", "Ash Blonde.001": "HAIR", "Ash Blonde.002": "HAIR",
          "Ash Blonde.003": "HAIR", "Ash Blonde.004": "HAIR", "brown": "ACC"}
# ★ 部位划分（提示词 §九.6，逐件核对过 z 范围）：
#   leg = Stocking / Shoes / Leg Belt / ACC ；arm = Arm warmers / Gloves / arm belt ；
#   wst = 本套兔尾 Tail（链与 ctc 在同一部位）；
#   其余躯干/胸/头部件（Suit / Headband / Choker / Bag）+ 头发 的 7 件 → body。
#   ★★ 用户 2026-10-03 明确纠正：**`Suit` 是无裙摆的紧身连衣体（典型本套装扮）** ——
#      那 8+8 个 `Hip_Root_Suit.*` 段组是**髋/腿洞的蕾丝褶边**，不是裙摆；链与 ctc 都留在 body。
NEW = {
    # ================= 本套装（13 件，★ `Carrot` 四版全删 ⇒ 12 件）=================
    "BH_Suit":     ("body", "Suit",        MMAP_C, "UV1"),   # ★ 吃形态键 Stocking_ON=1.0（14.30mm）
    "BH_Headband": ("body", "Headband",    MMAP_C, "UV1"),   # 兔耳发饰（Fur1=耳绒 → FUR）
    "BH_Choker":   ("body", "Choker",      MMAP_C, "UV2"),
    "BH_Bag":      ("body", "Bag",         MMAP_C, "BAG"),   # ★ 用户确认保留（兜底开关 nobag）
    # ================= 头发_头发素材蓬蓬双马尾 7 件（一件不删）=================
    "TD_Main":     ("body", "-",       MMAP_H, "HAIR"),   # 源对象名就是一个连字符
    "TD_Bun":      ("body", "Bun",     MMAP_H, "HAIR"),
    "TD_Front":    ("body", "Front",   MMAP_H, "HAIR"),
    "TD_Side":     ("body", "Side",    MMAP_H, "HAIR"),
    "TD_Side2":    ("body", "Side2",   MMAP_H, "HAIR"),
    "TD_Tail":     ("body", "Tail.002", MMAP_H, "HAIR"),  # ★ 双马尾链按**这件**的几何建
    "TD_acc":      ("body", "acc",     MMAP_H, "HAIR"),   # ★ 会拆成 HAIR + ACC
    # ================= 其余部位 =================
    "BH_Arm":      ("arm",  "Arm warmers", MMAP_C, "UV1"),   # ★ v4 的关键：几何伸到 x=0.5286
    "BH_Gloves":   ("arm",  "Gloves",   MMAP_G, "GLOVE"),    # ★ 无 UV 层；只有 6 组（Hand/Wrist/Lower_arm）
    "BH_ArmBelt":  ("arm",  "arm belt", MMAP_C, "UV2"),
    "BH_Stocking": ("leg",  "Stocking", {},     "STOCK"),    # ★ FBX 里 0 个材质槽 ⇒ 直接给 STOCK
    "BH_Shoes":    ("leg",  "Shoes",    MMAP_C, "UV2"),
    "BH_LegBelt":  ("leg",  "Leg Belt", MMAP_C, "UV2"),
    "BH_ACC":      ("leg",  "ACC",      MMAP_C, "UV2"),
    "BH_Tail":     ("wst",  "Tail.003", MMAP_C, "FUR"),      # ★ 源对象是 `Tail`，被重名改成 `.003`
}
DROPPED_CLOTH = ("Carrot",)     # ★ 用户 2026-10-03 确认：四版全删（它的 4 根辅骨不占 MHW 功能号）
#   ⇒ 写死在 X1 的 SKIP_CLOTH 里，工作 blend 里根本不会出现它。
_DEL_BODY = ["Hair_Atama", "Hair_Center", "Hair_Tail_Back", "Hair_Tail_Front_L",
             "Hair_Tail_Front_R", "Acc_Ribbon",
             "Hair_Atama__Outline_Black", "Hair_Center__Outline_Black",
             "Hair_Tail_Back__Outline_Black", "Hair_Tail_Front_L__Outline_Black",
             "Hair_Tail_Front_R__Outline_Black"]
# ★★ 角色 原版的 `Animal_Ear` / `Tail` **默认删除**（v1/v2；用户明确要求）—— 这套衣服自带兔耳/兔尾。
#   它们的旧描边壳必须**一并删**（本体没了、壳留着会"有网格没材质"；`Z14` 的反向检查会抓）。
#   v3/v4 用 `origear` / `origtail` 保留。
if NO_EAR:
    _DEL_BODY += ["Animal_Ear", "Animal_Ear__Outline_Black"]
if NO_TAIL:
    _DEL_BODY += ["Tail", "Tail__Outline_Black"]
if NO_OUTLINE:
    _DEL_BODY += ["Animal_Ear__Outline_Black", "Tail__Outline_Black"]
DELETE = {
    "body": _DEL_BODY,
    "arm": ["旧套装件.Sleeve"],
    "wst": ["旧套装件.Tops", "旧套装件.Tie", "旧套装件.Collar",
            "旧套装件.Belt", "旧套装件.Skirt", "旧套装件.BeretHat"],
    "leg": ["旧套装件.Shoes"],
}
# ★ 变体开关跳过的件（`_SKIP_BUILD` 与 emit 循环共用同一张表，避免两处不一致）
VARIANT_SKIP = {}
if NO_STOCK:
    VARIANT_SKIP["BH_Stocking"] = "nostock"
if NO_SUIT:
    VARIANT_SKIP["BH_Suit"] = "nosuit"
if NO_GLOVES:
    VARIANT_SKIP["BH_Gloves"] = "nogloves"
if NO_HEADBAND:
    VARIANT_SKIP["BH_Headband"] = "noheadband"
if NO_BUNNYTAIL:
    VARIANT_SKIP["BH_Tail"] = "nobunnytail"
if NO_BAG:
    VARIANT_SKIP["BH_Bag"] = "nobag"
KMAX = 4
# ---------- 描边（inverted hull）：外扩 1mm + 反转绕序 + 顶点法线取反 + 独立材质 ----------
# 依据 `本项目调研记录\描边实现_报告.md`（**经实机验证**：`试验.zip` 头发/耳朵/尾巴都出了黑边、主体颜色正确）
#  · 外扩 0.10 mod3 单位 = 0.001 Blender 单位（1 mod3 单位 = 1 cm）
#  · 关键字段 = 材质项头部的 surfaceCoef=0x0011 + alphaCoef=00 70 04 04（照抄 参考件），见 `O2_描边材质.py`
#  · 壳必须**按"源件"整体建一个**（不是按按材质拆出来的子对象）：本版每件都被拆成 cloth+gold 两块，
#    拆出来的两块共面 ⇒ 按子对象各建壳会得到两层重合壳、金饰会被糊黑
#  · 排除带：只有"别的件夹在本体表面与壳之间"才会被糊黑 ⇒ 切掉当且仅当 d_别件 < min(d_本体, 2mm)
OUTLINE = not NO_OUTLINE
OUTLINE_OFF = 0.0010        # 沿本体法线外扩（米）
OUTLINE_EXCL = 0.0020       # 排除带半径（米）；0 = 关
OUTLINE_MAT = "Outline_Black"
# ★ 给**大部分**保留件建壳；★ 逐件判（提示词 §六："按它有没有独立轮廓判断"）：
#   · **不做壳**：`BH_LegBelt` / `BH_ACC` / `BH_ArmBelt`（细环，贴在腿/臂上、没有独立轮廓）、
#               `BH_Tail`（2550 顶点的绒球，紧贴骨盆后方、大半被 Suit/身体挡住 —— 第6版 同理排除了它的兔尾）
#   · **做壳**：Suit / Headband / Choker / Bag / Arm warmers / Gloves / Shoes / Stocking + 头发 7 件
#   ★ 风险点（已记入报告）：`BH_Arm`（袖子）的壳与 `BH_Gloves`（毛手套）在指尖段重叠 ——
#     靠"排除带"（别的件夹在本体与壳之间就切掉）挡住；若实机看到袖口被糊黑，把 `BH_Arm` 从本表去掉即可。
OUTLINE_SRC = [k for k in NEW if k not in ("BH_LegBelt", "BH_ACC", "BH_ArmBelt", "BH_Tail")]
for _k in VARIANT_SKIP:
    OUTLINE_SRC = [x for x in OUTLINE_SRC if x != _k]
# ★ 原版 Animal_Ear / Tail 的描边壳**不重建**（工作 blend 里已有 第1版 做好的那两个）；
#   本版默认把"本体 + 壳"一起删掉（见 DELETE），只有 origear/origtail 时才保留它们。

# ---------- ① 相似变换（预览 -> 工作）----------
A = np.array(OBJ["Body_base"]["co"], float)
bodyw = bpy.data.objects["Body_base"]
B = np.array([list(v.co) for v in bodyw.data.vertices], float)
assert len(A) == len(B), "Body_base 顶点数不一致 %d vs %d" % (len(A), len(B))
muA, muB = A.mean(0), B.mean(0)
Ac, Bc = A - muA, B - muB
U, D, Vt = np.linalg.svd((Bc.T @ Ac) / len(A))
dd_ = np.sign(np.linalg.det(U @ Vt))
R = U @ np.diag([1, 1, dd_]) @ Vt
S = float(np.trace(np.diag(D) @ np.diag([1, 1, dd_])) / (Ac ** 2).sum() * len(A))
t = muB - S * R @ muA
res = np.linalg.norm((S * (R @ A.T).T + t) - B, axis=1)
w("### ① 相似变换 预览->工作")
w("   s=%.6f 旋转=%.6f° t=(%.6f,%.6f,%.6f) 残差 max=%.3e 均值=%.3e m" %
  (S, np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))), t[0], t[1], t[2],
   res.max(), res.mean()))
w("   [对照] 第5版 实测：s=1.379583 t=(0,+0.024200,-1.026176) 残差 1.154e-06")
w("   ★ 两套素材都与 角色 同世界尺度（探针 ② / X1 ⑥ 实测）⇒ SCALE = 1.0，本处无需缩放")
w("   [开关] v-开关 nostock=%s nosuit=%s nogloves=%s noheadband=%s nobunnytail=%s nobag=%s ｜ "
  "nooutline=%s origear=%s origtail=%s nochain=%s" %
  (NO_STOCK, NO_SUIT, NO_GLOVES, NO_HEADBAND, NO_BUNNYTAIL, NO_BAG,
   NO_OUTLINE, ORIG_EAR, ORIG_TAIL, NO_CHAIN))


def xf(P):
    P = np.asarray(P, float)
    return (S * (R @ P.T)).T + t


# ---------- ② 链规格（本版共 31 根链骨；全部按链名固定分配）----------
w("")
w("### ② 链规格")
CLOTH_CHAINS = {"wst": [], "arm": [], "body": []}
# ---- body：双马尾（头发 的 `Tail.*`，9 个段组）★ 必须 5 节点（第2·3·4版 同一套已验收）----
#   实测（X1 ⑨）：段组 = `Tail.L` + `Tail.001.L`…`Tail.008.L`（每侧 9 个），
#   ★ 走折线（poly_nodes = **网格对象名** `Tail.002`）：弧长参数才能让整条马尾有梯度
#     （skill「附：链条的节点该放在哪」§1：弯曲的链必须走折线，弦上取点会让关节飘在网格外）。
#   ★ 段组**先按几何排序**（③ 里的 order_segs_geo）—— 作者编号不沿链。
if not NO_HAIR_CHAIN:
    for _sd in ("L", "R"):
        _segs = ["Tail.%s" % _sd] + ["Tail.%03d.%s" % (_i, _sd) for _i in range(1, 9)]
        CLOTH_CHAINS["body"].append(dict(
            name="TwinTail_%s" % _sd, roots=["Tail.%s" % _sd], segs=_segs,
            parent_fn=4, n_new=5, poly_nodes="Tail.002", preset="hair"))
        w("   [链组] 双马尾 %s：段组 %d 个 %s" % (_sd, len(_segs), _segs))
# ---- body：兔耳（`Headband` 的 `Head_Root_Headband.*` 6 段）----
#   ★★ 实测（X1 ⑩）**不是"每耳 3 段"**：按质心 x 符号只有 **右 4 段 / 左 2 段**：
#       右(−x)：`.001`(Σw1239, x−0.018) `.002`(308, x−0.050) `.003`(185, x−0.068) `.004`(263, y−0.041 偏后)
#       左(+x)：`.005`(Σw2292, x+0.038) `.006`(706, x+0.080)
#     ⇒ **按实际段数取节点**（右 3 / 左 2），不假设 3+3。
#   ★ 走折线（弯的耳朵沿弧长取点才均匀）；段组由 order_segs_geo 排序。
if not NO_EAR_CHAIN:
    CLOTH_CHAINS["body"].append(dict(
        name="BunnyEar_R", roots=["Head_Root_Headband.001"], parent_fn=4, n_new=3,
        segs=["Head_Root_Headband.001", "Head_Root_Headband.002",
              "Head_Root_Headband.003", "Head_Root_Headband.004"],
        poly_nodes="Headband", preset="charm"))
    CLOTH_CHAINS["body"].append(dict(
        name="BunnyEar_L", roots=["Head_Root_Headband.005"], parent_fn=4, n_new=2,
        segs=["Head_Root_Headband.005", "Head_Root_Headband.006"],
        poly_nodes="Headband", preset="charm"))
    w("   [链组] 兔耳：R 4 段（3 节点）/ L 2 段（2 节点）—— ★ 实测左右不对称，不是 3+3")
# ---- body：包 `Bag`（`Chest_Root_Bag.001/.002`，Σw 6173 —— 全表最大）----
#   实测（X1 ⑨）：`.001` 质心(−0.065,−0.071,+0.861) Σw 566（靠上/贴胸）
#                `.002` 质心(−0.150,−0.032,+0.772) Σw 5607（包本体，主导 9982 顶点）
#   ⇒ 2 节点链，根 = `Chest_Root_Bag` 骨 head；走折线（两段质心连线）。
if not NO_BAG_CHAIN:
    CLOTH_CHAINS["body"].append(dict(
        name="Bag", roots=["Chest_Root_Bag"], parent_fn=2, n_new=2,
        segs=["Chest_Root_Bag.001", "Chest_Root_Bag.002"],
        poly_nodes="Bag", preset="charm"))
    w("   [链组] 包：2 段（2 节点）★ Σw 最大（6173）⇒ 会明显晃；兜底开关 nobagchain / nobag")
# ---- body：`Suit` 的髋部/腿洞蕾丝褶边 `Hip_Root_Suit.*`（★ 不是裙摆！用户 2026-10-03 明确纠正）----
#   实测（X1 ⑨，每侧 9 个段组、`.004` 无权重）：它们在**方位角**上绕腿洞一圈（z 几乎不变 0.72~0.77）：
#     L 侧 y：`.003`−0.066 → `.002`−0.045 → `.001`−0.018 → `.005`+0.011 → `.006`+0.035
#            → `.007`+0.060 → `.008`+0.076 → `.009`+0.080（−y 是前方）
#   ⇒ **不是一条链**，是"前半弧 + 后半弧"。硬拉成一条 4 节点链会得到绕髋一圈的怪折线。
#   ⇒ 每侧拆成 **2 条 2 节点链**（前弧 / 后弧），共 4 条 = 8 根骨（与提示词预算的 8 根一致）。
if not NO_SUIT_CHAIN:
    for _sd in ("L", "R"):
        CLOTH_CHAINS["body"].append(dict(
            name="SuitFrill_%s_F" % _sd, roots=["Hip_Root_Suit"],
            segs=["Hip_Root_Suit.%03d.%s" % (i, _sd) for i in (1, 2, 3)],
            parent_fn=13, n_new=2, poly_nodes="Suit", preset="charm"))
        CLOTH_CHAINS["body"].append(dict(
            name="SuitFrill_%s_B" % _sd, roots=["Hip_Root_Suit"],
            segs=["Hip_Root_Suit.%03d.%s" % (i, _sd) for i in (5, 6, 7, 8, 9)],
            parent_fn=13, n_new=2, poly_nodes="Suit", preset="charm"))
    w("   [链组] Suit 髋褶：每侧 2 条（前弧 3 段 / 后弧 5 段），各 2 节点")
# ---- body：颈饰 `Choker` 的 `Neck_Root_Choker.*`（11 段）----
#   实测（X1 ⑨）：全部挤在 x±0.035 / y −0.057~−0.024 / z 1.000~1.059（**整件只有 6cm 高**）
#   ⇒ 按几何分两组：**上面一圈**（z≥1.033：`.001/.002/.003/.006/.007/.008`）+
#                   **下面垂坠**（y≤−0.038 或 z<1.03：`.004/.005/.009/.010/.011`）。
#   ⇒ 2 条 2 节点链（共 4 根骨；提示词给的预算是 6 —— 但整件只有 6cm，2 节点已足够，见报告）。
if not NO_CHOKER_CHAIN:
    # ★★ **不走折线**：这 11 段是"上圈 + 下垂"两簇**散开的小片**，`seg_nodes` 排出来是
    #   往复折线（实测 ChokerBand 弧长 0.1079 而几何只跨 0.032 ⇒ 3.4 倍；ChokerDrop 7.6 倍）
    #   —— 与 第6版 的 BikiniStrap / ShoulderFrill 同一个坑 ⇒ 走 `chain_tip`（根 = 源骨 head、
    #   尖 = 几何 p95）的**直线轴**。
    CLOTH_CHAINS["body"].append(dict(
        name="ChokerBand", roots=["Neck_Root_Choker"], parent_fn=3, n_new=2,
        segs=["Neck_Root_Choker.%03d" % i for i in (1, 2, 3, 6, 7, 8)],
        preset="charm"))
    CLOTH_CHAINS["body"].append(dict(
        name="ChokerDrop", roots=["Neck_Root_Choker"], parent_fn=3, n_new=2,
        segs=["Neck_Root_Choker.%03d" % i for i in (4, 5, 9, 10, 11)],
        preset="charm"))
    w("   [链组] 颈饰：2 条 × 2 节点（上圈 6 段 / 下垂 5 段；★ 走 chain_tip 直线轴）")
# ---- wst：本套兔尾 `Tail`（★ 与 第6版 的衣服兔尾不同：**它有真权重**）----
#   实测（X1 ⑨ 与 `_probe2.txt` ①）：`Hips` 2518 / `Hip_Root_Tail.001` 2023 / `.002` 517 / `Spine` 207
#   ⇒ 2 节点链（根 = `Hip_Root_Tail.001` 骨 head），走折线；链与 ctc 同在 wst 部位。
if not NO_TAIL_CHAIN:
    # ★★ **不走折线**：`seg_nodes` 的选取规则是"该顶点的**链组权重和 > 非链组权重和**"，
    #   而兔尾的顶点大量是 `{Hip_Root_Tail.001:0.4, Hips:0.6}` 这种（**主导组**是链组、但
    #   链组权重和 < 非链组）⇒ 两个段组都收不到点、折线退化成 0 长度（实测弧长 0.0000）
    #   ⇒ 走 `chain_tip`（根 = 源骨 head，尖 = 该件链组几何的 p95 最远点）的**直线轴**。
    CLOTH_CHAINS["wst"].append(dict(
        name="BunnyTail", roots=["Hip_Root_Tail.001"], parent_fn=13, n_new=2,
        segs=["Hip_Root_Tail.001", "Hip_Root_Tail.002"], preset="charm"))
    w("   [链组] 兔尾：2 段（2 节点）★ 有真权重（Σw 2540）⇒ 会晃；★ 走 chain_tip 直线轴")

# 原组名 -> (链名, u)。u=None ⇒ 逐点按顶点在链上的投影算（折线链用**弧长参数**，直线链用弦投影）
CHAIN_GROUP = {}
for _p, _lst in CLOTH_CHAINS.items():
    for _c in _lst:
        for _g in _c["segs"]:
            CHAIN_GROUP[_g] = (_c["name"], None)
w("   [链组] 共 %d 个链组名" % len(CHAIN_GROUP))
for _p in ("wst", "arm", "body"):
    w("        %-5s %2d 条链 / %2d 节点：%s" %
      (_p, len(CLOTH_CHAINS[_p]), sum(c["n_new"] for c in CLOTH_CHAINS[_p]),
       [c["name"] for c in CLOTH_CHAINS[_p]]))

# ---------- ③ 链骨节点位置 ----------
w("")
w("### ③ 链骨位置计算（根 = 素材骨架对应骨 head 的均值；折线链走 seg_nodes 弧长取点；直线链走几何 p95）")
_grp_pts = {}
_grp_pts_all = {}
_SKIP_BUILD = set(VARIANT_SKIP.keys())
for _nm, (_pt, _src, _mm, _mk) in NEW.items():
    if _nm in _SKIP_BUILD:
        continue
    _o = OBJ.get(_src)
    if _o is None:
        continue
    _co = np.array(_o["world"], float)
    for _vi, _wd in enumerate(_o["vgw"]):
        if not _wd:
            continue
        _best = max(_wd.items(), key=lambda kv: kv[1])[0]
        for _g in _wd:
            if _g in CHAIN_GROUP:
                _grp_pts_all.setdefault(_g, []).append(_co[_vi])
        if _best in CHAIN_GROUP:
            _grp_pts.setdefault(_best, []).append(_co[_vi])
# ★ 有些链组**从来不是任何顶点的主导组**（那片的顶点主导组是权重 1.0 的那根真身骨）⇒ 主导组口径
#   会收集到 0 个点，chain_tip 退回"骨架骨 tail"（= 导入器的显示朝向，**不可靠**，skill 第八次实战 E）。
#   给它们一个 "权重>0" 的兜底。★ 判据：链长为 0 或恰好等于骨长时先怀疑这个。
_EMPTY = [g for g in CHAIN_GROUP if len(_grp_pts.get(g, [])) < 4 and len(_grp_pts_all.get(g, [])) >= 4]
for _g in _EMPTY:
    _grp_pts[_g] = _grp_pts_all[_g]
w("   [兜底] 主导组为空、改用「权重>0」口径的链组 %d 个：%s" % (len(_EMPTY), _EMPTY))
# ★★ 本版新增：`force_obj` 链（`Tail.001` 整件没有顶点组）—— 几何直接从该对象取。
for _c in [c for lst in CLOTH_CHAINS.values() for c in lst]:
    if _c.get("force_obj"):
        _fo = OBJ.get(_c["force_obj"])
        if _fo is None:
            w("   !! force_obj %s 不在采集结果里" % _c["force_obj"])
            continue
        _co = np.array(_fo["world"], float)
        _c["force_pts"] = _co
        w("   [force_obj] %-12s 取整件几何 %d 点（%s）→ 按 u 白送权重" %
          (_c["name"], len(_co), _c["force_obj"]))


def chain_tip(head_prev, groups):
    pts = []
    for g in groups:
        pts.extend(_grp_pts.get(g, []))
    if len(pts) < 4:
        return None, 0.0
    P = np.array(pts, float)
    dv = P - head_prev
    dl = np.linalg.norm(dv, axis=1)
    k = int(np.clip(np.searchsorted(np.sort(dl), 0.95 * len(dl)), 0, len(dl) - 1))
    tl = float(np.sort(dl)[k])
    far = P[int(np.argmin(np.abs(dl - tl)))] - head_prev
    if tl < 1e-6 or np.linalg.norm(far) < 1e-6:
        return None, 0.0
    return head_prev + far / np.linalg.norm(far) * tl, tl


def seg_nodes(srcname, segs, n_new, inclusive=False):
    """沿"段组质心的折线"均匀取 n_new 个点（**预览坐标**，调用者再过 xf）。
    ★ 弯曲的链（尾巴/双马尾）必须走这条路：用 head->p95 最远点的**直线弦**当中心线，
      实测尾巴的弧线中段偏离弦 **0.112 预览单位 ≈ 15cm**（弦长 0.55），关节会飘在网格外面。"""
    o = OBJ[srcname]
    co = np.array(o["world"], float)
    vgw = o["vgw"]
    n_orig = len(segs)
    segset = set(segs)
    cents = np.zeros((n_orig, 3))
    cnt = np.zeros(n_orig)
    for vi, wd in enumerate(vgw):
        if not wd:
            continue
        ch_w = sum(x for g, x in wd.items() if g in segset)
        bd_w = sum(wd.values()) - ch_w
        if ch_w <= bd_w:
            continue
        best = max(wd.items(), key=lambda kv: kv[1])[0]
        if best in segset:
            k = segs.index(best)
            cents[k] += co[vi] * wd[best]
            cnt[k] += wd[best]
    for i in range(n_orig):
        if cnt[i] > 0:
            cents[i] /= cnt[i]
    for i in range(n_orig):
        if cnt[i] > 0:
            continue
        lo = max([j for j in range(n_orig) if cnt[j] > 0 and j < i], default=None)
        hi = min([j for j in range(n_orig) if cnt[j] > 0 and j > i], default=None)
        if lo is None:
            cents[i] = cents[hi]
        elif hi is None:
            cents[i] = cents[lo]
        else:
            f = (i - lo) / (hi - lo)
            cents[i] = cents[lo] * (1 - f) + cents[hi] * f
    ext = cents[0] + (cents[0] - cents[1]) * 0.5 if n_orig >= 2 else cents[0] + np.array([0, 0, 0.03])
    poly = np.vstack([ext[None, :], cents])
    dl = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(dl)])
    total = max(cum[-1], 1e-9)
    nodes = np.zeros((n_new, 3))
    for k in range(n_new):
        # ★ inclusive=True：末节点取在**折线末端**（k/(n-1)），而不是 k/n。
        #   用 k/n 时最后一段（1/n）没有节点 ⇒ 那段顶点全落 u>1、被夹到 tip 骨上。
        #   实测尾巴：n=5 时**75% 的顶点**都堆在 tip 一根上 ⇒ 整条尾巴像"以尾尖为铰点的刚性片"
        #   （这就是用户说的"很沉"）。双马尾沿用默认 k/n（那条已实收认可）。
        s = total * k / ((n_new - 1) if (inclusive and n_new > 1) else n_new)
        j = int(np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(dl) - 1))
        f = 0.0 if dl[j] < 1e-12 else (s - cum[j]) / dl[j]
        nodes[k] = poly[j] * (1 - f) + poly[j + 1] * f
    return nodes.tolist(), int((cnt > 0).sum()), poly.tolist()


def order_segs_geo(srcname, segs, root_pt):
    """按**几何**把段组排成一条链：从离 root 最近的段组出发，逐步取最近的未访问段组。
    ★ 依据（本版实测，见文件头 ⑥）：**作者编号不沿链** ——
      · `arm_tentacle_2_L`：根 z0.965 → .007 z0.926 → .006 → .005 → .004 → .003 → .002 → .001 z0.727
        （编号从链尾往根数）
      · `RT_Hair_Twin_L`：根 z1.143 → .001 z1.107 → **.007 z1.005** → .002 z0.820 → .003 → .004 → .005
        （.007 排在链的第二位）
      ⇒ 照名字序号排会得到**锯齿折线**，seg_nodes 沿着它取节点＝关节飘在网格外面。
    返回 (ordered_segs, 说明)。段组质心用"权重>0"口径（该件内）。
    """
    o = OBJ[srcname]
    co = np.array(o["world"], float)
    acc = {}
    segset = set(segs)
    for vi, wd in enumerate(o["vgw"]):
        for g, x in wd.items():
            if g not in segset:
                continue
            d = acc.setdefault(g, [np.zeros(3), 0.0])
            d[0] += co[vi] * x
            d[1] += x
    pts = {g: acc[g][0] / acc[g][1] for g in acc if acc[g][1] > 0}
    if len(pts) < 2:
        return list(segs), "%d/%d 组有质心（不足以排序，保持原序）" % (len(pts), len(segs))
    root = np.asarray(root_pt, float)
    cur = min(pts, key=lambda g: float(np.linalg.norm(pts[g] - root)))
    order, left = [cur], [g for g in pts if g != cur]
    while left:
        nxt = min(left, key=lambda g: float(np.linalg.norm(pts[g] - pts[cur])))
        order.append(nxt)
        left.remove(nxt)
        cur = nxt
    order += [g for g in segs if g not in pts]      # 没质心的组：追加到末尾
    return order, ("几何序 %d 组（%s）" % (len(order), "与原序相同" if order == list(segs) else "与原序不同"))

for _p, _lst in CLOTH_CHAINS.items():
    for _c in _lst:
        hs = []
        for _rb in _c["roots"]:
            _src = A4.get(_rb)
            assert _src is not None, "素材骨架里没有 %s" % _rb
            hs.append(np.array(_src["head"], float))
        hp = np.mean(hs, axis=0)
        _src0 = A4.get(_c["roots"][0])
        # ★★ 坑2：折线链的段组必须先按**几何**排序（作者编号不沿链 —— 见文件头 ⑥）
        if _c.get("poly_nodes"):
            _ord, _diag = order_segs_geo(_c["poly_nodes"], _c["segs"], hp)
            if _ord != list(_c["segs"]):
                w("   [几何排序] %-13s 原序 %s" % (_c["name"], _c["segs"]))
                w("   %-13s            实序 %s" % ("", _ord))
            _c["segs"] = _ord
        if _c.get("poly_nodes"):
            # ★ 节点取 k/n（**不是** k/(n-1)）：末节点落在弧长的 80% 处，
            #   这样"末段 20% 的顶点（尾巴的蓬松尾尖，占 80% 顶点数）"是**绕 80% 处转**，
            #   会甩起来。取 k/(n-1) 会把末节点放到尾尖本身 ⇒ 尾尖绕自己转 = 不动。
            #   （双马尾用同一约定，那条用户认可。）
            _nodes, _nd, _poly = seg_nodes(_c["poly_nodes"], _c["segs"], _c["n_new"])
            _c["nodes"] = [xf(np.array(q, float)).tolist() for q in _nodes]
            _c["axis_poly"] = _poly
            _c["npts"] = len(_poly)
            _lenp = float(np.sum(np.linalg.norm(np.diff(np.array(_poly, float), axis=0), axis=1)))
            _chord = float(np.linalg.norm(np.array(_poly[-1], float) - np.array(_poly[0], float)))
            _rt = _lenp / max(_chord, 1e-9)
            w("   [折线链] %-13s 折线 %d 点，弧长 %.4f（预览）弦长 %.4f 比 %.2f 首 %s 末 %s" %
              (_c["name"], len(_poly), _lenp, _chord, _rt,
               np.round(_poly[0], 4).tolist(), np.round(_poly[-1], 4).tolist()))
            if _lenp < 1e-4:
                w("   !! %-13s 折线**退化成 0 长度**（段组收不到点）⇒ 请改用 chain_tip（去掉 poly_nodes）"
                  % _c["name"])
            elif _rt > 2.5:
                w("   !! %-13s 弧长/弦长 = %.2f > 2.5 ⇒ **往复折线**（节点会飘在几何外）⇒ 改用 chain_tip"
                  % (_c["name"], _rt))
            w("   %-13s %-4s 根 %-24s head×T=(%+.4f,%+.4f,%+.4f) 弧长%.4f 节点%d 段组%d" %
              (_c["name"], _p, _c["roots"][0], xf(hp)[0], xf(hp)[1], xf(hp)[2], _lenp,
               _c["n_new"], len(_c["segs"])))
            continue
        if _c.get("force_obj"):
            # ★★ 本版新增：整件没有顶点组的链（`Tail.001` 兔尾）—— 尖 = 该件几何的 p95 最远点，
            #   链轴 = 根→尖的**直线**（绒球是团块，没有可用的折线），权重走 FORCE_CHAIN 的逐点 u。
            _fp = np.array(_c.get("force_pts", []), float)
            if len(_fp) < 4:
                w("   !! force_obj %s 几何不足" % _c["name"])
                continue
            _dv = _fp - hp
            _dl = np.linalg.norm(_dv, axis=1)
            tl = float(np.percentile(_dl, 95))
            _far = _fp[int(np.argmin(np.abs(_dl - tl)))] - hp
            tp = hp + _far / max(np.linalg.norm(_far), 1e-9) * tl
            _nn = _c["n_new"]
            _c["nodes"] = [xf(hp + (tp - hp) * k / _nn).tolist() for k in range(_nn)]
            _c["axis"] = [hp.tolist(), tp.tolist()]
            _c["npts"] = len(_fp)
            w("   [整件链] %-13s %-4s 根 %-24s head×T=(%+.4f,%+.4f,%+.4f) 链长%.4f 节点%d 点%d"
              % (_c["name"], _p, _c["roots"][0], xf(hp)[0], xf(hp)[1], xf(hp)[2], tl, _nn, len(_fp)))
            w("   %-13s 预览轴 根(%+.4f,%+.4f,%+.4f) 尖(%+.4f,%+.4f,%+.4f)" %
              ("", hp[0], hp[1], hp[2], tp[0], tp[1], tp[2]))
            continue
        if _c.get("dir_from"):
            # 链方向取自**源骨链**（.001.head -> .002.head），长度取该链所有段组顶点沿此方向的最大投影
            _a = np.array(A4[_c["dir_from"][0]]["head"], float)
            _b = np.array(A4[_c["dir_from"][1]]["head"], float)
            _dv = _b - _a
            _n = float(np.linalg.norm(_dv))
            tp, tl = None, 0.0
            if _n > 1e-6:
                _dv = _dv / _n
                _pts = np.array([q for _g in _c["segs"] for q in _grp_pts.get(_g, [])], float)
                if len(_pts):
                    tl = float(np.max((_pts - hp) @ _dv))
                    if tl > 0.01:
                        tp = hp + _dv * tl
                w("   [方向链] %-13s 源骨方向 (%+.3f,%+.3f,%+.3f) 投影最长 %.4f m" %
                  (_c["name"], _dv[0], _dv[1], _dv[2], tl))
            if tp is None:
                tp = np.array(_src0["tail"], float)
                tl = float(np.linalg.norm(tp - hp))
        else:
            tp, tl = chain_tip(hp, _c["segs"])
            if tp is None:
                tp = np.array(_src0["tail"], float)
                tl = float(np.linalg.norm(tp - hp))
        _nn = _c["n_new"]
        if _nn == 2:
            _c["nodes"] = [xf(hp).tolist(), xf(tp).tolist()]
        else:
            # ★ 取 **k/n**，不是 k/(n-1)：末节点落在 100% 处时，最末端那批顶点是
            #   "绕自己转 = 不动"（skill「链条的节点该放在哪」§2 实测教训）。
            #   k/n 让末段（33% 的顶点）绕 67% 处的关节转 ⇒ 会甩。
            _c["nodes"] = [xf(hp + (tp - hp) * k / _nn).tolist() for k in range(_nn)]
        _c["axis"] = [hp.tolist(), tp.tolist()]
        _c["npts"] = sum(len(_grp_pts.get(g, [])) for g in _c["segs"])
        w("   %-13s %-4s 根 %-24s head×T=(%+.4f,%+.4f,%+.4f) 链长%.4f 节点%d 段组%d 点%5d" %
          (_c["name"], _p, _c["roots"][0], xf(hp)[0], xf(hp)[1], xf(hp)[2], tl, _nn,
           len(_c["segs"]), _c["npts"]))
CHAIN_SPEC = CLOTH_CHAINS
CSPEC = {}
for _p, _lst in CHAIN_SPEC.items():
    for _c in _lst:
        CSPEC[_c["name"]] = _c




NEED = {p: sum(c["n_new"] for c in CHAIN_SPEC[p]) for p in CHAIN_SPEC}
# ★★ 全部按**链名**固定分配骨号（不是"按部位顺序发"）—— 开关增删链条时其余链的号不会漂移，
#   Y4/Y4b 的硬编码列表永远对得上（skill「第九次实战 E」）。
#   号池实测（**本工程** `_X11_骨号现状.txt`，主 blend `MAIN_BLEND`）：
#     body 空闲 22-29,65,68,78-79,86-100,105-149,192-193,200,206-246,255
#     wst  空闲 同上 + 201-246 ；arm 空闲 105-149,201-246,255 ；leg 空闲 105-246,255
#   ★ `DEL_RANGE` 会先删掉 140~193 与 206~246（历史遗留的链骨，含 第1~5版 的）
#     ⇒ 实际可用池 = 140~193（54）+ 200 + 206~246（41）+ 255 = **97**（与提示词一致）。
#   ⇒ 本版需要 body 29 根 / wst 2 根 / arm 0 根 = **31 根**，池子很宽裕。
#   **不碰** 194~199（胸骨）/ 201~205（角色 原版尾巴链 —— v1/v2 删尾时其实可回收，
#   但没必要；v3/v4 保留原版尾 ⇒ 本来就不能动）/ 247~255（原版）。
CHAIN_FNS = {}
# ---- body（自己的号空间）----
CHAIN_FNS["TwinTail_L"] = [206, 207, 208, 209, 210]
CHAIN_FNS["TwinTail_R"] = [211, 212, 213, 214, 215]
CHAIN_FNS["BunnyEar_L"] = [216, 217]
CHAIN_FNS["BunnyEar_R"] = [218, 219, 220]
CHAIN_FNS["Bag"] = [221, 222]
CHAIN_FNS["SuitFrill_L_F"] = [223, 224]
CHAIN_FNS["SuitFrill_L_B"] = [225, 226]
CHAIN_FNS["SuitFrill_R_F"] = [227, 228]
CHAIN_FNS["SuitFrill_R_B"] = [229, 230]
CHAIN_FNS["ChokerBand"] = [231, 232]
CHAIN_FNS["ChokerDrop"] = [233, 234]
# ---- wst（自己的号空间）----
CHAIN_FNS["BunnyTail"] = [206, 207]
w("   [号] 需要：wst %d / arm %d / body %d = %d 个（四个部位各有独立号空间）" %
  (NEED["wst"], NEED["arm"], NEED["body"], sum(NEED.values())))
for _p, _lst in CHAIN_SPEC.items():
    for _c in _lst:
        assert _c["name"] in CHAIN_FNS, "链 %s 没有分配骨号" % _c["name"]
        assert len(CHAIN_FNS[_c["name"]]) == _c["n_new"], \
            "链 %s 的号数 %d != 节点数 %d" % (_c["name"], len(CHAIN_FNS[_c["name"]]), _c["n_new"])
ALLOC = {p: [f for c in CHAIN_SPEC[p] for f in CHAIN_FNS[c["name"]]] for p in CHAIN_SPEC}
for _p in ALLOC:
    assert len(set(ALLOC[_p])) == len(ALLOC[_p]), "%s 的骨号有重复" % _p
w("   [号] body 206~234 ｜ wst 206~207 ｜ arm 无（保留段 194~199 胸骨 / 200 / 201~205 原版尾 不动）")
w("   [号] wst %s / arm %s / body %s" % (ALLOC["wst"], ALLOC["arm"], ALLOC["body"]))

# ---------- ④ 建链骨 ----------
w("")
w("### ④ 建链骨")
try:
    bpy.ops.object.mode_set(mode="OBJECT")
except RuntimeError:
    pass
BONE_LEN = 0.05
# ★★ 本版把 140~193 **与 206~246** 全部先删掉（都是历史遗留的链骨：第1~5版 的裙摆/头发/
#   腰部褶边/缎带/触手链）。理由：`eb.new("MhBone_206")` 在同名骨已存在时会被 Blender
#   **静默改名**成 `MhBone_206.001` ⇒ 链骨号整体错位（skill 第五次实战 A 记过这个坑）。
#   **不碰** 194~199（胸骨）/ 200（arm 的旧链骨）/ 201~205（原版尾巴）/ 247~255（原版）。
DEL_RANGE = set(range(140, 194)) | set(range(206, 247))
ALL_CHAIN_FNS = set()
for part in ("wst", "arm", "body"):
    arm = bpy.data.objects[PART_ARM[part]]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    to_del = [nm for nm in eb.keys() if nm.startswith("MhBone_") and
              int(nm.split("_")[1]) in DEL_RANGE]
    for nm in to_del:
        eb.remove(eb[nm])
    made = {}
    pool = list(ALLOC[part])
    for c in CHAIN_SPEC[part]:
        pf = c["parent_fn"]
        prev = eb.get("MhBone_%03d" % pf)
        assert prev is not None, "找不到父骨 MhBone_%03d" % pf
        fns, prevb = [], prev
        for j in range(c["n_new"]):
            fn = pool.pop(0)
            b = eb.new("MhBone_%03d" % fn)
            h = np.array(c["nodes"][j], float)
            b.head = h.tolist()
            b.tail = (h + np.array([0.0, 0.0, BONE_LEN])).tolist()
            b.roll = 0.0
            b.use_connect = False
            b.parent = prevb
            prevb = b
            fns.append(fn)
        c["fns"] = fns
        made[c["name"]] = fns
        ALL_CHAIN_FNS |= set(fns)
        w("   %-13s %-4s 删旧链骨后新建：骨号 %s 父=MhBone_%03d  n=%d" %
          (c["name"], part, fns, pf, c["n_new"]))
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()

_a = bpy.data.objects[PART_ARM["wst"]]
_ref = _a.data.bones.get("MhBone_041")
for _nm in ("MhBone_206", "MhBone_216", "MhBone_218", "MhBone_221", "MhBone_234"):
    _b = _a.data.bones.get(_nm)
    if _b and _ref:
        _d = np.abs(np.array(_b.matrix_local)[:3, :3] - np.array(_ref.matrix_local)[:3, :3]).max()
        w("   %s matrix_local 3x3 与既有骨 MhBone_041 的最大差 = %.6f（应≈0 ⇒ 形态照抄成功）" %
          (_nm, _d))
w("   [号] 全部新链骨 %d 个：%s" % (len(ALL_CHAIN_FNS), sorted(ALL_CHAIN_FNS)))

# ★★ 把"本版实际建了哪些链"写成 JSON 给 `Y4b_物理ctc.py` 读 —— **单一数据源**：
#   否则开关改了链条数量、而 Y4b 里的 SPEC 还是硬编码的 ⇒ 号与链错配（skill 第五次实战 D 那类）。
CHAIN_DUMP = {}
for _p2, _lst2 in CHAIN_SPEC.items():
    CHAIN_DUMP[_p2] = [[c["name"], list(c["fns"]), c.get("preset", "charm")] for c in _lst2]
_js = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_Y1_链清单.json")
json.dump(CHAIN_DUMP, open(_js, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
w("   [链清单] 已写出 %s：%s" % (os.path.basename(_js),
                                 {k: [x[0] for x in v] for k, v in CHAIN_DUMP.items()}))

# ---------- ⑤ 建网格 ----------
w("")
w("### ⑤ 建网格（几何 + 权重 + 按材质拆件 + 逐面角 UV）")
PART_BONES = {p: set(b.name for b in bpy.data.objects[PART_ARM[p]].data.bones) for p in PART_ARM}
extra_mats = {}

# ---------- ⑤a 穿模修正（贴合衣物 -> 身体）----------
# ★ 本版的依据（`_X3_preview.txt` ⑦ 实测的"陷入比例 / 最深"）：
#     D_Tights 9.16% / −11.9mm（★ 由"为高跟鞋做的鞋楦"造成 ⇒ 先做 FOOT_FIX 旋转，再兜底）
#     C_Pants 16.91% / −3.9mm ；A_Tops 4.59% / −2.9mm ；C_Bunny 2.36% / −2.0mm
#     A_Collar 2.14% / −0.9mm ；F_Globe 1.24% / −0.9mm ；B_Bikini 0.61% ；B_Harness 0.43%
#   配方照抄 skill「第六次实战 E」——已实测有效，且**只动新件、只向外、从不内移**：
#     ① 逐顶点算到身体表面的有符号距离 d（正 = 在外）
#     ② need = max(0, 目标间隙 − d)
#     ③ 按穿透深度加权 + 向 1~2 环扩散（衰减 0.6）      ⇒ 防尖刺
#     ④ Laplacian 平滑位移 4 轮（α=0.6）                ⇒ 防折痕
#     ⑤ 沿**最近身体点的法线**外推；迭代 ≤4 次直到达标
#   ★ 必须在**建描边壳之前**做（`GEOM[objname]["P"]` 存的是 `newco`）⇒ 壳跟着走。
#   ★ 目标间隙：贴身的软件 0.6mm 就够；**粗环/带类**要 +1.5mm（面片弦切，skill 第十次实战 E）。
#   值 = (目标间隙, **累积位移上限**)。★ 上限是**累积**的（4 轮迭代的位移总量），不是每轮的
#   —— 第一版按"每轮"限幅 ⇒ 4 轮可累积 4 倍（LP_Tights 实测 43.76mm）。
PUSHOUT = {
           # ★ 依据 = `_probe4.txt`（FBX 直接叠在 preview2 身体上、零配准的有符号距离）：
           #     Choker   4.54% / −3.53mm   ← **真信号**（贴身件）
           #     Arm warmers 2.01% / −9.30mm ← **真信号**（袖子；v4 的重点，见 ⑥e）
           #     Suit     1.02% / −2.26mm
           #     Shoes    0.52% / −3.86mm（鞋底比脚底低 13mm 是**作者原样**，不要推鞋底）
           #     Stocking 0.53% / −0.82mm
           #     Bag      0.02% / −0.45mm（极好，不需要推）
           #     Gloves   1.22% / −31.2mm ← **先判真假**：Fur1 毛袖口 7062 面、x±0.598 远离身体，
           #                "最近点法线"在那里没有意义（第6版 §2.7 的假信号判读口径）⇒ 不推
           #   ★ 值 = (目标间隙, **累积位移上限**)，累积限幅见 pushout_fix 的说明。
           "BH_Choker":   (0.0015, 0.0060),   # 颈圈（4.54% / −3.53mm；粗环 ⇒ 目标 +1.5mm）
           "BH_Arm":      (0.0010, 0.0080),   # 袖子（2.01% / −9.30mm）
           "BH_Suit":     (0.0008, 0.0050),   # 紧身衣（1.02% / −2.26mm）
           "BH_Stocking": (0.0008, 0.0050)}   # 丝袜（0.53% / −0.82mm）
           # ★ 手套**不做外推**：它的 −31.2mm 是**假信号**（Fur1 毛袖口 7062 面、x±0.598 远离身体，
           #   那里的"最近点法线"没有几何意义 —— 与 第6版 §2.7 的耳/尾/头发同类），
           #   而且用户 2026-10-03 明确说"手套非常大，手指不管怎么动都不可能穿出手套"。
from mathutils.bvhtree import BVHTree as _BVH
_bb = bpy.data.objects["Body_base"]
_bmw = np.array(_bb.matrix_world)
BODY_V = [tuple(_bmw[:3, :3] @ np.array(v.co) + _bmw[:3, 3]) for v in _bb.data.vertices]
BODY_P = [tuple(p.vertices) for p in _bb.data.polygons]
BT_BODY = _BVH.FromPolygons(BODY_V, BODY_P)


def pushout_fix(objname, P0, polys, target, iters=4, cap=0.006, mode="push"):
    """把"陷进身体"的顶点沿身体法线**单调外推**到目标间隙。返回 (新坐标, 报告字符串)。
    ★ `cap` = **单个顶点的累积位移上限**（米，相对 P0）。理由（本版实测教训）：迭代里
      "最近特征会跳变" ⇒ `need` 每轮都算成正的、位移会**累积**（LP_Tights 第一版 4 轮累积 43.76mm）。
      限幅把失败模式变成"推不到位"（看得见的残差），而不是"把网格某一处拉成尖刺"。
    ★ `mode="proj"`（手套那种**凸的小曲面**用）：不再迭代外推，而是**直接投到"体表 + 余量"**
      （`P = loc + nrm·target`），位移仍按 cap 累积限幅。理由：指尖处"最近点"会在相邻手指/
      指节之间跳变，沿法线迭代会让 penetrate 更深（本版实测 −1.3mm → −2.5mm）。"""
    nv = len(P0)
    nb = [set() for _ in range(nv)]
    for p in polys:
        for k in range(len(p)):
            a, b = p[k], p[(k + 1) % len(p)]
            nb[a].add(b)
            nb[b].add(a)
    nb = [sorted(s) for s in nb]
    P = np.array(P0, float)
    pen0, dmin0, dmin1, pen1, dmax = 0, 0.0, 0.0, 0, 0.0
    for it in range(iters):
        loc = np.zeros_like(P)
        nrm = np.zeros_like(P)
        d = np.zeros(nv)
        for i in range(nv):
            r = BT_BODY.find_nearest(tuple(P[i]))
            if r[0] is None:
                d[i] = 1e9
                continue
            loc[i] = r[0]
            nrm[i] = r[1]
            d[i] = float(np.dot(P[i] - np.array(r[0]), np.array(r[1])))
        if it == 0:
            pen0 = int((d < 0).sum())
            dmin0 = float(d.min())
        need = np.maximum(0.0, target - d)
        if mode == "proj":
            # ★ 直接投影到"体表 + 目标余量"（只对**陷入**的顶点；已在外的一律不动）
            _m = d < target
            if _m.any():
                P = np.where(_m[:, None], loc + nrm * target, P)
            if it < iters - 1:
                continue
        # ★★ 面心也参与判据：低模环/带类件的**面片弦切**用"逐顶点"看不到 ——
        #    足リング 只有 504 顶点 / 1008 三角，绕大腿一圈的弦高可达 1~3mm：
        #    三个顶点都在皮肤外，**面片的中段却切进肉里**（= 用户说的"靠近大腿内侧的一半陷进腿里"）。
        for p in (() if mode == "proj" else polys):
            q = P[list(p)].mean(0)
            r = BT_BODY.find_nearest(tuple(q))
            if r[0] is None:
                continue
            _sd = float(np.dot(q - np.array(r[0]), np.array(r[1])))
            _nd = target - _sd
            if _nd > 0:
                for v in p:
                    if _nd > need[v]:
                        need[v] = _nd
        if need.max() <= 1e-7:
            break
        disp = need.copy()
        for _r in range(2):                       # 向 1~2 环扩散（衰减 0.6）
            old = disp.copy()
            for i in range(nv):
                if nb[i]:
                    m = max(old[j] for j in nb[i])
                    if m * 0.6 > disp[i]:
                        disp[i] = m * 0.6
        for _s in range(4):                       # Laplacian 平滑位移 4 轮（α=0.6）
            old = disp.copy()
            for i in range(nv):
                if nb[i]:
                    disp[i] = old[i] * 0.4 + 0.6 * float(np.mean([old[j] for j in nb[i]]))
        P = P + nrm * disp[:, None]
        # ★★ 累积限幅：相对 P0 的总位移整体缩到 cap 以内（每轮都做）
        _tot = P - np.array(P0, float)
        _L = np.linalg.norm(_tot, axis=1)
        P = np.array(P0, float) + _tot * np.where(_L > cap, cap / np.maximum(_L, 1e-12), 1.0)[:, None]
    # 复核
    for i in range(nv):
        r = BT_BODY.find_nearest(tuple(P[i]))
        if r[0] is None:
            continue
        dd = float(np.dot(P[i] - np.array(r[0]), np.array(r[1])))
        dmin1 = min(dmin1, dd)
        if dd < 0:
            pen1 += 1
    dmax = float(np.linalg.norm(P - np.array(P0, float), axis=1).max())
    dmv = np.linalg.norm(P - np.array(P0, float), axis=1)
    n_cap = int((dmv >= cap - 1e-6).sum())
    return P, ("穿入 %d -> %d（最深 %+.4f -> %+.4f m）；目标间隙 %+.2fmm；最大位移 %.2fmm%s" %
               (pen0, pen1, dmin0, dmin1, target * 1000, dmax * 1000,
                "（★ %d 个顶点触到 %.1fmm 累积限幅）" % (n_cap, cap * 1000) if n_cap else ""))
def foot_fix(P0):
    """★ 坑3：丝袜 `D_Tights` 的脚 —— 绕踝**刚体旋转** + 抬到"身体脚底 − FOOT_CLEAR"。
    依据（提示词 §2.5 实测 + 本次 X1 ⑦ 复核）：
      · 身体脚底**全程平**（z 起伏 3mm）；丝袜鞋底从脚跟 +0.0172 单调降到脚尖 −0.0022
        ⇒ 绕踝约 **6.19°** 的"脚尖下沉"，袜尖比身体脚底低 **17.3 mm**。
      · 做法：① 由鞋底剖面拟合斜率 m = dz/dy ⇒ 旋转角 θ = −atan(m)（把鞋底转平）；
              ② 绕踝（`Foot.L/R` 的骨 head）旋转，踝上下各 FOOT_FADE 用 smoothstep 淡入淡出；
              ③ 再整体抬到"身体脚底 − FOOT_CLEAR"（同样按 smoothstep 加权，踝以上不动）；
              ④ 只动**脚部**（踝以上一个顶点都不碰），且是**仿射**变换 ⇒ 不会引入折叠。
    返回 (新坐标, 报告行列表)。"""
    P = np.array(P0, float)
    legs = bpy.data.objects[PART_ARM["leg"]]
    lmw = np.array(legs.matrix_world)
    bb = bpy.data.objects["Body_base"]
    bmw = np.array(bb.matrix_world)
    BV = np.array([bmw[:3, :3] @ np.array(v.co) + bmw[:3, 3] for v in bb.data.vertices], float)
    out = np.array(P, float)
    msg = ["腿骨架 matrix_world 平移 %s（应≈0 ⇒ 网格数据坐标 = 世界坐标）" %
           np.round(lmw[:3, 3], 4).tolist()]
    for side, fn, sgn in (("L", 16, 1.0), ("R", 20, -1.0)):
        bone = legs.data.bones.get("MhBone_%03d" % fn)
        if bone is None:
            msg.append("!! 找不到 MhBone_%03d（%s 的踝）" % (fn, side))
            continue
        piv = lmw[:3, :3] @ np.array(bone.head_local) + lmw[:3, 3]
        # 身体脚底（同侧、z 在踝以下的区域）
        bm = (BV[:, 0] * sgn > 0) & (BV[:, 2] < piv[2])
        body_sole = float(BV[bm, 2].min()) if bm.any() else float("nan")
        # 本侧袜顶点的选择：x 同侧（按符号），脚尖朝 −y
        m = (P[:, 0] * sgn > 0)
        idx = np.where(m)[0]
        # 鞋底剖面：★ 只取**真正的鞋底**附近（z < 身体脚底 + 4cm）——
        #   第一版取"踝上 2cm 以下"把**小腿筒身**也圈进来了（筒身在 y 各档的最低 z 都远高于鞋底）
        #   ⇒ 拟合出的斜率 0.1615（应为 0.108）⇒ 多转了 3°，脚尖反而翘过头。
        zref = body_sole + 0.04 if body_sole == body_sole else piv[2] - 0.08
        foot = idx[P[idx, 2] < zref]
        prof = []
        if len(foot) > 20:
            y0, y1 = P[foot, 1].min(), P[foot, 1].max()
            nb = 18
            for k in range(nb):
                lo = y0 + (y1 - y0) * k / nb
                hi = y0 + (y1 - y0) * (k + 1) / nb
                sel = foot[(P[foot, 1] >= lo) & (P[foot, 1] < hi)]
                if len(sel) >= 3:
                    prof.append((float(P[sel, 1].mean()), float(P[sel, 2].min())))
        if len(prof) >= 4:
            A_ = np.array([[p[0], 1.0] for p in prof])
            b_ = np.array([p[1] for p in prof])
            mm_, cc_ = np.linalg.lstsq(A_, b_, rcond=None)[0]
        else:
            mm_, cc_ = 0.0, 0.0
        th = -np.arctan(mm_) if FOOT_ROT is None else np.radians(FOOT_ROT)
        ct, st = float(np.cos(th)), float(np.sin(th))
        # smoothstep 权重：踝 +FADE 以上 = 0，踝 −FADE 以下 = 1
        zz = P[:, 2]
        t = np.clip((piv[2] + FOOT_FADE - zz) / (2.0 * FOOT_FADE), 0.0, 1.0)
        s = t * t * (3.0 - 2.0 * t)
        dy = P[:, 1] - piv[1]
        dz = P[:, 2] - piv[2]
        # 逐顶点旋转（只对本侧、只对踝以下有权重的点起作用；s=0 的点完全不动）
        rot_y = dy * ct - dz * st
        rot_z = dy * st + dz * ct
        out[:, 1] = np.where(m, piv[1] + dy + (rot_y - dy) * s, out[:, 1])
        out[:, 2] = np.where(m, piv[2] + dz + (rot_z - dz) * s, out[:, 2])
        # 抬到"身体脚底 − FOOT_CLEAR"
        f2 = idx[out[idx, 2] < piv[2]]
        if len(f2) and body_sole == body_sole:
            sock_sole = float(out[f2, 2].min())
            want = body_sole - FOOT_CLEAR
            dzz = want - sock_sole
            out[:, 2] = np.where(m, out[:, 2] + dzz * s, out[:, 2])
            msg.append("%s：踝(preview %+.4f,%+.4f) 鞋底斜率 %+.4f ⇒ 旋转 **%+.2f°**；"
                       "身体脚底 %+.4f ／ 袜底 %+.4f → 抬 %+.2fmm 到 %+.4f（目标 %+.4f）" %
                       (side, piv[1], piv[2], mm_, np.degrees(th), body_sole, sock_sole,
                        dzz * 1000, sock_sole + dzz, want))
        else:
            msg.append("%s：!! 没找到脚部顶点（%d）" % (side, len(f2)))
        msg.append("%s：受影响顶点 %d（踝以上的 s=0 点 %d 个完全未动）" %
                   (side, int((s > 1e-6).sum()), int((s <= 1e-6).sum())))
    # 位移幅度（体检）
    dm = np.linalg.norm(out - P, axis=1)
    msg.append("位移：max %.2fmm 均值 %.3fmm  >0.5mm 的顶点 %d" %
               (dm.max() * 1000, dm.mean() * 1000, int((dm > 5e-4).sum())))
    return out, msg


BUILT = {}
BUILT_ALL = {}
UNKNOWN_GROUPS = set()
BONE_LOST = set()
FB_CNT = {}
REBIND_N = {}
FORCE_N = {}
DROP_STAT = {}


def resolve_group(g):
    if g in AUX:
        return "MhBone_%03d" % AUX[g]
    for pfx, fn in AUX_PREFIX:
        if g.startswith(pfx):
            return "MhBone_%03d" % fn
    fn = NAME2FN.get(g)
    if fn is not None:
        return "MhBone_%03d" % fn
    UNKNOWN_GROUPS.add(g)
    return "MhBone_002"


MADE_MATS = []
SHELLS = []
GEOM = {}
UDIST = {}      # 链名 -> 实际用到的 u 列表（诊断：看权重有没有均匀铺在链上）


def _tris(polys):
    out = []
    for p in polys:
        n = len(p)
        for k in range(1, n - 1):
            out.append((int(p[0]), int(p[k]), int(p[k + 1])))
    return out


def _tris_uv(polys, polyuv):
    """与 _tris 平行：每个扇三角的三个角的 UV。"""
    out = []
    for pi, p in enumerate(polys):
        n = len(p)
        row = polyuv[pi]
        for k in range(1, n - 1):
            out.append((row[0], row[k], row[k + 1]))
    return out


def _vnorm(P, tris):
    """按"该三角形自己的绕序"累加面积加权法线（= 本体外法线，前提是绕序朝外）。"""
    N = np.zeros_like(P)
    for i0, i1, i2 in tris:
        f = np.cross(P[i1] - P[i0], P[i2] - P[i0])
        N[i0] += f
        N[i1] += f
        N[i2] += f
    L = np.linalg.norm(N, axis=1)
    nz = int((L < 1e-12).sum())
    return N / np.maximum(L, 1e-12)[:, None], nz


def _vol(P, tris):
    v = 0.0
    for i0, i1, i2 in tris:
        v += float(np.dot(P[i0], np.cross(P[i1], P[i2]))) / 6.0
    return v


def build_shells():
    """⑤d 描边壳（inverted hull）：外扩 1mm + 反转绕序 + 顶点法线取反 + 独立材质 Outline_Black。
    见 `本项目调研记录\描边实现_报告.md`（实机验证过）。排除带：壳面若落在**别的**件表面 2mm 内就丢掉
    （上一版的坑：贴着头发卡片 0.09mm 的蝴蝶结被头发壳糊黑）。"""
    w("")
    w("### ⑤d 描边壳（外扩 %.1fmm；排除带 %.1fmm）" % (OUTLINE_OFF * 1000, OUTLINE_EXCL * 1000))
    from mathutils.bvhtree import BVHTree
    TRIS = {nm: _tris(g["polys"]) for nm, g in GEOM.items()}
    TUV = {nm: _tris_uv(g["polys"], g["polyuv"]) for nm, g in GEOM.items()}
    BOX = {nm: (g["P"].min(0), g["P"].max(0)) for nm, g in GEOM.items()}
    for objname in OUTLINE_SRC:
        g = GEOM.get(objname)
        if g is None:
            w("   !! %s 没有几何缓存（不在 NEW 里？）" % objname)
            continue
        P = g["P"]
        tris = TRIS[objname]
        N, nz = _vnorm(P, tris)
        v0 = _vol(P, tris)
        Ps = P + N * OUTLINE_OFF
        # ---- 排除带 ----
        # ★ 判据必须是「**别的件夹在本体表面与壳之间**」⇒ 只有这时它才会被壳糊黑
        #   （上一版的坑：贴着头发卡片 0.09mm 的蝴蝶结被 1mm 外的头发壳糊黑）。
        #   实测教训：第一版用"壳顶点到别件的距离 < 2mm"⇒ 相互贴着的两件会**互相吃掉**壳
        #   （内衣被吃 61%、内裤绳 78%、绷带整片被吃光），而那些面本来就不是轮廓。
        #   现在改成：`d_别件 < min(d_本体, EXCLUDE_M)` ——
        #     · 蝴蝶结：d_别件 0.91mm < d_本体 1.0mm ⇒ 切 ✓
        #     · 内衣在裙子里面：d_别件 = 间隙+1mm > 1mm ⇒ 不切 ✓
        #     · 内裤绳贴在绷带上：d_别件 0.7mm < 1mm ⇒ 切（对的：否则绳会把绷带糊黑）✓
        dd = np.full(len(P), 1e9)
        lo0, hi0 = Ps.min(0) - OUTLINE_EXCL, Ps.max(0) + OUTLINE_EXCL
        used = []
        if OUTLINE_EXCL > 0:
            for nm, Q in GEOM.items():
                if nm == objname:
                    continue
                lo, hi = BOX[nm]
                if (hi[0] < lo0[0] or lo[0] > hi0[0] or hi[1] < lo0[1] or lo[1] > hi0[1]
                        or hi[2] < lo0[2] or lo[2] > hi0[2]):
                    continue
                bt = BVHTree.FromPolygons([tuple(q) for q in Q["P"]],
                                          [tuple(t) for t in TRIS[nm]], all_triangles=True)
                for i in range(len(Ps)):
                    r = bt.find_nearest(tuple(Ps[i]))
                    if r and r[3] is not None and r[3] < dd[i]:
                        dd[i] = r[3]
                used.append(nm)
        # 本体表面到壳顶点的距离（≈ OUTLINE_OFF，但凹处会更大）
        down = np.full(len(P), OUTLINE_OFF)
        _bt_own = BVHTree.FromPolygons([tuple(q) for q in P],
                                       [tuple(t) for t in tris], all_triangles=True)
        for i in range(len(Ps)):
            r = _bt_own.find_nearest(tuple(Ps[i]))
            if r and r[3] is not None:
                down[i] = r[3]
        thr = np.minimum(down, OUTLINE_EXCL)
        keep_t = [t for t in tris if min(dd[t[0]], dd[t[1]], dd[t[2]]) >=
                  min(thr[t[0]], thr[t[1]], thr[t[2]])]
        n_cut = len(tris) - len(keep_t)
        # ★ 丢掉面之后会留下**孤立顶点** —— 必须一并去掉，否则导出器预检直接报
        #   LooseVerticesOnSubMesh（O1 实测踩过）。所以只保留"还有面的"顶点并重映射下标。
        used = sorted(set(v for t in keep_t for v in t))
        if not used:
            w("   !! %s 的壳被排除带吃光了，跳过" % objname)
            continue
        loc = {v: i for i, v in enumerate(used)}
        # ---- 建壳（绕序反转 ⇒ 顶点法线自动取反；UV 跟着换序，保持逐面角对应）----
        name = objname + "__Outline_Black"
        keep_uv = set(keep_t)
        fv, fu = [], []
        for ti, t in enumerate(tris):
            if t not in keep_uv:
                continue
            uvs = TUV[objname][ti]
            fv.append([loc[t[0]], loc[t[2]], loc[t[1]]])
            fu.append([uvs[0], uvs[2], uvs[1]])
        Ps2 = Ps[used]
        W2 = [g["W"][v] for v in used]
        me = bpy.data.meshes.new(name + "_mesh")
        me.from_pydata([tuple(map(float, q)) for q in Ps2], [], fv)
        me.update()
        uvl = me.uv_layers.new(name="UVMap")
        for pi2, poly in enumerate(me.polygons):
            for c, loi in enumerate(poly.loop_indices):
                uvl.data[loi].uv = (float(fu[pi2][c][0]), float(fu[pi2][c][1]))
        me.materials.append(get_mat(OUTLINE_MAT))
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        gs = {}
        for j, wl in enumerate(W2):
            for b, x in wl:
                if b not in gs:
                    gs[b] = o.vertex_groups.new(name=b)
                gs[b].add([int(j)], float(x), "REPLACE")
        o.parent = g["arm"]
        o.matrix_world = np.eye(4)
        md = o.modifiers.new(name="Armature", type="ARMATURE")
        md.object = g["arm"]
        g["coll"].objects.link(o)
        SHELLS.append(name)
        _pv = [tuple(q) for q in Ps2]
        _pt = [tuple(t) for t in fv]
        _v1 = _vol(_pv, _pt)
        _open = abs(v0 * 1e6) < 5.0     # 本体是"开放薄片"（头发卡片）⇒ 体积判据不适用
        _tag = "OK" if (v0 * _v1 < 0) else (
            "开放薄片：体积判据不适用（绕序由构造反转）" if _open else "!! 需查")
        w("   %-30s 顶点%6d 三角%6d（丢 %d 面 / 孤立 %d）| 体积 本体%+.4f 壳%+.4f cm3（%s）；"
          "法线为零 %d；用骨 %d" %
          (name, len(Ps2), len(fv), n_cut, len(Ps) - len(Ps2), v0 * 1e6, _v1 * 1e6,
           _tag, nz, len(gs)))
    w("   合计 %d 个描边壳" % len(SHELLS))


def get_mat(name):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    src = None
    for cand in ("Ch_Standard_Mt__5", "Ch_Standard_Mt__1", "Ch_Standard_Mt__3"):
        src = bpy.data.materials.get(cand)
        if src is not None:
            break
    m = src.copy() if src is not None else bpy.data.materials.new(name)
    m.name = name
    MADE_MATS.append(name)
    return m


def emit(objname, part, srcname, matmap, mainkey):
    d = OBJ[srcname]
    Wco = xf(np.array(d["world"], float))
    polys = d["polys"]
    nv = d["verts"]
    has_poly = np.zeros(nv, bool)
    for p in polys:
        has_poly[list(p)] = True
    n_loose = int((~has_poly).sum())
    z_top = float(Wco[:, 2].max())
    z_bot = float(Wco[:, 2].min())
    # 折线轴（弯曲链）：u = 顶点在折线上的**弧长参数**（贴根 0、尖部 1）
    cpoly = {}
    for _cn, c in CSPEC.items():
        if c.get("axis_poly"):
            _P = np.array(c["axis_poly"], float)
            _sg = _P[1:] - _P[:-1]
            _cum = np.concatenate([[0.0], np.cumsum(np.linalg.norm(_sg, axis=1))])
            cpoly[_cn] = (_P, _sg, _cum, max(float(_cum[-1]), 1e-9))
    caxis = {}
    for _cn, c in CSPEC.items():
        if c.get("axis"):
            a0 = np.array(c["axis"][0], float)
            a1 = np.array(c["axis"][1], float)
            dv = a1 - a0
            L2 = float(dv @ dv)
            caxis[_cn] = (a0, dv, L2 if L2 > 1e-12 else 1e-12)
    PW = np.array(d["world"], float)
    Wlist = []
    for vi in range(nv):
        wd = d["vgw"][vi]
        body = {}
        for g, x in wd.items():
            if x <= 0:
                continue
            if g in CHAIN_GROUP:
                cname, u = CHAIN_GROUP[g]
                c = CSPEC.get(cname)
                if c is None:
                    bn = resolve_group(g)
                    body[bn] = body.get(bn, 0.0) + x
                    continue
                # ★ 逐点 u：按顶点在链轴上的投影（贴根 0、尖部 1）⇒ 布片会"弯"而不是整片硬转
                if u is None and cname in cpoly:
                    _P, _sg, _cum, _tot = cpoly[cname]
                    _q = PW[vi]
                    _bd, _bu = 1e18, 0.0
                    for _k in range(len(_sg)):
                        _d = _sg[_k]
                        _L2 = float(_d @ _d)
                        _t = 0.0 if _L2 < 1e-12 else float(np.clip((_q - _P[_k]) @ _d / _L2, 0.0, 1.0))
                        _pr = _P[_k] + _d * _t
                        _dd = float(np.sum((_q - _pr) ** 2))
                        if _dd < _bd:
                            _bd = _dd
                            _bu = (_cum[_k] + _t * float(np.sqrt(_L2))) / _tot
                    u = float(np.clip(_bu, 0.0, 1.0))
                elif u is None and cname in caxis:
                    a0, dv, L2 = caxis[cname]
                    u = float(np.clip((PW[vi] - a0) @ dv / L2, 0.0, 1.0))
                elif u is None:
                    _gs = c["groups"]
                    u = ((_gs.index(g) if g in _gs else 0) + 0.5) / max(len(_gs), 1)
                UDIST.setdefault(cname, []).append(u)
                t_ = u * c["n_new"] - 0.5
                j0 = int(np.floor(t_))
                fr = t_ - j0
                for j, fx in ((j0, 1 - fr), (j0 + 1, fr)):
                    if fx <= 0:
                        continue
                    j = int(np.clip(j, 0, c["n_new"] - 1))
                    bn = "MhBone_%03d" % c["fns"][j]
                    body[bn] = body.get(bn, 0.0) + x * fx
            else:
                bn = resolve_group(g)
                body[bn] = body.get(bn, 0.0) + x
        # ★★ FORCE_CHAIN（坑2）：整件**没有任何顶点组**（`Tail.001` 兔尾，86 顶点）
        #   ⇒ 按顶点在链轴上的投影 u 把全部权重白送给该链（帐篷函数，与链权重同一套分配公式）。
        #   实测（`_probe2.txt` ⑤）：质心 (0,+0.0651,+0.7569)、盒 y +0.0319~+0.0982 z 0.7238~0.7901。
        if objname in FORCE_CHAIN:
            _fc = FORCE_CHAIN[objname]
            _cf = CSPEC.get(_fc)
            if _cf is not None and _fc in caxis:
                _a0f, _dvf, _L2f = caxis[_fc]
                _uf = float(np.clip((PW[vi] - _a0f) @ _dvf / _L2f, 0.0, 1.0))
                UDIST.setdefault(_fc, []).append(_uf)
                _t4 = _uf * _cf["n_new"] - 0.5
                _j4 = int(np.floor(_t4))
                _f4 = _t4 - _j4
                body = {}
                for _jj, _ff in ((_j4, 1 - _f4), (_j4 + 1, _f4)):
                    if _ff <= 0:
                        continue
                    _jj = int(np.clip(_jj, 0, _cf["n_new"] - 1))
                    body["MhBone_%03d" % _cf["fns"][_jj]] = body.get(
                        "MhBone_%03d" % _cf["fns"][_jj], 0.0) + _ff
                FORCE_N[objname] = FORCE_N.get(objname, 0) + 1
        # ★ 重绑（见 REBIND 注释）：把下垂那一段的权重按高度让给最近那条链
        if objname in REBIND:
            _sp = REBIND[objname]
            _tt = (z_top - Wco[vi, 2]) / max(z_top - z_bot, 1e-9)
            _sv = float(np.clip((_tt - _sp["t0"]) / max(1.0 - _sp["t0"], 1e-6), 0, 1)) * _sp["k"]
            if _sv > 0.001:
                _bn, _bu, _bd = None, 0.0, 1e18
                for _cn2, _ax in caxis.items():
                    _a0, _dv2, _L2b = _ax
                    _t2 = float(np.clip((PW[vi] - _a0) @ _dv2 / _L2b, 0.0, 1.0))
                    _dd2 = float(np.sum((PW[vi] - (_a0 + _dv2 * _t2)) ** 2))
                    if _dd2 < _bd:
                        _bd, _bu, _bn = _dd2, _t2, _cn2
                if _bn is not None:
                    _cc = CSPEC[_bn]
                    body = {b: x * (1.0 - _sv) for b, x in body.items()}
                    _t3 = _bu * _cc["n_new"] - 0.5
                    _j0b = int(np.floor(_t3))
                    _frb = _t3 - _j0b
                    for _j, _fx in ((_j0b, 1 - _frb), (_j0b + 1, _frb)):
                        if _fx <= 0:
                            continue
                        _j = int(np.clip(_j, 0, _cc["n_new"] - 1))
                        _b3 = "MhBone_%03d" % _cc["fns"][_j]
                        body[_b3] = body.get(_b3, 0.0) + _sv * _fx
                    REBIND_N[objname] = REBIND_N.get(objname, 0) + 1
        # 腰部褶边：分侧平滑跟腿（照抄 第2版、第3版、第4版 已验证做法 follow=0.55 / t0=0.45）
        if FOLLOW > 0 and objname in FOLLOW_OBJS:
            chain_names = set()
            for c in CSPEC.values():
                for fn in c.get("fns", []):
                    chain_names.add("MhBone_%03d" % fn)
            tt = (z_top - Wco[vi, 2]) / max(z_top - z_bot, 1e-9)
            sv = 0.0 if tt <= T0 else min(FOLLOW, FOLLOW * (tt - T0) / max(1.0 - T0, 1e-6))
            if sv > 0:
                uu = float(np.clip(Wco[vi, 0] / 0.12, -1.0, 1.0))
                wl, wr = sv * (0.5 + 0.5 * uu), sv * (0.5 - 0.5 * uu)
                ch = {b: x for b, x in body.items() if b in chain_names}
                cs = sum(ch.values())
                if cs > 0:
                    body = {b: x for b, x in body.items() if b not in chain_names}
                    for b, x in ch.items():
                        body[b] = (1.0 - sv) * x
                body["MhBone_014"] = body.get("MhBone_014", 0.0) + wl
                body["MhBone_018"] = body.get("MhBone_018", 0.0) + wr
        items = sorted(body.items(), key=lambda kv: -kv[1])
        items = [(b, x) for b, x in items if b in PART_BONES[part]]
        if len(items) < 1:
            # ★ 源素材里有个别顶点**没有任何顶点组**（实测：乳暖簾 2095 个顶点里有 6 个 ——
            #   2 个无组 + 4 个权重全 0）⇒ 用该部位"居中"的真身骨兜底，比硬编码 Head 稳
            #   （胸帘的散点挂到 Head 会被头拽着动）。
            BONE_LOST.add(objname)
            FB_CNT[objname] = FB_CNT.get(objname, 0) + 1
            items = [("MhBone_%03d" % FB_OBJ.get(objname, FB_FN.get(part, 2)), 1.0)]
        dropped = len(body) - len(items)
        if dropped > 0:
            DROP_STAT[objname] = DROP_STAT.get(objname, 0) + dropped
        items = items[:KMAX]
        tot = sum(x for _, x in items)
        if tot <= 0:
            items, tot = [("MhBone_004", 1.0)], 1.0
        Wlist.append([(b, x / tot) for b, x in items])

    keep = np.where(has_poly)[0]
    remap = -np.ones(len(Wco), int)
    remap[keep] = np.arange(len(keep))
    newco = Wco[keep]
    newpolys, src_pi = [], []
    for pi, p in enumerate(polys):
        q = [int(remap[i]) for i in p]
        if all(x >= 0 for x in q) and len(set(q)) == len(q):
            newpolys.append(q)
            src_pi.append(pi)
    # ★ 坑3：丝袜脚的"绕踝旋转 + 抬到脚底" —— **必须在 pushout 之前**（先摆正姿态，再兜底外推）
    if FOOT_FIX_OBJ and objname == FOOT_FIX_OBJ:
        newco, _fmsg = foot_fix(newco)
        for _l in _fmsg:
            w("       [丝袜脚] " + _l)
    # ★ ⑤a 穿模修正（在建描边壳 / 拆件之前做，两边都会跟着走）
    if objname in PUSHOUT and not NO_PUSHOUT:
        _tg, _cp = PUSHOUT[objname][0], PUSHOUT[objname][1]
        _md = PUSHOUT[objname][2] if len(PUSHOUT[objname]) > 2 else "push"
        newco, _msg = pushout_fix(objname, newco, newpolys, _tg, cap=_cp, mode=_md)
        w("       [穿模修正] %-18s %s" % (objname, _msg))
    uvloop = d["uv"]
    polyuv, li = [], 0
    for p in polys:
        row = []
        for _vi in p:
            row.append((float(uvloop[li][0]), float(uvloop[li][1])) if li < len(uvloop)
                       else (0.0, 0.0))
            li += 1
        polyuv.append(row)
    srcmats, srcidx = d["mats"], d["mat_index"]
    mm = matmap or {}
    tgt_of_poly = []
    for pi in range(len(polys)):
        sm = srcmats[srcidx[pi]] if pi < len(srcidx) and srcidx[pi] < len(srcmats) else None
        key = mm.get(sm, mainkey) if sm is not None else mainkey
        # ★ 哨兵 `__PIECE__`：源槽名 `NO.1` / `NO.1-1` / `NO.1-2` 是**通用槽名**（不代表第几套 UV，
        #   同一件的三个槽 UV 区间重叠）⇒ 一律归到该件的 mainkey。
        if key == "__PIECE__":
            key = mainkey
        tgt_of_poly.append(MAT_OF[part][key])
    primary = MAT_OF[part][mainkey]
    need = []
    for tgt in tgt_of_poly:
        if tgt not in need:
            need.append(tgt)
    need.sort(key=lambda x: (x != primary, x))
    fgroups = {}
    for fi, p in enumerate(newpolys):
        fgroups.setdefault(tgt_of_poly[src_pi[fi]], []).append((src_pi[fi], p))
    orig_of = -np.ones(len(newco), int)
    for vj in keep:
        orig_of[remap[vj]] = vj
    arm = bpy.data.objects[PART_ARM[part]]
    coll = bpy.data.collections[PART_COLL[part]]
    made = []
    for gi, tgt in enumerate(need):
        fps = fgroups.get(tgt, [])
        if not fps:
            continue
        vs = sorted(set(v for _pi, p in fps for v in p))
        loc = {v: i for i, v in enumerate(vs)}
        sub_co = newco[vs]
        sub_poly = [[loc[v] for v in p] for _pi, p in fps]
        sub_loopuv = [polyuv[_pi] for _pi, p in fps]
        sub_w = [Wlist[int(orig_of[v])] for v in vs]
        suffix = {("Ch_Standard_Mt__%d" % _i): ("Mt%d" % _i) for _i in range(5, 14)}.get(
                      tgt, tgt.replace("Ch_", "").replace("_", ""))
        subname = objname if gi == 0 else "%s_%s" % (objname, suffix)
        sme = bpy.data.meshes.new(subname + "_mesh")
        sme.from_pydata([tuple(map(float, q)) for q in sub_co], [], sub_poly)
        sme.update()
        # ★ 先写 per-corner UV（再三角化，bmesh 会保留 UV 层）
        suvl = sme.uv_layers.new(name="UVMap")
        for pi2, poly in enumerate(sme.polygons):
            for loi in poly.loop_indices:
                uu, vv = sub_loopuv[pi2][loi - poly.loop_start]
                suvl.data[loi].uv = (uu, vv)
        import bmesh as _bm
        bm = _bm.new()
        bm.from_mesh(sme)
        if any(len(f.verts) != 3 for f in bm.faces):
            _bm.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(sme)
        bm.free()
        sme.update()
        sme.materials.append(get_mat(tgt))
        so = bpy.data.objects.new(subname, sme)
        bpy.context.scene.collection.objects.link(so)
        sgs = {}
        for j, wl in enumerate(sub_w):
            for b, x in wl:
                if b not in sgs:
                    sgs[b] = so.vertex_groups.new(name=b)
                sgs[b].add([int(j)], float(x), "REPLACE")
        so.parent = arm
        so.matrix_world = np.eye(4)
        smd = so.modifiers.new(name="Armature", type="ARMATURE")
        smd.object = arm
        coll.objects.link(so)
        made.append((subname, tgt, len(sub_co), len(sub_poly), len(sgs)))
        if gi == 0:
            BUILT[objname] = so
    BUILT_ALL[objname] = [x[0] for x in made]
    # ★ 给描边壳留一份"整件（拆件前）"的几何 + 权重 + 逐面角 UV
    if OUTLINE and objname in OUTLINE_SRC:
        GEOM[objname] = dict(part=part, P=newco, polys=newpolys,
                             polyuv=[polyuv[_pi] for _pi in src_pi],
                             W=[Wlist[int(orig_of[i])] for i in range(len(newco))],
                             arm=arm, coll=coll)
    nn = [max(len(x) for x in Wlist), min(len(x) for x in Wlist)]
    rs = [sum(x for _, x in q) for q in Wlist]
    w("   %-20s %-4s 源顶点 %5d（丢松散 %d）→ 拆成 %d 个对象  z %.4f~%.4f" %
      (objname, part, len(Wco), n_loose, len(made), newco[:, 2].min(), newco[:, 2].max()))
    for subname, tgt, nv2, np2, ng2 in made:
        w("        %-26s 顶点%6d 三角%6d 材质 %-20s 用骨 %d" % (subname, nv2, np2, tgt, ng2))
    w("        影响数 %d~%d 行和 %.6f~%.6f" % (nn[1], nn[0], min(rs), max(rs)))
    extra_mats[objname] = [x[1] for x in made]


for objname, (part, srcname, matmap, mainkey) in NEW.items():
    if objname in VARIANT_SKIP:
        w("   [跳过] %s（开关 %s）" % (objname, VARIANT_SKIP[objname]))
        continue
    emit(objname, part, srcname, matmap, mainkey)

w("")
w("### ⑤c 链的 u 分布（权重是否均匀铺在整条链上；u 按 4 档计顶点-组对）")
for _cn in sorted(UDIST):
    _a = np.array(UDIST[_cn], float)
    _q = [int(((_a >= lo) & ((_a <= lo + 0.25) if lo == 0.75 else (_a < lo + 0.25))).sum())
          for lo in (0.0, 0.25, 0.5, 0.75)]
    w("   %-13s n=%5d  四档 %s  分位 %s" %
      (_cn, len(_a), _q, np.round(np.percentile(_a, [0, 25, 50, 75, 100]), 2).tolist()))

if OUTLINE:
    build_shells()

# ★ 本版 leg = Stocking / Shoes / Leg Belt / ACC（都有实体几何）⇒ **不需要隐形脚部载体**。

# ---------- ⑥ 贴合度体检：对**全部新建件**报"到身体的有符号距离"（正 = 在皮肤外）----------
w("")
w("### ⑥ 贴合度体检（全部新建件 -> Body_base 的有符号距离；正 = 在皮肤外）")
from mathutils.bvhtree import BVHTree
bb = bpy.data.objects["Body_base"]
bmw = np.array(bb.matrix_world)
BVS = [tuple(bmw[:3, :3] @ np.array(v.co) + bmw[:3, 3]) for v in bb.data.vertices]
BVSA = np.array(BVS, float)
BPS = [tuple(p.vertices) for p in bb.data.polygons]
bt = BVHTree.FromPolygons(BVS, BPS)
# ★ 单调外推的适用对象（本版默认**空** —— 两套素材都是作者按 角色 配好的，不做形状手术）。
#   若某件实测陷入，把它加进来：只把"贴进皮肤"的顶点沿身体法线推到 +MARGIN，**从不内移**。
# ★ ⑤a 的 `pushout_fix` 已经在 emit() 里做过外推 ⇒ 这里只做**体检读数**，不再重复外推
#   （第5版 在这里把 PUSHOUT 重置成空元组，那一段外推其实是死代码）
PUSHOUT_REPORT = {}
tot_pen = 0
for objname in NEW:
    if objname in VARIANT_SKIP:
        continue
    objs = [bpy.data.objects[nm] for nm in BUILT_ALL.get(objname, []) if bpy.data.objects.get(nm)]
    if not objs:
        continue
    if objname in PUSHOUT_REPORT:
        for so in objs:
            me = so.data
            moved = 0
            for _r in range(2):
                for v in me.vertices:
                    hit = bt.find_nearest(tuple(v.co))
                    if hit[0] is None:
                        continue
                    sd = float(np.dot(np.array(v.co) - np.array(hit[0]), np.array(hit[1])))
                    if sd < MARGIN - 0.0003:
                        v.co = np.array(hit[0]) + np.array(hit[1]) * MARGIN
                        moved += 1
                me.update()
            w("   [外推] %-16s 推到 +%.1fmm：作用 %d 个顶点" % (objname, MARGIN * 1000, moved))
    sg = []
    for so in objs:
        for v in so.data.vertices:
            hit = bt.find_nearest(tuple(v.co))
            if hit[0] is None:
                continue
            sg.append(float(np.dot(np.array(v.co) - np.array(hit[0]), np.array(hit[1]))))
    if not sg:
        continue
    sg = np.array(sg)
    n_pen = int((sg < 0).sum())
    tot_pen += n_pen
    w("   %-16s %-4s 顶点%6d  sgn 中位%+.4f 最小%+.4f  p1%+.4f  陷入(<0) %d (%.2f%%)" %
      (objname, NEW[objname][0], len(sg), float(np.median(sg)), float(sg.min()),
       float(np.percentile(sg, 1)), n_pen, 100.0 * n_pen / len(sg)))
w("   合计陷入顶点 %d（身体脚底 z=%.4f）" % (tot_pen, min(q[2] for q in BVS)))

# ---------- ⑥b 鞋/袜"鞋底沿脚长的剖面" vs 身体脚底（★ 本版是平底，只做**读数**，不做旋转）----------
for _pnm, _lab in (("BH_Shoes", "Shoes"), ("BH_Stocking", "Stocking")):
    _ob = BUILT.get(_pnm)
    if _ob is None:
        continue
    w("")
    w("### ⑥b 验收：%s 鞋底剖面 vs 身体脚底（eyu: 负值 = 在脚底下方，正常）" % _lab)
    _tv = np.array([list(v.co) for v in _ob.data.vertices], float)
    _legs = bpy.data.objects[PART_ARM["leg"]]
    _lmw = np.array(_legs.matrix_world)
    for _side, _sgn, _bfn in (("L", 1.0, 16), ("R", -1.0, 20)):
        _bb2 = _legs.data.bones.get("MhBone_%03d" % _bfn)
        _az = float((_lmw[:3, :3] @ np.array(_bb2.head_local) + _lmw[:3, 3])[2]) if _bb2 else 0.0
        # ★ 身体侧只取**脚部**（踝以下）—— 否则远端 y 档会把小腿/另一只脚的最低点算进来
        _BV = BVSA[(BVSA[:, 0] * _sgn > 0) & (BVSA[:, 2] < _az)]
        _tsel = _tv[_tv[:, 0] * _sgn > 0]
        if not len(_BV) or not len(_tsel):
            continue
        _y0 = min(float(_tsel[:, 1].min()), float(_BV[:, 1].min()))
        _y1 = max(float(_tsel[:, 1].max()), float(_BV[:, 1].max()))
        w("   --- %s 侧：y %.4f~%.4f（y 越小越靠脚尖）---" % (_side, _y0, _y1))
        w("        %-19s %12s %12s %10s" % ("y 档", "身体脚底", "该件鞋底", "差(mm)"))
        _nb = 6
        _bad = 0
        for _k in range(_nb):
            _lo = _y0 + (_y1 - _y0) * _k / _nb
            _hi = _y0 + (_y1 - _y0) * (_k + 1) / _nb
            _a = _BV[(_BV[:, 1] >= _lo) & (_BV[:, 1] < _hi)]
            _b = _tsel[(_tsel[:, 1] >= _lo) & (_tsel[:, 1] < _hi)]
            if not len(_a) or not len(_b):
                continue
            _bz, _sz = float(_a[:, 2].min()), float(_b[:, 2].min())
            _d = (_sz - _bz) * 1000.0
            _tag = ""
            if _d > 15.0:
                _bad += 1
                _tag = "  << 高出脚底 %.1fmm（该档贴不严）" % _d
            w("        %+.4f~%+.4f %12.4f %12.4f %+10.2f%s" % (_lo, _hi, _bz, _sz, _d, _tag))
        w("        => 高出 +15mm 的档数 = %d / %d（Shoes 是 13mm 厚底 ⇒ 负得更多是**作者原样**）" %
          (_bad, _nb))

# ---------- ⑥c ★ v4 重点：手套 BH_Gloves 的**逐指**读数 ----------
if bpy.data.objects.get("BH_Gloves"):
    w("")
    w("### ⑥c ★v4 重点：BH_Gloves（手套）逐指 -> 身体的有符号距离（判据：>2mm 的指才需要处理）")
    _go = bpy.data.objects["BH_Gloves"]
    _gi2n = {g.index: g.name for g in _go.vertex_groups}
    _grp = {}
    for _v in _go.data.vertices:
        _hit = BT_BODY.find_nearest(tuple(_v.co))
        if _hit[0] is None:
            continue
        _sd = float(np.dot(np.array(_v.co) - np.array(_hit[0]), np.array(_hit[1])))
        if _v.groups:
            _dom = max(_v.groups, key=lambda g: g.weight)
            _nm = _gi2n[_dom.group]
        else:
            _nm = "<无组>"
        _grp.setdefault(_nm, []).append(_sd)
    _tot_bad = 0
    for _nm in sorted(_grp, key=lambda k: min(_grp[k])):
        _a = np.array(_grp[_nm], float)
        _pen = int((_a < 0).sum())
        _tot_bad += _pen
        w("   %-26s 顶点%5d  sgn 最小%+.4f 中位%+.4f  p1%+.4f  陷入 %d%s" %
          (_nm, len(_a), float(_a.min()), float(np.median(_a)), float(np.percentile(_a, 1)),
           _pen, "   << 需处理" if _a.min() < -0.002 else ""))
    w("   合计陷入 %d 个顶点（★ 用户 2026-10-03：手套很大，手指不可能穿出手套 ⇒ 只跟手腕即可）" % _tot_bad)

# ---------- ⑥e ★ v4 专项：袖子 BH_Arm 沿手指轴的覆盖 + 逐指与皮肤的距离 ----------
if bpy.data.objects.get("BH_Arm"):
    w("")
    w("### ⑥e ★v4 专项：BH_Arm（袖子）沿 +x 手指轴的覆盖（判'袖子包到手指哪里'）")
    _ao = BUILT.get("BH_Arm")
    _av = np.array([list(v.co) for v in _ao.data.vertices], float)
    for _lo, _hi in ((0.35, 0.42), (0.42, 0.46), (0.46, 0.50), (0.50, 0.53), (0.53, 0.80)):
        _m = (_av[:, 0] >= _lo) & (_av[:, 0] < _hi)
        if _m.any():
            w("   x[%.2f,%.2f) 顶点=%4d  z %.4f~%.4f" %
              (_lo, _hi, int(_m.sum()), _av[_m, 2].min(), _av[_m, 2].max()))
        else:
            w("   x[%.2f,%.2f) 顶点=   0" % (_lo, _hi))
    w("   [参照骨·工作坐标] Hand.L x=%.4f  Little Distal.L x=%.4f（预览坐标 ≈ 工作 / 1.3796 后再变换）"
      % (xf(np.array([0.4411, 0.0081, 1.0055]))[0], xf(np.array([0.5287, 0.0207, 0.9997]))[0]))
    # 逐指（袖子在指尖段的权重覆盖；★ 提示词说它缺 Index/Middle/Ring Distal）
    _ai2n = {g.index: g.name for g in _ao.vertex_groups}
    _fing = {}
    for _v in _ao.data.vertices:
        if _v.co[0] < xf(np.array([0.42, 0.0, 1.0]))[0]:
            continue
        _nm = "<无组>"
        if _v.groups:
            _nm = _ai2n[max(_v.groups, key=lambda g: g.weight).group]
        _fing[_nm] = _fing.get(_nm, 0) + 1
    w("   [权重覆盖] 工作坐标 x>手腕 的顶点，主导组分布：%s" %
      sorted(_fing.items(), key=lambda kv: -kv[1])[:12])

# ---------- ⑥d 尖刺体检（面法线 vs 它自己三个顶点的顶点法线；自洽判据）----------
#   判据来源：skill「第七次实战 Q/T」—— 判"网格自身有没有被改坏"必须用**自洽**判据，
#   不要用"与另一个物体的法线比"（那测的是"两个形状像不像"，不是"网格坏没坏"）。
#   阈值：源素材本身可能就有少量折面（本版丝袜源几何 max 69.75°、152 个 >30°）
#   ⇒ 判读方式是"**与本版源几何的基线比**"，而不是看绝对值。
w("")
w("### ⑥d 尖刺体检（面法线 vs 自身顶点法线；>30° 的三角数越少越好）")


def spike_metric(me):
    Pv = np.array([list(v.co) for v in me.vertices], float)
    tr = []
    for p in me.polygons:
        v = list(p.vertices)
        for k in range(1, len(v) - 1):
            tr.append((v[0], v[k], v[k + 1]))
    if not tr:
        return None
    NV = np.zeros_like(Pv)
    for i0, i1, i2 in tr:
        f = np.cross(Pv[i1] - Pv[i0], Pv[i2] - Pv[i0])
        NV[i0] += f
        NV[i1] += f
        NV[i2] += f
    NV /= np.maximum(np.linalg.norm(NV, axis=1), 1e-12)[:, None]
    ang = []
    for i0, i1, i2 in tr:
        f = np.cross(Pv[i1] - Pv[i0], Pv[i2] - Pv[i0])
        L2 = float(np.linalg.norm(f))
        if L2 < 1e-16:
            continue
        n = f / L2
        vn = NV[i0] + NV[i1] + NV[i2]
        vn /= max(float(np.linalg.norm(vn)), 1e-12)
        ang.append(np.degrees(np.arccos(np.clip(float(n @ vn), -1, 1))))
    a = np.array(ang)
    return a


for _nm in [k for k in NEW if k not in _SKIP_BUILD]:
    _o = BUILT.get(_nm)
    if _o is None:
        continue
    _a = spike_metric(_o.data)
    if _a is None:
        continue
    w("   %-16s 三角%5d  面法线转角 max %6.2f°  均值 %.3f°  >30° %4d  >60° %3d" %
      (_nm, len(_a) + 2, float(_a.max()), float(_a.mean()), int((_a > 30).sum()),
       int((_a > 60).sum())))
w("   [基线] 本版**没有「改形状」的外科手术**（鞋/袜都是平底、不做绕踝旋转；只做「单调外推」）")
w("          ⇒ 各件读数应与「源几何」同量级；明显翻倍 = 外推把网格推坏了")

# ---------- ⑦ 删旧网格 ----------
w("")
w("### ⑦ 删除旧网格")
for part, names in DELETE.items():
    coll = bpy.data.collections[PART_COLL[part]]
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o is None:
            w("   !! 找不到 %s" % nm)
            continue
        mme = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if mme.users == 0:
            bpy.data.meshes.remove(mme)
        w("   删除 %s (%s)" % (nm, part))

# ---------- ⑦b ★ 空部位兜底：**隐形载体** ----------
#   ★ 依据（skill，实测教训）：**不能发空 mod3**（导出预检报 `NoMeshesInCollection` 直接中止），
#     也**不能删 mod3**（游戏会回落到原版模型）。⇒ 某部位一个网格都没有时，
#     放一个"**藏在身体里的隐形载体**"（做法照 第4版 的 `nosock` 脚部载体）：
#       取 `Body_base` 的一小块（骨盆/腰一圈）→ 绕其顶点质心**缩到 0.9 倍**
#       （质心在身体内部 ⇒ 每个点都往里挪 10% ⇒ 严格在身体内部 ⇒ 不可见）
#       → 权重直接沿用那批身体顶点的权重（只保留**本部位骨架里存在**的骨名）→ 挂到本部位骨架。
#   ★ 本版触发场景：v3/v4 `nobunnytail` 去掉兔尾后，**wst 部位会变空**。
w("")
w("### ⑦b 空部位兜底（隐形载体）")
CARRY_BAND = {"wst": (0.00, 0.10), "body": (0.00, 0.10), "arm": (0.30, 0.42), "leg": (-0.35, -0.20)}
for _part in ("wst", "arm", "leg", "body"):
    _coll = bpy.data.collections[PART_COLL[_part]]
    if any(x.type == "MESH" for x in _coll.objects):
        continue
    _bb = bpy.data.objects["Body_base"]
    _BW = np.array([list(v.co) for v in _bb.data.vertices], float)
    _gi2n = {g.index: g.name for g in _bb.vertex_groups}
    _bw = [dict((_gi2n[g.group], float(g.weight)) for g in v.groups if g.weight > 0.0)
           for v in _bb.data.vertices]
    _lo, _hi = CARRY_BAND[_part]
    _polys = [list(pp.vertices) for pp in _bb.data.polygons
              if all(_lo <= _BW[i, 2] <= _hi for i in pp.vertices)]
    _used = np.zeros(len(_BW), bool)
    for _pp in _polys:
        _used[list(_pp)] = True
    _ksel = np.where((_BW[:, 2] >= _lo) & (_BW[:, 2] <= _hi) & _used)[0]
    if len(_ksel) < 8:
        w("   !! %s 在 z[%.2f,%.2f] 找不到足够的身体面（%d）⇒ 跳过" % (_part, _lo, _hi, len(_ksel)))
        continue
    _C = _BW[_ksel].mean(0)
    _newco = _C + 0.9 * (_BW[_ksel] - _C)
    _remap = -np.ones(len(_BW), int)
    _remap[_ksel] = np.arange(len(_ksel))
    _newpolys = []
    for _pp in _polys:
        _q = [int(_remap[i]) for i in _pp]
        if all(x >= 0 for x in _q) and len(set(_q)) == len(_q):
            _newpolys.append(_q)
    _me = bpy.data.meshes.new("%sCarrier_mesh" % _part)
    _me.from_pydata([tuple(map(float, q)) for q in _newco], [], _newpolys)
    _me.update()
    _uvs = _bb.data.uv_layers[0]
    _firstuv = {}
    for _pp in _bb.data.polygons:
        for _li in _pp.loop_indices:
            _vi = _bb.data.loops[_li].vertex_index
            if _vi not in _firstuv:
                _firstuv[_vi] = tuple(_uvs.data[_li].uv)
    _uvl = _me.uv_layers.new(name="UVMap")
    for _poly in _me.polygons:
        for _loi in _poly.loop_indices:
            _vi = int(_me.loops[_loi].vertex_index)
            _uvl.data[_loi].uv = _firstuv.get(int(_ksel[_vi]), (0.0, 0.0))
    _cm = MAT_OF[_part].get("FUR") or list(MAT_OF[_part].values())[0]
    _me.materials.append(get_mat(_cm))
    _co_ = bpy.data.objects.new("%sCarrier" % _part, _me)
    bpy.context.scene.collection.objects.link(_co_)
    _pb = PART_BONES[_part]
    _gs = {}
    _nfb = 0
    for _j, _vi in enumerate(_ksel):
        _wd = dict((b, x) for b, x in _bw[_vi].items() if x > 0 and b in _pb)
        if not _wd:
            _wd = {"MhBone_%03d" % FB_FN.get(_part, 13): 1.0}
            _nfb += 1
        _tot = sum(_wd.values())
        for b, x in _wd.items():
            if b not in _gs:
                _gs[b] = _co_.vertex_groups.new(name=b)
            _gs[b].add([int(_j)], float(x / _tot), "REPLACE")
    _arm = bpy.data.objects[PART_ARM[_part]]
    _co_.parent = _arm
    _co_.matrix_world = np.eye(4)
    _md = _co_.modifiers.new(name="Armature", type="ARMATURE")
    _md.object = _arm
    _coll.objects.link(_co_)
    w("   [%s] 补隐形载体：顶点 %d 面 %d ；材质 %s ；缩到 0.9（最大位移 %.1fmm）；用骨 %d（兜底 %d）" %
      (_part, len(_newco), len(_newpolys), _cm,
       float(np.abs(_BW[_ksel] - _newco).max()) * 1000, len(_gs), _nfb))
    _btb = _BVH.FromPolygons([tuple(q) for q in _BW], [tuple(pp) for pp in
                             [list(p.vertices) for p in _bb.data.polygons]])
    _sd = []
    for _q in _newco:
        _r = _btb.find_nearest(tuple(_q))
        if _r[0] is None:
            continue
        _sd.append(float(np.dot(np.array(_q) - np.array(_r[0]), np.array(_r[1]))))
    _sd = np.array(_sd) if _sd else np.array([0.0])
    w("        载体顶点到身体表面的有符号距离 min %+.2fmm max %+.2fmm ⇒ %s" %
      (_sd.min() * 1000, _sd.max() * 1000,
       "全在体内 ✓（看不到）" if _sd.max() < -0.0005 else "!! 有顶点露在体外，需复核"))

w("")
if MADE_MATS:
    w("★ 新建的材质（原本不在 blend 里，按 X5 的 mrl3 清单取名）：%s" % sorted(set(MADE_MATS)))
if UNKNOWN_GROUPS:
    w("!! 未在映射表里的顶点组（已并入 Chest）：%s" % sorted(UNKNOWN_GROUPS))
else:
    w("未在映射表里的顶点组：无 ✓")
if BONE_LOST:
    w("★ 源素材里有「没有任何顶点组」的孤立顶点，已用兜底骨（★ 按件优先，见 FB_OBJ）：%s" %
      {k: "%d 个 -> MhBone_%03d" % (FB_CNT[k], FB_OBJ.get(k, FB_FN.get(NEW[k][0], 2)))
       for k in sorted(BONE_LOST)})
if REBIND_N:
    w("★ 重绑（把下垂段的权重按高度让给链骨）：%s" % REBIND_N)
if FORCE_N:
    w("★ FORCE_CHAIN（整件无顶点组 ⇒ 按链投影白送权重）：%s" % FORCE_N)
if DROP_STAT:
    w("!! 有顶点因子骨不在本部位而被丢弃：%s" % DROP_STAT)

w("")
w("### 各部位集合现有网格")
for part in ("body", "arm", "wst", "leg"):
    coll = bpy.data.collections[PART_COLL[part]]
    ms = sorted([x.name for x in coll.objects if x.type == "MESH"])
    w("   %-5s (%2d)：%s" % (part, len(ms), ", ".join(ms)))
    w("        骨数 %d" % len(bpy.data.objects[PART_ARM[part]].data.bones))

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
w("")
w("SAVED %s" % bpy.data.filepath)
w("WROTE " + OUT)
print("DONE")

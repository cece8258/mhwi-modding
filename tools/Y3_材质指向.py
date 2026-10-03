# -*- coding: utf-8 -*-
"""Y3_材质指向.py —— 纯 python。把成品包 4 个 mrl3 的材质指向改成「本套装 本套（天蓝 Sky Blue）
+ 头发素材 蓬蓬双马尾 Yellow」的贴图，并按**贴图亮度**给出配方的实测依据。

框架照抄 C25_材质指向.py（已验证）：槽位复用改路径 / 材质身份查 various_hash_dict /
资源码从 master_material_dict 反查 / CB 按 property_dict 字段偏移精确写 / 幂等（从 .bak_y3 重算）。

★ 本版改动（第7版）：
  ① 贴图指向：9 张新图（4 张来自 `第7版\服装素材\贴图\`、3 张是生成的纯色图、
     2 张来自 头发素材 头发），与 `Y1_构建.py` 的 `MAT_OF` **一一对应**：
       body  __5 UV1 / __6 UV2 / __7 BAG / __9 FUR / __10 METAL / __12 头发 / __13 发饰
       arm   __5 UV1 / __10 METAL / __11 GLOVE
       wst   __9 FUR（本套兔尾）
       leg   __6 UV2 / __8 STOCK / __10 METAL
     `__1`(身体) `__2`(脸) `__3`(耳/尾基壳) 三个基壳材质**贴图指回原样、配方一个数都不动**。
     ★ 同一个材质名在不同部位指向不同贴图是**允许且必须**的（skill 第十次实战 J）。
  ② 配方：沿用 第6版 **最终实机验收**的那一档（改回"用户一直满意的身体材质 `Ch_Standard_Mt__1`"
     的同一档）：`Base 0.40 / EmiF 2.00 / fSpecular 1.00`。
     ★★ 但本套是**天蓝 Sky Blue**（不是 第6版 的纯白）⇒ 等效发光 = EmiF × 面料亮度会**变低**，
        必须用 `X8_面料亮度定标.py`（**带部位过滤**）重标一次，别照抄 第6版 的数字。
  ③ 细节法线 tDetailNormalMap -> 游戏/模组空法线（源材质只有一张 albedo，没有法线图）。
  ④ 不动 CMM / fMetalic / fRoughness / fTranslucency（沿用原值）。
  ⑤ `tAlbedoBlendMap` -> `assets\\snow_Col_CMM`（alpha 全 0）⇒ **关掉积雪发白**（v1 已实机验收的手法）。
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


import os, sys, json, struct

ROOT = ADDON_ROOT
VH = os.path.join(ROOT, "addons", "MHW_Model_Editor", "modules", "mrl3", "dict",
                  "various_hash_dict.json")
MMTR_PATH = os.path.join(ROOT, "addons", "MHW_Model_Editor", "modules", "mrl3", "dict",
                         "master_material_dict.json")
PD_PATH = os.path.join(ROOT, "addons", "MHW_Model_Editor", "modules", "mrl3", "dict",
                       "property_dict.json")
BASE = PKG_DIR
MILFY = "贴图目录名\\"
GAME_PREFIX = ("assets\\default_tex",)
CB_LOCAL = "CBMhMaterialPLLocal__disclosure"
OUT = Y3_OUT
L = []


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


# 配方（= 第5版 已实机验收的那一档，**修过"阳光直射变成一团白光"**）
# ★ 那次的判据：把材质与**用户满意的基壳材质**（body `__1` 身体）逐字段对拍 CB 的 44 个字段，
#   发现只有两个字段不同（`fBaseMapFactor` 0.30 vs 0.40、`fEmissiveMapFactor` 2.35 vs 2.00）；
#   选旋钮的判据 = "这个字段只影响被光照到的那部分吗"：
#     · `fBaseMapFactor` 0.30 → **0.10**（自发光占比 88.7% → 96%，直射的漫反射贡献削掉 2/3，
#       阴凉处由自发光主导 ⇒ 几乎不变）
#     · `fSpecular` 1.0 → **0.30**（直射下的镜面高光降到 30%）
#   ★ 若实机仍偏亮：只降 `fEmissiveMapFactor`（2.35 → 2.0）；若发闷：把 `fBaseMapFactor` 抬回 0.20。
# ★★ 2026-09-23 实机反馈改档：用户说"衣服看起来灰暗、没有反光"。
#   实测对拍（`_cb_full.py`）：我们的材质与 第4版、第5版（**用户都认可**）的
#   ColorMaskMap / FxMap / FurMap / PanoramaMap **逐项相同** ⇒ 不是资源指向的问题；
#   唯一动过的是 第5版 末期为了治"阳光直射变成一团白光"而压下去的那两个数
#   （`fBaseMapFactor` 0.30→0.10、`fSpecular` 1.0→0.30）——
#   白贴图下"发光占 96%" ⇒ 只剩一片**平的发光**，没有明暗、没有高光 ⇒ 看着就是"灰暗、没反光"。
#   ⇒ 本版默认取 **Base 0.40 / EmiF 2.35 / fSpecular 1.00**：
#     · `Base 0.40` = 用户一直满意的身体材质 `Ch_Standard_Mt__1` 的同一档（第6版 末期实机验收过）
#     · `fSpecular 1.00` = 标准值（第6版 实测 0.30 会"没有反光"）
#     · `EmiF 2.35` 让**主面料 UV1** 的等效发光 = 2.35 × 0.910 = **2.14**，
#       正好落在用户认可过的 2.08 / 2.19 两档之间（`_Y2_贴图.txt` ④ 实测亮度）。
#       副面料 UV2（0.660）只有 1.55、头发 HAIR（0.834）1.96 —— 一套贴图一个系数，取不到全中，
#       以**最显眼的紧身衣 UV1** 为准；实机若某件偏暗/偏亮再单独调。
#   ★ 命令行可覆盖（一次迭代 ~20 秒，不用改代码）：
#       python Y3_材质指向.py base=0.30 emi=2.10 spec=1.0
CB_FIX = {"fBaseMapFactor__uiColor": [0.40, 0.40, 0.40, 1.0],
          "fEmissiveMapFactor__uiColor": [2.35] * 3,
          "fSpecular__uiUNorm": 1.00}
for _a in sys.argv:
    if not isinstance(_a, str):
        continue
    if _a.startswith("base="):
        _v = float(_a.split("=", 1)[1])
        CB_FIX["fBaseMapFactor__uiColor"] = [_v, _v, _v, 1.0]
    elif _a.startswith("emi="):
        CB_FIX["fEmissiveMapFactor__uiColor"] = [float(_a.split("=", 1)[1])] * 3
    elif _a.startswith("spec="):
        CB_FIX["fSpecular__uiUNorm"] = float(_a.split("=", 1)[1])
w("### 配方：Base %.2f / EmiF %.2f / fSpecular %.2f（命令行可覆盖 base=/emi=/spec=）" %
  (CB_FIX["fBaseMapFactor__uiColor"][0], CB_FIX["fEmissiveMapFactor__uiColor"][0],
   CB_FIX["fSpecular__uiUNorm"]))

PLAN = {
    "body": {
        # ---- 基壳 角色 的材质：贴图指回原样（幂等复核，**配方不动**）----
        #   `__3` 是基壳的耳/尾材质。★ v1/v2 删了原版耳尾 ⇒ 它是**死材质**，指到的文件不必在包里
        #   （Z14 只查活材质）；**v3/v4 用 origear/origtail 保留耳尾 ⇒ 它变活**，必须有这张图。
        #   ★★ 名字必须是 `ExtraHair` 而**不能是 `Hair`**：Windows 大小写不敏感 ⇒ `Hair.tex`
        #      会和我们的 `HAIR.tex`（头发素材 黄发）变成**同一个文件**，耳尾会静默地贴上头发贴图。
        "Ch_Standard_Mt__1":  ("Body_Base",     None,          None,          None),
        "Ch_Standard_Mt__2":  ("Face_Base",     None,          None,          None),
        "Ch_Standard_Mt__3":  ("ExtraHair",      None,          None,          None),
        # ---- 本版 7 个目标材质（★ 与 Y1 的 MAT_OF["body"] 一一对应）----
        "Ch_Standard_Mt__5":  ("UV1",          "assets\\NM", "assets\\RMT", None),  # Suit / Headband
        "Ch_Standard_Mt__6":  ("UV2",          "assets\\NM", "assets\\RMT", None),  # Choker
        "Ch_Standard_Mt__7":  ("BAG",          "assets\\NM", "assets\\RMT", None),  # Bag
        "Ch_Standard_Mt__9":  ("FUR",          "assets\\NM", "assets\\RMT", None),  # Suit 毛边 / 耳绒
        "Ch_Standard_Mt__10": ("METAL",        "assets\\NM", "assets\\RMT", None),  # 金属件（平涂）
        "Ch_Standard_Mt__12": ("HAIR",         "assets\\NM", "assets\\RMT", None),  # 头发素材 Yellow
        "Ch_Standard_Mt__13": ("ACC",          "assets\\NM", "assets\\RMT", None),  # 头发素材 Accessories
    },
    "arm": {
        "Ch_Standard_Mt__5":  ("UV1",          "assets\\NM", "assets\\RMT", None),  # Arm warmers
        "Ch_Standard_Mt__6":  ("UV2",          "assets\\NM", "assets\\RMT", None),  # arm belt 的布面
        "Ch_Standard_Mt__10": ("METAL",        "assets\\NM", "assets\\RMT", None),  # arm belt 的金属
        "Ch_Standard_Mt__11": ("GLOVE",        "assets\\NM", "assets\\RMT", None),  # Gloves（纯色淡蓝）
    },
    "wst": {
        # wst 本版只有本套兔尾一件（材质键 FUR）
        "Ch_Standard_Mt__9":  ("FUR",          "assets\\NM", "assets\\RMT", None),
    },
    "leg": {
        "Ch_Standard_Mt__6":  ("UV2",          "assets\\NM", "assets\\RMT", None),  # Shoes/Leg Belt/ACC
        "Ch_Standard_Mt__8":  ("STOCK",        "assets\\NM", "assets\\RMT", None),  # Stocking
        "Ch_Standard_Mt__10": ("METAL",        "assets\\NM", "assets\\RMT", None),
    },
}
# 细节法线：源材质只有一张 albedo ⇒ 统一指向空法线
DETAIL_NM = {p: {k: "assets\\NM" for k in plan} for p, plan in PLAN.items()}
# 配方只改"我们新 claim 的材质"（**不动** __1/__2/__3 = 身体/脸/基壳耳尾 的既有配方）
CB_FIX_MATS = {p: sorted(plan.keys() - {"Ch_Standard_Mt__1", "Ch_Standard_Mt__2",
                                        "Ch_Standard_Mt__3"})
               for p, plan in PLAN.items()}
# 积雪修正（v1 已实机验收的 1 字节改动手法）：`tAlbedoBlendMap` 未绑定时采样器返回**不透明白**
# ⇒ 积雪混合权重=1 ⇒ 整片纯白。★ 对**全部新 claim 的材质**都绑上 alpha 全 0 的图。
AB_NAME = "tAlbedoBlendMap__disclosure"
AB_BLEND = "assets\\snow_Col_CMM"
AB_MATS_BY_PART = CB_FIX_MATS

VH_D = json.load(open(VH, encoding="utf-8"))
NAME2HASH = {n: int(h) for h, n in VH_D.items() if isinstance(n, str)}
MMTR = json.load(open(MMTR_PATH, encoding="utf-8", errors="replace"))
PDICT = json.load(open(PD_PATH, encoding="utf-8", errors="replace"))
FMT = {"float": (4, "f"), "uint": (4, "I"), "int": (4, "i"), "ubyte": (1, "B"),
       "byte": (1, "b"), "bbool": (4, "I")}


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def u64(b, o):
    return struct.unpack_from("<Q", b, o)[0]


def field_offset(buf, start, fields, target):
    o = start
    for name, info in fields.items():
        t = info[1]
        if t in FMT:
            sz = FMT[t][0]
        elif t.endswith("]"):
            base, n = t[:-1].split("[")
            sz = FMT[base][0] * int(n)
        else:
            return None
        if name == target:
            return o
        o += sz
    return None


def codes_for(mmtr_hash):
    d = MMTR.get(str(mmtr_hash))
    if not isinstance(d, dict):
        return {}
    return {v.get("name"): int(k) for k, v in d.get("resourceDict", {}).items()
            if isinstance(v, dict)}


w("=" * 104)
w("### Y3 · 材质贴图指向（本套 套装 + 头发素材 灰米色）+ 配方复核")
w("=" * 104)
for part, plan in PLAN.items():
    path = os.path.join(BASE, part, "mod", "f_%s040_0010.mrl3" % part)
    if not os.path.exists(path):
        w("!! 找不到 %s" % path)
        continue
    bak = path + ".bak_y3"
    if os.path.exists(bak):
        data = bytearray(open(bak, "rb").read())
        w("")
        w("--- %s （以 %s 为基础重算）---" % (part, os.path.basename(bak)))
    else:
        data = bytearray(open(path, "rb").read())
        open(bak, "wb").write(bytes(data))
        w("")
        w("--- %s （首次运行，已备份 .bak_y3）---" % part)
    size0 = len(data)
    matOff, matCount = u64(data, 32), u32(data, 16)
    texCount, texOff = u32(data, 20), u64(data, 24)
    texList, tex_entry_off = [], []
    for i in range(texCount):
        tex_entry_off.append(texOff + i * 272)
        p = texOff + i * 272 + 16
        e = data.find(b"\x00", p)
        texList.append(data[p:e].decode("ascii", "replace"))

    entries, hash2idx, plan_ref = {}, {}, set()
    plan_hashes = {NAME2HASH[n] for n in plan if n in NAME2HASH}
    miss = [n for n in plan if n not in NAME2HASH]
    if miss:
        w("   !! 这些材质名不在 various_hash_dict 里：%s" % miss)
    for mi in range(matCount):
        e = matOff + mi * 56
        nh, bsize = u32(data, e + 4), u32(data, e + 16)
        rc, bo = struct.unpack_from("<H", data, e + 22)[0], u64(data, e + 48)
        entries[nh] = (bsize, rc, bo)
        hash2idx[nh] = mi
        if nh in plan_hashes:
            for j in range(rc // 2):
                v = u32(data, bo + j * 16 + 8)
                if 1 <= v <= texCount:
                    plan_ref.add(v - 1)
    alloc = set()
    w("   [诊断] 活材质 %d 个占用的贴图槽：%s" % (len(plan_hashes), sorted(plan_ref)))

    def ensure_tex(tname):
        full = tname if tname.lower().startswith(GAME_PREFIX) else MILFY + tname
        if full in texList:
            return texList.index(full)
        free = [i for i in range(texCount)
                if i not in plan_ref and i not in alloc and texList[i] != full]
        if not free:
            w("   !! 没有空闲槽位可复用（活材质占用 %d 个槽）: %s" % (len(plan_ref), tname))
            return None
        slot = free[0]
        alloc.add(slot)
        nb = full.encode("ascii")
        data[tex_entry_off[slot] + 16: tex_entry_off[slot] + 16 + 256] = nb + bytes(256 - len(nb))
        texList[slot] = full
        w("   [贴图表] 槽%-2d -> %s" % (slot, full))
        return slot

    w("   材质 %d 个，贴图槽 %d 个" % (matCount, texCount))
    for mat, (alb, nrm, rmt, emis) in plan.items():
        mh = NAME2HASH.get(mat)
        if mh is None or mh not in entries:
            w("   !! %s 不在 %s 的 mrl3 里" % (mat, part))
            continue
        bsize, rc, bo = entries[mh]
        region = bytearray(data[bo:bo + bsize])
        nres = rc // 2
        mmtr_hash = u32(data, matOff + hash2idx[mh] * 56 + 8)
        codes = codes_for(mmtr_hash)
        want = [("tAlbedoMap__disclosure", alb),
                ("tEmissiveMap__disclosure", alb)]
        if nrm:
            want.append(("tNormalMap__disclosure", nrm))
        if rmt:
            want.append(("tRMTMap__disclosure", rmt))
        dn = DETAIL_NM.get(part, {}).get(mat)
        if dn:
            want.append(("tDetailNormalMap__disclosure", dn))
        done = []
        for code_name, tname in want:
            ci = codes.get(code_name)
            if ci is None:
                done.append("%s(无此资源名)" % code_name.split("__")[0])
                continue
            slot = ensure_tex(tname)
            if slot is None:
                continue
            hit = False
            for j in range(nres):
                rhash = struct.unpack_from("<I", region, j * 16 + 4)[0]
                if (rhash >> 12) == ci:
                    struct.pack_into("<I", region, j * 16 + 8, slot + 1)
                    done.append("%s=%s" % (code_name.replace("t", "").split("__")[0], tname))
                    hit = True
                    break
            if not hit:
                done.append("%s(没找到资源项)" % code_name.split("__")[0])
        data[bo:bo + bsize] = region
        # ---- CB 配方（只对 CB_FIX_MATS 里列出的材质）----
        if mat in CB_FIX_MATS.get(part, []):
            cbcode = {int(c): v.get("name", "") for c, v in
                      MMTR.get(str(mmtr_hash), {}).get("resourceDict", {}).items()
                      if isinstance(v, dict) and v.get("name", "").startswith("CB")}
            for j in range(nres):
                rh, rv = struct.unpack_from("<2I", data, bo + j * 16 + 4)
                if cbcode.get(rh >> 12) != CB_LOCAL:
                    continue
                fields = PDICT.get(str(rh >> 12), {}).get("fields")
                if not fields:
                    continue
                for pname, pval in CB_FIX.items():
                    off_f = field_offset(data, bo + rv, fields, pname)
                    if off_f is None:
                        done.append("%s(找不到)" % pname)
                        continue
                    if isinstance(pval, (list, tuple)):
                        old_v = struct.unpack_from("<%df" % len(pval), data, off_f)[0]
                        struct.pack_into("<%df" % len(pval), data, off_f, *pval)
                        done.append("%s %.2f->%.2f" % (pname.split("__")[0], old_v, pval[0]))
                    else:
                        old_v = struct.unpack_from("<f", data, off_f)[0]
                        struct.pack_into("<f", data, off_f, float(pval))
                        done.append("%s %.2f->%.2f" % (pname.split("__")[0], old_v, float(pval)))
        w("   %-26s %s" % (mat, " | ".join(done)))

    # ---- 积雪修正：`tAlbedoBlendMap` → alpha 全 0 的图 ----
    for abm in AB_MATS_BY_PART.get(part, []):
        mh = NAME2HASH.get(abm)
        if mh not in entries:
            continue
        bsize, rc, bo = entries[mh]
        mmtr_hash = u32(data, matOff + hash2idx[mh] * 56 + 8)
        ci = codes_for(mmtr_hash).get(AB_NAME)
        slot = ensure_tex(AB_BLEND)
        if ci is None or slot is None:
            w("   [albedoBlend] %s 失败 ci=%s slot=%s" % (abm, ci, slot))
            continue
        hit = False
        for j in range(rc // 2):
            rhash, rv = struct.unpack_from("<2I", data, bo + j * 16 + 4)
            if (rhash >> 12) != ci:
                continue
            hit = True
            if rv == slot + 1:
                w("   [albedoBlend] %-22s 已是槽%d，未改" % (abm, slot))
            else:
                struct.pack_into("<I", data, bo + j * 16 + 8, slot + 1)
                w("   [albedoBlend] %-22s rv %d -> %d（槽%d = %s）" %
                  (abm, rv, slot + 1, slot, AB_BLEND))
            break
        if not hit:
            w("   !! %s 没找到 tAlbedoBlendMap 资源项" % abm)

    open(path, "wb").write(bytes(data))
    w("   已写入（%d -> %d 字节，%s）" % (size0, len(data),
                                    "大小不变 ✓" if size0 == len(data) else "!! 大小变了"))

    # ---- 回读复核 ----
    chk = open(path, "rb").read()
    for mat in plan:
        mh = NAME2HASH.get(mat)
        if mh is None or mh not in entries:
            continue
        bsize, rc, bo = entries[mh]
        mmtr_hash = u32(chk, matOff + hash2idx[mh] * 56 + 8)
        rb = re_ = rs = rn = rr = rdm = None
        codes = codes_for(mmtr_hash)
        for j in range(rc // 2):
            rh, rv = struct.unpack_from("<2I", chk, bo + j * 16 + 4)
            key = codes.get(rh >> 12)
            for role, tag in (("tAlbedoMap__disclosure", "alb"), ("tNormalMap__disclosure", "nm"),
                              ("tRMTMap__disclosure", "rmt"), ("tDetailNormalMap__disclosure", "dn")):
                if key == codes.get(role):
                    v = texList[rv - 1] if 1 <= rv <= texCount else "?"
                    if tag == "alb":
                        rn = v
                    elif tag == "nm":
                        rr = v
                    elif tag == "dn":
                        rdm = v
        w("   [复核] %-26s Albedo=%-26s NM=%-16s DetailNM=%-16s" % (mat, rn, rr, rdm))

w("")
w("### 配方依据（实测亮度见 _Y2_贴图.txt ④ 与 _X8_面料亮度.txt）")
w("   等效发光 = EmiF × 贴图面料区亮度（衡量口径 = **UV 覆盖区**，不是全图均值）")
w("   [基准] v1 军装 4.0×0.52 = 2.08 ；花瓣裙 0.93×2.35 = 2.19 —— 用户明确认可过的两档")
w("   ★ 本套 White 配色的 A/B/F 三张贴图**接近纯白**（alpha≥250 区均值 255）⇒ 等效发光 ≈ 2.35，")
w("     比基准高约 13%。若实机偏亮：只改本脚本 CB_FIX 里 fEmissiveMapFactor（2.35 → 2.0）。")
w("")
w("WROTE " + OUT)

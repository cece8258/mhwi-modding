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


r"""
O2_描边材质.py — 在成品包 4 个 mrl3 里新建描边材质 `Outline_Black`
=====================================================================
做法（照抄 `_模组调研\epv与描边_调研.md` B 部分 + 本次 _outline\o1/o3/o12 复核）：

  1. **复用死条目**：每个部位挑 `Ch_Standard_Mt__4`（非该部位 mod3 使用的材质、
     mmtr=PL_Mt、blockSize=752、resourceCount=24）——与 Alf 的描边材质
     `Outline_Brown` 的 mmtrHash / shaderHash / blockSize / resourceCount
     **逐项相同**，且整块 CB 只有 2 个字段不同（o12 实测），所以是 drop-in。
  2. 只改该条目的 `nameHash`（材质项 +4）= `crc32("Outline_Black") ^ 0xFFFFFFFF`
     —— 语料实测的材质名哈希公式（2738/2738，见调研 §5）。
  3. 按 Alf 描边模板设置资源指向：
       tAlbedoMap / tEmissiveMap   -> `Assets\\default_tex\\null_black`（平黑；Alf 的 wst/Outline 就是这么写的）
       tNormalMap / tDetailNormalMap -> `Assets\\default_tex\\null_NM`
       tRMTMap                     -> `Assets\\default_tex\\null_RMT`
       tColorMaskMap / tFxMap / tFurVelocityMap -> `Assets\\default_tex\\null_black`
       tFurMap                     -> `Assets\\default_tex\\noise_LIN`
       tPanoramaMap                -> `Assets\\default_tex\\null_gray_LIN`
       tAlbedoBlendMap             -> 沿用（snow_Col_CMM，与 Alf 同）
  4. 按 Alf 描边模板设置 CB（**用 property_dict 的字段偏移精确写入**，不再用
     "找 4 个 float 的字节模式"那种做法——那有改错字段的风险）：
       fBaseMapFactor__uiColor      = 0.2,0.2,0.2,1   （Alf 描边值）
       fEmissiveMapFactor__uiColor  = 1,1,1           （Alf 描边值；本体是 3）
       其余 47 个字段**一个都不动**（含 bBackFaceNormalFilp / iOutlineId —— 实测两个作者都没动）

  ★ 绝不动任何活材质：脚本会先算出「该部位 mod3 实际用到的材质名」，
    再断言被改的条目不在其中；并在写完前校验「被改动的贴图槽只被死材质 + 新描边材质引用」。

幂等：**直接在当前 mrl3 上就地打补丁**（第4版 版：不再从 `.bak_c25` 还原、也不再内部跑 C25）。
      ★ 在 `Z9_出一版.sh` 里的顺序必须是 **Y3_材质指向.py → 本脚本**（Y3 每次从 `.bak_y3` 重算，
        跑在它前面会被它覆盖掉）。重跑本脚本是安全的：它会把同一个条目的字段刷成同一组值。
      4 个部位的 `Ch_Standard_Mt__4` 都是死条目（本版 body 用 __1/__2/__3/__5/__7/__8/__10/__11/__12、
      arm 用 __6/__10、wst 用 __5/__7/__9、leg 用 __6），脚本仍会断言它不在该部位的活材质里。

用法: python O2_描边材质.py
"""
import os
import re
import sys
import zlib
import json
import struct
import shutil
import subprocess
import hashlib

PROJ = PROJ
PKG = os.path.join(PROJ, "05_导出成品", "nativePC", "pl", "f_equip", "pl040_0010")
os.makedirs(os.path.join(PROJ, "_outline"), exist_ok=True)
LOG = os.path.join(PROJ, "_outline", "o18_mat_log.txt")
REP = os.path.join(PROJ, "_outline", "o18_mat_report.json")

ROOT = (BLENDER_CFG_DIR +

        r"\extensions\user_default\MHW_Mod3_Editor\addons\MHW_Model_Editor")
ROOT2 = (BLENDER_CFG_DIR +

         r"\scripts\addons\MHW_Model_Editor-main\addons\MHW_Model_Editor")
DICT = None
for cand in (os.path.join(ROOT, "modules", "mrl3", "dict"),
             os.path.join(ROOT2, "modules", "mrl3", "dict")):
    if os.path.isdir(cand):
        DICT = cand
        break
if DICT is None:
    print("!! 找不到 mrl3 dict 目录"); sys.exit(1)

MMTR = json.load(open(os.path.join(DICT, "master_material_dict.json"), encoding="utf-8", errors="replace"))
PDICT = json.load(open(os.path.join(DICT, "property_dict.json"), encoding="utf-8", errors="replace"))
VH = json.load(open(os.path.join(DICT, "various_hash_dict.json"), encoding="utf-8", errors="replace"))

OUTLINE_NAME = "Outline_Black"
OUTLINE_HASH = zlib.crc32(OUTLINE_NAME.encode("ascii")) ^ 0xFFFFFFFF
DONOR_NAME = "Ch_Standard_Mt__4"

# mod3 实际用到的活材质（正则与 C0/C32 同法，并加白名单）
MATPAT = re.compile(rb"Ch_(?:Pl_)?Standard_Mt_[0-9_]*")
PARTS = ("body", "arm", "wst", "leg")

# 目标资源指向（资源名 -> 贴图槽路径；None = 保持不动）
WANT_TEX = {
    "tAlbedoMap__disclosure":         "Assets\\default_tex\\null_black",
    "tEmissiveMap__disclosure":       "Assets\\default_tex\\null_black",
    "tNormalMap__disclosure":         "Assets\\default_tex\\null_NM",
    "tDetailNormalMap__disclosure":   "Assets\\default_tex\\null_NM",
    "tRMTMap__disclosure":            "Assets\\default_tex\\null_RMT",
    "tColorMaskMap__disclosure":      "Assets\\default_tex\\null_black",
    "tFxMap__disclosure":             "Assets\\default_tex\\null_black",
    "tFurVelocityMap__disclosure":    "Assets\\default_tex\\null_black",
    "tFurMap__disclosure":            "Assets\\default_tex\\noise_LIN",
    "tPanoramaMap__disclosure":       "Assets\\default_tex\\null_gray_LIN",
    "tAlbedoBlendMap__disclosure":    None,
}
# CB 目标值（Alf 描边模板）
WANT_CB = {
    "fBaseMapFactor__uiColor":         (0.2, 0.2, 0.2, 1.0),
    "fEmissiveMapFactor__uiColor":     (1.0, 1.0, 1.0),
}
# ★ 材质项 56 字节头部里另外两个「渲染状态」字段（不在 CB 里，是材质项自己的字节）。
#   2026-09-18 第二轮：Alf 的 3 个描边材质 (Outline_Brown / Outline_Red / Outline) 在这一对
#   取值上**完全一致**，而我们第一版沿用了死条目的原值 —— 逐字节比对后这是**唯一**还剩下的差异
#   （CB 全部字段差异 = 0 字节）。插件源码注释把 surfaceCoef[1] 当"背面剔除"相关字段：
#       blender_mod3_mrl3.py:351  use_backface_culling = (surfaceCoef[1] > 4 not in {0, 14})
#   —— 那个表达式对任何 ubyte 都恒为 True（是插件自己的 bug），所以插件无法识别真正的语义；
#   既然"我们的黑壳没被剔除、Alf 的壳被剔除了"是实测现象，就把这两项照抄 Alf。
WANT_HDR = {
    "surfaceCoef": bytes([0x00, 0x11]),      # Alf 描边全部是 0011；我们原来是 00e1
    "alphaCoefB3": 0x04,                     # Alf 描边 alphaCoef = 00 70 04 04；我们原来是 00 70 04 00
}
FMT = {"float": (4, "f"), "uint": (4, "I"), "int": (4, "i"), "ubyte": (1, "B"),
       "byte": (1, "b"), "bbool": (4, "I")}

L = []


def P(s=""):
    L.append(str(s)); print(s, flush=True)


def u32(b, o): return struct.unpack_from("<I", b, o)[0]
def u64(b, o): return struct.unpack_from("<Q", b, o)[0]


def cb_field_offsets(fields):
    """按声明顺序 + C ABI 自然对齐，返回 {字段名: (块内偏移, 元素数, 基础类型)}
    （与 mhwlib.cb_layout 同一套对齐规则，实测能复现 PL_Mt 的真实字段值）"""
    out, off = {}, 0
    for name, info in fields.items():
        typ = info[1]
        cnt, base_t = 1, typ
        if "[" in typ:
            base_t, n = typ[:-1].split("[")
            cnt = int(n)
        es = FMT.get(base_t, (None, None))[0]
        if es is None:
            return None
        off = (off + es - 1) // es * es
        out[name] = (off, cnt, base_t)
        off += es * cnt
    return out


def codes_for(mmtr_hash):
    d = MMTR.get(str(mmtr_hash))
    if not isinstance(d, dict):
        return {}
    return {v.get("name"): int(k) for k, v in d.get("resourceDict", {}).items()
            if isinstance(v, dict)}


def mod3_active_materials(part):
    mp = os.path.join(PKG, part, "mod", "f_%s040_0010.mod3" % part)
    if not os.path.exists(mp):
        return set()
    raw = open(mp, "rb").read()
    return {m.group().decode() for m in MATPAT.finditer(raw)
            if m.end() < len(raw) and raw[m.end():m.end() + 1] == b"\x00"}


def main():
    P("=" * 110)
    P("### O2 · 新建描边材质 %s (nameHash=%d) —— 复用死条目 %s" %
      (OUTLINE_NAME, OUTLINE_HASH, DONOR_NAME))
    P("=" * 110)

    # ---- 第4版：不再"还原 .bak_c25 + 内部跑 C25"（那是 第1版 时代的框架）----
    #   本版材质指向由 Y3_材质指向.py 负责，Z9 里 Y3 跑在本脚本**之前**；本脚本只就地打补丁。
    P("   就地打补丁（不改活材质、不改文件大小）；重跑安全（字段刷成同一组值）")

    report = {"outlineName": OUTLINE_NAME, "outlineHash": OUTLINE_HASH, "parts": {}}
    for part in PARTS:
        path = os.path.join(PKG, part, "mod", "f_%s040_0010.mrl3" % part)
        if not os.path.exists(path):
            P("!! 缺 %s" % path); continue
        data = bytearray(open(path, "rb").read())
        base = bytes(data)

        matOff, matCount = u64(data, 32), u32(data, 16)
        texCount, texOff = u32(data, 20), u64(data, 24)
        tex = []
        for i in range(texCount):
            p = texOff + i * 272 + 16
            e = data.find(b"\x00", p)
            tex.append(data[p:e].decode("ascii", "replace"))

        active = mod3_active_materials(part)
        P("")
        P("--- %s : mod3 活材质 %s" % (part, sorted(active)))

        # 找 donor：优先"已经是 Outline_Black 的条目"（幂等重跑），否则找 Ch_Standard_Mt__4
        donor_idx = None
        already = False
        for mi in range(matCount):
            if u32(data, matOff + mi * 56 + 4) == OUTLINE_HASH:
                donor_idx = mi
                already = True
                break
        if donor_idx is None:
            for mi in range(matCount):
                if VH.get(str(u32(data, matOff + mi * 56 + 4))) == DONOR_NAME:
                    donor_idx = mi
                    break
        if donor_idx is None:
            P("   !! 既没有 Outline_Black 条目、也找不到 donor %s，跳过" % DONOR_NAME); continue
        e = matOff + donor_idx * 56
        old_hash = u32(data, e + 4)
        mmtr_hash = u32(data, e + 8)
        shader_hash = u32(data, e + 12)
        bsize = u32(data, e + 16)
        rc = struct.unpack_from("<H", data, e + 22)[0]
        bo = u64(data, e + 48)
        if already:
            P("   （已存在 Outline_Black 条目 idx=%d ⇒ 幂等重跑，只刷新字段）" % donor_idx)
        elif VH.get(str(old_hash)) in active:
            P("   !! donor 竟然是活材质，中止"); continue
        P("   donor idx=%d 旧名=%s hash=%d mmtr=%s shaderHash=%d blockSize=%d res=%d" %
          (donor_idx, VH.get(str(old_hash)), old_hash,
           (MMTR.get(str(mmtr_hash)) or {}).get("mmtrName"), shader_hash, bsize, rc))

        # ---- 1) 改 nameHash ----
        struct.pack_into("<I", data, e + 4, OUTLINE_HASH)

        # ---- 1b) 改材质项头部的渲染状态字节（照抄 Alf 的描边材质）----
        hdr_done = []
        old_surf = bytes(data[e + 20:e + 22])
        data[e + 20:e + 22] = WANT_HDR["surfaceCoef"]
        hdr_done.append("surfaceCoef %s -> %s" % (old_surf.hex(), WANT_HDR["surfaceCoef"].hex()))
        old_b3 = data[e + 27]
        data[e + 27] = WANT_HDR["alphaCoefB3"]
        hdr_done.append("alphaCoef[3] %02x -> %02x (alphaCoef=%s)" %
                        (old_b3, WANT_HDR["alphaCoefB3"],
                         bytes(data[e + 24:e + 28]).hex()))

        # ---- 2) 改资源指向 ----
        codes = codes_for(mmtr_hash)
        if not codes:
            P("   !! mmtr 不在字典里，中止"); continue
        code2name = {v: k for k, v in codes.items()}
        nres = rc // 2

        # ---- 先算「槽位安全表」：哪些槽被活材质引用？----
        slot_ref_live = {}          # slot0based -> set(材质名)  只统计活材质
        slot_ref_dead = {}
        for mi2 in range(matCount):
            e2 = matOff + mi2 * 56
            nh2 = u32(data, e2 + 4)
            nm2 = VH.get(str(nh2)) or ("#%d" % nh2)
            live2 = nm2 in active
            rc2 = struct.unpack_from("<H", data, e2 + 22)[0]
            bo2 = u64(data, e2 + 48)
            for j in range(rc2 // 2):
                v = u32(data, bo2 + j * 16 + 8)
                if 1 <= v <= texCount:
                    (slot_ref_live if live2 else slot_ref_dead).setdefault(v - 1, set()).add(nm2)
        never = [i for i in range(texCount) if i not in slot_ref_dead and i not in slot_ref_live]
        # ★ body 的 45 个槽全都被"死材质"引用（它原来一张 default_tex 都没有）⇒ 只靠 never 会取不满
        #   5 个空槽（实测报"没有可用空槽"）。所以退一步：**只被死材质引用**的槽也可以用
        #   —— 游戏不实例化死材质（skill 已验证），改它引用的槽对观感无影响。
        deadonly = sorted(i for i in range(texCount)
                          if i in slot_ref_dead and i not in slot_ref_live)

        def ensure_slot(tname, taken):
            """返回 (slot, how)。只用「从未被任何材质引用」或「只被死材质引用」的槽。"""
            for i, t in enumerate(tex):
                if t == tname:
                    if i in slot_ref_live:
                        continue          # 活材质在用，不碰
                    return i, "沿用"
            for i in never + deadonly:
                if i in taken or i in slot_ref_live:
                    continue
                nb = tname.encode("ascii")
                if len(nb) > 255:
                    return None, "路径太长"
                data[texOff + i * 272 + 16: texOff + i * 272 + 16 + 256] = nb + bytes(256 - len(nb))
                tex[i] = tname
                return i, ("新建(从未引用)" if i in never else "新建(仅死材质引用)")
            return None, "没有可用空槽"

        slot_of = {}
        taken = set()
        for rname, tname in WANT_TEX.items():
            if tname is None:
                continue
            s, how = ensure_slot(tname, taken)
            if s is None:
                P("   !! %s 取槽失败：%s" % (tname, how)); continue
            slot_of[rname] = s
            taken.add(s)
            if how != "沿用":
                P("   [表] 槽%-2d -> %s (%s)" % (s, tname, how))

        changed_slots = set()
        done = []
        for j in range(nres):
            code, rhash, rval = struct.unpack_from("<3I", data, bo + j * 16)
            rname = code2name.get(rhash >> 12)
            if rname in WANT_TEX and WANT_TEX[rname] is not None:
                s = slot_of.get(rname)
                if s is None:
                    continue
                struct.pack_into("<I", data, bo + j * 16 + 8, s + 1)
                changed_slots.add(s)
                done.append("%s->%s(槽%d)" % (rname.replace("t", "").split("__")[0],
                                              WANT_TEX[rname].split("\\")[-1], s))

        # ---- 3) 改 CB（按字段偏移）----
        cbcode = {int(c): v.get("name", "") for c, v in
                  MMTR.get(str(mmtr_hash), {}).get("resourceDict", {}).items()
                  if isinstance(v, dict) and v.get("name", "").startswith("CB")}
        cb_done = []
        for j in range(nres):
            code, rhash, rval = struct.unpack_from("<3I", data, bo + j * 16)
            cbname = cbcode.get(rhash >> 12)
            if not cbname:
                continue
            fields = PDICT.get(str(rhash >> 12), {}).get("fields")
            if not fields:
                continue
            lay = cb_field_offsets(fields)
            if lay is None:
                continue
            for fname, vals in WANT_CB.items():
                if fname not in lay:
                    continue
                rel, cnt, base_t = lay[fname]
                if cnt != len(vals):
                    cb_done.append("%s(元素数不符 %d vs %d)" % (fname, cnt, len(vals)))
                    continue
                at = bo + rval + rel
                old = struct.unpack_from("<%df" % cnt, data, at)
                struct.pack_into("<%df" % cnt, data, at, *vals)
                cb_done.append("%s %s -> %s" % (fname.split("__")[0],
                                                ",".join("%g" % x for x in old),
                                                ",".join("%g" % x for x in vals)))

        # ---- 4) 写前校验：被改的槽不能有活材质引用 ----
        bad = []
        for mi2 in range(matCount):
            e2 = matOff + mi2 * 56
            nh2 = u32(data, e2 + 4)
            nm2 = VH.get(str(nh2)) or ("#%d" % nh2)
            is_active = (nh2 != OUTLINE_HASH) and (VH.get(str(nh2)) in active)
            rc2 = struct.unpack_from("<H", data, e2 + 22)[0]
            bo2 = u64(data, e2 + 48)
            live_slots = set()
            for j in range(rc2 // 2):
                v = u32(data, bo2 + j * 16 + 8)
                if 1 <= v <= texCount:
                    live_slots.add(v - 1)
            if is_active and (live_slots & changed_slots):
                bad.append((nm2, sorted(live_slots & changed_slots)))
        if bad:
            P("   !! 校验失败：活材质引用了被改动的槽 %s —— 不写盘" % bad)
            continue

        # 校验贴图槽总数/材质数没变
        assert u32(data, 16) == matCount and u32(data, 20) == texCount
        assert len(data) == len(base), "文件大小变了！"
        open(path, "wb").write(bytes(data))
        n_diff = sum(1 for a, b in zip(base, data) if a != b)
        # ★ 写完立刻回读，确认落盘（历史上出现过「写了但最终文件里没有」的情况）
        chk = open(path, "rb").read()
        chk_ok = struct.unpack_from("<I", chk, matOff + donor_idx * 56 + 4)[0] == OUTLINE_HASH
        chk_diff = sum(1 for a, b in zip(base, chk) if a != b)
        P("   已写入 %s（大小 %d 不变，差异字节 %d；回读校验=%s，回读差异字节=%d）" %
          (os.path.basename(path), len(data), n_diff, chk_ok, chk_diff))
        if not chk_ok:
            P("   !! 回读校验失败：磁盘上的 nameHash 不是 Outline_Black！")
        P("   资源指向: %s" % " | ".join(done))
        P("   CB      : %s" % " | ".join(cb_done))
        P("   材质项头: %s" % " | ".join(hdr_done))
        report["parts"][part] = dict(donorIdx=donor_idx, donorOldName=VH.get(str(old_hash)),
                                     donorOldHash=old_hash, mmtrHash=mmtr_hash,
                                     shaderHash=shader_hash, blockSize=bsize,
                                     resourceCount=rc, changedSlots=sorted(changed_slots),
                                     slots={k: v for k, v in sorted(slot_of.items())},
                                     texChanged=done, cbChanged=cb_done, hdrChanged=hdr_done,
                                     diffBytes=n_diff)

    json.dump(report, open(REP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(LOG, "w", encoding="utf-8").write("\n".join(L))
    P("")
    P("wrote %s / %s" % (LOG, REP))


main()

# -*- coding: utf-8 -*-
"""Z14_四包终验.py —— 对 第4版 成品目录下的 zip 做**成品级**反向验收：
 ① 每个条目与磁盘文件逐字节一致（CRC 口径）—— 证明"装进去的就是工作目录里的东西"
 ② 每个**活材质**指到的贴图路径必须在 zip 里存在（反向检查，0 个洞才算过）
 ③ zip 里的 4 个 mod3 / ctc / mrl3 / tex 结构自检
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


import os, re, struct, json, zipfile, hashlib, glob

P = PROJ
D = os.path.join(P, "05_导出成品")
NP = os.path.join(D, "nativePC")
ROOT = ADDON_ROOT
VH = json.load(open(os.path.join(ROOT, "addons", "MHW_Model_Editor", "modules", "mrl3", "dict",
                                 "various_hash_dict.json"), encoding="utf-8"))
MMTR = json.load(open(os.path.join(ROOT, "addons", "MHW_Model_Editor", "modules", "mrl3", "dict",
                                   "master_material_dict.json"), encoding="utf-8", errors="replace"))
N2H = {n: int(h) for h, n in VH.items() if isinstance(n, str)}
MAGIC = 4476749
OUT = os.path.join(P, "_Z14_四包终验.txt")
L = []


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def u64(b, o):
    return struct.unpack_from("<Q", b, o)[0]


ok_all = True
ZS = sorted(os.path.basename(x) for x in glob.glob(os.path.join(D, "*.zip")))
ZS = [z for z in ZS if z.endswith(".zip")]
for z in ZS:
    zp = os.path.join(D, z)
    if not os.path.exists(zp):
        w("!! 缺 %s" % z)
        ok_all = False
        continue
    with zipfile.ZipFile(zp) as zf:
        names = [i.filename.replace("\\", "/") for i in zf.infolist() if not i.is_dir()]
        E = {i.filename.replace("\\", "/"): zf.read(i.filename)
             for i in zf.infolist() if not i.is_dir()}
    w("")
    w("=" * 100)
    w("### %s ：%d 条目  %.1f MB" % (z, len(E), os.path.getsize(zp) / 1048576))
    w("=" * 100)
    # ① 逐字节 vs 磁盘
    # ★ 优先用"该版本的成品树快照"（_snap_<版本>/）比对；没有快照才退回当前树
    vname = z[:-4]
    snap = os.path.join(P, "_snap_" + vname)
    use_snap = os.path.isdir(snap)
    src_lab = "该版快照 _snap_%s%s" % (vname, "" if use_snap else "（无，退回当前树）")
    bad = []
    for k, v in E.items():
        rel = k.replace("/", os.sep)
        if use_snap:
            cand = os.path.join(snap, os.path.basename(rel))
            p = cand if os.path.exists(cand) else os.path.join(NP, rel)
        else:
            p = os.path.join(NP, rel)
        if not os.path.exists(p):
            bad.append(k + "（找不到）")
        elif open(p, "rb").read() != v:
            bad.append(k + "（内容不同）")
    w("① 逐字节一致（对照 %s）：%d/%d %s" %
      (src_lab, len(E) - len(bad), len(E), "✓" if not bad else "!! " + str(bad)))
    if bad:
        ok_all = False

    # ③ 结构自检
    for part in ("body", "arm", "wst", "leg"):
        raw = E.get("pl/f_equip/pl040_0010/%s/mod/f_%s040_0010.mod3" % (part, part))
        if raw is None:
            w("   !! 缺 %s 的 mod3" % part)
            ok_all = False
            continue
        mg, ver, bc, mc, matc = struct.unpack_from("<IHHHH", raw, 0)
        if mg != MAGIC:
            w("   !! %s mod3 magic 错" % part)
            ok_all = False
        ctc = E.get("pl/f_equip/pl040_0010/%s/mod/f_%s040_0010.ctc" % (part, part))
        ncc = u32(ctc, 16) if ctc else -1
        nnn = u32(ctc, 20) if ctc else -1
        ctclen = (80 + 80 * ncc + 112 * nnn == len(ctc)) if ctc else False
        w("   %-4s mod3 骨%3d 网格%2d 材质%2d ；ctc %3d链/%3d节点 长度自检=%s" %
          (part, bc, mc, matc, ncc, nnn, ctclen))
        if not ctclen:
            ok_all = False
    for nm in ("UV1", "UV2", "BAG", "STOCK", "FUR", "METAL", "GLOVE",
               "HAIR", "ACC", "Body_Base", "Face_Base", "Hair"):
        raw = E.get("贴图目录名/%s.tex" % nm)
        if raw is None:
            continue
        mips = u32(raw, 20)
        ln = 184 + 8 * mips <= len(raw)
        w("   %-11s.tex %8d B format=%d mip=%d @17=%d 长度自检=%s" %
          (nm, len(raw), u32(raw, 36), mips, u32(raw, 68), ln))
        if u32(raw, 36) != 31 or u32(raw, 68) != 1 or not ln:
            ok_all = False

    # ② 反向检查
    holes = []
    for part in ("body", "arm", "wst", "leg"):
        r3 = "pl/f_equip/pl040_0010/%s/mod/f_%s040_0010.mod3" % (part, part)
        rm = "pl/f_equip/pl040_0010/%s/mod/f_%s040_0010.mrl3" % (part, part)
        if r3 not in E or rm not in E:
            continue
        live = [x.decode("ascii", "replace") for x in
                re.findall(rb"Ch_[A-Za-z0-9_]{2,40}|Outline[A-Za-z0-9_]*", E[r3])]
        live = sorted(set(x for x in live if x in N2H))
        mr = E[rm]
        matOff, matCount = u64(mr, 32), u32(mr, 16)
        texCount, texOff = u32(mr, 20), u64(mr, 24)
        tl = [mr[texOff + i * 272 + 16:mr.find(b"\x00", texOff + i * 272 + 16)].decode("ascii", "replace")
              for i in range(texCount)]
        for mname in live:
            import zlib as _z
            mh = N2H.get(mname)
            if mh is None:
                mh = (_z.crc32(mname.encode("ascii")) ^ 0xFFFFFFFF) & 0xFFFFFFFF
            for mi in range(matCount):
                e = matOff + mi * 56
                if u32(mr, e + 4) != mh:
                    continue
                rc, bo = struct.unpack_from("<H", mr, e + 22)[0], u64(mr, e + 48)
                codes = {int(k): v.get("name", "") for k, v in
                         MMTR.get(str(u32(mr, e + 8)), {}).get("resourceDict", {}).items()
                         if isinstance(v, dict)}
                for j in range(rc // 2):
                    rh, rv = struct.unpack_from("<2I", mr, bo + j * 16 + 4)
                    cn = codes.get(rh >> 12)
                    if not cn or not cn.startswith("t") or not (1 <= rv <= texCount):
                        continue
                    path = tl[rv - 1]
                    if path.lower().startswith("assets\\default_tex"):
                        continue
                    key = path.replace("\\", "/") + ".tex"
                    if key not in E:
                        holes.append("%s.%s -> %s" % (mname, cn.split("__")[0], key))
                break
    w("② 反向检查（活材质→贴图都在包里）：%s" % ("✓ 0 个洞" if not holes else "!! " + str(holes)))
    if holes:
        ok_all = False
w("")
w("=" * 100)
w("四包终验总判定：%s" % ("全部通过 ✓" if ok_all else "有不通过项，见上 !!"))
w("WROTE " + OUT)

# -*- coding: utf-8 -*-
"""Y4b_物理ctc.py —— 纯 python。给 wst/body/arm 的 ctc **重建/追加**布料链。

依据（Y4a 诊断实测）：
  · 基壳 ctc 的链全部驱动 150~200 号骨；新版 mod3 里这些号的含义变了：
      wst 150-191 = 我们新做的**裙摆 14 列 × 3 节**；194-199 = 三部位共用的**胸骨**（保留）
      body 201-205 = 上一版做的**尾巴**（保留）；194-199 = 胸骨（保留）
      arm 194-199 = 胸骨（保留）；150-193/200 = 新 mod3 里已经没有 ⇒ 悬空（已证无害）
  · ⇒ 过滤规则：**删掉**那些"节点号落在新 mod3 骨表里、但不在白名单里"的链
    （这些链会用**旧形状**去驱动我们的新裙摆骨，必须删）；
    以及"所有节点号都 >=150 且都不在新 mod3 里"的链（旧的头发/袖子链，纯属浪费）。
  · 追加我们自己的链：wst = 14 裙列 ×3 + 2 缎带 ×4 ；body = 2 双马尾 ×5 ；arm = 2 臂带 ×7
  · 节点矩阵约定照抄 C22（已用 30 个现成节点验证误差 0.0000）：
      方向 -> 游戏坐标 v_game = A^T · v_blender（A = Rot(X,+90)），
      取「把局部 +X 转到 v_game 的最小旋转 R」，存 R 的转置（第 0 行 = 该段方向）
  · 链头/节点其余字节一律取自同文件链 0 的模板（保留 colShape/colRadius 等既有字段）
用法: python Y4b_物理ctc.py
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


import os, sys, struct, shutil, json
import numpy as np

P = PROJ
NP = os.path.join(P, "05_导出成品", "nativePC", "pl", "f_equip", "pl040_0010")
BONES = json.load(open(os.path.join(P, "_Y4_链骨位置.json"), encoding="utf-8"))
OUT = os.path.join(P, "_Y4b_物理ctc.txt")
L = []
HDR, CHAIN, NODE = 80, 80, 112
A = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=np.float64)
Ai = A.T


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


# 每部位：白名单（允许被链驱动的既有骨号）+ 新链规格（骨号分组 + preset）
# ★★ 与 Y1_构建.py 的 CHAIN_FNS **逐号一致**（见 `_Y1_构建_*.txt` 的 [号] 行）。
#   本版全部新链骨在 **206~234**（body 206~234 / wst 206~207）；arm 无新链。
#   ★ 但正常情况下 `SPEC[*]["new"]` 会被 `_Y1_链清单.json` 覆盖（单一数据源）——下面只是兜底。
SPEC = {
    "wst": dict(allowed={194, 195, 196, 197, 198, 199},
                new=[("BunnyTail", [206, 207], "charm")],
                preset="charm"),
    "body": dict(allowed={194, 195, 196, 197, 198, 199, 201, 202, 203, 204, 205},
                 new=[("TwinTail_L", [206, 207, 208, 209, 210], "hair"),
                      ("TwinTail_R", [211, 212, 213, 214, 215], "hair"),
                      ("BunnyEar_L", [216, 217], "charm"),
                      ("BunnyEar_R", [218, 219, 220], "charm"),
                      ("Bag", [221, 222], "charm"),
                      ("SuitFrill_L_F", [223, 224], "charm"),
                      ("SuitFrill_L_B", [225, 226], "charm"),
                      ("SuitFrill_R_F", [227, 228], "charm"),
                      ("SuitFrill_R_B", [229, 230], "charm"),
                      ("ChokerBand", [231, 232], "charm"),
                      ("ChokerDrop", [233, 234], "charm")],
                 preset="hair"),
    # arm：本版**没有新链**（袖子/手套/臂环都跟随身体）⇒ 只做"清理"（allowed 只留胸骨 ⇒
    #   任何"节点落在新 mod3 骨表里"的旧链都会被删掉，因为它们会用**旧形状**驱动我们的骨）。
    "arm": dict(allowed={194, 195, 196, 197, 198, 199}, new=[], preset="charm"),
    # leg：同样只清理（Stocking/Shoes/Leg Belt/ACC 都不需要物理），allowed 留空。
    "leg": dict(allowed=set(), new=[], preset="charm"),
}
# ★★ 单一数据源：优先读 `_Y1_链清单.json`（`Y1_构建.py` 每次建链后写出，含 preset）。
#   有它就以它为准 —— 开关改了链条数量时，ctc 自动跟着变，不会出现"号与链错配"（skill 第五次实战 D）。
_CJ = os.path.join(P, "_Y1_链清单.json")
if os.path.exists(_CJ):
    try:
        _d = json.load(open(_CJ, encoding="utf-8"))
        for _p, _lst in _d.items():
            if _p in SPEC:
                SPEC[_p]["new"] = [(x[0], list(x[1]), x[2] if len(x) > 2 else "charm")
                                   for x in _lst]
        print("SPEC 取自 _Y1_链清单.json：%s" % {k: [x[0] for x in v["new"]] for k, v in SPEC.items()})
    except Exception as _e:
        print("!! 读 _Y1_链清单.json 失败，退回内置 SPEC：%s" % _e)

# 物理预设：双马尾 = 头发档；所有挂件（缎带/褶边/飘带）= charm 档
PRESET = {
    "skirt": dict(grav=(0.0, -60.0, 0.0), damp=0.120, trans=0.350, spring=0.030,
                  limit=100.0, friction=0.0, reflect=0.1, wind=0.25, colflag=0),
    "hair":  dict(grav=(0.0, -112.5, 0.0), damp=0.055, trans=0.620, spring=0.010,
                  limit=100.0, friction=0.0, reflect=0.1, wind=0.25, colflag=0),
    # ★ 衣服尾巴专用（用户反馈"飘不起来、很沉"）。
    #   三处改动 + 一处几何改动：① 重力 −112.5 → −45（"挂件要悬垂感就得弱很多"，skill 里
    #   参考包的尾巴是 −90 对发链 −250，比例 0.36 ⇒ 本工程 −112.5 × 0.36 ≈ −40）；
    #   ② transForce 0.620 → 0.72（跟随/拖尾更多 ⇒ 更飘）；③ damping 0.055 → 0.040；
    #   ④ 链节点 3 → 5（Y1）—— 3 节点时权重是"前段全 root / 后段全 tip"的两段式硬折，
    #   整条尾巴像"以尾尖为铰点的刚性片"，这才是"沉"的主因。
    #   ★ 命令行可覆盖：tailgrav=<负数> tailtrans=<0..1> taildamp=<数>
    "tail":  dict(grav=(0.0, -45.0, 0.0), damp=0.040, trans=0.720, spring=0.015,
                  limit=100.0, friction=0.0, reflect=0.1, wind=0.25, colflag=0),
    # ★ 挂件档（本版新增）：腕リング 的 6 条触手用。触手是"挂在腕环上的软触须"——
    #   按 skill 的折算（参考包 发链 −250 : 尾巴 −90 ≈ 0.36）⇒ 比头发档弱得多、跟随更强。
    #   ★ 观感无法离线验证 ⇒ 三个数做成命令行开关（charmgrav/charmtrans/charmdamp）。
    "charm": dict(grav=(0.0, -45.0, 0.0), damp=0.040, trans=0.720, spring=0.015,
                  limit=100.0, friction=0.0, reflect=0.1, wind=0.25, colflag=0),
    # ★ 腰部褶边 专用（2026-09-23 新增）：用户反馈"看不出腰部褶边 的物理"。
    #   原来套 skirt 档（阻尼 0.120 / 平移 0.350 = 长裙的参数）对**短褶边**太稳。
    #   改成：阻尼 0.120→**0.060**（衰减慢、余摆长）、平移 0.350→**0.700**（跟手/拖尾多）、
    #         重力 −60→**−50**（少往下坠）。三个数都是命令行开关。
    "frill": dict(grav=(0.0, -50.0, 0.0), damp=0.060, trans=0.700, spring=0.030,
                  limit=100.0, friction=0.0, reflect=0.1, wind=0.25, colflag=0),
}
# 命令行覆盖（观感类参数 ⇒ 让用户一句话迭代，别让助手猜）：
#   tailgrav= tailtrans= taildamp=    → 衣服尾巴档（本版未用，保留兼容）
#   charmgrav= charmtrans= charmdamp= → 挂件（腕リング 触手）档
#   skirtgrav= skirttrans= skirtdamp= → 长裙档（本版未用）
#   frillgrav= frilltrans= frilldamp= → 腰部褶边 档
for _a in sys.argv:
    if not isinstance(_a, str):
        continue
    for _pn in ("tail", "charm", "skirt", "frill"):
        if _a.startswith(_pn + "grav="):
            PRESET[_pn]["grav"] = (0.0, float(_a.split("=", 1)[1]), 0.0)
        elif _a.startswith(_pn + "trans="):
            PRESET[_pn]["trans"] = float(_a.split("=", 1)[1])
        elif _a.startswith(_pn + "damp="):
            PRESET[_pn]["damp"] = float(_a.split("=", 1)[1])


def mod3_bones(part):
    raw = open(os.path.join(P, "_mod3", "f_%s040_0010.mod3" % part), "rb").read()
    bc = struct.unpack_from("<H", raw, 6)[0]
    bo = struct.unpack_from("<Q", raw, 48)[0]
    return set(struct.unpack_from("<H", raw, bo + i * 24)[0] for i in range(bc))


def parse(raw):
    nc = struct.unpack_from("<I", raw, 16)[0]
    heads, nodes = [], []
    o = HDR + CHAIN * nc
    for i in range(nc):
        cn = struct.unpack_from("<I", raw, HDR + i * CHAIN)[0]
        heads.append((cn, bytes(raw[HDR + i * CHAIN:HDR + (i + 1) * CHAIN])))
        nodes.append([bytes(raw[o + k * NODE:o + (k + 1) * NODE]) for k in range(cn)])
        o += NODE * cn
    return nc, struct.unpack_from("<I", raw, 20)[0], heads, nodes


def min_rot_to_x(d):
    x = np.array([1.0, 0.0, 0.0])
    v = np.cross(x, d)
    c = float(np.dot(x, d))
    s = float(np.linalg.norm(v))
    if s < 1e-9:
        if c > 0:
            return np.eye(3)
        perp = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([0.0, 0.0, 1.0])
        u = np.cross(d, perp)
        u /= np.linalg.norm(u)
        return 2.0 * np.outer(u, u) - np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1.0 / (1.0 + c))


total_ok = True
for part, spec in SPEC.items():
    path = os.path.join(NP, part, "mod", "f_%s040_0010.ctc" % part)
    if not os.path.exists(path):
        w("!! 缺 %s" % path)
        continue
    bak = path + ".bak_y4"
    if os.path.exists(bak):
        raw0 = open(bak, "rb").read()
        w("")
        w("--- %s（以 .bak_y4 为基础重算）---" % part)
    else:
        raw0 = open(path, "rb").read()
        shutil.copy2(path, bak)
        w("")
        w("--- %s（首次运行，已备份 .bak_y4）---" % part)
    nc, nnode, heads, nodes = parse(raw0)
    B = mod3_bones(part)
    w("   原 %d 条链 / %d 节点；新 mod3 骨 %d 根" % (nc, nnode, len(B)))
    keep = []
    for i in range(nc):
        cn, h = heads[i]
        ids = [struct.unpack_from("<H", nd, 72)[0] for nd in nodes[i]]
        bad_a = any((x in B) and (x not in spec["allowed"]) for x in ids)
        bad_b = all(x >= 150 and x not in B for x in ids)
        why = "删：会用旧形状驱动我们的新链骨 %s" % [x for x in ids if x in B and x not in spec["allowed"]] \
            if bad_a else ("删：全部悬空且号>=150（旧头发/袖子链）" if bad_b else "保留")
        w("      链%-3d 节点%2d %-3s %s" % (i, cn, ",".join(str(x) for x in ids), why))
        if not (bad_a or bad_b):
            keep.append(i)
    # ---- 造新链 ----
    if not heads:
        w("   !! 原文件没有链，无法取模板")
        continue
    tpl_head = bytearray(heads[0][1])
    tpl_node = bytearray(nodes[0][0])
    new_heads, new_nodes = [], []
    for ent in spec["new"]:
        cname, fns = ent[0], ent[1]
        pname = ent[2] if len(ent) > 2 else spec["preset"]      # 每条链可用自己的 preset
        P_ = PRESET[pname]
        pts = []
        for fn in fns:
            k = "%03d" % fn
            if k not in BONES[part]:
                w("   !! 缺 %s 的位置" % k)
                pts = None
                break
            pts.append(np.array(BONES[part][k], float))
        if pts is None:
            continue
        hb = bytearray(tpl_head)
        struct.pack_into("<I", hb, 0, len(fns))
        hb[4] = P_["colflag"]
        struct.pack_into("<fff", hb, 32, *P_["grav"])
        struct.pack_into("<f", hb, 48, P_["damp"])
        struct.pack_into("<f", hb, 52, P_["trans"])
        struct.pack_into("<f", hb, 56, P_["spring"])
        struct.pack_into("<f", hb, 60, P_["limit"])
        struct.pack_into("<f", hb, 64, P_["friction"])
        struct.pack_into("<f", hb, 68, P_["reflect"])
        struct.pack_into("<f", hb, 72, P_["wind"])
        new_heads.append(bytes(hb))
        w("      + 链 %-12s preset=%-6s 重力(%.1f,%.1f,%.1f) 阻尼%.3f 平移%.3f 弹簧%.3f" %
          (cname, pname, P_["grav"][0], P_["grav"][1], P_["grav"][2], P_["damp"],
           P_["trans"], P_["spring"]))
        for k, fn in enumerate(fns):
            nd = bytearray(tpl_node)
            d = (pts[k + 1] - pts[k]) if k + 1 < len(pts) else (pts[k] - pts[k - 1])
            d = d / max(np.linalg.norm(d), 1e-9)
            R = min_rot_to_x(Ai @ d)
            m4 = np.eye(4)
            m4[:3, :3] = R.T
            struct.pack_into("<16f", nd, 0, *m4.reshape(-1).tolist())
            struct.pack_into("<H", nd, 66, 1 if k == 0 else 0)
            struct.pack_into("<H", nd, 72, fn)
            # ★★ 决定性的一个字段：节点的 `colShape`（+70）必须是 **257**。
            #   模板是从"该文件第一条链"抄的，而 `wst.ctc` 的第一条是 第1版 的旧裙链
            #   （colShape=258）⇒ 抄出来的链**完全零反应**（用户实机："腰部褶边 跑起来一点没动"）。
            #   实测对照：第4版 用户认可过的包（裙摆会动）里 **14 条链全部 257**；
            #             第5版 的 body 链（双马尾/缎带，会动）也是 257 —— 只有 wst 的抄成了 258。
            #   ⇒ 模板不再信任，**显式写成 257**。
            struct.pack_into("<H", nd, 70, 257)
            new_nodes.append(bytes(nd))
    # ---- 组装 ----
    n_new_ch = len(new_heads)
    n_new_nd = len(new_nodes)
    out = bytearray()
    out += raw0[:HDR]
    struct.pack_into("<I", out, 16, len(keep) + n_new_ch)
    struct.pack_into("<I", out, 20, sum(heads[i][0] for i in keep) + n_new_nd)
    for i in keep:
        out += heads[i][1]
    for h in new_heads:
        out += h
    for i in keep:
        for nd in nodes[i]:
            out += nd
    for nd in new_nodes:
        out += nd
    exp = HDR + CHAIN * (len(keep) + n_new_ch) + NODE * (sum(heads[i][0] for i in keep) + n_new_nd)
    open(path, "wb").write(bytes(out))
    # ---- 复核 ----
    chk = open(path, "rb").read()
    nc1, nn1, heads1, nodes1 = parse(chk)
    same = all(heads1[j][1] == heads[keep[j]][1] and all(a == b for a, b in zip(nodes1[j], nodes[keep[j]]))
               for j in range(len(keep)))
    w("   原链保留 %s ；新增 %d 条 / %d 节点" %
      (keep, n_new_ch, n_new_nd))
    w("   新文件 %d 字节（应为 %d）%s ；链数 %d 节点数 %d ；长度自检=%s" %
      (len(chk), exp, "OK" if len(chk) == exp else "!!", nc1, nn1,
       HDR + CHAIN * nc1 + NODE * nn1 == len(chk)))
    w("   原有保留链逐字节一致 = %s ；文件头 24~79 未动 = %s" %
      (same, chk[24:80] == raw0[24:80]))
    if len(chk) != exp or not same or chk[24:80] != raw0[24:80]:
        total_ok = False
w("")
w("全部复核通过 = %s" % total_ok)
w("WROTE " + OUT)

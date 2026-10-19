# -*- coding: utf-8 -*-
"""Y2_贴图烘焙与生成.py —— 纯 python（PIL+numpy+texconv）。为 **第7版 本套装 本套（天蓝 Sky Blue）
+ 头发素材 蓬蓬双马尾 Yellow** 生成 **9 张 .tex**。

 ★ 9 个目标材质（4 张有源图 + 3 张"只有颜色"⇒ 生成纯色图 + 头发 2 张）：
   UV1   <- 服装素材/贴图/UV1/Skyblue.png        2048²  Suit / Headband / Arm warmers
   UV2   <- 服装素材/贴图/UV2/Skyblue.png        2048²  Choker / arm belt / Leg Belt / Shoes / ACC
   BAG   <- 服装素材/贴图/Bag/Skyblue.png        2048²  Bag
   STOCK <- 服装素材/贴图/Stockings/Stockings.png 2048²  Stocking（★ 官方蓝系**没有**丝袜配色）
   FUR   <- 源**无贴图**，作者脚本给 (0.97,0.97,0.98) ⇒ 生成纯色（Suit 毛边 / 兔耳绒 / 兔尾）
   METAL <- 源**无贴图**，作者脚本给 (0.80,0.82,0.86) ⇒ 生成纯色（金属件；平涂，非真金属）
   GLOVE <- 源**无贴图**，源 `Gloves/4. Sky Blue.mat _BaseColor` = (0.6667,0.859,1.0) ⇒ 生成纯色
   HAIR  <- 第1版/hair/HAIR_PACK_DIR/PNG/Yellow.png   4096²  头发（Yellow）
   ACC   <- 同上目录 /PNG/Accessories.png                 4096²  发饰
   ★★ 源图目录是**本工程内**的 `素材\\贴图\\`（作者脚本引用的
     unity3d 解包路径另有一份，内容相同）；这是本版**新增**的东西（前六版都用 第1版/cloth 的 resolved）。
   ★ 纯色图的取值 = **把源 baseColor（线性）转成 sRGB 再存** —— 因为我们的 .tex 是
     BC7_UNORM_**SRGB**（format 31），游戏采样时会 sRGB→线性解回来 ⇒ 这样预览里看到的灰度才能复现。
       FUR   = sRGB(0.970,0.970,0.980) = (252,252,253)
       METAL = sRGB(0.800,0.820,0.860) = (231,234,239)
       GLOVE = sRGB(0.6667,0.859,1.000) = (213,238,255)
   ★ 换配色 = 只改本文件的 `SRC` 里那个 PNG 名并重跑（贴图差分：材质名与几何都不动）。
     本套源包是多配色的（`Materials/` 下每件都有十几个配色 .mat；预览用的是 **6. Sky Blue**）。
     ★★ 丝袜的 8 个配色（`Materials/Stockings/1..8`）只是同一张 `Stockings.png` 上的 `_BaseColor`
        染色 ⇒ 要换色就把 tint 乘进贴图（用户 2026-10-03 选了**原图 / White**）。

 ① 源图实测：尺寸 / alpha 分布 / alpha 分档与 RGB
 ② 烘焙（照抄 C31 的最终规则）：
    - **只填 alpha==0 的真空像素**（用最近的已知像素颜色撑开，1/4 分辨率 8 邻域生长）
      —— 0<alpha<250 的软边**保留原 RGB**，只把 alpha 拉平到 255
    - **不做预乘**（skill 的教训：透明区 RGB 若不是颜色，预乘只会把空白变黑）
    - 不变量：改动像素必须**全部**来自 alpha<250
 ③ PNG -> DDS（texconv BC7_UNORM）-> .tex（184 头 + mip 表 + DDS 载荷）
 ④ 逐张自检：format=31 / @17=1 / @31=@34=@37=(W<<16)|(W>>1) / 长度公式 / 载荷逐字节
 ⑤ 色彩空间：**raw**（沿用 第2版~第6版 多次实机验收过的口径：源 PNG 原样存）
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


import os, sys, struct, subprocess, shutil
import numpy as np
from PIL import Image

PROJ = PROJ
TEXCONV = TEXCONV
TEMPLATE = TEX_TEMPLATE
KEEP = WORK_ASCII      # 纯 ASCII，texconv 只吃这个
PKG = os.path.join(PROJ, "05_导出成品", "nativePC", "贴图目录名")
WORK = os.path.join(PROJ, "_texwork")
OUT = os.path.join(PROJ, "_Y2_贴图.txt")
SRCDIR_CLOTH = (CLOTH_TEX_DIR)   # ★ 本版新增：本套自己的贴图
SRCDIR_HAIR = HAIR_SRC_DIR
L = []


def w(s=""):
    print(s, flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


# (目标名, 源 PNG 路径 或 None, 纯色 RGB（**已经是 sRGB 字节**）或 None)
SRC = [
    ("UV1",   os.path.join(SRCDIR_CLOTH, "UV1", "Skyblue.png"), None),
    ("UV2",   os.path.join(SRCDIR_CLOTH, "UV2", "Skyblue.png"), None),
    ("BAG",   os.path.join(SRCDIR_CLOTH, "Bag", "Skyblue.png"), None),
    ("STOCK", os.path.join(SRCDIR_CLOTH, "Stockings", "Stockings.png"), None),
    ("FUR",   None, (252, 252, 253)),      # sRGB(0.970,0.970,0.980) 作者脚本给的毛色
    ("METAL", None, (231, 234, 239)),      # sRGB(0.800,0.820,0.860) 作者脚本给的银灰
    ("GLOVE", None, (213, 238, 255)),      # sRGB(源 Gloves/4. Sky Blue.mat _BaseColor 0.6667,0.859,1.0)
    ("HAIR",  os.path.join(SRCDIR_HAIR, "Yellow.png"), None),
    ("ACC",   os.path.join(SRCDIR_HAIR, "Accessories.png"), None),
]

# ★ v3/v4（`origear`/`origtail` 保留原版耳/尾）要用：基壳 `Ch_Standard_Mt__3`（耳/尾材质）。
#   **不重新烘焙、不重编码** —— 直接**原样拷贝 第1版 的那张 `Hair.tex`**：
#     · 它和 `第5版` 的成品**逐字节相同**（MD5 `b1331e08…`），而 第5版 正是"保留原版耳尾 + 用户验收过"的那版；
#     · 它是**线性化**存的（skill 记过："Hair 与军装是 sRGB→线性"），与 `__3` 那个**未改动的基壳 CB**
#       是配套的 —— 我们自己去 bake 成 raw 反而会偏离这套已知能跑的组合。
#   ★★ 名字必须是 `ExtraHair` 而**不能是 `Hair`**：Windows 大小写不敏感 ⇒ `Hair.tex` 会和我们的
#      `HAIR.tex`（头发素材 黄发）变成**同一个文件**，原版耳/尾会静默地贴上头发贴图。
COPY_TEX = {"ExtraHair": os.path.join(PROJ, "素材", "ExtraHair.tex")}
BAKED = os.path.join(WORK, "烘焙_y2")
os.makedirs(BAKED, exist_ok=True)
os.makedirs(KEEP, exist_ok=True)
w("### 源图目录：%s" % SRCDIR_CLOTH)
w("###            %s" % SRCDIR_HAIR)
w("### 无贴图的材质（源里只有 _Color）⇒ 生成纯色图：Metal(173,171,171) / Fur(247,244,240)")
for _n, _p, _s in SRC:
    if _p and not os.path.exists(_p):
        w("!! 源图不存在：%s" % _p)


def src_image(path, solid):
    """返回 RGBA ndarray；path=None 时按 solid 生成 64² 纯色图。"""
    if path is None:
        a = np.zeros((64, 64, 4), np.uint8)
        a[..., 0], a[..., 1], a[..., 2], a[..., 3] = solid[0], solid[1], solid[2], 255
        return a
    if not os.path.exists(path):
        raise SystemExit("!! 源图不存在：%s" % path)
    return np.array(Image.open(path).convert("RGBA"))


# ★★ v1 修正（用户 2026-10-03 实机反馈："丝袜不应该是纯色的，其实原本应该是渔网袜"）：
#   `Stockings.png` 的 RGB **全是纯白（std=0）、图案完全在 alpha 通道里**
#   （alpha==0 占 62.60% = 菱形网眼；alpha 从 1 到 255 是抗锯齿的网线；另有右侧一条实心带）。
#   原来的"填满 alpha==0 + alpha 拉平到 255"正好把渔网**抹平成一个白筒** —— 这就是实机看到纯色的原因。
#   ⇒ STOCK 走**专用配方**（与其它 8 张相反）：
#     **把渔网整个画进 RGB，alpha 全置 255（不透明）**：
#       `RGB = lerp(皮肤色, 网线色, alpha)`，网眼 = 皮肤色、网线 = 网线色；然后 `alpha = 255`。
#   ★★ 为什么最终选了"不透明"（第二轮实机反馈："黑色版出现了奇怪的杂色，白色版也是"）：
#     第一版试过"保留 alpha"，实机看到网眼处是**抖动噪点/彩色杂色**。最可能的原因是
#     MHW 对带 alpha 的材质做**抖动式（dithered/stipple）透明** —— 网眼被随机裁掉、露出
#     `Body_base` 的身体贴图（它本身有颜色细节），再加上 mip 链上"直通 alpha"的平均
#     ⇒ 屏幕上就是彩色噪点。**alpha 混合 + mip 还会让低 mip 的 RGB 与 alpha 不同步**。
#     ⇒ 只要**完全不依赖 alpha**，就不存在 dithering / 混合排序 / mip-alpha 三类问题。
#      代价：网眼是**平涂的皮肤色**（没有真实透光/阴影），远处看没问题、贴脸看会发平。
#   ★ 网线色默认 **黑**（用户给的参考图 2）；`netwhite=1` 改成白网。
# ★★ 第 4 轮（用户："这套衣服的丝袜是**不透明**的，你可以参考 `旧工程目录`（同一套衣服）"）：
#   去比对参照工程的成品贴图 ⇒ 逐像素差 **0.00** 地等于 **`RGB' = RGB源 × (alpha/255)`**，
#   且**存成不透明的 RGB**（alpha 全 255）。正是 skill 里那条现成配方：
#     "作者贴图常把网纹/镂空/线条画在 alpha 通道（Blender 预览时预乘显示），游戏不透明渲染会丢失
#      ⇒ 用 PIL 把 RGB×alpha **预乘**后存不透明版"。
#   ⇒ 本版就用这个：网线（alpha 高）= 白、网眼（alpha=0）= **黑**；整张当不透明 RGB。
#   ★★ 但**不照抄它的 format 30**：参照工程那个包是用户第一个 MHWI 模组（"几乎全是 bug"），
#     而 skill 的普查把"albedo 用 30"明确列为**错误写法**（99.2% 的 albedo 是 31；
#     且"albedo=30"的去重样本里 15/20 张正是我们自己那个包）—— 见 skill §2.6 / §8.2：
#     数据本是 sRGB 却标成线性 ⇒ 整体被抬亮。**我们保持 format 31**。
#   ⇒ 组合 = **预乘变换（照参照）+ format 31（照 skill）**。
#   ★ 前几轮的教训保留在注释里（都实测过）：
#     · 直接"填满 alpha==0 + alpha 拉平" ⇒ 渔网被抹成一个白筒（第 1 轮）
#     · 保留 alpha ⇒ 实机是**抖动杂色**（第 2 轮，MHW 疑为 dithered 透明）
#     · `lerp(皮肤, 网线色, 原始 alpha)` ⇒ 网线被低值软边稀释成**浅灰**，腿"整体变白"（第 3 轮）
NET_RGB = None               # ★ 默认走"预乘"（= 参照工程的做法）；`netwhite=1` 才切到"白/黑 lerp"对照
SKIN_RGB = (252, 228, 222)   # 仅 netwhite 对照模式用
NET_LO, NET_HI = 0.10, 0.50  # 仅 netwhite 对照模式用（陡化 alpha）
USE_SKIN_BG = False          # 关掉"腿皮投影"（第 3 轮做法；纯预乘不需要）
for _a in sys.argv:
    if isinstance(_a, str) and _a.startswith("netwhite"):
        NET_RGB = (255, 255, 255)
w("### ★ 渔网袜配方：STOCK = **预乘**（RGB×alpha，照参照工程 milfy/1）+ 不透明 + **format 31**%s" %
  ("（netwhite 对照：改用白/黑 lerp）" if NET_RGB is not None else ""))
# ★★ 第三轮（用户："图一是本套_有描边，图二是…_白渔网。显然整体变白了"）：
#   真因 = **源图 alpha 的大部分是"低值软边"**：`alpha>=250` 只占 5.13%，而 `alpha>=1` 占 37.4%
#   （直方图从 1 平滑衰减）。所以 `lerp(皮肤, 网线色, 原始 alpha)` 得到的是**浅灰的网线**；
#   再叠加"腿皮贴图本身在腿那块就接近纯白 (252,228,222)" ⇒ 整体就是一条**白腿 + 淡网**。
#   ⇒ 把 alpha **陡化**（线性重映射，砍掉 <0.10 的晕、>=0.50 就当作实心），网线才是实的黑：
#       alpha' = clip((a/255 - LO) / (HI - LO), 0, 1)
#     实测覆盖率：`alpha>=1` 37.4% ／ `>=32` 29.1% ／ `>=128` 19.0% ／ `>=250` 5.1%
#     ⇒ LO=0.10、HI=0.50：实心(>=128) 19% + 抗锯齿过渡 ⇒ 干净的黑色渔网（线宽 ~3px @2048²，菱形周期 ~24px）。
#   ★ 想更粗/更细就调这两个数（LO 越小线越粗）。
KEEP_ALPHA = set()           # 一律存不透明 RGB（第 2 轮的实测教训：保留 alpha 会出抖动杂色）
SPECIAL = {"STOCK": "fishnet"}     # 走 bake_stock

# ★★ 第二轮：网眼底色改成「**按位置投影的腿皮颜色**」（用户反馈："显然整体变白了"）。
#   第一版用"身体贴图不透明区的**中位色** (252,228,222)"当网眼——那是接近纯白的肤色，
#   而实际腿在游戏里被光照与贴图明暗压暗 ⇒ 一块平的亮色盖上去，整条腿就发白。
#   ⇒ 改：把 Stocking 每个面角投影到 `Body_base` 表面、取那里的 **UV**（`Y2b_渔网投影UV.py` 算好），
#     再在 UV 空间光栅化、采 `Body_Base.png` ⇒ 网眼 = "这条腿在那一处的真实颜色"。
#   ★ 丝袜法线 ≈ 腿皮法线、光照也一致 ⇒ 底色对了，观感就与"真透明"几乎一样。
#   算不出来（缺 npy）就退回平涂 SKIN_RGB。
PROJ_JSON = os.path.join(PROJ, "_X3_preview.json")
PROJ_NPY = os.path.join(WORK, "STOCK_proj_uv.npy")
BODY_PNG = BODY_PNG


def stock_skin_map(res=2048):
    """把 Stocking 的 UV 三角形光栅化，插值「投影后的腿皮 UV」，再采身体贴图。
    返回 (skin_rgb float32 (res,res,3), 覆盖率 float)。失败返回 (None, 0)。"""
    if not (os.path.exists(PROJ_NPY) and os.path.exists(PROJ_JSON) and os.path.exists(BODY_PNG)):
        w("   !! 缺投影数据（%s / %s）⇒ 网眼退回平涂肤色" % (PROJ_NPY, BODY_PNG))
        return None, 0.0
    import json as _json
    d = _json.load(open(PROJ_JSON, encoding="utf-8"))["objs"]["Stocking"]
    uv = np.array(d["uv"], float)                 # per-loop
    polys = d["polys"]
    proj = np.load(PROJ_NPY).astype(np.float64)   # (n_loops, 2) 投影后的腿皮 UV
    bpng = np.array(Image.open(BODY_PNG).convert("RGB"))
    BH, BW = bpng.shape[:2]
    out = np.zeros((res, res, 2), np.float32)     # 投影后的腿皮 UV（每 texel 两个通道）
    mask = np.zeros((res, res), bool)
    li = 0
    for p in polys:
        n = len(p)
        U = uv[li:li + n]
        Pj = proj[li:li + n]
        li += n
        for k in range(1, n - 1):                 # 扇形三角化（源面多是四边形）
            a, b, c = U[0], U[k], U[k + 1]
            pa, pb, pc = Pj[0], Pj[k], Pj[k + 1]
            x0 = np.floor(np.array([a[0], b[0], c[0]]) * res).astype(int)
            y0 = np.floor(np.array([a[1], b[1], c[1]]) * res).astype(int)
            xmin, xmax = max(0, x0.min()), min(res - 1, x0.max())
            ymin, ymax = max(0, y0.min()), min(res - 1, y0.max())
            if xmax < xmin or ymax < ymin:
                continue
            xs = (np.arange(xmin, xmax + 1) + 0.5) / res
            ys = (np.arange(ymin, ymax + 1) + 0.5) / res
            X, Y = np.meshgrid(xs, ys)
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            l0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
            l1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
            l2 = 1.0 - l0 - l1
            ins = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            if not ins.any():
                continue
            sub = out[ymin:ymax + 1, xmin:xmax + 1]
            sub[ins] = (l0[ins, None] * pa + l1[ins, None] * pb + l2[ins, None] * pc)
            mask[ymin:ymax + 1, xmin:xmax + 1] |= ins
    n = int(mask.sum())
    if n == 0:
        return None, 0.0
    uu = np.clip(out[..., 0], 0.0, 1.0)
    vv = np.clip(out[..., 1], 0.0, 1.0)
    ii = np.clip((vv * (BH - 1)).astype(int), 0, BH - 1)
    jj = np.clip((uu * (BW - 1)).astype(int), 0, BW - 1)
    skin = np.zeros((res, res, 3), np.float32)
    skin[mask] = bpng[ii[mask], jj[mask]].astype(np.float32)
    # 没覆盖到的 texel 用平涂肤色兜底（它们本来不会被采样）
    skin[~mask] = np.array(SKIN_RGB, np.float32)
    return skin, n / float(res * res)


STOCK_SKIN, _cover = (None, 0.0)
if USE_SKIN_BG:
    STOCK_SKIN, _cover = stock_skin_map()
    if STOCK_SKIN is not None:
        _flat = STOCK_SKIN.reshape(-1, 3)
        _sel = _flat[np.abs(_flat - np.array(SKIN_RGB, np.float32)).max(axis=1) > 1.0]
        w("### ★ 渔网网底 = **腿皮投影**：UV 覆盖率 %.1f%%；投影到的腿皮色 均值 %s" %
          (100.0 * _cover,
           np.round(_sel.mean(0), 1).tolist() if len(_sel) else "无"))


def bake_stock(np_img, net, skin_map, skin_flat):
    """STOCK 专用。
    ★ 默认（net is None）= **预乘**：`RGB' = RGB源 × (alpha/255)`，`alpha = 255`。
      与参照工程 `milfy/1/04_贴图转换/成品/Stockings.png` 逐像素差 0.00 的做法一致
      （skill：「网纹画在 alpha 通道 ⇒ 把 RGB×alpha 预乘后存不透明版」）。
    ★ 对照模式（net 给了颜色）= 陡化 alpha 后 `lerp(腿皮, 网线色, a')`（第 3 轮做法）。"""
    a = np_img.copy()
    al_raw = (a[..., 3:4].astype(np.float32) / 255.0)
    if net is None:
        rgb = a[..., :3].astype(np.float32) * al_raw
    else:
        al = np.clip((al_raw - NET_LO) / max(NET_HI - NET_LO, 1e-6), 0.0, 1.0)
        nt = np.array(net, np.float32)
        if skin_map is not None and skin_map.shape[:2] == a.shape[:2]:
            sk = skin_map
        else:
            sk = np.array(skin_flat, np.float32)[None, None, :] * np.ones(a.shape[:2] + (1,), np.float32)
        rgb = sk * (1.0 - al) + nt[None, None, :] * al
    a[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    a[..., 3] = 255
    return a, dict(n_unknown=int((np_img[..., 3] == 0).sum()), n_soft=0, rounds=0,
                   rgb_of_unknown=np.zeros(3))


def bake(np_img):
    """只填 alpha==0；0<alpha<250 只拉平 alpha、RGB 原样。alpha 全不透明时原图直通。"""
    a = np_img.copy()
    alpha = a[..., 3]
    known = alpha >= 250
    unknown = ~known
    n_unknown = int(unknown.sum())
    n_soft = int(((alpha > 0) & (alpha < 250)).sum())
    if n_unknown == 0:
        a[..., 3] = 255
        return a, dict(n_unknown=0, n_soft=n_soft, rounds=0, rgb_of_unknown=np.zeros(3))
    rgb0 = a[..., :3][unknown].mean(axis=0)
    small = a[::4, ::4].astype(np.float64)
    sk = known[::4, ::4].copy()
    rounds = 0
    for it in range(400):
        if sk.all():
            break
        acc = np.zeros(small.shape[:2] + (3,))
        cnt = np.zeros(small.shape[:2])
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                sh = np.roll(np.roll(small[..., :3], dy, 0), dx, 1)
                shk = np.roll(np.roll(sk, dy, 0), dx, 1)
                acc += sh * shk[..., None]
                cnt += shk
        new = (~sk) & (cnt > 0)
        if new.sum() == 0:
            break
        small[..., :3][new] = (acc[new] / cnt[new, None]).round()
        sk = sk | new
        rounds = it + 1
    up = np.repeat(np.repeat(small[..., :3], 4, axis=0), 4, axis=1)[:a.shape[0], :a.shape[1]]
    out = a.copy()
    out[..., :3][unknown] = np.clip(up[unknown], 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return out, dict(n_unknown=n_unknown, n_soft=n_soft, rounds=rounds,
                     filled=int(sk.sum()) * 16, rgb_of_unknown=rgb0)


w("")
w("### ① 源图实测")
w("   %-14s %6s %10s %10s %10s %12s %12s" %
  ("贴图", "尺寸", "alpha=0", "0<a<250", "a=255", "alpha0区RGB", "alpha255区RGB"))
rep = {}
for nm, orig, solid in SRC:
    a = src_image(orig, solid)
    al = a[..., 3]
    z, s, f = int((al == 0).sum()), int(((al > 0) & (al < 250)).sum()), int((al >= 250).sum())
    m0 = a[..., :3][al == 0].mean(0).round(1) if z else [np.nan] * 3
    m1 = a[..., :3][al >= 250].mean(0).round(1) if f else [np.nan] * 3
    w("   %-14s %6s %9.2f%% %9.2f%% %9.2f%% %12s %12s" %
      (nm, "%dx%d" % (a.shape[1], a.shape[0]), 100.0 * z / al.size, 100.0 * s / al.size,
       100.0 * f / al.size, m0, m1))
    rep[nm] = dict(alpha255_mean=float(np.mean(m1)) if f else 0.0,
                   bright_alpha255=float(np.mean(m1) / 255.0) if f else 0.0)

w("")
w("### ② 烘焙（默认：只填 alpha==0；0<a<250 只拉平 alpha）★ STOCK 走渔网专用配方")
for nm, orig, solid in SRC:
    a = src_image(orig, solid)
    if nm in SPECIAL:
        out, st = bake_stock(a, NET_RGB, STOCK_SKIN, SKIN_RGB)
    else:
        out, st = bake(a)
    changed = np.any(out != a, axis=2)
    n_opq_rgb = int(((a[..., 3] >= 250) & np.any(out[..., :3] != a[..., :3], axis=2)).sum())
    n_soft_rgb = int(((a[..., 3] > 0) & (a[..., 3] < 250) &
                      np.any(out[..., :3] != a[..., :3], axis=2)).sum())
    dst = os.path.join(BAKED, nm + ".png")
    if nm in KEEP_ALPHA:
        # ★ 保留 alpha：存 RGBA（texconv BC7 带 alpha、.tex format 31 也带 alpha）
        Image.fromarray(out, "RGBA").save(dst)
    else:
        Image.fromarray(out, "RGBA").convert("RGB").save(dst)
    if nm in SPECIAL:
        _src_al = a[..., 3]
        _mode = ("**预乘** RGB×alpha（照参照工程 milfy/1）" if NET_RGB is None
                 else "陡化 alpha 后 lerp(腿皮, 网线色%s)" % (list(NET_RGB),))
        w("   %-14s ★渔网配方（**不透明**）：%s；源 alpha==0 占 %.2f%%、满不透明占 %.2f%%；"
          "输出 alpha 全 255" %
          (nm, _mode, 100.0 * (_src_al == 0).sum() / _src_al.size,
           100.0 * (_src_al >= 250).sum() / _src_al.size))
        _nt = out[..., :3][_src_al >= 250]
        _ho = out[..., :3][_src_al == 0]
        _mid = out[..., :3][(_src_al > 0) & (_src_al < 250)]
        w("        实测：网线区（a>=250）RGB %s ／ 网眼区（a==0）RGB %s ／ 软边区 RGB %s" %
          (np.round(_nt.mean(0), 1).tolist() if len(_nt) else "无",
           np.round(_ho.mean(0), 1).tolist() if len(_ho) else "无",
           np.round(_mid.mean(0), 1).tolist() if len(_mid) else "无"))
    else:
        w("   %-14s alpha=0 %9d（%5.2f%%）；生长 %d 轮；改动像素 %d；"
          "不透明区RGB被改 %d；软边RGB被改 %d" %
          (nm, st["n_unknown"], 100.0 * st["n_unknown"] / a[..., 3].size, st["rounds"],
           int(changed.sum()), n_opq_rgb, n_soft_rgb))
    if st["n_unknown"] == 0 and nm not in SPECIAL:
        w("        alpha 全不透明 ⇒ 原图直通、一个像素都没动")
    elif nm not in SPECIAL:
        w("        原 alpha=0 区 RGB 均值 %s -> 烘焙后 %s" %
          (np.round(st["rgb_of_unknown"], 1).tolist(),
           np.round(out[..., :3][a[..., 3] == 0].mean(axis=0), 1).tolist()))
    shutil.copy2(dst, os.path.join(KEEP, "Y3_" + nm + ".png"))

# ---------- ③ DDS + .tex ----------
BLK = 16
SRGB_FLAG = {28: 1, 30: 1, 31: 1, 22: 0, 23: 0, 26: 0}
TXFMT = 31          # BC7_UNORM_SRGB（颜色图标准写法；语料 99.2%）


def packed_width(x):
    return ((x & 0xFFFF) << 16) | ((x >> 1) & 0xFFFF)


def dds_parts(p):
    b = open(p, "rb").read()
    h = struct.unpack_from("<I", b, 4)[0]
    height, width = struct.unpack_from("<2I", b, 12)
    mip = struct.unpack_from("<I", b, 28)[0]
    fourcc = struct.unpack_from("<I", b, 84)[0]
    has10 = fourcc == 0x30315844
    return width, height, mip, b[4 + h + (20 if has10 else 0):]


def mip_sizes(x, y, mips, blk):
    return [max(1, (max(1, x >> i) + 3) // 4) * max(1, (max(1, y >> i) + 3) // 4) * blk
            for i in range(mips)]


def build_tex(template, dds):
    head = bytearray(open(template, "rb").read()[:184])
    x, y, mips, payload = dds_parts(dds)
    struct.pack_into("<I", head, 20, mips)
    struct.pack_into("<I", head, 24, x)
    struct.pack_into("<I", head, 28, y)
    struct.pack_into("<I", head, 120, x)
    struct.pack_into("<I", head, 36, TXFMT)
    struct.pack_into("<I", head, 68, SRGB_FLAG[TXFMT])
    for off3 in (124, 136, 148):
        struct.pack_into("<I", head, off3, packed_width(x))
    off = 184 + 8 * mips
    tab = bytearray()
    for s in mip_sizes(x, y, mips, BLK):
        tab += struct.pack("<II", off, 0)
        off += s
    return bytes(head) + bytes(tab) + payload, x, y, mips


w("")
w("### ③ 生成 .tex（format 31 / raw 色彩空间 / 完整 mip 链）")
for nm in COPY_TEX:
    src = COPY_TEX[nm]
    if not os.path.exists(src):
        w("   !! 缺 %s（v3/v4 的原版耳/尾要用）" % src)
        continue
    dst = os.path.join(PKG, nm + ".tex")
    shutil.copy2(src, dst)
    b = open(dst, "rb").read()
    u = lambda o: struct.unpack_from("<I", b, o)[0]
    w("   %-14s ★**原样拷贝**（不重编）：%d B  format=%d(应31) @17=%d(应1) mips=%d  ＜- %s" %
      (nm, len(b), u(36), u(68), u(20), src))
for nm, orig, solid in SRC:
    if nm in COPY_TEX:
        continue
    srcp = os.path.join(KEEP, "Y3_" + nm + ".png")
    if not os.path.exists(srcp):
        continue
    subprocess.run([TEXCONV, "-f", "BC7_UNORM", "-y", "-o", KEEP, srcp],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
    cand = os.path.join(KEEP, "Y3_" + nm + ".dds")
    if not os.path.exists(cand):
        w("   !! texconv 失败 %s" % nm)
        continue
    data, x, y, mips = build_tex(TEMPLATE, cand)
    dst = os.path.join(PKG, nm + ".tex")
    open(dst, "wb").write(data)
    b = open(dst, "rb").read()
    fmt = struct.unpack_from("<I", b, 36)[0]
    ok_len = 184 + 8 * mips + sum(mip_sizes(x, y, mips, BLK)) == len(b)
    ss = all(struct.unpack_from("<I", b, o)[0] == packed_width(x) for o in (124, 136, 148))
    same = b[184 + 8 * mips:] == dds_parts(cand)[3]
    w("   %-14s %dx%d mip%-2d %6.2f MB  format=%d(应31) @17=%d(应1) @31=@34=@37 一致=%s 长度=%s 载荷逐字节=%s" %
      (nm, x, y, mips, len(b) / 1048576, fmt, struct.unpack_from("<I", b, 68)[0], ss, ok_len, same))

w("")
w("### ④ 定标用亮度（alpha>=250 区均值，即画出来的内容）")
for nm in rep:
    w("   %-14s alpha>=250 区 RGB 均值 %6.1f ⇒ 0~1 = %.3f" %
      (nm, rep[nm]["alpha255_mean"], rep[nm]["bright_alpha255"]))
w("   [参照] 用户明确认可过的两档：v1 军装 4.0×0.52 = 2.08 ；花瓣裙 0.93×2.35 = 2.19")
w("   [判据] 等效发光 = EmiF × 面料亮度（**UV 覆盖区**口径，见 X8_面料亮度定标.py）")
w("   ★ 本版决定：**沿用已验收的同一档配方 Base 0.30 / EmiF 2.35 / fSpecular 1.0**，")
w("     只换贴图（单变量）。等效发光由 X8 的实测亮度直接算出（见 _X8_面料亮度.txt）。")
w("WROTE " + OUT)

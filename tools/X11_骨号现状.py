# -*- coding: utf-8 -*-
"""X11_骨号现状.py —— 只读。<工作 blend> 里 4 副骨架的：
 ① 每副骨架的骨数 + MhBone 号区间 + 空闲号（0~255 内本骨架未用）
 ② 链骨段（号≥150）逐根：名字/父级/head/tail/是否被网格顶点组引用
 ③ 关键身体骨（Hips/Spine/Chest/Head/Shoulder/Upper_arm 等）的**名字→号**映射，
    供链根挂靠用（我们要把链根挂到 Hips / Head / 手臂骨上）
 ④ 各部位网格已引用的顶点组骨名集合（判断哪些链骨"已经在用"）
用法: blender -b <工作.blend> --python X11_骨号现状.py -- <输出txt>
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
import numpy as np

argv = sys.argv
args = argv[argv.index("--") + 1:]
OUT = args[0]
L = []


def w(s=""):
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(str(s).encode("gbk", "replace").decode("gbk", "replace"), flush=True)
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


ARMS = ["f_body040_0010 Armature", "f_arm040_0010 Armature",
        "f_leg040_0010 Armature", "f_wst040_0010 Armature"]

# 各部位网格引用的顶点组
used_by = {}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    for g in o.vertex_groups:
        used_by.setdefault(g.name, set()).add(o.name)

for an in ARMS:
    a = bpy.data.objects.get(an)
    if a is None:
        w("!! 没有骨架 %s" % an)
        continue
    bones = a.data.bones
    nums = {}
    for b in bones:
        if b.name.startswith("MhBone_"):
            try:
                nums[int(b.name.split("_")[1])] = b
            except ValueError:
                pass
    w("")
    w("=" * 104)
    w("### %s ：骨 %d 根；MhBone 号 %d 个，区间 %d~%d" %
      (an, len(bones), len(nums), min(nums), max(nums)))
    w("=" * 104)
    free = [i for i in range(256) if i not in nums]
    rng, st = [], free[0]
    for x, y in zip(free, free[1:] + [None]):
        if y is None or y != x + 1:
            rng.append(str(st) if st == x else "%d-%d" % (st, x))
            st = y
    w("   本骨架空闲号（%d 个）：%s" % (len(free), ",".join(rng)))
    w("")
    w("   -- 号>=150 的链骨 --")
    w("   %-14s %-14s %8s %8s %8s %8s   %s" % ("名字", "父级", "head x", "head y", "head z", "长度", "被哪些网格引用"))
    for k in sorted(nums):
        if k < 150:
            continue
        b = nums[k]
        h = a.matrix_world @ b.head_local
        users = sorted(used_by.get(b.name, []))
        w("   %-14s %-14s %8.4f %8.4f %8.4f %8.4f   %s" %
          (b.name, b.parent.name if b.parent else "-", h.x, h.y, h.z, b.length,
           (",".join(users)[:60] if users else "（无）")))
    w("")
    w("   -- 号 0~149 的名字（找身体骨，供链根挂靠）--")
    for k in sorted(nums):
        if k >= 150:
            continue
        b = nums[k]
        h = a.matrix_world @ b.head_local
        w("      %-14s 父=%-14s head=(%+.4f,%+.4f,%+.4f)" %
          (b.name, b.parent.name if b.parent else "-", h.x, h.y, h.z))
    # 非 MhBone 名字的骨
    odd = [b.name for b in bones if not b.name.startswith("MhBone_")]
    if odd:
        w("")
        w("   -- 非 MhBone_ 命名的骨（%d）：%s" % (len(odd), odd[:20]))

w("")
w("### 全局：网格引用的顶点组名（排除骨架骨名后应是空的）")
allg = sorted(used_by.keys())
w("   共 %d 个顶点组名" % len(allg))
w("   " + ", ".join(allg[:80]))
w("WROTE " + OUT)

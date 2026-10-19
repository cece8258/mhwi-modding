# -*- coding: utf-8 -*-
"""Z0_改写路径.py（第7版）—— 把从 第6版/project 拷来的脚本里的工程路径批量改成 第7版/project。
★ 只改"工程目录"这一种路径（`<根目录名>\\\\N\\\\project`）；`<根目录名>\\\\1\\\\preview2`、`<根目录名>\\\\2\\\\素材` 等
  参考模组/素材源保持不动。
★ 保留原编码（utf-8）与换行不动，只做字符串替换。幂等。
用法： python Z0_改写路径.py [--check]
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


import io, os, glob, sys

BASE = PROJ
BS = "\\"
TGT = "7"                      # ← 目标版本号
ROOT_NAME = "proj"             # ← 你的工程根目录名（脚本里写成 <根目录名>\<版本>\project）
PAIRS = []
for _old in ("6", "5", "4", "3", "2"):
    PAIRS.append((ROOT_NAME + BS + _old + BS + "project", ROOT_NAME + BS + TGT + BS + "project"))
    PAIRS.append((ROOT_NAME + "/" + _old + "/project", ROOT_NAME + "/" + TGT + "/project"))
    PAIRS.append((ROOT_NAME + BS * 2 + _old + BS * 2 + "project", ROOT_NAME + BS * 2 + TGT + BS * 2 + "project"))

CHECK = "--check" in sys.argv
files = sorted(glob.glob(os.path.join(BASE, "*.py"))) + sorted(glob.glob(os.path.join(BASE, "*.sh")))
n_file = n_rep = 0
for p in files:
    if os.path.basename(p) == "Z0_改写路径.py":
        continue
    s = io.open(p, encoding="utf-8", errors="replace").read()
    o = s
    for a, b in PAIRS:
        c = s.count(a)
        if c:
            s = s.replace(a, b)
            n_rep += c
    if s != o:
        if not CHECK:
            io.open(p, "w", encoding="utf-8", newline="").write(s)
        n_file += 1
        print("  改: %s" % os.path.basename(p))
print("改写了 %d 个脚本，共 %d 处路径%s" % (n_file, n_rep, "（--check 未落盘）" if CHECK else ""))

# 残留检查（只看前三条 = 真正的工程绝对路径）
bad = set()
for p in files:
    if os.path.basename(p) == "Z0_改写路径.py":
        continue
    s = io.open(p, encoding="utf-8", errors="replace").read()
    for a, _b in PAIRS[:3]:
        if a in s:
            bad.add(os.path.basename(p))
print("残留 第6版/project 的脚本：%s" % (sorted(bad) if bad else "无 ✓"))

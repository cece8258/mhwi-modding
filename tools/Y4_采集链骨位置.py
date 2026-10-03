# -*- coding: utf-8 -*-
"""Y4_采集链骨位置.py —— 只读。<工作副本.blend> 里把新链骨的**世界 head 位置**导出 JSON，
供 ctc 节点矩阵计算（节点方向 = 相邻节点位置之差）。
用法: blender -b <工作副本.blend> --python Y4_采集链骨位置.py -- <输出json>
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
OUT = args[0]
# ★ 第7版：所有新链骨在 206~234（body 206~234 / wst 206~207；arm 无新链）。
#   与 Y1 的 CHAIN_FNS 逐号一致（见 `_Y1_构建_*.txt` 的 [号] 行）。
RANGE = {"wst": list(range(206, 208)),                  # 本套兔尾 2 节点（206~207）
         "body": list(range(206, 235)),                 # 双马尾 2x5 + 兔耳 3+2 + 包 2 + 髋褶 4x2 + 颈饰 2x2
         "arm": []}                                     # arm 本版**不做链**
ARMS = {"wst": "f_wst040_0010 Armature", "body": "f_body040_0010 Armature",
        "arm": "f_arm040_0010 Armature"}
out = {}
for part, fn_list in RANGE.items():
    a = bpy.data.objects[ARMS[part]]
    mw = np.array(a.matrix_world)
    rec = {}
    for fn in fn_list:
        b = a.data.bones.get("MhBone_%03d" % fn)
        if b is None:
            print("!! %s 缺 MhBone_%03d" % (part, fn))
            continue
        h = mw[:3, :3] @ np.array(b.head_local) + mw[:3, 3]
        rec["%03d" % fn] = [float(x) for x in h]
    out[part] = rec
    # ★ 额外：把该骨架**全部**骨的世界 head 也存一份（Z4 造腿部碰撞体要用 014/015/018/019）
    allb = {}
    for b in a.data.bones:
        h = mw[:3, :3] @ np.array(b.head_local) + mw[:3, 3]
        allb[b.name] = [float(x) for x in h]
    out[part + "_all"] = allb
    print("%s: %d 根链骨位置（另存全骨 %d）" % (part, len(rec), len(allb)))
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print("WROTE " + OUT)

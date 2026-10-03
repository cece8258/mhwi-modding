# -*- coding: utf-8 -*-
"""
C33 · 打包成品 zip（唯一入口，以后都走这里，不再在 C10 里内联打包）
=================================================================
规则：
  · 排除备份/临时文件（*.bak*、Thumbs.db、*.blend1、desktop.ini）—— 游戏用不到，
    但工程目录里保留着，随时能回退
  · 打包前先跑一遍 C32（只看模式），如果有人手动往 nativePC 里塞了"没被任何
    活槽引用的贴图"，就大声提醒
  · 版本号自动取现有 试验N.zip 的最大 N + 1（同版本号重复安装会失败）

用法: python C33_打包zip.py [名字]
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


import os
import re
import sys
import glob
import time
import zipfile
import subprocess

PROJ = PROJ
PKG = os.path.join(PROJ, "05_导出成品")
NATIVEPC = os.path.join(PKG, "nativePC")
JUNK = (".bak", "thumbs.db", ".blend1", "desktop.ini")


def next_zipname():
    n = 1
    for f in glob.glob(os.path.join(PKG, "试验[0-9]*.zip")):
        m = re.match(r"试验(\d+)", os.path.basename(f))
        if m:
            n = max(n, int(m.group(1)) + 1)
    return os.path.join(PKG, "试验%d.zip" % n)


def main():
    t0 = time.time()
    print("=" * 100)
    print("### C33 · 打包成品 zip")
    print("=" * 100)

    # ---- 1. 先自检：nativePC 里有没有"没人引用"的贴图 ----
    try:
        p = subprocess.run([sys.executable, os.path.join(PROJ, "C32_精简成品包.py")],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=PROJ)
        out = (p.stdout or "") + (p.stderr or "")
        for line in out.splitlines():
            if "可以减掉" in line or "nativePC 现在" in line:
                print("   [自检] " + line.strip())
        m = re.search(r"包内总计可减掉 ([\d.]+) MB", out)
        if m and float(m.group(1)) > 0.5:
            print("   !! 包里还有 %.1f MB 无用资源，建议先跑:  python C32_精简成品包.py apply"
                  % float(m.group(1)))
    except Exception as e:
        print("   [自检] 跳过（%s）" % e)

    # ---- 2. 打包 ----
    if not os.path.isdir(NATIVEPC):
        print("!! 找不到 %s" % NATIVEPC); return
    zname = sys.argv[1] if len(sys.argv) > 1 else next_zipname()
    if not os.path.isabs(zname):
        zname = os.path.join(PKG, zname)
    n_all = n_skip = 0
    tex, others = [], 0
    with zipfile.ZipFile(zname, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, _, files in os.walk(NATIVEPC):
            for f in files:
                full = os.path.join(root, f)
                if any(x in f.lower() for x in JUNK):
                    n_skip += 1
                    continue
                z.write(full, os.path.relpath(full, NATIVEPC))
                n_all += 1
                if f.lower().endswith(".tex"):
                    tex.append((os.path.relpath(full, NATIVEPC), os.path.getsize(full)))
                else:
                    others += 1
    print("")
    print("排除备份/临时文件 %d 个" % n_skip)
    print("打包 %d 个文件（贴图 %d 张，其它 %d 个）" % (n_all, len(tex), others))
    for rel, sz in sorted(tex):
        print("      %-44s %8.1f MB" % (rel, sz / 1048576))
    print("")
    print("-> %s   %.1f MB   （%.1f 秒）" % (zname, os.path.getsize(zname) / 1048576,
                                             time.time() - t0))
    print("=" * 100)


main()

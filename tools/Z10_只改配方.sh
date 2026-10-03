#!/bin/bash
# Z10_只改配方.sh —— 只重写材质配方（Y3 + O2）+ 重打包，约 20 秒。迭代观感用。
# 用法: bash Z10_只改配方.sh <已有包名> [base=.. emi=.. spec=..]
#   base = fBaseMapFactor（直射漫反射倍率，越大明暗越强）
#   emi  = fEmissiveMapFactor（自发光倍率，白贴图下 1.0 就已经"满亮"）
#   spec = fSpecular（高光倍率，0.3 = 几乎没反光，1.0 = 标准）
# ★ 只有带描边的包需要跑 O2；无描边包加 nooutline。
set -u
V="$1"; shift
OPTS="$*"
P="/d/blender project/第7版/project"
cd "$P" || exit 1
PYTHONIOENCODING=utf-8 python Y3_材质指向.py $OPTS || exit 1
if [[ "$OPTS" != *nooutline* ]]; then
  PYTHONIOENCODING=utf-8 python O2_描边材质.py || exit 1
fi
PYTHONIOENCODING=utf-8 python C33_打包zip.py "$V.zip" || exit 1
echo "=== [$V] 配方已更新（$OPTS）==="

#!/bin/bash
# Z9_出一版.sh —— 第7版（本套装 本套 天蓝 Sky Blue + 头发 头发素材 蓬蓬双马尾 Yellow）的一条完整流水线，
# 产出一个 zip。
# 用法: bash Z9_出一版.sh <zip名(不含.zip)> [开关...]
#   变体开关：nostock  nosuit          （v2 = 去掉 Stocking + Suit）
#             noheadband  nobunnytail  （v3 = 兔耳/兔尾换回原版）  配 origear / origtail
#             nogloves                 （v4 = 再去掉 Gloves）
#             nobag                    （★ 兜底：去掉 Bag；默认**保留**）
#             nooutline（不做描边）
#   物理开关：nochain / nohairchain / noearchain / nobagchain / nosuitchain / nochokerchain / notailchain
#   其他：    nobuttfix / nocrotchfix（跳过身体侧 Z26/Z27）  nocrotchstretch（跳过 Z34 裆部拉伸修正）
#             nopushout（全部不做穿模外推，对照用）  margin=<mm>（兜底外推余量）
# ★ 贴图（Y2_贴图烘焙与生成.py）是**一次性**的，本流水线不再重跑；
#   第 8b 步只删"本版确定用不到的上一版（第6版 本套）贴图"，删完必须重跑 Z14。
set -u
V="$1"; shift
OPTS="$*"
MAIN_BLEND="${MAIN_BLEND:-主工程副本.blend}"    # 主工程 = 你的工作 blend（拷一份当副本用）
BL="${BLENDER:-/d/blender.exe}"
P="/d/blender project/第7版/project"
cd "$P" || exit 1
LOG="_Z9_${V}.log"
: > "$LOG"

echo "=== [$V] 选项：$OPTS ===" | tee -a "$LOG"

echo "--- 1/10 从主文件复制工作副本" | tee -a "$LOG"
cp "$MAIN_BLEND" "_p_work.blend" || exit 1

echo "--- 2/10 Y1 构建（含选项 $OPTS）" | tee -a "$LOG"
PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Y1_构建.py -- \
  "$P/_X3_preview.json" "$P/_Y1_构建_${V}.txt" $OPTS >> "$LOG" 2>&1
# ★ 哨兵：Blender 脚本抛异常时退出码仍是 0，必须查它有没有把报告写出来
grep -q "SAVED" "$P/_Y1_构建_${V}.txt" || { echo "!! Y1 没跑完（见 $LOG）"; exit 1; }

echo "--- 3/10 Y11 补回手指修复权重（必须在导出前）" | tee -a "$LOG"
PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Y11_施加54权重.py >> "$LOG" 2>&1
grep -q "SAVED" "$P/_Y11_施加54.txt" || { echo "!! Y11 没跑完（见 $LOG）"; exit 1; }

if [[ "$OPTS" == *nobuttfix* ]]; then
  echo "--- 4/10 跳过 Z26（臀部左右甩）" | tee -a "$LOG"
else
  echo "--- 4/10 Z26 修臀部左右甩" | tee -a "$LOG"
  PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Z26_修臀部左右甩.py -- \
    "$P/_Z26_臀部_${V}.txt" >> "$LOG" 2>&1
  grep -q "SAVED" "$P/_Z26_臀部_${V}.txt" || { echo "!! Z26 没跑完（见 $LOG）"; exit 1; }
fi

if [[ "$OPTS" == *nocrotchfix* ]]; then
  echo "--- 4b/10 跳过 Z27（裆部硬跳）" | tee -a "$LOG"
else
  echo "--- 4b/10 Z27 修裆部（腿权重让给骨盆）" | tee -a "$LOG"
  PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Z27_修裆部.py -- \
    "$P/_Z27_裆部_${V}.txt" >> "$LOG" 2>&1
  grep -q "SAVED" "$P/_Z27_裆部_${V}.txt" || { echo "!! Z27 没跑完（见 $LOG）"; exit 1; }
fi

echo "--- 4c/10 Z31 修脚踝权重（身体侧：腿部权重按高度抹平）" | tee -a "$LOG"
PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Z31_修脚踝权重.py -- \
  "$P/_Z31_脚踝_${V}.txt" >> "$LOG" 2>&1
grep -q "SAVED" "$P/_Z31_脚踝_${V}.txt" || { echo "!! Z31 没跑完（见 $LOG）"; exit 1; }

echo "--- 4d/10 Z33 修胯/大腿上部/裆底的 Hips↔腿 分配（★ 必须在衣物对齐之前）" | tee -a "$LOG"
PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Z33_修胯与裆部权重.py -- \
  "$P/_Z33_胯部权重_${V}.txt" >> "$LOG" 2>&1
grep -q "SAVED" "$P/_Z33_胯部权重_${V}.txt" || { echo "!! Z33 没跑完（见 $LOG）"; exit 1; }

if [[ "$OPTS" == *nocrotchstretch* ]]; then
  echo "--- 4e/10 跳过 Z34（裆部拉伸修正）" | tee -a "$LOG"
else
  echo "--- 4e/10 Z34 修裆/大腿内侧拉伸（身体侧：腿权重让给骨盆；★ 必须在 Z32 之前）" | tee -a "$LOG"
  PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Z34_修裆部拉伸.py -- \
    "$P/_Z34_裆部拉伸_${V}.txt" >> "$LOG" 2>&1
  grep -q "SAVED" "$P/_Z34_裆部拉伸_${V}.txt" || { echo "!! Z34 没跑完（见 $LOG）"; exit 1; }
fi

echo "--- 5/10 Z32 贴身衣物权重对齐身体（★ 必须在所有改身体权重的步骤之后）" | tee -a "$LOG"
PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Z32_衣物权重对齐身体.py -- \
  "$P/_Z32_权重对齐_${V}.txt" >> "$LOG" 2>&1
grep -q "SAVED" "$P/_Z32_权重对齐_${V}.txt" || { echo "!! Z32 没跑完（见 $LOG）"; exit 1; }

echo "--- 6/10 Y4 采集链骨位置" | tee -a "$LOG"
PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python Y4_采集链骨位置.py -- \
  "$P/_Y4_链骨位置.json" >> "$LOG" 2>&1
test -f "$P/_Y4_链骨位置.json" || { echo "!! Y4 没产出 JSON"; exit 1; }

echo "--- 7/10 B7 导出 4 个 mod3" | tee -a "$LOG"
PYTHONIOENCODING=utf-8 "$BL" -b "_p_work.blend" --python B7_导出mod3.py >> "$LOG" 2>&1
grep -q "成功导出 4 / 4" "$LOG" || { echo "!! 导出未 4/4，见 $LOG"; exit 1; }

echo "--- 8/10 换入成品树 + ctc 物理链" | tee -a "$LOG"
for p in body arm wst leg; do
  cp "_mod3/f_${p}040_0010.mod3" "05_导出成品/nativePC/pl/f_equip/pl040_0010/$p/mod/f_${p}040_0010.mod3" || exit 1
done
PYTHONIOENCODING=utf-8 python Y4b_物理ctc.py >> "$LOG" 2>&1 || { echo "Y4b 失败"; exit 1; }

echo "--- 8b/10 删掉上一版（第6版 本套）遗留的、本版确定用不到的贴图" | tee -a "$LOG"
# ★ 不能删 MiliCuteNavy / ribbon_black：它们还被 mrl3 里**活材质**的 tFurMap / tPanoramaMap
#   资源项指着（Z14 反向检查会报洞）—— 与 第3版~第6版 的处置一致，留着。
# ★ 不能写 `Hair`：Windows 文件系统**大小写不敏感** ⇒ `rm Hair.tex` 会把本版的 `HAIR.tex` 一起删掉
#   （第一次出 v1 时就是这么踩的：Z14 报 `Ch_Standard_Mt__12.tAlbedoMap -> 贴图目录名/HAIR.tex` 缺）。
# ★ `ExtraHair.tex` 只服务 v3/v4（`origear`/`origtail` 保留原版耳/尾时，基壳 `Ch_Standard_Mt__3` 变活）
#   ⇒ v1/v2 把它删掉省 21 MB。
# ★ 删完**必须重跑 Z14**（"0 个洞"才算过）。
for t in PrevA PrevB PrevC PrevD PrevE PrevF \
         PrevMetal PrevFur PrevJewel PrevHairA PrevHairB \
         Sock候选A SockBody Sock候选C SilverSocks SilverBody; do
  rm -f "05_导出成品/nativePC/贴图目录名/$t.tex"
done
case "$OPTS" in
  *origear*|*origtail*)
    # ★ v3/v4 保留原版耳/尾 ⇒ 基壳 `Ch_Standard_Mt__3` 变活，必须补上这张图
    #   （`素材/ExtraHair.tex` = 第1版 那张 `Hair.tex` 的原样拷贝，与 第5版 逐字节相同）
    # ★ 若要保留原版耳 / 尾：请**自备**那张耳尾贴图（本仓库不含任何贴图），
    #   设好 EXTRA_HAIR 环境变量后，取消下面这行注释即可
    # cp "$EXTRA_HAIR" "05_导出成品/nativePC/贴图目录名/ExtraHair.tex"
    echo "      + 若自备了 EXTRA_HAIR，则补上 ExtraHair.tex（v3/v4 的原版耳/尾要用）" | tee -a "$LOG" ;;
  *)
    rm -f "05_导出成品/nativePC/贴图目录名/ExtraHair.tex"    # 本版用不到（省 21MB）
    echo "      - 删掉 ExtraHair.tex（本版无原版耳/尾，省 21MB）" | tee -a "$LOG" ;;
esac
ls "05_导出成品/nativePC/贴图目录名/"*.tex | while read f; do echo "      $(basename "$f")"; done >> "$LOG"

echo "--- 9/10 mrl3 指向 + 描边材质 + 打包" | tee -a "$LOG"
PYTHONIOENCODING=utf-8 python Y3_材质指向.py $OPTS >> "$LOG" 2>&1 || { echo "Y3 失败"; exit 1; }
# ★ 顺序铁律：O2 必须在 Y3 **之后**（Y3 每次从 .bak_y3 重算，跑在它前面会被覆盖）
case "$OPTS" in
  *nooutline*)
    echo "      - 跳过 O2（本版无描边）" | tee -a "$LOG" ;;
  *)
    echo "      + O2 描边材质 Outline_Black（复用死条目 Ch_Standard_Mt__4）" | tee -a "$LOG"
    PYTHONIOENCODING=utf-8 python O2_描边材质.py >> "$LOG" 2>&1 || { echo "O2 失败"; exit 1; } ;;
esac
PYTHONIOENCODING=utf-8 python C33_打包zip.py "$V.zip" >> "$LOG" 2>&1 || { echo "打包失败"; exit 1; }

echo "--- 10/10 本版成品树快照（否则旧包无法再逐字节复核）" | tee -a "$LOG"
mkdir -p "_snap_${V}"
for p2 in body arm wst leg; do
  d2="05_导出成品/nativePC/pl/f_equip/pl040_0010/$p2/mod"
  cp "$d2/f_${p2}040_0010.mod3" "$d2/f_${p2}040_0010.ctc" "$d2/f_${p2}040_0010.mrl3" "_snap_${V}/" 2>/dev/null
done
tail -6 "$LOG" | grep -E "^->|打包 |排除" || true
echo "=== [$V] 完成 ===" | tee -a "$LOG"

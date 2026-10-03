# MHWI 模组制作：笔记 + 流水线工具

《怪物猎人世界：冰原》**玩家模型替换模组**（`pl040_0010`）的制作笔记与一套可复用的 Blender 脚本。
内容是"借壳移植一套服装 / 头发"全流程里踩出来的东西：格式反解、权重对齐、材质指向、物理链、描边、反向验收。

> **本仓库只有文本与代码。**
> 不含任何游戏本体文件（`mod3` / `mrl3` / `ctc` / `ccl` / `tex`）、不含任何第三方素材、
> 也不含任何他人的模组文件。缘由与发布边界见 [NOTICE.md](NOTICE.md)。

---

## 目录

```
skills/
  mhwi-blender-modding/SKILL.md   制作全流程：借壳、权重传递、二进制打补丁、材质观感、描边、踩坑清单
  mhwi-mod-anatomy/SKILL.md       解剖陌生模组：.tex / mrl3 / mod3 的字段实测、样本普查口径、判据陷阱
tools/                            可复用脚本（Python + Blender + bash），见下
```

两份 `SKILL.md` 各自带一份 `改动清单.md` —— 记录"为了公开发布做了什么中性化处理"，方便对照。

## tools/ 是什么

一条可重跑的流水线：**采集 → 构建（搬件/建链/拆件/描边壳）→ 贴图烘焙与 `.tex` 编码 → mrl3 指向 →
ctc 物理链 → 导出 → 打包 → 从 zip 反向验收**，外加 7 个权重脚本与 3 个诊断脚本。

依赖：**Blender 4.2 LTS** + [MHW_Model_Editor](https://github.com/chikichikibangbang/MHW_Model_Editor) 插件
（唯一必需插件）+ `texconv`（DirectXTex）+ 纯 Python 部分的 `numpy` / `Pillow`。

用法：先改 `tools/_config.py`（**所有路径都集中在那一个文件**），然后

```bash
cd tools
bash Z9_出一版.sh 我的包名 [开关...]
```

各步的作用、顺序、以及"顺序为什么不能换"都写在 `Z9_出一版.sh` 与每个脚本的文件头里。

## 两条笔记里最值得先看的

1. **`mhwi-mod-anatomy/SKILL.md` 的"可信度分级"** —— 哪些结论是几百张样本背书的（可以直接抄），
   哪些只是"存在这种写法"（只能当参考）。这份笔记里所有数字都注明了样本量。
2. **`mhwi-blender-modding/SKILL.md` 的"最贵的一条教训"与"判据事故"几节** ——
   症状治不好时，**先造一个能区分假设的测量**，并且**先标定你的判据回路**
   （故意做一个必然可见的改动，确认度量会变），比继续按"听起来合理"的猜测动手快得多。

## 许可

代码与笔记：**MIT**，见 [LICENSE](LICENSE)。
使用前请读 [NOTICE.md](NOTICE.md) —— 尤其是"借壳 = 你的发布包会带上壳作者的派生二进制文件"这一条。

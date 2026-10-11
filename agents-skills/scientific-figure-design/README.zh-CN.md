# Scientific Figure Design

**让 Agent 能生成、让研究者仍然能修改的科研插图。**

[English](README.md) · [案例](examples/README.md) ·
[学术审美规范](references/academic-aesthetics.md) ·
[论文配色系统](references/paper-color-system.md)

Scientific Figure Design 是一个可开源复用的 Agent Skill 和确定性绘图工具链：
它把论文中的研究主张转化为可编辑的 Draw.io 源文件，并导出适合论文排版的
SVG、PDF 与 300 dpi PNG。

它主要解决生成式科研绘图中的两个问题：

- Agent 直接生成的位图难以修改，标签、连线、拓扑和配色无法稳定迭代；
- 看起来“像图”的图片不一定满足论文对字体、线宽、矢量质量、可复现性和
  跨图一致性的要求。

在本项目中，`.drawio` 是可编辑的源文件，SVG/PDF 是论文使用的矢量母版，
PNG 只用于审阅和预览。

![可编辑的 Kernel Agent 科研插图](examples/kernel-agent-loop/preview.png)

## 包含内容

- 完整的 [`scientific-figure-design` Skill](SKILL.md)；
- 先写 Figure Contract、再绘图的科研表达流程；
- 强制执行的字体、字号、线宽、布局、色彩和图标审美规范；
- 一篇论文共用一份配色合同，并自动检查 Figure 1–N 是否发生颜色漂移；
- 从结构化 JSON 生成可编辑 Draw.io 的桥接工具；
- **581 个 SVG 科研图标**，支持语义搜索、重着色、来源追踪和校验；
- 基于 arXiv HTML 的论文图片、caption、alt text 和上下文下载整理；
- SVG/PDF/300 dpi PNG 导出与严格质量门禁；
- 来自 [KerSor](https://github.com/qhy991/KerSor) 和
  [Agents-Native-Engine](https://github.com/qhy991/Agents-Native-Engine)
  的真实可编辑案例。

## 端到端流程

```text
研究主张
  → Figure Contract
  → 全文统一配色
  → 语义图标检索
  → 结构化 Figure Spec
  → 可编辑 .drawio
  → 严格校验
  → .svg + .pdf + 300 dpi .png
```

每个图标都会以矢量形式嵌入 Draw.io，同时生成 `.icons.json` 来源清单。
因此研究者可以在 Draw.io 中继续调整节点、字体、连线、颜色和布局，而不是
重新生成一张不可控的位图。

## 快速开始

核心构建器和校验器只依赖 Python 3.10+ 标准库。

```bash
git clone https://github.com/qhy991/Scientific-Figure-Design.git
cd Scientific-Figure-Design

cp assets/drawio-system-overview.json figure-spec.json
cp assets/paper-palette.yaml paper-palette.yaml

# 正式出图前填写 paper_id、palette_id，并将 status 改为 frozen。
python3 scripts/build_drawio_figure.py figure-spec.json \
  --paper-palette paper-palette.yaml \
  --out figure.drawio

python3 scripts/validate_drawio_figure.py figure.drawio \
  --paper-palette paper-palette.yaml --strict
```

工具会自动使用仓库内置图标库，无需额外安装 `paper-icons`。如需覆盖，才传入
`--paper-icons-skill /path/to/paper-icons`。

安装 Draw.io Desktop CLI 后可以导出：

```bash
python3 scripts/export_drawio_figure.py figure.drawio --mode preview
python3 scripts/export_drawio_figure.py figure.drawio \
  --mode final --formats svg,pdf,png
```

如果一篇论文有多张 Draw.io 图片，使用同一配色文件统一检查：

```bash
python3 scripts/validate_paper_palette.py \
  --palette paper-palette.yaml figures/*.drawio --strict
```

## 安装为 Agent Skill

```bash
git clone https://github.com/qhy991/Scientific-Figure-Design.git \
  ~/.agents/skills/scientific-figure-design
```

之后让 Agent 使用 `scientific-figure-design`。它支持四类任务：

1. 从 arXiv HTML 下载、整理论文图片；
2. 分析相关工作的构图、视觉语言和常见问题；
3. 从研究主张设计并制作可编辑科研插图；
4. 重绘、导出或审计已有的整套论文图片。

## 学术审美是约束，不是装饰

项目内置的主要限制包括：

- 单栏按约 85 mm、双栏按约 178 mm 的最终尺寸设计；
- 主要文字优先 8–9 pt，任何文字不得低于 7 pt；
- 一张图最多三种可见字号、两种字体族；
- 普通线条约 0.8–1.4 pt；
- 三到五种语义色，加一套中性色；
- 禁止装饰性渐变、发光、玻璃、浮雕和阴影；
- 同一方法、基线、成功/失败状态在 Figure 1–N 中保持同一语义；
- 红/绿状态必须同时使用文字、形状、图标或线型作为冗余编码；
- 图标必须是矢量、可追溯且保持统一视觉家族。

完整规范见
[`references/academic-aesthetics.md`](references/academic-aesthetics.md)，
机器可读配置见
[`assets/academic-style.yaml`](assets/academic-style.yaml)。

## 一篇论文只使用一套配色合同

把 [`assets/paper-palette.yaml`](assets/paper-palette.yaml) 复制到论文项目中，
一次性确定 `ours`、重复出现的 baseline、理论上界、成功和失败颜色，然后冻结。
Draw.io 源文件会绑定 palette ID 和 SHA-256；如果后续某张图偷偷更换颜色，
严格校验会直接失败。

这能避免常见问题：同一个方法在架构图里是蓝色，在柱状图里变成橙色；同一种
红色在一张图表示失败，在另一张图又表示本文方法。

## 581 个图标全部内置

| 图标族 | 数量 | 许可或状态 |
| --- | ---: | --- |
| Lucide | 177 | ISC |
| Tabler | 131 | MIT |
| Phosphor | 114 | MIT |
| Phosphor duotone | 51 | MIT |
| Lobe 品牌图标 | 39 | SVG 代码为 MIT；商标权仍归品牌所有者 |
| 按需获取的 Lucide | 32 | ISC |
| 项目原创科研图标 | 37 | 本仓库 MIT |
| **合计** | **581** | |

搜索示例：

```bash
python3 assets/paper-icons/scripts/search_icons.py \
  "retrieval database" --limit 8
```

一张图一般只选择一个通用图标族。品牌图标只用于准确说明实际使用的产品、
模型、框架或厂商，必须保留官方配色，不得暗示品牌背书；不必要时优先使用
中性文字或通用图标。许可说明见
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## arXiv 图片下载整理

项目优先读取 arXiv HTML，因为 HTML 能保留 figure 分组、caption、子图、
alt text、原始资源链接和正文上下文：

```bash
python3 scripts/collect_arxiv_figures.py \
  --readme path/to/paper-list.md \
  --output-dir path/to/corpus \
  --workers 4
```

下载需要 `requests` 与 `beautifulsoup4`；统计与 contact sheet 还需要 Pillow
和 CairoSVG。

## 案例

| 案例 | 可编辑源文件 | 矢量母版 | 设计目的 |
| --- | --- | --- | --- |
| Kernel Agent 闭环 | [Draw.io](examples/kernel-agent-loop/figure.drawio) | [SVG](examples/kernel-agent-loop/figure.svg) | 端到端自动生成流程 |
| KerSor motivated example | [Draw.io](examples/kersor-motivated-example/figure.drawio) | [SVG](examples/kersor-motivated-example/figure.svg) | before/after 证据迁移 |
| KerSor control state | [Draw.io](examples/kersor-control-state/figure.drawio) | [SVG](examples/kersor-control-state/figure.svg) | 拓扑、控制状态与经验先验 |
| Agent-native engine | [Draw.io](examples/agent-native-engine/figure.drawio) | [SVG](examples/agent-native-engine/figure.svg) | 问题动机与系统底座 |

详细来源和设计解读见 [`examples/README.md`](examples/README.md)。

## 开发与贡献

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py tests/*.py
ruff check scripts tests
```

欢迎贡献新的 Figure Contract、可编辑案例、绘图约束和图标。新增案例必须提交
可编辑源文件；新增图标必须具有明确的宽松许可证和机器可读来源。详见
[`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 许可证

本仓库原创内容采用 [MIT License](LICENSE)。第三方图标继续使用各自的
ISC/MIT 许可证；品牌名称和 Logo 的商标权仍归各自所有者。

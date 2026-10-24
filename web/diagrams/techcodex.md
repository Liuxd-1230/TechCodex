<!-- diagram-design-profile
name: TechCodex
slug: techcodex
source-url: https://liuxd-1230.github.io/TechCodex/
created: 2026-10-23
updated: 2026-10-24
notes: TechCodex colors, system Chinese fonts, and teaching diagrams
-->
# Style Guide

This project profile adapts Diagram Design to TechCodex. `DESIGN.md` is authoritative for the reading site's identity; this file supplies the color and type roles for conceptual diagrams. Preserve scientific colors and branch meanings.

---

## Tokens

### Semantic roles

Use these roles in diagram references and type specifications. The dark values are available only for an explicitly dark diagram variant; they do not imply a dark-mode reading site.

| Role | Purpose | TechCodex light | Diagram dark variant |
|---|---|---|---|
| `paper` | Page background and default node fill | `#ffffff` | `#173c50` |
| `paper-2` | Secondary surface | `#eff4f8` | `#21485a` |
| `ink` | Primary text and stroke | `#173c50` | `#eff4f8` |
| `ink-strong` | High-contrast text | `#173c50` | `#173c50` |
| `muted` | Supporting text and default arrows | `#566976` | `#bacbd4` |
| `soft` | Secondary labels and boundaries | `#526974` | `#bacbd4` |
| `rule` | Hairline borders | `#d5e0e8` | `#526974` |
| `rule-solid` | Strong borders and baselines | `#566976` | `#bacbd4` |
| `accent` | Teal causal emphasis | `#126e63` | `#80cbb9` |
| `accent-tint` | Pale teal explanatory fill | `#f2f8f5` | `#214c49` |
| `link` | Scientific blue and linked relationships | `#315bc5` | `#a3baff` |

### Color use

Ink and teal establish the book identity; spectral blue identifies selected regions and frequency evidence. Flicker amber is reserved for material whose meaning is already flicker-related. Pair scientific color with a label and preserve its meaning in comparisons. Do not force a one-accent rule onto plots or circuit branches that need distinct scientific colors.

---

## Typography

| Role | Family | Size | Weight | Usage |
|---|---|---|---|---|
| `title` | "Noto Serif SC","Source Han Serif SC","Songti SC","SimSun",serif | 1.75rem | 400 | Diagram title |
| `node-name` | "Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif | 13px | 600 | Main Chinese labels |
| `sublabel` | "Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif | 13px | 400 | Supporting Chinese labels; technical values may be smaller |
| `eyebrow` | "Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif | 13px | 500 | Short Chinese category labels |
| `arrow-label` | "Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif | 13px | 400 | Causal arrow annotations |
| `callout` | "Noto Serif SC","Source Han Serif SC","Songti SC","SimSun",serif | 14px | 400 | Short explanatory aside |

### Font stack

No font download. Use the Chinese system stacks above with their generic serif or sans fallback. Keep Chinese labels at least 13px; shorten a label or allow local diagram scrolling when it does not fit.

### Font source

Font source: `system`

---

## Stroke, radius, spacing

| Token | Value | Use |
|---|---|---|
| `stroke-thin` | `0.8` | Fine outlines |
| `stroke-default` | `1` | Most strokes |
| `stroke-strong` | `1.2` | Emphasis strokes |
| `radius-sm` | `4` | Small tags |
| `radius-md` | `6` | Node boxes |
| `radius-lg` | `8` | Containers and rings |
| `grid` | `4` | Diagram coordinates, sizes, and gaps |

## Node type → treatment

Use role combinations to distinguish causal function. Keep labels explicit so color does not carry meaning alone.

| Type | Fill | Stroke |
|---|---|---|
| `focal` | `accent-tint` | `accent` |
| `node` | `paper` | `ink` |
| `supporting` | `paper-2` | `rule-solid` |
| `input` | `paper-2` | `soft` |
| `output` | `paper` | `ink` |
| `optional` | `paper` | `muted` dashed `4,3` |

## Diagram forms

Use white paper, compact strokes, and restrained corners. Fit conceptual diagrams to a 320 SVG-unit canvas. Causal arrows show relationships, not electrical wiring, unless the image is explicitly a circuit schematic. Conceptual charge and current layers explain physics; they do not claim manufacturing geometry. On narrow screens, let the diagram viewport scroll locally instead of shrinking Chinese labels below 13px.

## TechCodex application

`DESIGN.md` remains authoritative. Preserve established circuit branch colors and scientific plot meanings; use this profile for conceptual teaching diagrams without implying a new site theme.

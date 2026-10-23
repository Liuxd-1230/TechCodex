---
name: "TechCodex · 从零开始的模电生活"
description: "A calm Chinese CMOS textbook whose circuit evidence and measured interactions support continuous reading."
colors:
  ink: "#173c50"
  title-ink: "#17394a"
  prose: "#253440"
  muted: "#566976"
  running-metadata: "#566f7d"
  caption: "#526974"
  current-teal: "#126e63"
  spectral-blue: "#315bc5"
  flicker-amber: "#9b5b18"
  paper: "#fff"
  margin: "#eff4f8"
  rule: "#d5e0e8"
  source-soft: "#eef3fa"
  teaching-note: "#f2f8f5"
  teaching-rule: "#c9ddd7"
  focus-on-ink: "#c9e8df"
  demo-border: "#bed0d8"
  demo-focus: "#327aa0"
typography:
  display:
    fontFamily: '"Noto Serif SC","Source Han Serif SC","Songti SC","SimSun",serif'
    fontSize: "2.65rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: ".02em"
  headline:
    fontFamily: '"Noto Serif SC","Source Han Serif SC","Songti SC","SimSun",serif'
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: ".02em"
  section:
    fontFamily: '"Noto Serif SC","Source Han Serif SC","Songti SC","SimSun",serif'
    fontSize: "1.27rem"
    fontWeight: 700
    letterSpacing: ".02em"
  subsection:
    fontFamily: '"Noto Serif SC","Source Han Serif SC","Songti SC","SimSun",serif'
    fontSize: "1.06rem"
    fontWeight: 700
    letterSpacing: ".02em"
  body:
    fontFamily: '"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif'
    fontSize: ".9rem"
    lineHeight: 1.95
    letterSpacing: ".01em"
  label:
    fontFamily: '"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif'
    fontSize: ".64rem"
    letterSpacing: ".06em"
  code:
    fontFamily: '"Cascadia Code","Consolas",monospace'
    fontSize: ".73rem"
    lineHeight: 1.65
  result:
    fontFamily: '"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif'
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "-.02em"
rounded:
  control-small: "3px"
  control: "4px"
  surface: "5px"
spacing:
  compact: ".4rem"
  control: ".6rem"
  inset: ".8rem"
  unit: "1rem"
  panel: "1.15rem"
  section-gap: "1.8rem"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: ".65rem .9rem"
  button-primary-hover:
    backgroundColor: "{colors.current-teal}"
  button-reset:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.current-teal}"
    rounded: "{rounded.control-small}"
    padding: ".4rem .6rem"
  nav-link:
    rounded: "{rounded.control}"
    padding: ".24rem .4rem"
  chapter-row:
    padding: "1rem .2rem"
  teaching-note:
    backgroundColor: "{colors.teaching-note}"
    textColor: "#334e5d"
    rounded: "{rounded.surface}"
    padding: ".35rem 1.15rem"
  source-select:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: ".4rem .6rem"
    height: "2.2rem"
  circuit-panel:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.surface}"
    padding: "1.15rem"
  noise-result:
    typography: "{typography.result}"
    padding: "1.1rem 0 1rem"
---

# Design System: TechCodex

## Overview

**Creative North Star: "The Circuit Reading Atlas"**

The existing ink-blue and current-teal book identity provides the frame for rigorous Chinese CMOS learning. White reading paper sits within cool margins; Chinese serif headings mark the chapter structure, while system sans prose carries long explanations. Actual curriculum numbers, circuit paths and scientific plots supply the visual character.

The system is quiet during reading and responsive during an experiment. Interaction supports a specific physical judgment: change a band, inspect its variance contribution and read one primary RMS result. The full chapter remains meaningful as Markdown, without scripts, and in print. This is an extension of the incumbent MkDocs Material reading world; no replacement identity or approved visual comp is implied.

**Key Characteristics:**

- Continuous reading on white paper within cool blue margins.
- Serif Chinese chapter hierarchy paired with system sans explanations.
- Actual chapter numbers, ruled atlas rows and a visible reading spine.
- Circuit and spectral evidence with explicit source identity.
- Native controls and brief, interruptible motion.

The normative primitives above are extracted from `web/assets/book.css` and `web/assets/demos/circuit-demo.css`. Components and behavior are evidenced by `web/home.html`, `web/overrides/main.html`, `web/demos/`, `web/assets/book.js` and `web/assets/demos/noise-band.js`. `mkdocs.yml` owns the native shell. This document and its sidecar are development references; `scripts/book.py` stages the reading site through an explicit source list.

## Colors

Ink and teal establish the book; spectral blue identifies the frequency-band evidence. Pale surfaces give supporting information a place without competing with the prose.

### Primary

- **Circuit Ink** (`ink`): masthead, footer, primary start action, key readings and spectral ASD line.
- **Current Teal** (`current-teal`): article links, control accents, current-path identity and primary-action hover.

### Secondary

- **Spectral Blue** (`spectral-blue`): selected frequency band, variance-density curve and article/navigation focus.
- **Flicker Amber** (`flicker-amber`): the declared book accent for flicker-related scientific material. The current interactive noise chart uses ink and blue; do not recolor it merely to consume this token. Older circuit diagrams retain their local branch amber.

### Neutral

- **Reading Paper / Cool Margin** (`paper`, `margin`): article and surrounding canvas.
- **Title Ink / Prose** (`title-ink`, `prose`): hierarchy and sustained body reading.
- **Muted / Running Metadata / Caption** (`muted`, `running-metadata`, `caption`): supporting text with distinct existing contexts.
- **Book Rule / Demo Border** (`rule`, `demo-border`): chapter boundaries, navigation structure and experiment containment.
- **Source Soft / Teaching Note / Teaching Rule** (`source-soft`, `teaching-note`, `teaching-rule`): data-source disclosure and explanatory observations.
- **Focus on Ink / Demo Focus** (`focus-on-ink`, `demo-focus`): visible keyboard focus on the dark header and inside legacy circuit experiments.

**The Evidence Color Rule.** Scientific color identifies a curve, branch or selected region; preserve its label and meaning when extending a figure.

**The Surface Focus Rule.** Use the pale focus outline on the ink header and the blue outline on the reading surface; retain the established demo-specific outline in circuit controls.

## Typography

**Display Font:** locally available Chinese serif stack from `display`, shared by chapter headings.

**Body Font:** locally available Chinese sans stack from `body`.

**Label/Mono Font:** labels use the body stack; code and circuit control outputs use the `code` family.

**Character:** Serif headings give chapters a book-like cadence. Sans prose and native controls keep the technical explanation direct. No external font download is required; the exact rendered face depends on the reader's installed fonts.

### Hierarchy

- **Display:** home title; the mobile override is (2.1rem).
- **Headline:** article title; the mobile override is (1.55rem).
- **Section:** major reasoning divisions; the mobile override is (1.15rem).
- **Subsection:** local derivations and explanations.
- **Body:** desktop reading uses the frontmatter role; mobile uses (.85rem), the same line height and no added letter spacing.
- **Label:** compact running-head metadata. Demo labels vary by function and remain subordinate to their headings.
- **Code:** preformatted examples use the recorded role; inline code is (.85em).
- **Result:** the principal noise result; mobile uses (1.6rem).

**The Reading and Measurement Rule.** Keep sustained prose in the sans reading face. Use tabular numerals for tables, controls and measured results; do not apply them as a general decorative treatment.

Math retains MathJax's own typography and horizontal overflow containment. Display equations are centered, with the existing small local size adjustment; do not replace them with images.

## Layout

The native Material shell holds navigation, search and contents around one white article. The outer grid is capped at (84rem); the inner reading region is capped at (46rem), centered with desktop padding (2.1rem 2.5rem 3.5rem). Paragraph leading and heading separation carry the reading rhythm. Figures occupy a full reading row, retain their aspect ratio and are capped in height (39rem).

At (70em) and above, the home opening and chapter atlas each become two columns. Below that point they remain one continuous sequence. Desktop sidebars receive their local widths at (76.25em); below (76.234em), article padding becomes (1.7rem 2rem 2.5rem) and the secondary running-head text is hidden.

At (44.984em) and below, article borders and corner rounding disappear into the viewport, article padding becomes (1.1rem 1rem 2rem), and typography steps down as described above. Navigation links have a minimum height (2.2rem), atlas rows (3.4rem). Circuit drawing and chart share columns only at (64em) and above. The two frequency-band controls stack on mobile; charts stay fluid and their labels grow within the SVG coordinate system.

**The Reading Spine Rule.** Keep native chapter navigation, contents, running chapter identity and the reading-progress line aligned with continuous article reading. Chapter numbers represent the actual curriculum sequence.

## Elevation & Depth

The article, notes and experiments use restrained borders and tonal layering. The masthead has one soft separating shadow (`0 2px 12px #173c5014`). Details and tables explicitly carry no shadow. Scientific evidence remains flat and readable; hover changes surface color.

The reading progress line is fixed below the header and scales horizontally with article position. It is hidden until the script initializes and does not conceal or gate the article.

## Shapes

Surfaces have gently softened corners: the frontmatter's surface radius applies to the article, teaching notes, details and experiments; controls use the smaller recorded radii. Rules, curve strokes and circuit geometry provide structure. The home atlas is a series of ruled links, and the noise preview is one tinted teaching entry with an inline vector spectrum.

## Components

### Buttons

The primary start action is a link with ink fill, white text and compact padding; hover changes it to teal. Reset buttons inside experiments use a white ground, teal text, a thin pale border and the small control radius. Preserve native button/link semantics and visible focus.

### Inputs / Fields

Radio buttons and sliders remain native, with teal accents and associated labels. Sliders occupy the panel width with a hit region (2.25rem) high and retain vertical page panning. The source selector uses a white field, explicit label and pale border; its minimum height is (2.2rem). Disabled experimental inputs retain the existing subdued state. There is no separate custom validation/error field design to extend.

### Navigation

The Material header keeps native search and navigation. Article navigation uses compact sans text, gentle hover fill and a pale teal active row with heavier type. The contents rail uses a fine left rule. On mobile, native drawers and navigation continue to own the shell behavior. The native back-to-top action sits in the bottom-right corner (0.8rem from both edges), where it retains its native action and visible focus without covering chapter headings.

The home chapter atlas uses actual curriculum numbers, a title, one descriptive line and an inline SVG arrow. Its ruled rows are links; their hover is a subtle surface change.

### Cards / Containers

The reading paper, teaching note and circuit panel are the reusable containers. Teaching notes use a pale green ground and border. Experiments keep a white ground and a pale border around controls and evidence. Source disclosures use a separate pale fill; they remain readable text near the result or chart.

### Details

Native disclosure preserves keyboard behavior and no-script availability. Its summary uses a cool pale fill, rounded outer boundary and background-only hover. The smaller disclosure inside a circuit panel inherits the same language at a denser scale.

### Spectrum and Result

The noise experiment pairs logarithmic ASD with variance per frequency decade, then presents one prominent RMS result. The selected region and variance curve use spectral blue. Only the lower chart's area represents integrated variance. Controls, band edges, area and result follow the same displayed bounds during the interruptible band transition (180ms, cubic ease-out). A new input interrupts from the displayed state; source changes settle immediately without mixing curves. Reduced motion and a hidden document settle to the target immediately.

Source text distinguishes live analytic models from fixed precomputed GF180 data. If enhancement cannot initialize, static chapter explanations and figures remain available; the experiment's error message explains the fallback. Print hides interactive panels and the site shell.

### Concept Figures

Concept figures add a narrow causal or physical explanation to the reading sequence; they do not replace circuit schematics or measured plots. Keep their SVG viewBox at (320 units), cap the displayed figure at (400px), and preserve its label size instead of shrinking it to fit a narrow viewport. The diagram alone scrolls horizontally and receives keyboard focus; show its scroll hint at widths up to (374px). Every figure caption includes a visible link to the original image. Use the book's existing ink, teal, paper and Chinese system-font stacks, while retaining established scientific colors and meaning in legacy circuits and plots.

**The Figure Reading Rule.** A reader can identify the figure, read its caption and open the original image without relying on a script; narrow causal diagrams keep their label size inside a focusable, diagram-local scroll region.

### Shared Select

Native source selectors keep an associated visible label, the white field, pale border and control radius. Their minimum height is (2.2rem), or (44px) at a (20px) root size; retain a visible blue focus outline. This shared control sizing does not change the existing radio, slider or chapter-navigation patterns.

Native page view transitions use a short fade (100ms out, 180ms in) where supported. Reduced-motion CSS removes animations and transitions. No perpetual motion is part of this system.

## Do's and Don'ts

### Do:

- **Do** preserve native MkDocs navigation, search, math, disclosure semantics and the complete static reading path.
- **Do** pair scientific colors with explicit labels and retain a figure's source identity.
- **Do** keep the primary noise result synchronized with the displayed selected band.
- **Do** provide a visible focus treatment appropriate to its adjacent surface.
- **Do** retain the one-column reading measure and stack experiment controls at the existing mobile breakpoint.

### Don't:

- **Don't** substitute decorative interface structure for a derivation, circuit or scientific plot.
- **Don't** present fixed precomputed process data as a live simulation.
- **Don't** animate between different data sources or require motion to understand a result.
- **Don't** make scripts or externally downloaded fonts a prerequisite for reading.

Recorded scope: the final review disposition in `.impeccable/review/finish-verdict.md` resolves three specific finishing fixes, not a whole-site certification. Screenshot evidence spans desktop, tablet, mobile and the supplied intermediate width; physical touch and broad browser coverage were not certified. Local scientific branch colors and native Material defaults remain contextual; this extraction does not normalize them into a new global palette.

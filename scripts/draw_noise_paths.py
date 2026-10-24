#!/usr/bin/env python3
"""Regenerate the Diagram Design 7.4 HTML source and its standalone SVG.

The project marker selects the user's `techcodex` profile. This source only
uses its local system-font stack and the tokens documented in DESIGN.md; it
does not modify the profile or the repository's profile marker.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "diagrams" / "noise-paths.html"
SVG_OUTPUT = ROOT / "模拟" / "图" / "noise-paths.svg"


SVG = r'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 336" role="img" aria-labelledby="noise-paths-title noise-paths-desc">
<title id="noise-paths-title">同一噪声源的路径先合成，独立源的方差再相加</title>
<desc id="noise-paths-desc">同源噪声经过两条同相路径后加倍，经过符号相反的差分路径后抵消；两个等方差独立源相加时，理论输出方差为单个源的两倍。</desc>
<defs>
  <marker id="arr-muted" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#566976"/></marker>
  <marker id="arr-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#126e63"/></marker>
  <marker id="arr-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#315bc5"/></marker>
</defs>
<rect width="320" height="336" fill="#ffffff"/>
<g font-family="'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif" stroke-linecap="round" stroke-linejoin="round">
  <text x="12" y="23" fill="#173c50" font-size="16" font-weight="700">噪声源怎样沿路径合成</text>

  <!-- Path connectors are drawn before the nodes. They show transfer relations, not wires. -->
  <!-- Same source, same phase. -->
  <path d="M48 76 H56" fill="none" stroke="#566976" stroke-width="1.5"/>
  <path d="M56 76 H60 Q68 76 68 68 V60 H72" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M56 76 H60 Q68 76 68 84 V92 H72" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M136 60 H152" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M136 92 H152" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>

  <!-- Same source, opposite signed differential paths. -->
  <path d="M48 160 H56" fill="none" stroke="#566976" stroke-width="1.5"/>
  <path d="M56 160 H60 Q68 160 68 152 V144 H72" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M56 160 H60 Q68 160 68 168 V176 H72" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M136 144 H152" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M136 176 H152" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>

  <!-- Two distinct input-device sources, each with its own transfer path. -->
  <path d="M48 244 H72" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M48 268 H72" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M136 244 H152" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>
  <path d="M136 268 H152" fill="none" stroke="#566976" stroke-width="1.5" marker-end="url(#arr-muted)"/>

  <!-- Dividers -->
  <path d="M12 120 H308 M12 208 H308 M12 296 H308" fill="none" stroke="#d5e0e8" stroke-width="1"/>

  <!-- Row 1 nodes -->
  <text x="12" y="43" fill="#173c50" font-size="13" font-weight="600">同源 · 同相</text>
  <ellipse cx="28" cy="76" rx="20" ry="16" fill="#eef3fa" stroke="#173c50" stroke-width="1.2"/>
  <text x="28" y="81" text-anchor="middle" fill="#173c50" font-size="13">n</text>
  <circle cx="56" cy="76" r="3.5" fill="#173c50"/>
  <rect x="72" y="48" width="64" height="24" rx="4" fill="#ffffff" stroke="#d5e0e8" stroke-width="1"/>
  <rect x="72" y="80" width="64" height="24" rx="4" fill="#ffffff" stroke="#d5e0e8" stroke-width="1"/>
  <text x="104" y="65" text-anchor="middle" fill="#173c50" font-size="13">H₁ = 1</text>
  <text x="104" y="97" text-anchor="middle" fill="#173c50" font-size="13">H₂ = 1</text>
  <rect x="152" y="56" width="28" height="40" rx="4" fill="#f2f8f5" stroke="#126e63" stroke-width="1.2"/>
  <text x="166" y="81" text-anchor="middle" fill="#173c50" font-size="16">Σ</text>
  <text x="188" y="73" fill="#126e63" font-size="14" font-weight="700">y = 2n</text>
  <text x="188" y="92" fill="#253440" font-size="13">σᵧ² = 4σ²</text>

  <!-- Row 2 nodes -->
  <text x="12" y="127" fill="#173c50" font-size="13" font-weight="600">同源 · 差模相减</text>
  <ellipse cx="28" cy="160" rx="20" ry="16" fill="#eef3fa" stroke="#173c50" stroke-width="1.2"/>
  <text x="28" y="165" text-anchor="middle" fill="#173c50" font-size="13">n</text>
  <circle cx="56" cy="160" r="3.5" fill="#173c50"/>
  <rect x="72" y="132" width="64" height="24" rx="4" fill="#ffffff" stroke="#d5e0e8" stroke-width="1"/>
  <rect x="72" y="164" width="64" height="24" rx="4" fill="#ffffff" stroke="#d5e0e8" stroke-width="1"/>
  <text x="104" y="149" text-anchor="middle" fill="#173c50" font-size="13">H₁ = 1</text>
  <text x="104" y="181" text-anchor="middle" fill="#173c50" font-size="13">H₂ = −1</text>
  <rect x="152" y="140" width="28" height="40" rx="4" fill="#f2f8f5" stroke="#126e63" stroke-width="1.2"/>
  <text x="166" y="165" text-anchor="middle" fill="#173c50" font-size="16">Σ</text>
  <text x="188" y="157" fill="#173c50" font-size="14" font-weight="700">y = 0</text>
  <text x="188" y="176" fill="#253440" font-size="13">理想尾源抵消</text>

  <!-- Row 3 nodes -->
  <text x="12" y="221" fill="#173c50" font-size="13" font-weight="600">两个独立输入管噪声</text>
  <ellipse cx="28" cy="244" rx="20" ry="10" fill="#eef3fa" stroke="#173c50" stroke-width="1.2"/>
  <ellipse cx="28" cy="268" rx="20" ry="10" fill="#eef3fa" stroke="#173c50" stroke-width="1.2"/>
  <text x="28" y="249" text-anchor="middle" fill="#173c50" font-size="13">n₁</text>
  <text x="28" y="273" text-anchor="middle" fill="#173c50" font-size="13">n₂</text>
  <rect x="72" y="232" width="64" height="24" rx="4" fill="#ffffff" stroke="#d5e0e8" stroke-width="1"/>
  <rect x="72" y="256" width="64" height="24" rx="4" fill="#ffffff" stroke="#d5e0e8" stroke-width="1"/>
  <text x="104" y="249" text-anchor="middle" fill="#173c50" font-size="13">H₁ = 1</text>
  <text x="104" y="273" text-anchor="middle" fill="#173c50" font-size="13">H₂ = 1</text>
  <rect x="152" y="232" width="28" height="48" rx="4" fill="#ffffff" stroke="#173c50" stroke-width="1"/>
  <text x="166" y="261" text-anchor="middle" fill="#173c50" font-size="16">Σ</text>
  <text x="188" y="251" fill="#173c50" font-size="13" font-weight="700">σᵧ² = 2σ²</text>
  <text x="188" y="270" fill="#253440" font-size="13">理论期望</text>

  <text x="12" y="310" fill="#526974" font-size="13">箭头表示传递关系，不是导线。</text>
  <text x="12" y="328" fill="#526974" font-size="13">有限记录的非零协方差，不等于物理相关。</text>
</g>
</svg>'''


HTML = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>7.4 噪声源与传递路径的合成</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ margin: 0; padding: 16px; background: #fff; color: #173c50;
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif; }}
    main {{ max-width: 420px; margin: auto; }}
    h1 {{ margin: 0 0 8px; font: 700 1.25rem/1.5 "Noto Serif SC", "Source Han Serif SC", "Songti SC", "SimSun", serif; }}
    p {{ margin: 0 0 12px; color: #566976; line-height: 1.7; }}
    svg {{ display: block; width: 100%; min-width: 320px; height: auto; }}
    @media print {{ svg {{ min-width: 0; }} }}
  </style>
</head>
<body>
  <main>
    <h1>7.4 噪声源与传递路径的合成</h1>
    <p>同一源的路径先合并；彼此独立的源按方差合成。</p>
    {SVG}
  </main>
</body>
</html>
'''


def mean(values: tuple[float, ...]) -> float:
    return sum(values) / len(values)


def variance(values: tuple[float, ...]) -> float:
    center = mean(values)
    return sum((value - center) ** 2 for value in values) / len(values)


def covariance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    left_mean = mean(left)
    right_mean = mean(right)
    return sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right)) / len(left)


def verify_moments() -> None:
    """Run exact teaching-vector checks before writing either deliverable."""
    source = (-2.0, -1.0, 0.0, 1.0, 2.0)  # zero mean, population variance 2
    same = tuple(value + value for value in source)
    cancelled = tuple(value - value for value in source)
    assert variance(source) == 2.0
    assert variance(same) == 4 * variance(source)
    assert variance(cancelled) == 0.0

    # Two exact finite records with equal variance; their nonzero sample
    # covariance is sampling evidence only, not a claim of physical coupling.
    independent_1 = (-2.0, -1.0, 0.0, 1.0, 2.0)
    independent_2 = (1.0, -2.0, 2.0, -1.0, 0.0)
    sample_cov = covariance(independent_1, independent_2)
    observed_sum_variance = variance(
        tuple(a + b for a, b in zip(independent_1, independent_2))
    )
    assert variance(independent_1) == variance(independent_2) == 2.0
    assert sample_cov == -0.2
    assert observed_sum_variance == (
        variance(independent_1) + variance(independent_2) + 2 * sample_cov
    )

    # Independence means zero covariance in expectation, so equal source
    # variances of 2 give the theoretical output variance 2 + 2 = 4.
    expected_independent_variance = variance(independent_1) + variance(independent_2)
    assert expected_independent_variance == 4.0
    # Enumerate the independent product distribution: each of 25 pairs has
    # probability 1/25. This verifies the expectation, not just one record.
    pairs = tuple((a,b) for a in independent_1 for b in independent_2)
    assert covariance(tuple(a for a,b in pairs),tuple(b for a,b in pairs)) == 0.0
    assert variance(tuple(a+b for a,b in pairs)) == expected_independent_variance
    print("Math check: same source n+n variance=8=4*2; n-n variance=0.")
    print("Math check: independent-source theory=4; finite pair covariance=-0.2, observed sum variance=3.6.")


def main() -> None:
    verify_moments()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(HTML, encoding="utf-8")
    SVG_OUTPUT.write_text(SVG + '\n', encoding="utf-8", newline='\n')
    print(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()

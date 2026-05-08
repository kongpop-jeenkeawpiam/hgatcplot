# SRplot Exact Match Tracker

This project currently exposes 125 SRplot-inspired modules. Every module renders
all export formats, but exact SRplot visual parity is tracked separately from
basic renderer availability.

## Status Meanings

- `reference-needed`: module renders, but its concrete SRplot page/reference output
  still needs to be captured and compared.
- `reference-known`: the SRplot page is known and linked in module metadata.
- `pixel-close`: local output has been visually compared and is close to SRplot.
- `exact-match`: local output is accepted as matching SRplot style.

## Initial Reference Targets

| Module | SRplot reference | Style profile | Status |
| --- | --- | --- | --- |
| `volcano` | https://bioinformatics.com.cn/plot_basic_3_color_volcano_plot_086_en | `srplot-volcano-three-color` | `reference-known` |
| `wordcloud` | https://www.bioinformatics.com.cn/plot_basic_wordcloud_118_en | `srplot-wordcloud` | `reference-known` |

## Current Counts

- Total modules: 125
- Reference-known modules: 2
- Reference-needed modules: 123
- Pixel-close modules: 0
- Exact-match modules: 0

Exact-match implementation should move modules through these statuses only after
capturing SRplot output and comparing local PNG/SVG/PDF artifacts against it.

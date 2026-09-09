# Charts — how they are built and why

Everything behind `Compendium_5_Charts.ipynb`. Read this before changing how a
chart looks: it records what was measured and what was chosen, so none of it has
to be worked out twice.

```
merged_long_files\<Chapter>_EN.xlsx   ->   <chapter>_charts\
```

Run it after notebook 3. It reads the same long files notebook 4 does, so it
picks up the merged questionnaire rows and the calculated indicators. It is
independent of notebook 4 — neither needs the other.

`CHAPTERS` at the top of the config cell picks what runs. It is currently
`["Population"]`. Set it to `None` to chart every chapter found on disk.

## What comes out

`<chapter>_charts.xlsx` is the deliverable: one sheet per chart, each holding
that chart's picture with exactly the rows that produced it underneath, plus an
`Index` sheet linking to them all. Every chart's SVG and PNG sit in the same
folder, next to `charts_index.csv` and `chart_data_findings.txt`.

**Excel cannot hold an SVG.** openpyxl places images through Pillow, which does
not rasterise SVG, so the picture *inside* a sheet is the PNG. The SVG beside it
is the vector copy and the one to use anywhere that wants live text. There is no
way around this from Python — don't spend time trying again.

**Population** gets the numbered set the compendium prints — `1.1_pop_growth`,
`1.2_pop_size`, `1.3_sex_comp_gcc`, `1.6_sex_ratio`, `1.7_pop_age_sex`,
`1.8_fertility`, `1.9_life_exp`, `1.10_infant_mort`, `1.11_intl_migrant_gcc`,
`1.12_intl_migrant`, `1.13_refugees` — plus one pyramid per country, 31 charts in
all. **The numbering keeps its gaps on purpose**: no 1.4 or 1.5 was supplied to
copy, so those numbers are left free and the files still line up with the figure
numbers in the report. Don't close the gap.

**Every other chapter** is charted from what its indicators actually carry:
`_trend` (a line per country) where there is a country total over time, `_by_sex`
(a panel per country) where it is reported by sex, and `_<breakdown>` (stacked
shares, latest year) where it splits into parts that sum to a whole.

## The theme

Light, and not a matter of taste — every value was read back out of the published
SVGs in `population old charts\population copy\`.

| | value | |
|---|---|---|
| surface | `#FFFFFF` | figure and plot ground |
| ink | `#000000` | titles, ticks, values |
| muted ink | `#5A5A5A` | subtitles and units |
| axis line | `#444444` | exactly as the originals draw it |
| grid | `#E4E7EB` | **not in the originals** — see below |
| font | Times New Roman | the originals use 17px body, 20px title |
| sizes | 16 tick / 16 legend / 16 panel / 21 title | |
| line | `LINE_WIDTH = 1.45` | 2px at 100 dpi, as published |
| marker | `MARKER_SIZE = 5.0` | |
| bar gap | 0.9px in the surface colour | reads as space, not as a drawn keyline |

`dpi = 100`, so one figure inch is 100 px and every pixel calculation below is
literal. `svg.fonttype = "none"` keeps text as text — editable, and a smaller
file.

**The one deliberate deviation: the originals have no gridlines at all.** Their
`gridlayer` is empty. A faint grid was added because a value in the middle of a
tall panel is otherwise unreadable. Set `GRID_COLOR = SURFACE` to switch it off
and match the published figures exactly.

### Colours

The categorical triad, read out of 1.3, 1.7 and the pyramids:

- `#003F5C` navy · `#BC5090` pink · `#FFA600` amber

It separates well — Male/Female ΔE 42.8 colour-blind and 50.9 normal; the three
age bands 16.2 and 30.1. The amber sits at **1.96:1 against white**, which the
validator flags as needing relief (a visible label or a table view) rather than
as a free choice. **That relief is already drawn** and must stay: `stacked_shares`
prints the number inside every segment wide enough to hold one, and the workbook
puts the whole table on the sheet beneath the picture.

The published life-expectancy chart used blue and red instead, but those are
plotly's defaults showing through the label-lookup miss described below — not a
house choice — so the triad is used for every sex encoding.

Single-series bars use `#19516C`, from 1.11.

### The country palette, and the bug in the published charts

The 22 country colours are the published ones. **They are keyed on the name as it
appears in the long file, not on the printed label** — this is the one fix kept
from the originals. The published charts keyed theirs by label, so wherever a
legend wrote a country without spaces — `SaudiArabia`, `SyrianArabRepublic`,
`UnitedArabEmirates`, `StateofPalestine` — the lookup missed and plotly's default
sequence took over. That is why Saudi Arabia is olive on one published figure and
blue on the next. You can still see both values in the old SVGs.

**What the house palette costs, measured:** United Arab Emirates `#999999` has
zero chroma (it is grey, not a hue) and sits at ΔE 1.0 from Tunisia under a
deutan simulation; Iraq and Egypt are 7.8 apart under normal vision against a
floor of 15; ten of the twenty-two fall below 3:1 contrast on white. They are
kept because they are what the compendium prints.

`HOUSE_ALTERNATIVE` in the config cell is a measured replacement if the set is
ever allowed to change — worst pair anywhere 5.9 instead of 1.0, worst legend
neighbours 15.4, every colour at or above 3.11:1 and 0.106 chroma. Switch with
one line: `COUNTRY_COLORS = HOUSE_ALTERNATIVE`.

**5.9 is a ceiling, not a shortfall.** Twenty-two colours that must each clear
3:1 on white cannot do better on their worst pair; the search was exhaustive
enough to be confident of that. It is below the validator's target of 8, which is
exactly why **these charts never identify a line by colour alone**: the legend is
always drawn, and where one country's own path matters more than the ranking,
`small_multiples` is the shape to reach for.

Run the validator rather than reasoning about any of this:

```
node <dataviz skill>/scripts/validate_palette.js "<hex,hex,...>" --mode light --surface "#FFFFFF"
```

Add `--pairs all` for anything where any two series can end up side by side —
lines, scatter, small multiples. Adjacent-only is for stacks and bars. The CLI
guard requires the script to be invoked at a path ending in `validate_palette.js`,
and it is an ES module, so it needs a `package.json` holding `{"type":"module"}`
beside it.

## Sizes are measured, never guessed

This is the part most worth keeping. Nothing uses a character-count estimate; the
figure is sized from the rendered width of the text that has to fit, which is why
no label clips at any length.

- `widest_label_px(fig, labels, size)` measures real text through the renderer's
  `get_window_extent`.
- `label_margin()` turns that into a left margin, clamped to 0.12–0.55.
- `head_px()` / `draw_head()` reserve the title and subtitle band and return the
  fraction consumed, so a two-line title cannot land on a panel title.
- `stacked_shares` sets its own height from measured content:
  `head + panel titles + 46 px per row + 44 px + 32 px per legend row`, with the
  legend column count derived from the widest category label.
- `country_lines` measures the legend and widens the *figure* to hold it, keeping
  the plot itself a fixed `PLOT_WIDTH_PX = 700`. It used to fix the plot at 0.52
  of an 800 px figure, which gave a 19-country legend nearly 40% of the width and
  left twenty-one lines of data sharing 416 px. Sizing this way also keeps
  `Syrian Arab Republic` whole — the published SVGs cut it off.
- `small_multiples` lays out from a pixel budget, not from `subplots_adjust`
  fractions: head, legend band, then per row a `PANEL_TITLE_PX` and a `PANEL_PX`,
  `ROW_GAP_PX` between rows, and `FLOOR_PX` for the year labels. The fractions had
  `hspace = 0.75` — three quarters of a panel's height spent on the gap — which
  left every panel **180×90 px** on an 800 px figure. At that size a series reads
  as a flat line whatever it does, and the year labels only fit turned on their
  side. A panel is now a fixed **320×150 px** whatever the country count, the
  years sit upright, and the y axis gets `MaxNLocator(4)` instead of just a floor
  and a ceiling.
- **The year labels stay upright because the count is measured.** How many fit
  across one panel comes from `widest_label_px`, and the ticks are thinned to
  that. A column of sideways years was the hardest thing to read on the old
  figures.

Three fixes worth not re-breaking:

- **Shared axes invert once, not per axis.** Calling `invert_yaxis()` on each
  panel of a shared-y figure cancels itself on the second. `stacked_shares` uses
  a single `set_ylim`.
- **Shared x hides tick labels on every panel but the bottom row, and the bottom
  row is usually part empty.** `small_multiples` turns labels back on for the
  lowest *occupied* panel in each column.
- **The shared legend is collected from every panel, not from the first one.**
  Reading `get_legend_handles_labels()` off `axes[0][0]` drops a series from the
  legend whenever the first country alphabetically does not happen to report it —
  Iraq reports only one sex on several Labor indicators. The handles are gathered
  across all panels and ordered by the `series_colors` dict, so the legend reads
  Male, Female in house order rather than alphabetically.

`readable_on()` picks the text colour for a number sitting on a fill **by
measuring contrast**, not by a fixed lightness rule. A fixed rule is only correct
for one theme and silently inverts on the other — it did, when the theme moved
from dark to light, and every number inside a stacked bar went invisible.

## The five shapes

Every chart is one of these, in `cell_primitives`:

| | used by |
|---|---|
| `country_lines` | 1.1, 1.2, 1.6 — one line per country, legend right |
| `small_multiples` | 1.8, 1.9, 1.10 — a panel per country, **one shared y scale** |
| `stacked_shares` | 1.3, 1.7 — percentages that sum to 100 |
| `ranked_bars` | 1.11 — one bar per country, longest on top, no legend |
| `pyramid` | the country pyramids — male left, female right, one shared scale |

`small_multiples` shares its y scale deliberately: on separate scales a country
whose fertility moved 2.0 → 2.2 looks identical to one that moved 2 → 6.

The pyramid plots **percent of total population**, not percent of that sex —
verified against the published Bahrain figure (male 20-24: published 4.50%,
computed 4.48%) and the sheets sum to 100.00% across both halves.

## The data guards

The charts refuse a figure rather than draw a wrong one, and every refusal is
written to `chart_data_findings.txt`. These are findings about the
questionnaires, not the code, so they outlive the run and can go back to the
country that reported them. Population currently produces 22.

- `to_number()` — the same parser as notebook 3. Only 337 of 33,968 population
  cells are numeric; the rest are text like `' 701 956 '` with spaces as
  thousand separators.
- `total_or_derived()` — where a country has no `Area Total` row, the total is
  summed from an exhaustive partition (Urban + Rural, or Nationals +
  Non-nationals) and the fact is recorded. Egypt has no total rows at all.
- `drop_scale_outliers(factor=20)` — a point more than 20× off its own country's
  median is a unit or typing error, not a fact. Catches Lebanon's 2022 population
  filed as `100`. It used to catch Morocco's 2024 as `36,491` too; notebook 1 now
  reads the `الاعداد بالالف` note on that column and scales it to `36,491,000` at
  source, so the figure arrives correct instead of being dropped — which is the
  better outcome, and why Population's findings went from 22 to 18.
- `drop_impossible_percentages()` — a share cannot be more than all of it, so a
  value above 100 in an indicator whose own name says `(percent)` is dropped.
  Only that name is trusted: a rate per 1,000 women runs past 100 legitimately
  and a growth rate goes negative legitimately, so neither is bounded. This
  matters more than one wrong dot because `small_multiples` shares **one** y
  scale across every panel: Egypt's single 110% occupation share stretched the
  axis to 0–110 and flattened all fourteen countries onto the baseline. Algeria
  trips it too, for a different reason — it files head-counts (1,744 … 8,250)
  under a percent indicator, the same fault as the two Population `(%)`
  indicators in CLAUDE.md's known issues. Reported one line per indicator and
  country, not per point: per point it was 781 lines for Labor alone.
- `drop_contradictory_sexes()` — where Male + Female misses its own reported
  total by more than `SEX_TOTAL_TOLERANCE = 2.0`%, **the whole country-year is
  dropped**. Nothing in the file says which of the two figures is sound, so
  guessing would be worse than refusing. Catches Kuwait 2020 (total missing its
  leading digit) and Tunisia 2015 (male figure with an extra digit).
- **Population totals take only the `Total` slice of one indicator.** The
  by-nationality and by-area indicators describe the same people; summing them,
  or their parts, double-counts.
- `WHOLE_LABELS` holds *ordered fallbacks* per column, and **Age Group is
  deliberately excluded from `BREAKDOWN_COLUMNS`**. Labor's rates carry
  overlapping bands (15+, 15-24, 15-64, 25+) with no `Age Total`, so stacking
  them was meaningless; excluding the column took Labor from 19 charts to 29.

## The chart data on each sheet

Captured **inside the drawing primitives**, not in the chart functions. The
primitive is the last place that still holds exactly what was drawn, after every
filter and guard has run, so a sheet cannot drift away from the picture above it.
`record_data(stem, frame)` stores it; `CHART_DATA` holds it until the workbook is
written.

If you add a primitive, add a `record_data` call before its `save()` or its
charts will render but get no sheet — the run reports that rather than failing.

## Environment

- **plotly cannot be installed here** (no package index), and the originals were
  plotly exports. Everything is reproduced in matplotlib with the `Agg` backend.
  Don't try to install it again.
- Excel locks files it has open. If a write fails, check `<Chapter>_*.xlsx` and
  the output workbook are closed.
- **Everything is under OneDrive, and the source files can change mid-session.**
  `Population_EN.xlsx` was once observed going 0 bytes → 2 KB → 17.6 MB while a
  pipeline run finished in another window. Before charting, confirm the source is
  a valid zip and its size has stopped changing; treat the live file as
  authoritative over any earlier snapshot.
- Verify writes explicitly rather than assuming they landed — the notebook's last
  cell re-opens every file, checks it is a real SVG carrying drawn marks, and
  re-opens the workbook to confirm each sheet has both a picture and a table.
- Run the notebook by executing its cells from a script (`py -u`), not through a
  subagent.

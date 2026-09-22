# Arab Society Compendium — pipeline

Six notebooks make the deliverables, and two more in `data quality/` check
them. Nothing in `data quality/` changes data.

| # | Notebook | Reads | Writes |
|---|---|---|---|
| 1 | `Compendium_1_Long_Files.ipynb` | `datacollector_received_quest_<LANG>\<Chapter>\*.xlsx` | `<Chapter>_AR.xlsx`, and `<Chapter>_EN_questionnaires.xlsx` if English questionnaires exist |
| 2 | `Compendium_2_New_Indicators.ipynb` | `<Chapter>_AR.xlsx` | the calculated rows, in Arabic, appended to it |
| 3 | `Compendium_3_External_Data.ipynb` | `DATA COLLECTOR\external data\<Chapter>\*.xlsx` | `<Chapter>_EN_external.xlsx`, plus a `*_reshaped.xlsx` questionnaire-layout copy beside each source file |
| 4 | `Compendium_4_Translation.ipynb` | `<Chapter>_AR.xlsx` + `<Chapter>_EN_questionnaires.xlsx` + `<Chapter>_EN_external.xlsx` | `<Chapter>_EN.xlsx`; also appends external data's Arabic form to `<Chapter>_AR.xlsx` |
| 5 | `Compendium_5_Tabulations.ipynb` | `<Chapter>_EN.xlsx`, `<Chapter>_AR.xlsx` | `tabulations\<Chapter>_tabulations_<LANG>.xlsx` |
| 6 | `Compendium_6_Charts.ipynb` | `<Chapter>_EN.xlsx` | `<chapter>_charts\` — an SVG and a PNG per figure, `<chapter>_charts.xlsx`, `charts_index.csv`, `chart_data_findings.txt` |

`<chapter>_charts.xlsx` lives only in `<chapter>_charts\`, beside the SVGs and
PNGs it indexes. Nothing copies it into `merged_long_files\` — that folder is
the long files' own, and a chart workbook there would be one more place for
the two to drift apart.

Every long file lives in **`merged_long_files\`**, one folder for both languages.

**1 → 2 → 3 → 4 in that order**; each reads what the previous wrote. 3 is
optional in effect — it only has anything to do if a chapter has an
`external data\<Chapter>\` folder — but always sits between 2 and 4, so 4 can
fold in whatever 3 found on the same run. **5 and 6 are independent
siblings**: both read the finished long files, neither needs the other, and
either can be re-run alone. Both come after 4 so they pick up the calculated
indicators and anything external.

**Notebook 3 reads published indicator tables that never went through a
questionnaire** — one folder per chapter under `DATA COLLECTOR\external
data\<Chapter>\`. Nothing about their layout is assumed: the one real file
used to build this had six sheets in three different header shapes, worked
out by reading the actual file rather than guessing at a spec, and a column
it cannot confidently name is left out and reported - without taking the
rest of that sheet's good columns down with it, which refusing the whole
sheet used to do. Follows the `reshape-external-data-questionnaire-layout`
skill: alongside the rows it writes to `<Chapter>_EN_external.xlsx`, it saves
a reshaped, questionnaire-layout copy of each source file beside the source
file, for a person to check straight against the original. **Notebook 3 does
none of the translation itself** - it only extracts and reshapes; notebook 4
is the one place that decides every value's language, in both directions.
Full design and this split's reasoning are in notebook 3's own intro cell -
read that before touching it, most of what looks arbitrary there is a
finding from the real sample file, not a guess.

**Notebooks 1 to 5 record what they find wrong with the source data** in
**`pipeline_inconsistencies_<Chapter>.txt`, one file per chapter**, beside
the codes folder - plus `pipeline_inconsistencies_general.txt` for the rare
finding with no chapter of its own (a dictionary-level problem, not a
source-data one). Notebook 1 every column name and value it matched against
the dictionary - corrected or not - and every Value it had to correct;
notebook 2 the contradictions in the figures; notebook 3 the sheets or
columns it could not confidently read; notebook 4 the values with no
translation - section `4. TRANSLATION` for the normal Arabic → English
direction, `4b. EXTERNAL DATA` for external data's own English → Arabic
gaps; notebook 5 the tabulations that came out wrong. Every record carries
the country, indicator and year it came from, so a finding can be traced
back to the cell.

Each notebook still owns one named section (`### 1. LONG FILES ###`, and so
on) and rewrites only that section **within its own chapter's file**, exactly
as before - a chapter-scoped run has never overwritten another notebook's
findings, but until this split it *did* overwrite another **chapter's**:
running notebook 1 on Housing used to replace whatever notebook 1 had found
running on Education the day before, silently, because the one shared file
had no idea which chapter a section's findings belonged to. `save_inconsistencies()`
takes `chapters=` explicitly now, so even a chapter with nothing wrong gets its
own section correctly replaced with "Nothing found" rather than left stale.

**Every dictionary correction is logged, not only the ones the fuzzy matcher
gives up on.** `correct_with_dictionary()` used to log a label only when
nothing scored above `FUZZY_MATCH_CUTOFF`; a spelling it silently auto-fixed
never appeared anywhere but the console. It now logs both - `column name
corrected` / `value corrected` for the ones it fixed, `column name not in the
dictionary` / `value not in the dictionary` for the ones it could not - so the
full list of what changed in the source data is in one place, not split
between a saved file and a scrollback nobody kept.

Notebook 6 keeps its own `chart_data_findings.txt` in each chart folder rather
than a section of the shared log, because it refuses figures the other five
happily pass through — a value orders of magnitude off its own series, or men
and women that do not add up to their reported total.

**Notebook 1 cleans the Value column and reports every change.** A number
wrapped in a recognized unit phrase is scaled to match it: `بالالف` and its
common typo `بالاف` both mean "in thousands", so `7845(الاعداد بالالف)` →
`7845000`. A placeholder like `-` becomes blank, and so does a cell holding
only spaces — which is not an empty cell, and otherwise survives every "is it
blank" test to reach the charts as a value that cannot be plotted. A cell like
`51.2+1.2` is read as the sum. Wrapping text the pipeline does not recognize is
just dropped, keeping only the bare number — which is exactly why every one of
these is reported rather than quietly fixed: an unfamiliar phrase could carry a
multiplier too, and only the country that filled in the cell can say for certain.

**A unit note describes the whole column it sits in, not the one cell it is
written on.** Morocco's 2024 population is filed as `1444`, `1745`, `1815`, …
with `الاعداد بالالف` typed into the first cell only. Scaling that one cell
leaves it a thousand times *larger* than its own neighbours — worse than
leaving it alone — so the multiplier is applied to every figure sharing that
indicator, country and year, and the block is reported with the count of
figures it moved. The scope is the year, because that same file has 2010–2022
in whole units and only 2024 in thousands.

Each notebook owns a numbered section and rewrites only its own, so the file
always reflects the latest run of each step and stays in step order whatever
order they ran in. These are findings about the questionnaires, not the code, so
they outlive the run and can go back to the country that reported them.

**Why `<Chapter>_EN_questionnaires.xlsx` has its own name.** Notebook 1's
English output and notebook 4's are different files — one is English
questionnaires made long, the other is the translated Arabic with those rows
appended. Sharing `<Chapter>_EN.xlsx` would make notebook 4 read and overwrite
the same file, so a second run would append its own output to itself and
duplicate every row.

The Arabic side needs no such trick — notebook 2 strips its own previously-added
rows before appending, so writing back to `<Chapter>_AR.xlsx` in place is
idempotent.

**The calculations run before the translation, on the Arabic file.** They used
to run on the English file, which meant translating the new rows *back* into
Arabic afterwards — a round trip through an inverted dictionary for rows that
had only just been created. Inverting is lossy exactly where several Arabic
spellings share one English translation (43 terms on the current data). Doing
the arithmetic in Arabic means the calculated rows are part of the file before
anything is translated, and the whole file goes one way, once. **Never
reintroduce a back-translation.**

Notebook 2's code is written with English names — `"Male"`, `"Age Total"`,
`"Population size by nationality"` — and `term()` resolves each into whatever
the Arabic file says. A name the dictionary cannot resolve is reported rather
than silently passed through, because a calculation built on an unresolved name
matches nothing and quietly produces no rows.

**Checking the data lives in `data quality/`**, with its own `CLAUDE.md`. One
notebook, `Compendium_Data_Quality.ipynb`, in two parts that share nothing but
a file.

**Part 1 reads the raw questionnaires** - the same files notebook 1 reads -
and writes one file, `data_quality_review.txt`: every label with no exact
match in the dictionary, every Value cell `clean_one_value()` could not make
sense of on its own, and (reporting only) every sheet broken enough to fail at
read time. Open it, accept or edit each `CORRECTION:` line, save it, then tell
Claude `apply data_quality_review.txt` - it writes your decisions into
`translation dict.xlsx` and `value corrections.xlsx`, and the next pipeline
run uses them directly instead of guessing. Run this **before** notebook 1, so
a run starts with as few gaps as this can catch in advance.

**Part 2 reads the final `<Chapter>_EN.xlsx` files** and reports, per chapter:
completeness (how many of the 17 expected years each indicator × country
series actually carries, banded rather than averaged into one misleading
number), and contradictions (a reported total against the sum of its own
parts, year-on-year spikes, a percentage indicator holding absolute counts,
percentages not summing to 100, implausible values, conflicting duplicate
rows). Writes `data_gaps_report.xlsx` and regenerates the GitHub Pages
dashboard's `docs/data.js`. Run this after step 4, before building
tabulations or charts on figures that have not been sanity-checked.

Nothing here changes data on its own - the checks only measure and report, and
the one file Part 1 can change is changed by a person's own decision, read
back from a file they saved themselves.

**How the charts look is settled in `charts_design.md`**, beside notebook 6.
Colours, fonts, the measured-layout rules, the data guards and the trade-offs
behind each are recorded there with the numbers they were chosen on. Read it
before changing anything visual — it exists so none of that has to be
re-derived, and several of the odd-looking choices are load-bearing.

**Every chapter's charts are copies of the figures the compendium prints**, and
the originals are at
`COMPENDIUM-ARAB SOCIETY\old files\population old charts\<chapter>\` — one
folder of plotly SVGs per chapter, recorded in the notebook as
`OLD_CHARTS_PATH`. Notebook 6 has a hand-written set per chapter numbered to
match (`1.1`–`2.7` Population, `3.x` Housing, `4.x` Health, `5.x` Education,
`6.x` Labor, `7.x` Poverty); the old data-driven builder is now only the
fallback for a chapter with no such set. The SVGs keep their text as text, so a
legend or an axis label can be read straight out of one with `grep`.

Paths live outside this repo, under
`C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\`.

## Filling dictionary gaps — do this without being asked

**When the user asks to run the pipeline, treat closing dictionary gaps as part
of the job**, not as a separate request to come back for. There are two kinds,
and both must be closed before the run counts as finished.

This is the *during-and-after* loop: gaps found while running notebooks 2 and
4, closed by Claude's own judgement. The data quality notebook is the
*before* loop - the same two kinds of gap, found by reading the raw
questionnaires ahead of a run, closed by the person reading
`data_quality_review.txt` rather than by Claude - and the two are meant to
meet in the middle: the more that loop closes in advance, the fewer of these
a real run turns up.

### Kind 1 — a value the questionnaires used

A country writes a survey name the dictionary has not seen. Notebook 4 finds
these by comparing the table before and after translation: a value with no entry
passes through unchanged, and that is the gap. What is missing is always the
English side now that everything travels Arabic → English.

### Kind 2 — a label the pipeline invented

The calculations create indicator titles and age-group labels (`Sex ratio,
2010-2025 (per 100 females)`, `<15 years`, …) that appear in **no
questionnaire**. Notebook 2 needs their *Arabic* to write the rows at all, so a
missing one is caught immediately: `term()` reports it instead of falling back
silently, and the run lists it under "term missing from the dictionary".

### Kind 3 — external data introduces a new English-origin value

Notebook 3's `<Chapter>_EN_external.xlsx` output is genuinely new English
content with no Arabic form anywhere yet - a country, an indicator, a
citation. Notebook 4's own external-data-folding section finds these the
same way (`find_external_gaps()`), but travelling the other direction -
English → Arabic, not Arabic → English - since this content started in
English and the rule is still to give a value an Arabic form for the first
time, never to back-translate anything already correct. Closed the same way
as the other two kinds; see notebook 4's own intro cell for the two-part run
this needs (append first, review `EXTERNAL_GAPS`, `update_dictionary()`,
then `apply_external_gaps()`).

### The loop, any kind

1. Run the notebook.
2. Read them from that chapter's own `pipeline_inconsistencies_<Chapter>.txt` —
   no spreadsheet is written. Each carries the country, indicator and year of
   an example row.
3. Translate them yourself. Use the official English name of a statistical body
   where one exists — search `translation dict.xlsx` first, so wording stays
   consistent with what is already there.
4. Call `update_dictionary(filled)`. It backs the file up first, skips rows
   already present, and marks what it adds with `status = "updated"` so machine
   translations can be told from hand-typed ones.
5. Re-run the notebook and confirm the gap list is empty.
6. Report what you added, and flag any translation involving real judgement.

**Attach translations by position, never by retyping the Arabic or English
keys.** A retyped string that differs by one invisible character (non-breaking
space, different letter form) silently fails to match. Assert a couple of anchor
rows before writing.

## Running it

Two ways, and both are fine.

### Running it yourself, in Jupyter or VS Code

Open the notebook and run its cells top to bottom, same as any other notebook
— nothing about these requires a special runner. To limit a run to one
chapter, edit `CHAPTERS` in the cell whose id is `config`:

```python
CHAPTERS = ["Poverty"]      # instead of None
```

`None` means every chapter found on disk. Nothing resets this for you, so set
it back to `None` (or to the chapter you actually want) before the next full
run.

### Running it through Claude

Claude has no Jupyter kernel, so a notebook is run by reading its JSON and
`exec`-ing each code cell's source into one namespace, in cell order — after
the `config` cell has run, `CHAPTERS` is overridden in that namespace before
the rest continue. `run_pipeline.py`, if it is in the repo, is exactly that,
generalised and committed so it is not retyped every session. If it is not
there, Claude writes the same ~15 lines as a scratch script instead — the
technique does not depend on the file existing, only on a set of committed
notebooks to read.

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py -u run_pipeline.py 2 4 5 --only Population > run.log 2>&1
```

Then **poll the log** — never wait blind on a long run. `PYTHONUTF8=1` is not
optional: the Arabic in the progress output kills the default Windows
console encoding.

`--only` overrides `CHAPTERS` the same way the manual edit above does. Repeat
it for several chapters.

Measured on Population, 389,075 rows — useful for telling a slow run from a hung
one: notebook 2 about 2½ minutes, 4 about 3, 5 about 3¼. Most of it is Excel
I/O; each notebook reads and rewrites an 18 MB file. Notebook 3 has no
measurement here - it only has anything to do on a chapter with an
`external data\<Chapter>\` folder, and how long it takes depends entirely on
how many sheets are in there.

## Where everything lives

Nothing the pipeline reads or writes is inside this repo. Two roots, both under
`C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\`:

```
DATA COLLECTOR\
├── datacollector_received_quest_AR\   the Arabic questionnaires
│   └── Health\ Population\ Education\ Labor\ Poverty\ Housing\
├── datacollector_received_quest_EN\   the English ones, same six chapters
├── external data\                     published tables with no questionnaire behind them
│   └── Health\ Population\ Education\ Labor\ Poverty\ Housing\    - read by notebook 3
│       └── *_reshaped.xlsx            notebook 3's questionnaire-layout copy, beside each source file
├── translation dict.xlsx              the dictionary
└── value corrections.xlsx             confirmed readings for malformed Value cells

COMPENDIUM-ARAB SOCIETY\
├── merged_long_files\          <Chapter>_AR.xlsx, _EN.xlsx, _EN_questionnaires.xlsx, _EN_external.xlsx
├── tabulations\                <Chapter>_tabulations_<LANG>.xlsx
├── <chapter>_charts\           the SVGs, PNGs, workbook, index and findings
├── pipeline_inconsistencies_<Chapter>.txt   one per chapter, plus:
├── pipeline_inconsistencies_general.txt     findings with no chapter of their own
├── data_quality_review.txt     written by data quality/Compendium_Data_Quality.ipynb
└── codes\                      this repo
```

`translation dict.xlsx` has four columns — `col_ar`, `val_ar`, `col_en`,
`val_en` — plus `status`, which marks the rows the pipeline added. Read
**Arabic → English only** everywhere except notebook 4's external-data
section, which is not a back-translation of anything: it is giving a brand
new English value, from a file with no Arabic form anywhere in it, an Arabic
form for the first time, the same as notebook 4 already does for calculated
labels. Nothing should build a reverse map of the *existing*, already-correct
English content - that is the rule this was never an exception to. A row may
carry `val_ar`/`val_en` both blank on purpose - that teaches a **column**
name rather than a value, e.g. a raw sheet's mistyped header.
`update_dictionary()` (notebook 4, and its own copy in the data quality
notebook) keeps both kinds; do not reintroduce a `dropna()` across all four
columns, which silently discards the column-only rows.

`value corrections.xlsx` has `chapter`, `raw_value`, `corrected_value`, plus
`status` and `date` the same way. Written only by the data quality notebook's
`apply_review()`, read by notebook 1's `clean_one_value()` - see **Things that
look wrong but are deliberate** below.

## Where the data stands

The notebooks were renumbered and notebook 3b's translation step moved into
notebook 4 on 18 September 2026 (see git history) - every bullet below about
a run from before that date describes what the OLD numbering produced, not
the new one. The data itself did not move or change in that rename; only a
future re-run will go through the new split.

- **Population** is current: through the full pipeline since the reorder.
  389,075 rows, 317 of them calculated, 41 tabulation sheets per language, 36
  charts — the 1.x set, 2.1 to 2.5, and a pyramid per country. 2.6 and 2.7 are
  written but not drawn: no questionnaire reports child marriage or early
  childbearing, so the figures appear the moment such an indicator does.
- **Labor's long files and charts are current; its tabulations are not.**
  `Labor_AR.xlsx` (8 September) and `Labor_EN.xlsx` (10 September, re-run
  since) now match row for row - 168,597 each - so the "half-rebuilt" state
  documented here earlier is resolved. Its eight charts (6.1 to 6.8) were
  redrawn from the current file on 10 September and are correct.
  `tabulations\Labor_tabulations_*.xlsx` are still from 3-4 September, built
  from the old file - re-run notebook 5 on Labor before reading those two.
- **Poverty** is current: through the full pipeline, run 9 September 2026.
  8,757 rows, no calculated rows (Poverty carries none of notebook 2's
  population-based indicators), 5 tabulation sheets per language, all 5 charts
  (7.1 to 7.5). Two questionnaires have a genuine layout fault rather than a
  missing cover tab: Qatar's `Poverty_4` has a source-citation table but no
  response rows at all, and the United Arab Emirates' `Poverty_5` has its
  data-table header cell blank instead of reading `index`. Both are skipped and
  logged, not fixed — that's a source-file correction, not a code one.
- **Health has external data only, no questionnaire content.** Notebook 1 has
  never run on it - `Health_AR.xlsx` and `Health_EN.xlsx` exist only because
  the external-data step created them, most recently re-run 18 September 2026
  against an updated source file: 6,788 rows, all `Data Origin = External`,
  from the one sample file in `external data\Health\`: disability, health
  personnel and facility density, obesity, and expenditure, 22 countries,
  2000-2023. That run used the OLD, single 3b notebook (whole-sheet refusal,
  translation built in) - sheet `4.10` was skipped entirely, losing 781
  otherwise-good figures to one stray, unheaded value elsewhere in the same
  sheet. The new notebook 3 fixes exactly this (leaves out just the bad
  column, keeps the rest) but has not been re-run against the real file yet -
  do that before trusting Health's row count as final. 28 tabulation sheets
  per language, from the 13 September run. A real notebook 1 → 6 run on
  Health will fold questionnaire rows in alongside the external ones, not
  replace them.
- **Housing** is current: through the full pipeline, run 17 September 2026.
  58,689 rows from 22 questionnaires, no calculated rows (Housing carries
  none of notebook 2's population-based indicators), 8 tabulation sheets per
  language. All 7 hand-written charts draw (3.1-3.7) - country coverage
  improved sharply after the chart-logic fixes of 22 September (see **Things
  that look wrong but are deliberate** below and `charts_design.md`'s own
  "data guards" section), which stopped excluding a country from a share
  chart for an incomplete report: 3.1 went from 1 country to 11, 3.3 and 3.4
  from not drawing at all to 5 and 6, 3.5 from 1 to 7. Charts have not been
  re-run since the `total_slice()` fix specifically, which touches some of
  the same charts and may improve them further. No external data -
  `external data\Housing\` is empty.
- **Education** is current: through the full pipeline (notebook 3 a no-op -
  its `external data\Education\` is empty), run 14 September 2026. 48,648
  rows, no calculated rows (none of notebook 2's population-based
  indicators), 10 tabulation sheets per language, 7 charts (5.1-5.7). 268
  label corrections and 36 new Source citations closed on the 14 September
  run - net-new statistical bodies: Iraq's Central Statistical Organisation,
  Qatar's Planning and Statistics Authority, UNESCO Institute for Statistics
  (UIS), and several ministries of education across the region. Charts
  rebuilt 22 September 2026 after the `total_slice()` fix: the pupil-teacher
  ratio charts (5.5, 5.6) went from 1 country (Bahrain) to 15.

## Conventions

- `pandas` with `openpyxl`, `pathlib.Path` for every path — the paths contain
  spaces, never hardcode separators.
- Plain functions, no classes. One cell per step, each opening with a `"""`
  block saying what the cell does.
- `logging` for progress; `print()` only for the progress bar and per-row
  dictionary replacements, which are meant to be read inline.
- One `try`/`except` per sheet, with a `step` variable naming the stage. A bad
  sheet is logged and skipped — one malformed file never ends a run.
- Comments explain *why*, not what. Most of the odd-looking code here is
  load-bearing; see Known issues.
- Test against copies in the scratchpad. Never write to the user's folders to
  try something out.

## Things that look wrong but are deliberate

- **`Value` is parsed with `to_number()`, not `float()`.** Only 337 of 33,968
  population cells are numeric; the rest are text like `' 701 956 '` using
  spaces as thousand separators.
- **Source is translated but never fuzzy-matched.** Two citations differing by
  one digit score high enough to overwrite each other.
- **Notebook 4's Indicator resolution for external data never fuzzy-matches
  either, for a related but distinct reason.** A long, templated sentence
  carries its topic in a small fraction of the string: the external Health
  sample's "Government expenditure on health as % of Gross Domestic Product
  (GDP)" scored 0.628 - over the 0.6 cutoff - against the dictionary's
  *education*-spending indicator, on shared wording alone. Measured, not
  guessed; see `NEVER_FUZZY_MATCHED` in its own `extdict` cell. Country and
  Sex keep fuzzy matching there - proven useful, not just harmless, the same
  run reused "Comoros Islands" for the sample file's bare "Comoros" rather
  than filing a second, inconsistent country.
- **Missing dimension values render as `(not specified)`, never blank.** The
  tabulation layout blanks a repeated label to mean "same as above", so a blank
  would silently absorb a row into the group above it.
- **Every populated breakdown column becomes a nested row level**, not just the
  first — taking only the first collapsed 63% of Population's rows.
- **The sex ratio falls back to the sum of the age bands** when a country-year
  has bands but no `Age Total` row. The population is there either way, and
  dropping the year for the want of a total line would lose it for nothing. It
  is not the same figure, though — a band sum misses whoever the country left
  outside its bands, `Age unknown` included — so every one is logged as
  `sex ratio taken from the age bands`, and a year whose two sexes came by
  different routes is logged again as not quite comparable.
- **Population totals take only the `Total` slice of one indicator.** The
  by-nationality and by-area indicators describe the same people; summing them,
  or their parts, double-counts.
- **Merge keys are trimmed on both sides before merging.** `reshape_and_merge()`
  runs before `correct_with_dictionary()`, so an untrimmed key matched nothing
  and the row lost its citation silently.
- **`clean_one_value()` checks `value corrections.xlsx` before its own
  guesses, keyed on `(chapter, exact raw text)`.** A person confirms a reading
  once, in the data quality notebook's review file, and every occurrence of
  that same malformed text in that chapter is fixed the same way on every
  future run - not just the one cell that happened to be reviewed.
- **A share/breakdown chart (notebook 6) never excludes a country for an
  incomplete report or a total that does not sum to 100 - it charts exactly
  what was reported and logs the rest as a finding instead.** Most countries
  only report the categories they have any of at all, leaving the rest a
  silent zero rather than an explicit one - Bahrain's housing-type report is
  two categories summing to exactly 100, the other six never written down -
  so requiring every category before charting a country used to drop nearly
  everyone. `stacked_shares()`'s x-axis widens to fit a country whose
  reported categories sum past 100 (Qatar's housing-type report sums to
  200 - looks like doubled rows) rather than clipping it invisibly at 100.
  Full reasoning and the numbers it was measured on are in
  `charts_design.md`'s "data guards" section.
- **`total_slice()` (notebook 6) treats a blank breakdown column as its own
  total, not only an explicit label like `Nationality Total`.** Different
  countries use different conventions for the same thing - Bahrain is the
  only country that writes `Nationality Total` on its pupil-teacher ratio,
  every other country just leaves Nationality blank - and recognising only
  the explicit label meant every country using the blank convention was
  silently dropped the moment any country used the other one. Checked across
  all six chapters' current data: no country reports a figure both ways at
  once, so this creates no double-counted total today, but the explicit
  label wins over a blank duplicate if that ever changes.

## Known issues

- **Yemen is not in the compendium for Education, Health, Housing, Labor or
  Population.** Its five questionnaires sit directly under
  `datacollector_received_quest_AR\yemen\`, one level above where
  `discover_chapters()` looks - every other country's file is one level
  deeper, inside the matching `<Chapter>\` folder. `yemen` and a second stray
  folder, `country excel sheets` (two loose files, no chapter), both get
  discovered as if they were chapters themselves whenever `CHAPTERS = None`,
  which is the default in every notebook. Found running the data quality
  notebook with `CHAPTERS = None`; not fixed, because it means moving the
  user's source files rather than a code change. Move Yemen's five files each
  into their proper chapter subfolder to pick them up.
- **Two Population indicators labelled "(%)" hold absolute head-counts** for
  eight countries each, with values up to 29,258,382. This accounts for 97% of
  the data-gaps report's implausible-value findings. Needs fixing at source.
- **Labor has the same fault**: Algeria files head-counts (1,744 … 8,250) under
  `Persons outside the labor force … by reason of activity (percent)`, and Egypt
  reports one occupation share at 110%. Notebook 6's
  `drop_impossible_percentages()` refuses anything above 100 in a `(percent)`
  indicator and reports it per indicator and country, so Algeria simply does not
  appear on that chart. Also needs fixing at source.
- **13 country-year-sex cells where a reported total contradicts the sum of its
  own age bands**, some by three orders of magnitude. The sex-ratio calculation
  logs each one and uses the reported total, that being what the country stated.
- **3 country-year-sex cells report age bands but no all-ages total.** The sex
  ratio sums the bands for these; see above. Until 2026-09-08 this was reported
  as 256, which counted every `كلا الجنسين` (both sexes) row as a missing
  male/female total - those were never candidates for a ratio, and 253 of the
  256 were that.
- **Morocco's 2024 mean age at first marriage is 320 for men and 250 for
  women** — an age nobody has. `chart_age_at_first_marriage()` drops it with a
  `factor=2` scale guard and reports it, because on the one shared y scale of a
  small-multiples figure two impossible points flatten all nineteen countries
  onto the baseline. Needs fixing at source.
- **Oman files an average household size of 15.3 to 16.4 from 2011 to 2019**,
  dropping to 6.5 from 2022 — where every other country sits between 3.5 and 7,
  and where the published figure 2.1 runs 4 to 8. It is not dropped: it is
  internally consistent across nine years, so no guard here can tell a wrong
  measure from a real one, and the notebook refuses only what is provably
  impossible. It does stretch 2.1's axis to 16. Needs checking at source.
- **Several Poverty countries file an implausibly low national poverty
  headcount**: Jordan 0.07%, Lebanon 0.02%–0.9%, Qatar and the United Arab
  Emirates 0.0% exactly. Nothing about these values is internally inconsistent
  — each is one figure with no other year or series for that country to check
  it against — so 7.1 draws them as reported rather than guessing which
  countries meant a different number. Needs checking at source.
- **Libya's 2022 Gini index is 0.30**, against every other country's 25–48 on
  the same figure (7.3) — almost certainly filed as a fraction where every
  other country filed index points. A single point with nothing to compare it
  to cannot be told apart from a real value by any guard here. Needs fixing at
  source.
- **Two Health sheets use a legacy layout** and fail at `extract`:
  `Iraq health.xlsx` → `Iraq health - Health_4_a`, `jordan health.xlsx` →
  `Health_1_a`.
- **Health's external sample file, sheet `4.10`, has a stray value with no
  header anywhere above it** (Syrian Arab Republic, 2023, one cell one column
  too far right). This used to cost the whole sheet - 781 otherwise-good
  figures across all 22 countries - before notebook 3 was changed to leave
  out just that one column instead. The same sheet's "Number of beds per
  1000" and "population" columns read as two genuinely separate figures, not
  one header wrapped across two cells - the population column's values match
  the countries' real populations - but "Number of beds per 1000" alone reads
  as an incomplete sentence either way. Worth a source check regardless.
- **43 English terms have more than one Arabic spelling.** Harmless now that
  nothing is back-translated — the dictionary is only ever read Arabic →
  English, and several Arabic spellings mapping to one English term is exactly
  what it is for. It would matter again the moment anything inverted it. Mostly
  `Causes of death` variants and whitespace variants of the same citation —
  worth a dictionary cleanup regardless.
- Questionnaire cover tabs (`العنوان`, `قائمة الجداول`, `كيفية الإستخدام`,
  `البيانات الوصفية`) have no `index` column and are skipped by design.

## Environment

- Excel locks files it has open. Check `<Chapter>_*.xlsx` and
  `translation dict.xlsx` are closed before a run, and say which to close if a
  write fails.
- Everything is under OneDrive, including this repo. Sync has previously moved
  the git branch and made files appear to vanish. Prefer explicit verification
  over assuming a write landed - and re-verify a few minutes later, not just
  immediately after writing. `merged_long_files\Housing_AR.xlsx` and `_EN.xlsx`
  disappeared and reappeared several times in September before it turned out
  at least one of those was the user's own deletion, not OneDrive - a
  reminder that a surprising disappearance is worth asking about before
  assuming it is a sync bug. Housing has been stable since it was rebuilt on
  17 September - see **Where the data stands**.
- `pandas`, `openpyxl`, and for notebook 6 `matplotlib` and `Pillow`.
  `nbformat` is **not** installed — notebooks are edited as raw JSON, and any
  script that rewrites one must compile every code cell before saving.
- See **Running it** above for how to start a run either way. Claude's own
  runs never go through Jupyter - that's about what Claude can do, not a
  rule for you. A pipeline run can go through Claude directly or through the
  matching subagent in `.claude/agents/`, one per notebook.

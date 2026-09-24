# Arab Society Compendium — pipeline

- Six notebooks make the deliverables, and two more in `data quality/` check
  them. Nothing in `data quality/` changes data.

| # | Notebook | Reads | Writes |
|---|---|---|---|
| 1 | `Compendium_1_Long_Files.ipynb` | `datacollector_received_quest_<LANG>\<Chapter>\*.xlsx` | `<Chapter>_AR.xlsx`, and `<Chapter>_EN_questionnaires.xlsx` if English questionnaires exist |
| 2 | `Compendium_2_New_Indicators.ipynb` | `<Chapter>_AR.xlsx` | the calculated rows, in Arabic, appended to it |
| 3 | `Compendium_3_External_Data.ipynb` | `DATA COLLECTOR\external data\<Chapter>\*.xlsx` | `<Chapter>_EN_external.xlsx`, plus a `*_reshaped.xlsx` questionnaire-layout copy beside each source file |
| 4 | `Compendium_4_Translation.ipynb` | `<Chapter>_AR.xlsx` + `<Chapter>_EN_questionnaires.xlsx` + `<Chapter>_EN_external.xlsx` | `<Chapter>_EN.xlsx`; also appends external data's Arabic form to `<Chapter>_AR.xlsx` |
| 5 | `Compendium_5_Tabulations.ipynb` | `<Chapter>_EN.xlsx`, `<Chapter>_AR.xlsx` | `tabulations\<Chapter>_tabulations_<LANG>.xlsx` |
| 6 | `Compendium_6_Charts.ipynb` | `<Chapter>_EN.xlsx` | `<chapter>_charts\` — an SVG and a PNG per figure, `<chapter>_charts.xlsx`, `charts_index.csv`, `chart_data_findings.txt` |

- `<chapter>_charts.xlsx` lives only in `<chapter>_charts\`, beside the SVGs
  and PNGs it indexes.
  - Not copied into `merged_long_files\`, which is the long files' own — a
    copy there would just be one more place for the two to drift apart.
- Every long file lives in **`merged_long_files\`**, one folder for both
  languages.
- **1 → 2 → 3 → 4 in order**; each reads what the previous wrote.
  - 3 only has anything to do when a chapter has an
    `external data\<Chapter>\` folder, but always sits between 2 and 4 so 4
    can fold in whatever 3 found.
  - **5 and 6 are independent siblings** — both read the finished long
    files, neither needs the other, either can be re-run alone — and both
    come after 4 to pick up calculated indicators and anything external.
- **Notebook 3 reads published indicator tables that never went through a
  questionnaire**, one folder per chapter under
  `DATA COLLECTOR\external data\<Chapter>\`.
  - Nothing about their layout is assumed — the real sample file had six
    sheets in three different header shapes.
  - A column it can't confidently name is left out and reported, without
    discarding the rest of that sheet's good columns.
  - Follows the `reshape-external-data-questionnaire-layout` skill: besides
    the rows written to `<Chapter>_EN_external.xlsx`, it saves a reshaped,
    questionnaire-layout copy of each source file beside it, for a person to
    check against the original.
  - **It does no translation** — only extraction and reshaping; notebook 4
    decides every value's language, both directions.
  - Read notebook 3's own intro cell before changing it — most of what
    looks arbitrary there is a finding from the real file, not a guess.
- **Notebooks 1–5 record what they find wrong with the source data**, one
  file per chapter: `pipeline_inconsistencies_<Chapter>.txt`, beside the
  codes folder, plus `pipeline_inconsistencies_general.txt` for a
  dictionary-level finding with no chapter of its own.
  - Notebook 1 logs every column/value match against the dictionary
    (corrected or not) and every Value it corrected.
  - Notebook 2 logs contradictions in the calculated figures.
  - Notebook 3 logs sheets/columns it couldn't confidently read.
  - Notebook 4 logs values with no translation — `4. TRANSLATION` for
    Arabic → English, `4b. EXTERNAL DATA` for external data's own
    English → Arabic gaps.
  - Notebook 5 logs tabulations that came out wrong.
  - Every record carries the country, indicator and year, so a finding
    traces back to the cell.
  - These are findings about the questionnaires, not the code — they outlive
    the run and can go back to the country that reported them.
- Each notebook owns one named section (`### 1. LONG FILES ###`, and so on)
  and rewrites only that section **within its own chapter's file**.
  - A chapter-scoped run has never overwritten another notebook's findings,
    but before this split it did overwrite another **chapter's**: running
    notebook 1 on Housing silently replaced what it had found on Education
    the day before, because one shared file didn't track which chapter a
    section belonged to.
  - `save_inconsistencies()` now takes `chapters=` explicitly, so even a
    clean chapter gets its section replaced with "Nothing found" instead of
    left stale.
- **Every dictionary correction is logged, not only the ones the fuzzy
  matcher gives up on.**
  - `correct_with_dictionary()` used to log a label only when nothing scored
    above `FUZZY_MATCH_CUTOFF` — a silently auto-fixed spelling never
    appeared anywhere but the console.
  - It now logs both: `column name corrected` / `value corrected` for fixes,
    `column name not in the dictionary` / `value not in the dictionary` for
    misses — the full list of source-data changes lives in one place.
- Notebook 6 keeps its own `chart_data_findings.txt` per chart folder rather
  than a shared-log section, because it refuses figures the other five pass
  through — a value orders of magnitude off its own series, or sexes that
  don't sum to their reported total.
- **Notebook 1 cleans the Value column and reports every change.**
  - A number wrapped in a recognized unit phrase is scaled to match:
    `بالالف` and the typo `بالاف` both mean "thousands", so
    `7845(الاعداد بالالف)` → `7845000`.
  - A placeholder like `-` becomes blank, and so does a cell holding only
    spaces — not an empty cell, and otherwise it passes every "is it blank"
    test through to an unplottable chart value.
  - `51.2+1.2` is read as a sum.
  - An unrecognized wrapping phrase is just dropped, keeping the bare number
    — reported every time, since an unfamiliar phrase could carry a
    multiplier too, and only the reporting country can say for sure.
- **A unit note describes the whole column it sits in, not the one cell it's
  written on.**
  - Morocco's 2024 population is `1444`, `1745`, `1815`, … with
    `الاعداد بالالف` typed into only the first cell.
  - Scaling just that cell would leave it 1,000× larger than its neighbours,
    so the multiplier is applied to every figure sharing that
    indicator/country/year, and the block is reported with the count moved.
  - Scope is the year, because the same file has 2010–2022 in whole units
    and only 2024 in thousands.
- **Why `<Chapter>_EN_questionnaires.xlsx` has its own name.**
  - Notebook 1's English output and notebook 4's are different files — one
    is English questionnaires made long, the other translated Arabic with
    those rows appended.
  - Sharing `<Chapter>_EN.xlsx` would make notebook 4 read and overwrite the
    same file it writes, so a second run would append its own output to
    itself and duplicate every row.
  - The Arabic side needs no such trick — notebook 2 strips its own
    previously-added rows before appending, so writing back to
    `<Chapter>_AR.xlsx` in place is idempotent.
- **Calculations run before translation, on the Arabic file.**
  - They used to run on English, requiring the new rows to be translated
    *back* into Arabic — a round trip through an inverted dictionary that's
    lossy wherever several Arabic spellings share one English term (43 terms
    currently).
  - Doing the arithmetic in Arabic means calculated rows exist before
    anything is translated, and the whole file goes one way, once.
  - **Never reintroduce a back-translation.**
- Notebook 2's code uses English names — `"Male"`, `"Age Total"`,
  `"Population size by nationality"` — and `term()` resolves each into what
  the Arabic file says.
  - An unresolved name is reported, not silently passed through, since a
    calculation built on it matches nothing and quietly produces no rows.
- **Checking the data lives in `data quality/`**, its own `CLAUDE.md`. Two
  parts of one notebook, sharing nothing but a file:
  - **Part 1** scans the raw questionnaires before notebook 1 runs and
    writes `data_quality_review.txt` (labels the dictionary can't match,
    Value cells `clean_one_value()` can't parse) for a person to edit and
    Claude to `apply`, plus one brief, read-only
    `Data quality issues before pipeline execution_<Chapter>.txt` per
    chapter.
  - **Part 2** reads the finished `<Chapter>_EN.xlsx` files after notebook 4
    and writes `data_gaps_report.xlsx` plus the GitHub Pages dashboard's
    `docs/data.js` — completeness and contradictions across the whole
    finished series.
  - Neither changes data on its own; Part 1's one write only happens from a
    person's own saved decision.
  - Details, fields and known caveats: `data quality/CLAUDE.md`.
- **How the charts look is settled in `charts_design.md`**, beside notebook
  6 — colours, fonts, layout rules, data guards, and the trade-offs each was
  chosen on.
  - Read it before changing anything visual; several of the odd-looking
    choices are load-bearing.
- **Every chapter's charts are copies of the figures the compendium
  prints.**
  - Originals:
    `COMPENDIUM-ARAB SOCIETY\old files\population old charts\<chapter>\`
    (plotly SVGs, `OLD_CHARTS_PATH` in the notebook).
  - Notebook 6 has a hand-written set per chapter, numbered to match
    (`1.1`–`2.7` Population, `3.x` Housing, `4.x` Health, `5.x` Education,
    `6.x` Labor, `7.x` Poverty); the old data-driven builder is now only the
    fallback for a chapter with no such set.
  - SVG text stays text, so a legend or axis label reads straight out with
    `grep`.
- Paths live outside this repo, under
  `C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\`.

## Filling dictionary gaps — do this without being asked

- **When the user asks to run the pipeline, closing dictionary gaps is part
  of the job**, not a separate ask. Two kinds, both must close before a run
  counts finished.
- This is the *during-and-after* loop — gaps found while running notebooks 2
  and 4, closed by Claude's own judgement.
  - The data quality notebook is the *before* loop — the same two kinds,
    found by reading raw questionnaires ahead of a run, closed by a person
    via `data_quality_review.txt`.
  - The two are meant to meet in the middle: the more the before-loop
    closes, the fewer a real run turns up.

### Kind 1 — a value the questionnaires used

- A country writes a survey name the dictionary hasn't seen.
- Notebook 4 finds these by comparing the table before and after
  translation — an untranslated value passed through is the gap.
- Always the English side, since everything travels Arabic → English.

### Kind 2 — a label the pipeline invented

- The calculations invent indicator titles and age-group labels
  (`Sex ratio, 2010-2025 (per 100 females)`, `<15 years`, …) that appear in
  **no questionnaire**.
- Notebook 2 needs their Arabic to write the rows at all, so a missing one
  is caught immediately: `term()` reports it instead of falling back
  silently, listed as "term missing from the dictionary".

### Kind 3 — external data introduces a new English-origin value

- Notebook 3's `<Chapter>_EN_external.xlsx` output is genuinely new English
  content with no Arabic form anywhere yet.
- Notebook 4's external-data section finds these the same way
  (`find_external_gaps()`) but travelling English → Arabic, since this
  content started in English — giving it an Arabic form for the first time,
  never back-translating anything already correct.
- Closed the same way as the other two kinds; see notebook 4's own intro
  cell for the two-part run this needs (append first, review
  `EXTERNAL_GAPS`, `update_dictionary()`, then `apply_external_gaps()`).

### The loop, any kind

1. Run the notebook.
2. Read them from that chapter's own `pipeline_inconsistencies_<Chapter>.txt`
   — no spreadsheet is written. Each carries the country, indicator and year
   of an example row.
3. Translate them yourself. Use the official English name of a statistical
   body where one exists — search `translation dict.xlsx` first, so wording
   stays consistent with what is already there.
4. Call `update_dictionary(filled)`. It backs the file up first, skips rows
   already present, and marks what it adds with `status = "updated"` so
   machine translations can be told from hand-typed ones.
5. Re-run the notebook and confirm the gap list is empty.
6. Report what you added, and flag any translation involving real judgement.

- **Attach translations by position, never by retyping the Arabic or
  English keys** — a retyped string that differs by one invisible character
  (non-breaking space, different letter form) silently fails to match.
  - Assert a couple of anchor rows before writing.

## Running it

Two ways, and both are fine.

### Running it yourself, in Jupyter or VS Code

- Open the notebook and run its cells top to bottom, same as any other
  notebook — nothing about these requires a special runner.
- To limit a run to one chapter, edit `CHAPTERS` in the cell whose id is
  `config`:

```python
CHAPTERS = ["Poverty"]      # instead of None
```

- `None` means every chapter found on disk.
- Nothing resets this for you, so set it back to `None` (or to the chapter
  you actually want) before the next full run.

### Running it through Claude

- Claude has no Jupyter kernel, so a notebook is run by reading its JSON and
  `exec`-ing each code cell's source into one namespace, in cell order —
  after the `config` cell has run, `CHAPTERS` is overridden in that
  namespace before the rest continue.
- `run_pipeline.py`, if it is in the repo, is exactly that, generalised and
  committed so it is not retyped every session.
  - If it is not there, Claude writes the same ~15 lines as a scratch script
    instead — the technique does not depend on the file existing, only on a
    set of committed notebooks to read.

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py -u run_pipeline.py 2 4 5 --only Population > run.log 2>&1
```

- Then **poll the log** — never wait blind on a long run.
  - `PYTHONUTF8=1` is not optional: the Arabic in the progress output kills
    the default Windows console encoding.
- `--only` overrides `CHAPTERS` the same way the manual edit above does.
  Repeat it for several chapters.
- Measured on Population, 389,075 rows — useful for telling a slow run from
  a hung one: notebook 2 about 2½ minutes, 4 about 3, 5 about 3¼.
  - Most of it is Excel I/O; each notebook reads and rewrites an 18 MB file.
  - Notebook 3 has no measurement here — it only has anything to do on a
    chapter with an `external data\<Chapter>\` folder, and how long it takes
    depends entirely on how many sheets are in there.

## Where everything lives

Nothing the pipeline reads or writes is inside this repo. Two roots, both
under `C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\`:

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
├── data_quality_review.txt     written by data quality/Compendium_Data_Quality.ipynb, Part 1
├── Data quality issues before pipeline execution_<Chapter>.txt   also Part 1, one per chapter
└── codes\                      this repo
```

- `translation dict.xlsx` has four columns — `col_ar`, `val_ar`, `col_en`,
  `val_en` — plus `status`, which marks the rows the pipeline added.
  - Read **Arabic → English only** everywhere except notebook 4's
    external-data section, which is not a back-translation of anything: it
    is giving a brand new English value, from a file with no Arabic form
    anywhere in it, an Arabic form for the first time, the same as notebook
    4 already does for calculated labels.
  - Nothing should build a reverse map of the *existing*, already-correct
    English content — that is the rule this was never an exception to.
  - A row may carry `val_ar`/`val_en` both blank on purpose — that teaches a
    **column** name rather than a value, e.g. a raw sheet's mistyped header.
  - `update_dictionary()` (notebook 4, and its own copy in the data quality
    notebook) keeps both kinds; do not reintroduce a `dropna()` across all
    four columns, which silently discards the column-only rows.
- `value corrections.xlsx` has `chapter`, `raw_value`, `corrected_value`,
  plus `status` and `date` the same way.
  - Written only by the data quality notebook's `apply_review()`, read by
    notebook 1's `clean_one_value()` — see **Things that look wrong but are
    deliberate** below.

## Where the data stands

- **Population** is current, through the full pipeline since the reorder.
  - 389,075 rows, 317 calculated, 41 tabulation sheets/language.
  - 36 charts (1.x, 2.1–2.5, a pyramid per country).
  - 2.6/2.7 are written but undrawn — no questionnaire reports child
    marriage or early childbearing yet.
- **Labor's long files and charts are current; its tabulations are not.**
  - `Labor_AR.xlsx`/`_EN.xlsx` match row for row (168,597 each, re-run 10
    September).
  - Charts 6.1–6.8 redrawn 10 September, correct.
  - `tabulations\Labor_tabulations_*.xlsx` are still from 3–4 September,
    built from the old file — re-run notebook 5 on Labor before reading
    those.
- **Poverty** is current, full pipeline run 9 September 2026.
  - 8,757 rows, no calculated rows (none of notebook 2's population-based
    indicators), 5 tabulation sheets/language, all 5 charts (7.1–7.5).
  - Qatar's `Poverty_4` (source-citation table, no response rows) and the
    United Arab Emirates' `Poverty_5` (data-table header cell blank instead
    of `index`) are genuine source-file faults — skipped and logged, not
    fixed.
- **Health has external data only, no questionnaire content.**
  - Notebook 1 has never run on it — `Health_AR.xlsx`/`_EN.xlsx` exist only
    from the external-data step, most recently re-run 18 September 2026
    against an updated source: 6,788 rows, all `Data Origin = External`
    (disability, health personnel/facility density, obesity, expenditure;
    22 countries, 2000–2023).
  - That run used the old, single "3b" external-data-plus-translation
    notebook (whole-sheet refusal) — sheet `4.10` was skipped entirely,
    losing 781 otherwise-good figures to one stray, unheaded value.
  - The current notebook 3 fixes exactly this (leaves out just the bad
    column) but hasn't been re-run against the real file yet — do that
    before trusting Health's row count as final.
  - 28 tabulation sheets/language, from the 13 September run.
  - A real 1 → 6 run will fold questionnaire rows in alongside the external
    ones, not replace them.
- **Housing** is current, full pipeline run 17 September 2026.
  - 58,689 rows from 22 questionnaires, no calculated rows, 8 tabulation
    sheets/language.
  - All 7 hand-written charts draw (3.1–3.7) — coverage improved sharply
    after the 22 September chart-logic fixes (see **Things that look wrong
    but are deliberate** and `charts_design.md`'s "data guards"): 3.1 went
    from 1 country to 11, 3.3/3.4 from undrawn to 5/6, 3.5 from 1 to 7.
  - Not yet re-run since the `total_slice()` fix specifically, which
    touches some of the same charts.
  - No external data — `external data\Housing\` is empty.
- **Education** is current, full pipeline run 14 September 2026 (notebook 3
  a no-op — `external data\Education\` is empty).
  - 48,648 rows, no calculated rows, 10 tabulation sheets/language, 7
    charts (5.1–5.7).
  - 268 label corrections and 36 new Source citations closed on the 14
    September run — net-new statistical bodies: Iraq's Central Statistical
    Organisation, Qatar's Planning and Statistics Authority, UNESCO
    Institute for Statistics (UIS), and several ministries of education.
  - Charts rebuilt twice on 22 September: first after the `total_slice()`
    fix (5.6 pupil-teacher-secondary went from 1 country to 13), then again
    after fixing `chart_pupil_teacher()`'s primary/secondary level-picking,
    which had still capped 5.5 at 2 countries (Egypt, Jordan) even after
    the `total_slice()` fix — see **Things that look wrong but are
    deliberate**.
  - 5.5 now draws 15 countries.

## Conventions

- `pandas` with `openpyxl`, `pathlib.Path` for every path — the paths contain
  spaces, never hardcode separators.
- Plain functions, no classes.
- One cell per step, each opening with a `"""` block saying what the cell
  does.
- `logging` for progress; `print()` only for the progress bar and per-row
  dictionary replacements, which are meant to be read inline.
- One `try`/`except` per sheet, with a `step` variable naming the stage.
  - A bad sheet is logged and skipped — one malformed file never ends a run.
- Comments explain *why*, not what.
  - Most of the odd-looking code here is load-bearing; see Known issues.
- Test against copies in the scratchpad.
  - Never write to the user's folders to try something out.

## Things that look wrong but are deliberate

- **`Value` is parsed with `to_number()`, not `float()`.**
  - Only 337 of 33,968 population cells are numeric; the rest are text like
    `' 701 956 '` using spaces as thousand separators.
- **Source is translated but never fuzzy-matched.**
  - Two citations differing by one digit score high enough to overwrite each
    other.
- **Notebook 4's Indicator resolution for external data never fuzzy-matches
  either, for a related but distinct reason.**
  - A long, templated sentence carries its topic in a small fraction of the
    string: the external Health sample's "Government expenditure on health
    as % of Gross Domestic Product (GDP)" scored 0.628 — over the 0.6
    cutoff — against the dictionary's *education*-spending indicator, on
    shared wording alone.
  - Measured, not guessed; see `NEVER_FUZZY_MATCHED` in its own `extdict`
    cell.
  - Country and Sex keep fuzzy matching there — proven useful, not just
    harmless: the same run reused "Comoros Islands" for the sample file's
    bare "Comoros" rather than filing a second, inconsistent country.
- **Missing dimension values render as `(not specified)`, never blank.**
  - The tabulation layout blanks a repeated label to mean "same as above",
    so a blank would silently absorb a row into the group above it.
- **Every populated breakdown column becomes a nested row level**, not just
  the first.
  - Taking only the first collapsed 63% of Population's rows.
- **The sex ratio falls back to the sum of the age bands** when a
  country-year has bands but no `Age Total` row.
  - The population is there either way, and dropping the year for want of a
    total line would lose it for nothing.
  - It's not the same figure, though — a band sum misses whoever the
    country left outside its bands (`Age unknown` included) — so every one
    is logged as `sex ratio taken from the age bands`.
  - A year whose two sexes came by different routes is logged again as not
    quite comparable.
- **Population totals take only the `Total` slice of one indicator.**
  - The by-nationality and by-area indicators describe the same people;
    summing them, or their parts, double-counts.
- **Merge keys are trimmed on both sides before merging.**
  - `reshape_and_merge()` runs before `correct_with_dictionary()`, so an
    untrimmed key matched nothing and the row lost its citation silently.
- **`clean_one_value()` checks `value corrections.xlsx` before its own
  guesses, keyed on `(chapter, exact raw text)`.**
  - A person confirms a reading once, in the data quality notebook's review
    file, and every occurrence of that same malformed text in that chapter
    is fixed the same way on every future run — not just the one cell that
    happened to be reviewed.
- **A share/breakdown chart (notebook 6) never excludes a country for an
  incomplete report or a total that doesn't sum to 100 — it charts exactly
  what was reported and logs the rest as a finding.**
  - Most countries only report the categories they have any of, leaving the
    rest a silent zero rather than an explicit one — Bahrain's housing-type
    report is two categories summing to exactly 100, the other six never
    written down — so requiring every category before charting a country
    used to drop nearly everyone.
  - `stacked_shares()`'s x-axis widens to fit a country whose reported
    categories sum past 100 (Qatar's housing-type report sums to 200 —
    looks like doubled rows) rather than clipping it invisibly at 100.
  - Full reasoning and the numbers it was measured on are in
    `charts_design.md`'s "data guards" section.
- **`total_slice()` (notebook 6) treats a blank breakdown column as its own
  total, not only an explicit label like `Nationality Total`.**
  - Different countries use different conventions for the same thing —
    Bahrain is the only country that writes `Nationality Total` on its
    pupil-teacher ratio, every other country just leaves Nationality blank —
    and recognising only the explicit label meant every country using the
    blank convention was silently dropped the moment any country used the
    other one.
  - Checked across all six chapters' current data: no country reports a
    figure both ways at once, so this creates no double-counted total
    today, but the explicit label wins over a blank duplicate if that ever
    changes.
- **`chart_pupil_teacher()`'s primary figure (5.5) tries "Primary" before
  falling back to "Basic", per country — not a single, alphabetically-picked
  label.**
  - Jordan and Egypt file their primary-equivalent stage as "Basic" (grades
    1–9/10); every other country uses "Primary".
  - `matching_values()` sorts its matches alphabetically, so a single
    pattern `"primary|basic"` picked "Basic" — 2 countries — over
    "Primary" — 14 — for *every* country, not just Jordan's, capping 5.5 at
    2 countries even after the `total_slice()` fix above fixed 5.6.
  - `level_slice()` now applies the same preferred/fallback rule
    `preferred_edition()` uses for by-nationality / by-area splits: the
    first pattern that covers a country wins, a later one only fills the
    gap.

## Known issues

- **Yemen is not in the compendium for Education, Health, Housing, Labor or
  Population.**
  - Its five questionnaires sit directly under
    `datacollector_received_quest_AR\yemen\`, one level above where
    `discover_chapters()` looks — every other country's file is one level
    deeper, inside the matching `<Chapter>\` folder.
  - `yemen` and a second stray folder, `country excel sheets` (two loose
    files, no chapter), both get discovered as if they were chapters
    themselves whenever `CHAPTERS = None`, which is the default in every
    notebook.
  - Not fixed, because it means moving the user's source files rather than
    a code change. Move Yemen's five files each into their proper chapter
    subfolder to pick them up.
- **Two Population indicators labelled "(%)" hold absolute head-counts** for
  eight countries each, with values up to 29,258,382.
  - 97% of the data-gaps report's implausible-value findings.
  - Needs fixing at source.
- **Labor has the same fault**: Algeria files head-counts (1,744 … 8,250)
  under `Persons outside the labor force … by reason of activity (percent)`,
  and Egypt reports one occupation share at 110%.
  - Notebook 6's `drop_impossible_percentages()` refuses anything above 100
    in a `(percent)` indicator and reports it per indicator and country, so
    Algeria simply doesn't appear on that chart.
  - Also needs fixing at source.
- **13 country-year-sex cells where a reported total contradicts the sum of
  its own age bands**, some by three orders of magnitude.
  - The sex-ratio calculation logs each one and uses the reported total,
    that being what the country stated.
- **3 country-year-sex cells report age bands but no all-ages total.**
  - The sex ratio sums the bands for these; see above.
- **Morocco's 2024 mean age at first marriage is 320 for men and 250 for
  women** — an age nobody has.
  - `chart_age_at_first_marriage()` drops it with a `factor=2` scale guard
    and reports it, because on the one shared y scale of a small-multiples
    figure two impossible points flatten all nineteen countries onto the
    baseline.
  - Needs fixing at source.
- **Oman files an average household size of 15.3 to 16.4 from 2011 to
  2019**, dropping to 6.5 from 2022 — every other country sits between 3.5
  and 7, and the published figure 2.1 runs 4 to 8.
  - Not dropped: it's internally consistent across nine years, so no guard
    here can tell a wrong measure from a real one, and the notebook refuses
    only what's provably impossible.
  - It does stretch 2.1's axis to 16.
  - Needs checking at source.
- **Several Poverty countries file an implausibly low national poverty
  headcount**: Jordan 0.07%, Lebanon 0.02%–0.9%, Qatar and the United Arab
  Emirates 0.0% exactly.
  - Nothing about these values is internally inconsistent — each is one
    figure with no other year or series for that country to check it
    against — so 7.1 draws them as reported rather than guessing which
    countries meant a different number.
  - Needs checking at source.
- **Libya's 2022 Gini index is 0.30**, against every other country's 25–48
  on the same figure (7.3) — almost certainly filed as a fraction where
  every other country filed index points.
  - A single point with nothing to compare it to cannot be told apart from
    a real value by any guard here.
  - Needs fixing at source.
- **Two Health sheets use a legacy layout** and fail at `extract`:
  - `Iraq health.xlsx` → `Iraq health - Health_4_a`
  - `jordan health.xlsx` → `Health_1_a`
- **Health's external sample file, sheet `4.10`, has a stray value with no
  header anywhere above it** (Syrian Arab Republic, 2023, one cell one
  column too far right).
  - This used to cost the whole sheet — 781 otherwise-good figures across
    all 22 countries — before notebook 3 was changed to leave out just that
    one column instead.
  - The same sheet's "Number of beds per 1000" and "population" columns
    read as two genuinely separate figures, not one header wrapped across
    two cells — the population column's values match the countries' real
    populations — but "Number of beds per 1000" alone reads as an
    incomplete sentence either way.
  - Worth a source check regardless.
- **43 English terms have more than one Arabic spelling.**
  - Harmless now that nothing is back-translated — the dictionary is only
    ever read Arabic → English, and several Arabic spellings mapping to one
    English term is exactly what it is for.
  - It would matter again the moment anything inverted it.
  - Mostly `Causes of death` variants and whitespace variants of the same
    citation — worth a dictionary cleanup regardless.
- Questionnaire cover tabs (`العنوان`, `قائمة الجداول`, `كيفية الإستخدام`,
  `البيانات الوصفية`) have no `index` column and are skipped by design.

## Environment

- Excel locks files it has open.
  - Check `<Chapter>_*.xlsx` and `translation dict.xlsx` are closed before a
    run, and say which to close if a write fails.
- Everything is under OneDrive, including this repo.
  - Sync has previously moved the git branch and made files appear to
    vanish.
  - Prefer explicit verification over assuming a write landed — and
    re-verify a few minutes later, not just immediately after writing.
- `pandas`, `openpyxl`, and for notebook 6 `matplotlib` and `Pillow`.
  - `nbformat` is **not** installed — notebooks are edited as raw JSON, and
    any script that rewrites one must compile every code cell before
    saving.
- See **Running it** above for how to start a run either way.
  - Claude's own runs never go through Jupyter — that's about what Claude
    can do, not a rule for you.
  - A pipeline run can go through Claude directly or through the matching
    subagent in `.claude/agents/`, one per notebook.

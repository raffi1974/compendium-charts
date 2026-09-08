# Arab Society Compendium — pipeline

Five notebooks. Four are a chain; the fifth is a diagnostic.

| # | Notebook | Reads | Writes |
|---|---|---|---|
| 1 | `Compendium_1_Long_Files.ipynb` | `datacollector_received_quest_<LANG>\<Chapter>\*.xlsx` | `<Chapter>_AR.xlsx`, and `<Chapter>_EN_questionnaires.xlsx` if English questionnaires exist |
| 2 | `Compendium_2_New_Indicators.ipynb` | `<Chapter>_AR.xlsx` | the calculated rows, in Arabic, appended to it |
| 3 | `Compendium_3_Translation.ipynb` | `<Chapter>_AR.xlsx` + `<Chapter>_EN_questionnaires.xlsx` | `<Chapter>_EN.xlsx` |
| 4 | `Compendium_4_Tabulations.ipynb` | `<Chapter>_EN.xlsx`, `<Chapter>_AR.xlsx` | `tabulations\<Chapter>_tabulations_<LANG>.xlsx` |

Every long file lives in **`merged_long_files\`**, one folder for both languages.

Run 1 → 2 → 3 → 4 in order; each reads what the previous wrote. Tabulation is
last so it picks up the calculated indicators.

**All four notebooks record what they find wrong with the source data** in
`pipeline_inconsistencies.txt`, beside the codes folder. Notebook 1 the sheets
it could not read, the labels it could not match and every Value it had to
correct; notebook 2 the contradictions in the figures; notebook 3 the values
with no translation; notebook 4 the tabulations that came out wrong. Every
record carries the country, indicator and year it came from, so a finding can be
traced back to the cell.

**Notebook 1 cleans the Value column and reports every change.** A number
wrapped in text keeps only the number (`7845(الاعداد بالالف)` → `7845`), and a
placeholder like `-` becomes blank. Dropping `الاعداد بالالف` also drops the
fact that the figure is in thousands, which leaves it a thousand times smaller
than its neighbours — which is exactly why each one is reported rather than
quietly fixed.

Each notebook owns a numbered section and rewrites only its own, so the file
always reflects the latest run of each step and stays in step order whatever
order they ran in. These are findings about the questionnaires, not the code, so
they outlive the run and can go back to the country that reported them.

**Why `<Chapter>_EN_questionnaires.xlsx` has its own name.** Notebook 1's
English output and notebook 3's are different files — one is English
questionnaires made long, the other is the translated Arabic with those rows
appended. Sharing `<Chapter>_EN.xlsx` would make notebook 3 read and overwrite
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

**Checking the data lives in `data quality/`**, with its own `CLAUDE.md`. It holds `Compendium_Data_Quality.ipynb` (structural checks
on the questionnaires, contradiction checks on the final files) and
`Compendium_Data_Gaps.ipynb` (completeness, and the dashboard in `docs/` at the
repository root).
Nothing there changes data — it only measures and reports. Run it after step 3,
before building tabulations on figures that have not been sanity-checked.

Paths live outside this repo, under
`C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\`.

## Filling dictionary gaps — do this without being asked

**When the user asks to run the pipeline, treat closing dictionary gaps as part
of the job**, not as a separate request to come back for. There are two kinds,
and both must be closed before the run counts as finished.

### Kind 1 — a value the questionnaires used

A country writes a survey name the dictionary has not seen. Notebook 3 finds
these by comparing the table before and after translation: a value with no entry
passes through unchanged, and that is the gap. What is missing is always the
English side now that everything travels Arabic → English.

### Kind 2 — a label the pipeline invented

The calculations create indicator titles and age-group labels (`Sex ratio,
2010-2025 (per 100 females)`, `<15 years`, …) that appear in **no
questionnaire**. Notebook 2 needs their *Arabic* to write the rows at all, so a
missing one is caught immediately: `term()` reports it instead of falling back
silently, and the run lists it under "term missing from the dictionary".

### The loop, either kind

1. Run the notebook.
2. Read them from `pipeline_inconsistencies.txt` — no spreadsheet is written.
   Each carries the country, indicator and year of an example row.
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

## Known issues

- **Two Population indicators labelled "(%)" hold absolute head-counts** for
  eight countries each, with values up to 29,258,382. This accounts for 97% of
  the data-gaps report's implausible-value findings. Needs fixing at source.
- **13 country-year-sex cells where a reported total contradicts the sum of its
  own age bands**, some by three orders of magnitude. The sex-ratio calculation
  logs each one and uses the reported total, that being what the country stated.
- **3 country-year-sex cells report age bands but no all-ages total.** The sex
  ratio sums the bands for these; see above. Until 2026-09-08 this was reported
  as 256, which counted every `كلا الجنسين` (both sexes) row as a missing
  male/female total - those were never candidates for a ratio, and 253 of the
  256 were that.
- **Two Health sheets use a legacy layout** and fail at `extract`:
  `Iraq health.xlsx` → `Iraq health - Health_4_a`, `jordan health.xlsx` →
  `Health_1_a`.
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
  over assuming a write landed.
- Run notebooks by executing their cells from a script (`py -u`), polling a log
  file for the progress bar. Do not use a subagent for pipeline runs.

# Arab Society Compendium — pipeline

Five notebooks. Four are a chain; the fifth is a diagnostic.

| # | Notebook | Reads | Writes |
|---|---|---|---|
| 1 | `Compendium_1_Long_Files.ipynb` | `DATA COLLECTOR\datacollector_received_quest_<LANG>\<Chapter>\*.xlsx` | `merged longfiles_<LANG>\<Chapter>_<LANG>.xlsx` |
| 2 | `Compendium_2_Translation.ipynb` | both `merged longfiles_*` | `<Chapter>_EN.xlsx` |
| 3 | `Compendium_3_New_Indicators.ipynb` | `<Chapter>_EN.xlsx` + `merged longfiles_AR\` | calculated rows added to `<Chapter>_EN.xlsx`; `<Chapter>_AR.xlsx` |
| 4 | `Compendium_4_Tabulations.ipynb` | both final files | `tabulations\<Chapter>_tabulations_<LANG>.xlsx` |

Run 1 → 2 → 3 → 4 in order; each reads what the previous wrote. Tabulation is
last so it picks up the calculated indicators.

**Notebook 3 translates only the rows it creates.** It used to back-translate
the whole English file into Arabic, which meant pushing hundreds of thousands of
rows through an inverted dictionary — lossy exactly where several Arabic
spellings share one English translation (43 terms on the current data). There is
no need: the Arabic long file from notebook 1 is the *original*, straight from
the questionnaires. Only the calculated rows are missing from it, so only those
are translated. Never reintroduce a whole-file back-translation.

**Checking the data lives in `data quality/`**, with its own `CLAUDE.md`. It holds `Compendium_Data_Quality.ipynb` (structural checks
on the questionnaires, contradiction checks on the final files) and
`Compendium_Data_Gaps.ipynb` (completeness, and the dashboard in `docs/` at the
repository root).
Nothing there changes data — it only measures and reports. Run it after step 2,
before building tabulations on figures that have not been sanity-checked.

Paths live outside this repo, under
`C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\`.

## Filling dictionary gaps — do this without being asked

**When the user asks to run the pipeline, treat closing dictionary gaps as part
of the job**, not as a separate request to come back for. There are two kinds,
and both must be closed before the run counts as finished.

### Kind 1 — a value the questionnaires used

A country writes a survey name the dictionary has not seen. Notebooks 2 and 3
find these by comparing a table before and after translation: a value with no
entry passes through unchanged, and that is the gap. The blank column is
`val_en` in notebook 2, `val_ar` in notebook 3.

### Kind 2 — a label the pipeline invented

The calculations create indicator titles and age-group labels (`Sex ratio,
2010-2025 (per 100 females)`, `<15 years`, …) that appear in **no
questionnaire**, so no before/after comparison can ever surface them. Notebook 3
reports any it could not translate when it builds the Arabic rows, and
`export_gaps(REPORTS)` writes them out with `val_ar` blank.

Without this they come out in English from notebook 3 and nothing flags it. Any
new calculation added later is caught automatically, because the check is
derived from the same constants the calculations use.

### The loop, either kind

1. Run the notebook.
2. Call `export_untranslated(REPORTS)` in notebook 2 for kind 1,
   `export_gaps(REPORTS)` in notebook 3 for kind 2.
3. Translate them yourself. Use the official English name of a statistical body
   where one exists — search `translation dict.xlsx` first, so wording stays
   consistent with what is already there.
4. Call `update_dictionary(filled)`. It backs the file up first, skips rows
   already present, and writes `translation_dict_snapshot.csv` into this repo.
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
- **25 country-years where a reported total contradicts the sum of its own age
  bands**, some by three orders of magnitude. The sex-ratio calculation logs
  these rather than silently using them.
- **Two Health sheets use a legacy layout** and fail at `extract`:
  `Iraq health.xlsx` → `Iraq health - Health_4_a`, `jordan health.xlsx` →
  `Health_1_a`.
- **43 English terms have more than one Arabic spelling.** This is why notebook 3
  translates only the rows it creates rather than the whole file: inverting the
  dictionary is lossy, and the calculated rows' vocabulary is small enough to be
  safe. Mostly `Causes of death` variants and whitespace variants of the same
  citation — worth a dictionary cleanup.
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

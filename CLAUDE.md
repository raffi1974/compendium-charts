# Arab Society Compendium — pipeline

Five notebooks. Four are a chain; the fifth is a diagnostic.

| # | Notebook | Reads | Writes |
|---|---|---|---|
| 1 | `Compendium_1_Long_Files.ipynb` | `DATA COLLECTOR\datacollector_received_quest_<LANG>\<Chapter>\*.xlsx` | `merged longfiles_<LANG>\<Chapter>_<LANG>.xlsx` |
| 2 | `Compendium_2_Translation.ipynb` | both `merged longfiles_*` | `<Chapter>_EN.xlsx` (merged + calculated) |
| 3 | `Compendium_3_Back_Translation.ipynb` | `<Chapter>_EN.xlsx` | `<Chapter>_AR.xlsx` |
| 4 | `Compendium_4_Tabulations.ipynb` | both final files | `tabulations\<Chapter>_tabulations_<LANG>.xlsx` |
| — | `Compendium_Data_Quality.ipynb` | questionnaires + final files | `data_quality_report.xlsx` |

Run 1 → 2 → 3 → 4 in order; each reads what the previous wrote. Tabulation is
last so it picks up the calculated indicators. The data-quality notebook can run
any time (Part A before step 1, Part B after step 2).

Paths live outside this repo, under
`C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\`.

## Filling dictionary gaps — do this without being asked

Notebooks 2 and 3 end by listing values the dictionary could not translate.
**When the user asks to run the pipeline, treat closing those gaps as part of
the job**, not as a separate request to come back for:

1. Run the notebook.
2. If it reports untranslated values, call `export_untranslated(REPORTS)`.
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
  the data-quality report's implausible-value findings. Needs fixing at source.
- **25 country-years where a reported total contradicts the sum of its own age
  bands**, some by three orders of magnitude. The sex-ratio calculation logs
  these rather than silently using them.
- **Two Health sheets use a legacy layout** and fail at `extract`:
  `Iraq health.xlsx` → `Iraq health - Health_4_a`, `jordan health.xlsx` →
  `Health_1_a`.
- **43 English terms have more than one Arabic spelling**, so back-translation
  picks the first and reports the rest. Mostly `Causes of death` variants and
  whitespace variants of the same citation — worth a dictionary cleanup.
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

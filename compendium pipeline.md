# Project: Arab Society Compendium Data Pipeline

The pipeline lives in `Compendium_Data_Pipeline.ipynb` — one notebook, one cell
per step. It reads the country questionnaires for a chapter, reshapes each
sheet from wide to long, attaches each figure's source, corrects the labels
against the translation dictionary, translates them into the other language,
and writes one Excel file per language.

## Folder structure

### Input — questionnaires, filed by language

The questionnaires live in **two folders, one per language**, each with the
same six chapter subfolders:

```
C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\DATA COLLECTOR\
├── datacollector_received_quest_AR\     the Arabic questionnaires
│   ├── Health\   Population\   Education\
│   └── Labor\    Poverty\      Housing\
└── datacollector_received_quest_EN\     the English questionnaires
    └── (same six chapter subfolders)
```

A run reads **one** of these folders — whichever holds the language it is
translating *from*. Nothing has to be configured per file.

### Dictionary / translation file

```
C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\DATA COLLECTOR\translation dict.xlsx
```

Four columns: `col_ar`, `val_ar`, `col_en`, `val_en`. Loaded once per run and
turned into **two dictionaries**:

| Name | Maps |
| --- | --- |
| `DICTIONARY_AR_TO_EN` | Arabic column names and values → English |
| `DICTIONARY_EN_TO_AR` | English column names and values → Arabic |

Each is a `(column_map, value_map)` pair. The keys of each also serve as that
language's **vocabulary** — the known spellings that misspelled labels are
fuzzy-matched against.

### Output

```
C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\COMPENDIUM-ARAB SOCIETY\
├── <Chapter>_AR.xlsx            every chapter's rows, in Arabic
├── <Chapter>_EN.xlsx            the same rows, in English
├── all_values_AR_EN.xlsx        every distinct value, both languages
├── untranslated_values.xlsx     the gaps the dictionary could not translate
└── tabulations\                 cross-tab workbooks (see the skill)
```

Both language files are written on every run, whichever direction it runs in:
the corrected source sheets go to their own language's file, their translations
to the other.

## Translation direction

`TRANSLATE_TO` controls everything:

| `TRANSLATE_TO` | Reads | Dictionary used |
| --- | --- | --- |
| `"EN"` | `datacollector_received_quest_AR\` | `DICTIONARY_AR_TO_EN` |
| `"AR"` | `datacollector_received_quest_EN\` | `DICTIONARY_EN_TO_AR` |

`TRANSLATE_FROM` and `RECEIVED_QUEST_PATH` are derived from it — never set them
by hand.

It is read from the **`TRANSLATE_TO` environment variable** if one is set, and
otherwise from `DEFAULT_TRANSLATE_TO` in the config cell:

```python
DEFAULT_TRANSLATE_TO = "EN"
TRANSLATE_TO = os.environ.get("TRANSLATE_TO", DEFAULT_TRANSLATE_TO).strip().upper()
```

So a one-off run in the other direction never edits the notebook:

```bash
TRANSLATE_TO=AR jupyter nbconvert --execute Compendium_Data_Pipeline.ipynb
```

or, from a cell above the config cell:

```python
os.environ["TRANSLATE_TO"] = "AR"
```

The value is trimmed and upper-cased, so `ar` and ` AR ` both work; anything
that is not `AR` or `EN` raises immediately rather than silently falling back
to the default. The run cell prints the direction it resolved and whether it
came from the environment or the notebook default.

**Asking Claude Code to run it.** "Run the pipeline and translate to English"
is enough — it sets the environment variable for that run, so your file is left
alone. Change `DEFAULT_TRANSLATE_TO` only when you want the *default* to change.
Note that `CHAPTERS` still decides which chapters run, so say "all chapters" if
you want the full six rather than whatever is currently listed.

## How a sheet is processed

1. **`extract_tables()`** — each sheet holds two tables marked by an `index`
   column: `index=1` is the data, `index=2` is the source. The row reading
   `index` in column 0 carries the column names for the table below it.
2. **`detect_language()`** — reads the *script* of the column names (Arabic
   occupies its own Unicode block). Needs no dictionary, so it works on columns
   the dictionary has never seen. This does **not** decide what happens — the
   folder does. It exists to warn you when a file has been filed in the wrong
   folder, which would otherwise surface as a whole sheet of untranslated rows.
3. **`reshape_and_merge()`** — unpivots the year columns (any column whose name
   is all digits) into a year column and a value column, then merges the source
   table on year + indicator + country so every figure carries its citation.
4. **`correct_with_dictionary()`** — fixes misspelled column names and values
   against the vocabulary of the language being read. An exact match is left
   alone; otherwise the closest known spelling is used, but only if it clears
   `FUZZY_MATCH_CUTOFF` (0.6). Anything below that is left alone and logged.
5. **`translate()`** — swaps values for their equivalents in the other
   language, then renames the column. Anything the dictionary has no entry for
   passes through unchanged.

## Filling the dictionary's gaps

The dictionary is the source of truth and always wins, but it does not yet know
every value — Source citations especially, since each country writes its own
survey names. A value with no entry passes through translation unchanged, which
is exactly how it is spotted:

1. Run the pipeline.
2. **`export_untranslated()`** writes every such value to
   `untranslated_values.xlsx`, with the target-language column blank.
3. **Ask Claude Code to fill it in.** It reads the file, translates the blank
   column, and calls `update_dictionary()`.
4. **`update_dictionary()`** appends the completed rows to
   `translation dict.xlsx`, after taking a timestamped backup. Rows already in
   the dictionary are skipped, so running it twice is safe.
5. Run the pipeline again — the new entries are ordinary dictionary hits.

Translations land in the dictionary rather than being generated fresh each run,
so the pipeline stays **deterministic and reviewable**: the same input always
gives the same output, and every machine translation is a row you can inspect,
correct, or delete.

`export_all_values()` writes the whole picture — every distinct value in both
languages — to `all_values_AR_EN.xlsx`, in the dictionary's own column shape.

## Conventions

- `pandas` for reading/writing Excel (`openpyxl` engine) and `pathlib.Path` for
  every path — never hardcode separators, the paths contain spaces.
- Plain functions, no classes. One cell per step, each opening with a `"""`
  block saying what the cell does.
- `logging` for progress and failures; `print()` only for the per-replacement
  dictionary lines and the progress bar, which are meant to be read inline.
- **One `try`/`except` per sheet.** A bad sheet is logged with its chapter,
  file, sheet, step, exception and a plain-language likely cause, then skipped —
  one malformed file never ends a run. The last cell prints every failure
  grouped by chapter.
- The run cell prints a progress bar (`[##--] chapter 2/4: Labor`) so a long
  run is legible without reading the log.
- Column names the pipeline creates itself (year, value, chapter) are written
  once in Arabic; `column_name(name, language)` looks up the English spelling in
  the dictionary, so it can never drift from what `translate()` produces.

## Known issues

- **`reshape_and_merge()` runs before `correct_with_dictionary()`.** A merge key
  (year / indicator / country) misspelled in the data table but not the source
  table fails to match, and that row silently loses its citation — the spelling
  is corrected a step later, too late. Whitespace is the usual culprit: of the
  Labor run's fuzzy corrections, 331 were pure whitespace fixes against 27 real
  spelling corrections. Fix would be to strip the merge keys on both sides
  before merging.
- **Two Health sheets use a legacy layout** and fail at `extract`:
  `Iraq health.xlsx` → `Iraq health - Health_4_a`, and `jordan health.xlsx` →
  `Health_1_a`.
- Questionnaire cover tabs (`العنوان`, `قائمة الجداول`, `كيفية الإستخدام`,
  `البيانات الوصفية`) have no `index` column and are skipped by design.
- Four dictionary rows under `سبب الوفاة` map one Arabic value to two different
  English ones (three differ only by trailing non-breaking spaces); the last row
  in the file wins.

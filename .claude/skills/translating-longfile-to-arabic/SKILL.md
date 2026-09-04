---
name: translating-longfile-to-arabic
description: Translate a long/tidy ENGLISH compendium file back into Arabic using translation dict.xlsx, then fill whatever the dictionary does not know by translating it here and writing it back into the dictionary. Use when the user wants the Arabic version of a long file that was produced in English - typically COMPENDIUM-ARAB SOCIETY/<Chapter>_EN.xlsx after new calculated indicators (sex ratio, age-group percentages) have been added to it. Trigger on "I need the Arabic version", "translate the long file to Arabic", "make an Arabic Population file", "translate back to Arabic".
---

# Translating a long file back into Arabic

The pipeline runs Arabic → English: questionnaires arrive in Arabic, and
`Compendium_2_Translation.ipynb` produces `<Chapter>_EN.xlsx`. That English file
is also where the calculated indicators are added, and where English-only
questionnaire data is merged in. So the English file is the fuller one, and
getting an Arabic version means translating **back**.

## When to use this

The user asks for the Arabic version of a long file that only exists in
English — most often `Population_EN.xlsx` after the sex-ratio and age-group
indicators have been appended to it.

Do **not** use this to rebuild `merged longfiles_AR/<Chapter>_AR.xlsx`. That
file is built from the Arabic questionnaires by notebook 1 and is the original,
not a translation. This skill produces a *derived* Arabic file from the
combined English one.

## The dictionary only goes one way

`translation dict.xlsx` is Arabic → English. The script **inverts** it.

Inverting is lossless only where the mapping is one-to-one, and it is not
always: several Arabic spellings can share one English translation — typo
variants of the same survey name, for instance, where 202 Arabic citations
collapsed onto 157 English strings. When that happens the script uses the first
Arabic spelling and **prints every collision** so the choice is visible rather
than assumed. Any of the spellings is a correct translation; if the user cares
which, they can reorder the dictionary rows or edit the output.

## Workflow

1. **Translate.** From the skill's directory:

   ```bash
   python scripts/translate_to_arabic.py "C:/.../COMPENDIUM-ARAB SOCIETY/Population_EN.xlsx"
   ```

   Writes `Population_AR.xlsx` beside the input (`_EN` → `_AR`) and, if
   anything could not be translated, `untranslated_to_arabic.xlsx`.

   Useful flags: `--output`, `--gaps`, `--dictionary`.

   **Check the output path before running.** If an
   `merged longfiles_AR/<Chapter>_AR.xlsx` already exists, do not overwrite it —
   that is the original built from the Arabic questionnaires. Pass `--output`
   to write somewhere else, e.g. `<Chapter>_AR_from_english.xlsx`.

2. **Read the gaps file.** Its `val_ar` column is blank. Values already in
   Arabic, plain numbers, and URLs are not listed — only English text with no
   dictionary entry.

3. **Translate the gaps yourself and fill in `val_ar`.** These are usually
   statistical terms, survey names, or newly calculated indicator titles. Use
   the official Arabic name of a statistical body where one exists (the
   dictionary already holds many — search it before inventing wording, so the
   file stays internally consistent).

   Attach translations **by position** on the exported file rather than
   retyping the English keys, and assert a couple of anchor rows first: a
   retyped string that differs by one invisible character silently fails to
   match. Write the filled file with pandas rather than by hand.

4. **Write them back into the dictionary:**

   ```bash
   python scripts/translate_to_arabic.py --update-dictionary untranslated_to_arabic.xlsx
   ```

   Takes a timestamped backup first, skips rows already present (so it is safe
   to repeat), and reports how many were added.

5. **Translate again.** The gap list should now come back empty. Report the row
   count, the number of newly added dictionary entries, and any collisions the
   script printed.

## Verifying before delivering

- **No English left where it matters.** Every column name should be Arabic, and
  no column should still hold Latin-script values apart from `Year`, `Value`,
  and genuinely English source citations (URLs, `MICS 2022`).
- **Row count matches the input exactly** — translation renames, it never adds
  or drops rows.
- **Spot-check a calculated indicator.** `نسبة الذكور إلى الإناث` and
  `التوزيع النسبي للسكان حسب الفئة العمرية والجنس` should be present with the
  same number of rows as in the English file, and the age-group labels should
  read `أقل من 15 سنة` / `15-64 سنة` / `65 سنة فأكثر`.

## Implementation notes

- `Year` and `Value` are never translated — they hold numbers, and a value like
  `2024` could otherwise collide with a dictionary entry.
- Values are replaced *before* the column is renamed: the value lookup is keyed
  by the column's original English name, so renaming first would lose it.
- A gap is English text that came through unchanged. Something already in
  Arabic is not a gap, and neither is a number or a bare URL.
- The script never edits the dictionary during a translation run — only
  `--update-dictionary` writes to it, and only after a backup.

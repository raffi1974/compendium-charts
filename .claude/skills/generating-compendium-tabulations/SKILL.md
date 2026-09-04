---
name: generating-compendium-tabulations
description: Build multiindex Excel tabulations (one sheet per indicator) from a long/tidy compendium-style Excel file, with sourced values marked by a superscript and a numbered footnote list per sheet. Use this whenever the user asks to turn a long-format indicator dataset (e.g. Country/Sex/Nationality/Year/Value/Source columns) into a proper cross-tab table, especially for compendium, statistical yearbook, or indicator-dashboard style deliverables. Trigger on requests like "create a multiindex tabulation", "cross-tab this by year", "show sources as footnotes/superscripts", or "one sheet per indicator."
---

# Generating Compendium Tabulations

Turns a long-format ("tidy") Excel file — one row per Country/Sex/Nationality/
Year/Value/Source combination — into readable, presentation-style tabulations:
one sheet per indicator, years across the columns, a hierarchical row index,
and sourced values flagged with a superscript footnote marker.

## When to use this

The user has a long-format indicator file (typically produced by an earlier
data pipeline step — see the sibling data-pipeline conventions if this project
uses one) and wants a human-readable cross-tab version, e.g. for a compendium,
report annex, or statistical yearbook.

## Workflow

1. **Inspect the file first.** Read it with pandas and identify:
   - The **indicator column** (one sheet will be created per unique value)
   - The **row-level columns** that should form the hierarchical row index
     (commonly Country, Sex, Nationality — but confirm with the user)
   - Any **indicator-specific breakdown columns** (e.g. Age Group, Main
     Occupation, Economic Activity) — check which ONE of these is populated
     for each indicator; that becomes the innermost row level for that sheet
   - The **Year**, **Value**, and **Source** columns

2. **Confirm with the user before building**, if not already established
   earlier in the conversation:
   - Which columns form the row hierarchy, and in what order
   - Whether it's really one sheet per indicator (vs. per chapter/domain)
   - How footnotes should be numbered (numbered-per-distinct-source is the
     default this skill implements; ask if the user wants something else)

3. **Output goes in a `tabulations/` subfolder, one file per source file.**
   - The output folder is `tabulations/`, created (if missing) *inside the
     same folder as the source file* — e.g. a source at
     `COMPENDIUM-ARAB SOCIETY/Labor_EN.xlsx` gets its tabulation written to
     `COMPENDIUM-ARAB SOCIETY/tabulations/Labor_tabulations_EN.xlsx`.
   - Name the output `<name>_tabulations_<AR|EN>.xlsx`, where `<name>` is the
     source file's name with its own `_AR`/`_EN` suffix stripped, and
     `<AR|EN>` matches which language file it was built from — e.g.
     `Labor_EN.xlsx` → `Labor_tabulations_EN.xlsx`,
     `Labor_AR.xlsx` → `Labor_tabulations_AR.xlsx`.
   - **Build a tabulation for both the AR and EN source files when both
     exist for the same chapter/dataset** — running the script only against
     one language leaves the other undelivered. Treat "build tabulations for
     X" as "build them for every AR/EN pair belonging to X" unless the user
     asks for one language specifically.

4. **Run the script**, once per source file (so twice per chapter, if both
   AR and EN exist):
   ```bash
   mkdir -p "$(dirname INPUT.xlsx)/tabulations"
   python scripts/build_tabulations.py INPUT.xlsx "$(dirname INPUT.xlsx)/tabulations/OUTPUT_NAME.xlsx" \
     --indicator-col "Indicator" \
     --row-cols "Country,Sex,Nationality" \
     --year-col "Year" --value-col "Value" --source-col "Source" \
     --breakdown-cols "Age Group,Main occupation,Institutional sector,Economic activity,Employment status,Reasons for inactivity"
   ```
   Adjust the column-name flags to match the actual file — run with just the
   two required positional args first and read the error message (it lists
   available columns) if a default doesn't match. Note the AR source file's
   row/indicator/breakdown values will be in Arabic — pass Arabic column
   names to `--row-cols`/`--indicator-col`/etc. if the AR file's headers
   weren't translated (check with a quick `df.columns` read first).

5. **Verify before delivering.** Convert to PDF and visually check at least
   two sheets (one simple, one with a deep row hierarchy) per output file —
   merged-cell logic for hierarchical row labels is the most error-prone part:
   ```bash
   soffice --headless --convert-to pdf --outdir /tmp/preview OUTPUT.xlsx
   ```
   Look specifically for: labels merging across the WRONG boundary (e.g. a
   "Nationality" value appearing merged across two different countries — this
   means the cascade logic broke), and superscript markers rendering next to
   the correct sourced values.

6. **Flag the numeric trade-off to the user**: cells with a footnote marker
   become rich-text strings, not live numbers — sums/charts on that sheet
   won't work directly. Offer a second, plain-number workbook (same script,
   values only, no superscripts) if the user needs the data to stay numeric.

## Implementation notes

- Uses `openpyxl.cell.rich_text.CellRichText` for the superscript — this
  requires openpyxl ≥ 3.1.
- Row-label merging must cascade: if an outer level (e.g. Country) changes
  between two rows, every inner level (Sex, Nationality, breakdown) must also
  be treated as "changed" even if its own value happens to repeat. Compute
  all levels' changed-flags against the PREVIOUS row before merging, then
  update — updating `prev_vals` level-by-level mid-loop causes the outer-
  change check to always see stale-but-equal values and silently produces
  wrong merges (looks fine on row 1-2 boundaries, breaks on deeper nesting).
- A row level that is missing for some rows must be filled with a visible
  marker (`(not specified)`), never left blank. Blank means "same as the row
  above" in this merged layout, so a genuinely-missing value would be read as
  belonging to the group above it and misattribute real numbers.
- An indicator may have NO breakdown column, or SEVERAL. Every breakdown
  column that carries data for an indicator becomes a nested row level for
  that sheet (innermost last); taking only the first would collapse the rest
  under `aggfunc="first"` and silently drop rows.
- Year columns and rows that are entirely empty for a given indicator are
  dropped automatically — don't leave blank tabulation columns/rows.
- Sheet names are capped at Excel's 31-character limit and de-duplicated
  automatically (`Employment (15 years and ov (2)`, etc.) if two indicators
  truncate to the same name. For a nicer final deliverable, consider asking
  the user for short display names per indicator, or hand-curate a name map
  before running (see script's `--indicator-col` inputs).

## Reference

See `scripts/build_tabulations.py` for the full implementation — it's a
single, dependency-light script (`pandas` + `openpyxl`) with `--help` for all
options.

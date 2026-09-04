#!/usr/bin/env python3
"""
Build multiindex Excel tabulations, one sheet per indicator, from a long
("tidy") compendium-style Excel file.

Usage:
    python build_tabulations.py INPUT.xlsx OUTPUT.xlsx [options]

Default column conventions (override with flags if your file differs):
    --indicator-col   "Indicator"   column naming each indicator (-> one sheet each)
    --row-cols        "Country,Sex,Nationality"   hierarchical row levels (in order)
    --year-col        "Year"        pivoted across the columns
    --value-col       "Value"       the cell content
    --source-col      "Source"      drives the superscript + footnote
    --breakdown-cols  "Age Group,Main occupation,Institutional sector,
                        Economic activity,Employment status,Reasons for inactivity"
                      candidate extra row-level columns; EVERY one that has
                      non-null values for a given indicator is appended as a
                      nested row level for that indicator's sheet, in the order
                      listed (innermost last). An indicator may have none (then
                      the sheet is just the row levels x Year) or several (e.g.
                      causes of death, which carries both the ICD classification
                      and the specific cause within it).

What it does, per indicator / sheet:
    1. Groups rows into (row levels + breakdowns) x Year, taking Value/Source.
    2. Drops Year columns that are entirely empty for that indicator.
    3. Drops rows that are entirely empty across all remaining years.
    4. Writes a hierarchical row header with merged cells for repeated labels.
    5. Writes values as text with a small superscript footnote marker whenever
       a Source is present for that cell.
    6. Appends a numbered footnote list at the bottom of the sheet, one line
       per distinct source (numbered in order of first appearance).

Known trade-off: cells carrying a footnote marker become rich-text STRINGS,
not live numbers. If you need the numeric data for calculation/charting,
generate a second, plain (no-superscript) workbook from the same source data.
"""
import argparse
import re
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.utils import get_column_letter

# Shown when a row has no value for one of the row-level dimensions. Must be a
# visible label, not a blank - see build_sheet() for why.
MISSING_LABEL = "(not specified)"

HEADER_FONT = Font(bold=True)
THIN = Side(style="thin", color="B0B0B0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
SUPERSCRIPT_FONT = InlineFont(vertAlign="superscript", sz="9")


def sanitize_sheet_name(name: str, used: set) -> str:
    clean = re.sub(r'[\[\]\:\*\?/\\]', '', str(name)).replace("\xa0", " ").strip()
    base = clean[:31] if clean else "Sheet"
    candidate = base
    n = 2
    while candidate in used:
        suffix = f" ({n})"
        candidate = base[: 31 - len(suffix)] + suffix
        n += 1
    used.add(candidate)
    return candidate


def get_breakdown_cols(sub: pd.DataFrame, breakdown_cols):
    """Every candidate breakdown column that actually carries data for this
    indicator, in the order given.

    An indicator may legitimately have NONE (a plain Country/Sex/Nationality x
    Year table, e.g. "Crude birth rate") or SEVERAL (e.g. causes of death
    carries both the ICD classification and the specific cause within it).
    All populated ones become nested row levels, innermost last - taking only
    the first would silently collapse the rest under aggfunc="first".
    """
    return [c for c in breakdown_cols if c in sub.columns and sub[c].notna().any()]


def to_display_str(value):
    """Best-effort clean numeric formatting; falls back to plain string."""
    try:
        fval = float(value)
    except (ValueError, TypeError):
        return str(value)
    if fval.is_integer():
        return str(int(fval))
    return f"{fval:.1f}"


def build_sheet(ws, sub: pd.DataFrame, row_cols, breakdown_cols_present, year_col, value_col, source_col):
    full_row_cols = row_cols + list(breakdown_cols_present)

    # A row can legitimately have no value for one of the row levels (e.g. an
    # Area total on a sheet that also breaks down by Age Group). Fill those
    # rather than leaving NaN: pivot_table drops rows with NaN index keys, so
    # leaving them would silently lose data.
    sub = sub.copy()
    for c in full_row_cols:
        sub[c] = sub[c].fillna("").astype(str).str.strip()

    # Drop any level that is empty for EVERY row of this indicator - it would
    # otherwise render as a headed but completely blank column.
    full_row_cols = [c for c in full_row_cols if (sub[c] != "").any()]
    if not full_row_cols:
        ws["A1"] = "No row dimensions available for this indicator."
        return

    # Remaining blanks get an explicit marker. They must NOT stay empty: this
    # layout blanks out a repeated label to show it continues from the row
    # above, so an empty cell reads as "same as above". A row that genuinely
    # has no value for a dimension would then be silently absorbed into the
    # group above it (e.g. rows with no Nationality inheriting "Nationality
    # Total"), which misattributes real numbers.
    for c in full_row_cols:
        sub[c] = sub[c].replace("", MISSING_LABEL)

    grouped = (
        sub.groupby(full_row_cols + [year_col], dropna=False, observed=True)
        .agg(**{value_col: (value_col, "first"), source_col: (source_col, "first")})
        .reset_index()
    )

    def has_value(x):
        if pd.isna(x):
            return False
        if isinstance(x, str) and x.strip() == "":
            return False
        return True

    years_with_data = sorted(
        y for y in grouped[year_col].unique()
        if grouped.loc[grouped[year_col] == y, value_col].apply(has_value).any()
    )
    if not years_with_data:
        ws["A1"] = "No data available for this indicator."
        return

    val_pivot = grouped.pivot_table(
        index=full_row_cols, columns=year_col, values=value_col, aggfunc="first"
    ).reindex(columns=years_with_data)
    src_pivot = grouped.pivot_table(
        index=full_row_cols, columns=year_col, values=source_col, aggfunc="first"
    ).reindex(index=val_pivot.index, columns=val_pivot.columns)

    keep_mask = val_pivot.apply(lambda col: col.map(has_value)).any(axis=1).to_numpy()
    val_pivot = val_pivot.loc[keep_mask].sort_index()
    src_pivot = src_pivot.loc[keep_mask].reindex(val_pivot.index)

    if val_pivot.empty:
        ws["A1"] = "No data available for this indicator."
        return

    n_row_levels = len(full_row_cols)
    n_years = len(years_with_data)
    first_data_row = 2
    last_data_row = first_data_row + len(val_pivot) - 1

    # Header
    for lvl, col_name in enumerate(full_row_cols, start=1):
        c = ws.cell(row=1, column=lvl, value=col_name)
        c.font = HEADER_FONT
        c.border = BORDER
    for j, year in enumerate(years_with_data):
        c = ws.cell(row=1, column=n_row_levels + 1 + j, value=int(year) if float(year).is_integer() else year)
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center")
        c.border = BORDER

    # Footnote numbering
    footnote_map, footnote_order = {}, []

    def footnote_num(source):
        if pd.isna(source) or str(source).strip() == "":
            return None
        key = str(source).strip()
        if key not in footnote_map:
            footnote_map[key] = len(footnote_order) + 1
            footnote_order.append(key)
        return footnote_map[key]

    # Row labels with cascading vertical merges
    idx_tuples = list(val_pivot.index)
    level_start = {lvl: first_data_row for lvl in range(n_row_levels)}
    prev_vals = [None] * n_row_levels

    for i, tup in enumerate(idx_tuples):
        r = first_data_row + i
        row_vals = list(tup) if n_row_levels > 1 else [tup]

        level_changed = [False] * n_row_levels
        cascade = False
        for lvl in range(n_row_levels):
            if i == 0 or row_vals[lvl] != prev_vals[lvl]:
                cascade = True
            level_changed[lvl] = cascade

        for lvl in range(n_row_levels):
            if level_changed[lvl]:
                start_r = level_start[lvl]
                if i != 0 and r - 1 > start_r:
                    ws.merge_cells(start_row=start_r, start_column=lvl + 1,
                                    end_row=r - 1, end_column=lvl + 1)
                cell = ws.cell(row=r, column=lvl + 1, value=row_vals[lvl])
                cell.alignment = Alignment(vertical="center")
                cell.border = BORDER
                level_start[lvl] = r

        prev_vals = row_vals

    for lvl in range(n_row_levels):
        start_r = level_start[lvl]
        if last_data_row > start_r:
            ws.merge_cells(start_row=start_r, start_column=lvl + 1,
                            end_row=last_data_row, end_column=lvl + 1)
    for r in range(first_data_row, last_data_row + 1):
        for lvl in range(n_row_levels):
            ws.cell(row=r, column=lvl + 1).border = BORDER

    # Value cells
    for i in range(len(idx_tuples)):
        r = first_data_row + i
        for j in range(n_years):
            col = n_row_levels + 1 + j
            value = val_pivot.iloc[i, j]
            source = src_pivot.iloc[i, j]
            cell = ws.cell(row=r, column=col)
            cell.border = BORDER
            cell.alignment = Alignment(horizontal="center")
            if not has_value(value):
                continue
            val_str = to_display_str(value)
            fn = footnote_num(source)
            cell.value = (
                CellRichText(val_str, TextBlock(SUPERSCRIPT_FONT, str(fn)))
                if fn else val_str
            )

    # Footnotes
    fn_row = last_data_row + 2
    for src, num in sorted(footnote_map.items(), key=lambda kv: kv[1]):
        c = ws.cell(row=fn_row, column=1, value=f"{num}  Source: {src}")
        c.font = Font(size=9, italic=True)
        fn_row += 1

    for lvl in range(n_row_levels):
        ws.column_dimensions[get_column_letter(lvl + 1)].width = 20
    for j in range(n_years):
        ws.column_dimensions[get_column_letter(n_row_levels + 1 + j)].width = 10

    ws.freeze_panes = ws.cell(row=first_data_row, column=n_row_levels + 1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input_xlsx")
    p.add_argument("output_xlsx")
    p.add_argument("--sheet", default=0, help="Source sheet name/index to read (default: first sheet)")
    p.add_argument("--indicator-col", default="Indicator")
    p.add_argument("--row-cols", default="Country,Sex,Nationality")
    p.add_argument("--year-col", default="Year")
    p.add_argument("--value-col", default="Value")
    p.add_argument("--source-col", default="Source")
    p.add_argument(
        "--breakdown-cols",
        default="Age Group,Main occupation,Institutional sector,Economic activity,Employment status,Reasons for inactivity",
    )
    args = p.parse_args()

    row_cols = [c.strip() for c in args.row_cols.split(",") if c.strip()]
    breakdown_cols = [c.strip() for c in args.breakdown_cols.split(",") if c.strip()]

    try:
        sheet = int(args.sheet)
    except ValueError:
        sheet = args.sheet

    df = pd.read_excel(args.input_xlsx, sheet_name=sheet)

    missing = [c for c in [args.indicator_col, args.year_col, args.value_col, args.source_col] + row_cols if c not in df.columns]
    if missing:
        sys.exit(f"Error: column(s) not found in source file: {missing}\nAvailable columns: {list(df.columns)}")

    indicators = df[args.indicator_col].dropna().unique()
    wb = Workbook()
    wb.remove(wb.active)
    used_names = set()

    for ind in indicators:
        sub = df[df[args.indicator_col] == ind]
        present = get_breakdown_cols(sub, breakdown_cols)
        ws = wb.create_sheet(title=sanitize_sheet_name(ind, used_names))
        build_sheet(ws, sub, row_cols, present, args.year_col, args.value_col, args.source_col)

    wb.save(args.output_xlsx)
    print(f"Saved: {args.output_xlsx}  ({len(indicators)} indicator sheet(s))")


if __name__ == "__main__":
    main()

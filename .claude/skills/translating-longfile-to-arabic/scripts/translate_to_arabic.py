#!/usr/bin/env python3
"""
Translate a long ("tidy") English compendium file into Arabic, using
translation dict.xlsx, and collect whatever the dictionary cannot translate.

The project dictionary is Arabic -> English, because that is the direction the
questionnaires need. This script INVERTS it to go back the other way. Inverting
is only lossless where the mapping is one-to-one, so it reports every English
term that several Arabic spellings map to and says which one it picked.

Two modes:

  translate   (default)
      python translate_to_arabic.py Population_EN.xlsx
          -> Population_AR.xlsx           the translation
          -> untranslated_to_arabic.xlsx  values with no dictionary entry,
                                          with val_ar blank to fill in

  update-dictionary
      python translate_to_arabic.py --update-dictionary untranslated_to_arabic.xlsx
          appends the filled-in rows to translation dict.xlsx (after a
          timestamped backup) so the next translate run covers them
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

DEFAULT_DICTIONARY = Path(
    r"C:\Users\RSHIRINI\OneDrive - United Nations\Desktop\DSS\DATA COLLECTOR\translation dict.xlsx"
)

# Columns that hold numbers rather than vocabulary - never translated.
NUMERIC_COLUMNS = {"Year", "Value"}


def looks_arabic(text) -> bool:
    """True if the text contains at least one Arabic letter. U+0600-U+06FF is
    the Arabic Unicode block; English text has nothing in it."""
    return any("\u0600" <= ch <= "\u06ff" for ch in str(text))


def load_english_to_arabic(dictionary_path: Path):
    """Invert the Arabic -> English dictionary.

    Returns (column_map, value_map, collisions):
        column_map = {English column name: Arabic column name}
        value_map  = {English column name: {English value: Arabic value}}
        collisions = list of (column, english, [arabic spellings]) where more
                     than one Arabic value maps to the same English one

    Where several Arabic spellings share an English translation - typo variants
    of the same survey name, for instance - the FIRST is used. Any of them is a
    correct translation; the point of reporting them is so a human can see the
    choice was made rather than assume it was unique.
    """
    dictionary = pd.read_excel(dictionary_path, engine="openpyxl")

    column_map = {}
    for _, row in dictionary[["col_ar", "col_en"]].dropna().drop_duplicates().iterrows():
        column_map.setdefault(str(row["col_en"]).strip(), str(row["col_ar"]).strip())

    value_map, seen, collisions = {}, {}, []
    rows = dictionary.dropna(subset=["col_en", "val_en", "val_ar"])
    for _, row in rows.iterrows():
        english_column = str(row["col_en"]).strip()
        english_value = str(row["val_en"]).strip()
        arabic_value = row["val_ar"]

        bucket = value_map.setdefault(english_column, {})
        key = (english_column, english_value)
        if english_value in bucket:
            seen[key].append(arabic_value)
            continue
        bucket[english_value] = arabic_value
        seen[key] = [arabic_value]

    for (column, english), spellings in seen.items():
        if len(spellings) > 1:
            collisions.append((column, english, spellings))

    return column_map, value_map, collisions


def translate(table: pd.DataFrame, column_map, value_map):
    """English -> Arabic.

    Values are replaced first and the column renamed second, because the value
    lookup is keyed by the column's ORIGINAL English name - renaming first would
    lose it.

    For a NUMERIC_COLUMNS column only the header is translated: 'Year' becomes
    'السنة', but the year 2024 stays 2024. Running its values through the
    dictionary could rewrite a figure that happens to match an entry.
    """
    table = table.copy()
    for column in list(table.columns):
        if column in value_map and column not in NUMERIC_COLUMNS:
            table[column] = table[column].replace(value_map[column])
        if column in column_map:
            table = table.rename(columns={column: column_map[column]})
    return table


def is_web_address(text) -> bool:
    """A URL or bare domain. These are citations that read the same in either
    language, so they are not something the dictionary is missing."""
    t = str(text).strip().lower()
    return t.startswith(("http://", "https://", "www.")) or "://" in t


def find_gaps(english_table: pd.DataFrame, arabic_table: pd.DataFrame):
    """Values that came through unchanged and are still in Latin script.

    A value with no dictionary entry is copied through untouched, so comparing
    before against after finds them exactly. A value already in Arabic is not a
    gap, and neither is a figure or a web address - those are correct as they
    stand and asking a human to "translate" them would be noise.
    """
    gaps = []
    for english_column, arabic_column in zip(english_table.columns, arabic_table.columns):
        if english_column in NUMERIC_COLUMNS:
            continue
        pairs = pd.DataFrame({
            "val_en": english_table[english_column],
            "val_ar": arabic_table[arabic_column],
        }).dropna()

        for (english_value, arabic_value), count in pairs.groupby(["val_en", "val_ar"]).size().items():
            if str(english_value).strip() != str(arabic_value).strip():
                continue                       # translated fine
            if looks_arabic(english_value):
                continue                       # already Arabic
            if not re.search(r"[A-Za-z]", str(english_value)):
                continue                       # a number, code or symbol
            if is_web_address(english_value):
                continue                       # a link - the same in both languages
            gaps.append({
                "col_en": english_column,
                "col_ar": arabic_column,
                "val_en": english_value,
                "val_ar": None,                # <- to be filled in
                "rows": count,
            })
    return pd.DataFrame(gaps)


def update_dictionary(filled_path: Path, dictionary_path: Path, backup: bool = True):
    """Append reviewed translations to the dictionary.

    Rows missing either side are skipped, and an (Arabic column, Arabic value)
    pair already present is left alone - so running this twice changes nothing
    the second time.
    """
    filled = pd.read_excel(filled_path, engine="openpyxl")
    needed = ["col_ar", "val_ar", "col_en", "val_en"]
    missing = [c for c in needed if c not in filled.columns]
    if missing:
        sys.exit(f"Error: {filled_path.name} is missing column(s) {missing}")

    new_rows = filled[needed].dropna()
    new_rows = new_rows[(new_rows["val_ar"].astype(str).str.strip() != "")
                        & (new_rows["val_en"].astype(str).str.strip() != "")]
    if new_rows.empty:
        print("No completed rows to add - is the val_ar column filled in?")
        return

    dictionary = pd.read_excel(dictionary_path, engine="openpyxl")
    already = set(zip(dictionary["col_ar"], dictionary["val_ar"]))
    to_add = new_rows[~new_rows.apply(
        lambda r: (r["col_ar"], r["val_ar"]) in already, axis=1)]
    if to_add.empty:
        print("Every row is already in the dictionary - nothing to add.")
        return

    if backup:
        stamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        backup_path = dictionary_path.with_name(
            f"{dictionary_path.stem} backup {stamp}.xlsx")
        dictionary.to_excel(backup_path, index=False, engine="openpyxl")
        print(f"Backed up the dictionary to {backup_path.name}")

    updated = pd.concat([dictionary, to_add.reindex(columns=dictionary.columns)],
                        ignore_index=True)
    updated.to_excel(dictionary_path, index=False, engine="openpyxl")
    print(f"Added {len(to_add):,} row(s) to {dictionary_path.name} "
          f"({len(dictionary):,} -> {len(updated):,}). Re-run the translation to use them.")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input_xlsx", nargs="?", help="the long ENGLISH file to translate")
    p.add_argument("--output", help="where to write the Arabic file "
                                    "(default: alongside the input, _EN -> _AR)")
    p.add_argument("--gaps", help="where to write the untranslated values "
                                  "(default: untranslated_to_arabic.xlsx beside the output)")
    p.add_argument("--dictionary", default=str(DEFAULT_DICTIONARY))
    p.add_argument("--update-dictionary", metavar="FILLED_XLSX",
                   help="append a filled-in gaps file to the dictionary and exit")
    args = p.parse_args()

    dictionary_path = Path(args.dictionary)
    if not dictionary_path.exists():
        sys.exit(f"Error: dictionary not found: {dictionary_path}")

    if args.update_dictionary:
        update_dictionary(Path(args.update_dictionary), dictionary_path)
        return

    if not args.input_xlsx:
        p.error("give an input file, or use --update-dictionary")

    input_path = Path(args.input_xlsx)
    if not input_path.exists():
        sys.exit(f"Error: input not found: {input_path}")

    stem = input_path.stem
    default_out = input_path.with_name(
        (stem[:-3] + "_AR" if stem.endswith("_EN") else stem + "_AR") + ".xlsx")
    output_path = Path(args.output) if args.output else default_out
    gaps_path = Path(args.gaps) if args.gaps else output_path.with_name("untranslated_to_arabic.xlsx")

    column_map, value_map, collisions = load_english_to_arabic(dictionary_path)
    print(f"Dictionary: {len(column_map)} column names, "
          f"{sum(len(v) for v in value_map.values())} values (English -> Arabic)")
    if collisions:
        print(f"\n{len(collisions)} English term(s) have MORE THAN ONE Arabic spelling. "
              f"The first is used:")
        for column, english, spellings in collisions[:10]:
            print(f"   [{column}] {english!r}")
            print(f"       using {spellings[0]!r}, also seen: "
                  f"{[str(s) for s in spellings[1:4]]}")
        if len(collisions) > 10:
            print(f"   ... and {len(collisions) - 10} more")

    english_table = pd.read_excel(input_path, engine="openpyxl")
    print(f"\n{input_path.name}: {len(english_table):,} rows x {english_table.shape[1]} cols")

    arabic_table = translate(english_table, column_map, value_map)
    arabic_table.to_excel(output_path, index=False, engine="openpyxl")
    print(f"Wrote {output_path.name}: {len(arabic_table):,} rows")

    gaps = find_gaps(english_table, arabic_table)
    if gaps.empty:
        print("\nEvery value was translated - the dictionary covered all of them.")
        return

    gaps = (gaps.drop_duplicates(subset=["col_en", "val_en"])
                .sort_values(["col_en", "val_en"])
                .reset_index(drop=True))
    gaps.to_excel(gaps_path, index=False, engine="openpyxl")
    print(f"\n{len(gaps)} value(s) had NO dictionary entry and stayed in English:")
    for _, row in gaps.head(12).iterrows():
        print(f"   [{row['col_en']}] {str(row['val_en'])[:70]}   ({row['rows']} rows)")
    if len(gaps) > 12:
        print(f"   ... and {len(gaps) - 12} more")
    print(f"\nWrote {gaps_path.name}. Fill in the val_ar column, then run:")
    print(f"   python translate_to_arabic.py --update-dictionary \"{gaps_path.name}\"")
    print("and translate again.")


if __name__ == "__main__":
    main()

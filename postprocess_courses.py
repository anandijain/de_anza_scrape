#!/usr/bin/env python3
"""
Post-process a scraped CSV of summer courses:
 1. Remove all newlines in text cells (replace with a space).
 2. Split the Status column into four numeric fields:
    - seats_remaining
    - seats_capacity
    - waitlist_remaining
    - waitlist_capacity
 3. Normalize all column names for coding: lowercase, underscores instead of spaces/special chars.
 4. Ensure row count is preserved and warn if not.
 5. Save the enhanced dataset back to CSV, using CLI args for input/output.
"""
import argparse
import pandas as pd
import re

def remove_newlines(val):
    if isinstance(val, str):
        return val.replace('\r', ' ').replace('\n', ' ')
    return val

status_pattern = re.compile(
    r"(?:FULL:\s*)?(?P<seats_remaining>\d+)\s*of\s*(?P<seats_capacity>\d+)\s*seats\s*remain.*?"
    r"(?P<waitlist_remaining>\d+)\s*of\s*(?P<waitlist_capacity>\d+)\s*waitlist",
    re.IGNORECASE
)

def parse_status(text):
    m = status_pattern.search(str(text))
    if not m:
        return pd.Series({
            'seats_remaining': pd.NA,
            'seats_capacity': pd.NA,
            'waitlist_remaining': pd.NA,
            'waitlist_capacity': pd.NA
        })
    return pd.Series({k: int(v) for k, v in m.groupdict().items()})

def normalize_col(col_name):
    name = col_name.strip().lower()
    name = re.sub(r"[^0-9a-z]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip('_')

def main():
    parser = argparse.ArgumentParser(
        description="Process course CSV: split status, clean text, normalize columns."
    )
    parser.add_argument(
        '-i', '--input', default='summer_courses.csv',
        help='Path to input CSV file'
    )
    parser.add_argument(
        '-o', '--output', default='summer_courses_processed.csv',
        help='Path for output processed CSV file'
    )
    args = parser.parse_args()

    # 1) Load the scraped CSV
    df = pd.read_csv(args.input)

    # 2) Remove newlines in all string cells
    df = df.applymap(remove_newlines)

    # 3) Parse the Status field into numeric columns
    status_df = df['Status'].apply(parse_status)

    # 4) Combine new columns and drop original Status
    processed_df = pd.concat([df.drop(columns=['Status']), status_df], axis=1)

    # 5) Normalize column names
    processed_df.columns = [normalize_col(c) for c in processed_df.columns]

    # 6) Sanity check row counts
    orig_count = len(df)
    proc_count = len(processed_df)
    if orig_count != proc_count:
        print(f"⚠️ Warning: row count mismatch (original={orig_count}, processed={proc_count})")

    # 7) Save to CSV
    processed_df.to_csv(args.output, index=False)
    print(f"✅ Saved processed data with split status fields to {args.output}")

if __name__ == '__main__':
    main()

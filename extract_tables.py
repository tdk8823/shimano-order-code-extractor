import argparse
import os

import pandas as pd
import pdfplumber

# 表に対するタイトルの位置を特定するためのオフセット
TABLE_TOP_OFFSET = 20
TABLE_LEFT_OFFSET = 10


def sanitize_filename(filename):
    return "".join(c if c.isalnum() else "-" for c in filename)


def extract_table_coordinates(input_pdf_path, output_dir):
    if os.path.exists(output_dir):
        raise ValueError(f"{output_dir} already exists. Please remove it first.")
    os.makedirs(output_dir)

    with pdfplumber.open(input_pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.find_tables()
            for table in tables:

                # extract table title
                x0, top, x1, _ = table.bbox
                table_title_area = (
                    x0 - TABLE_LEFT_OFFSET,
                    top - TABLE_TOP_OFFSET,
                    x1,
                    top,
                )
                cropped_page = page.within_bbox(table_title_area)
                title = cropped_page.extract_text()
                sanitized_title = sanitize_filename(title)

                # extract table
                table_extracted = table.extract()
                # remove \n
                table_extracted = [
                    [
                        cell.replace("\n", "") if cell is not None else None
                        for cell in row
                    ]
                    for row in table_extracted
                ]
                df = pd.DataFrame(table_extracted[1:], columns=table_extracted[0])

                if "発注コード" not in df.columns:
                    continue

                # fill nan with previous row value
                df = df.ffill()

                # save as csv
                df.to_csv(
                    f"{output_dir}/{page_number}_{sanitized_title}.csv", index=False
                )


def main():
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(
        description="Extract table as csv from a PDF file."
    )
    parser.add_argument("--input_path", type=str, help="Path to the input PDF file.")
    parser.add_argument(
        "--output_dir", type=str, help="Directory to save the extracted tables."
    )
    args = parser.parse_args()

    extract_table_coordinates(args.input_path, args.output_dir)


if __name__ == "__main__":
    main()

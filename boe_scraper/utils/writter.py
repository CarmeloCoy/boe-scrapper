import polars as pl

schema = {
    "occurrence": pl.String,
    "date": pl.Date,
    "reference_id": pl.String,
    "department": pl.String,
}


def boe_jsonl_to_delta(input_filename: str, delta_table_path: str):
    """
    Reads a boe_parser output file (likely ndjson or JSON) and writes it to a Delta table using polars.

    Args:
        input_filename (str): Path to the boe_parser output file.
        delta_table_path (str): Path to the Delta table directory to write to.
    """
    # Read the data with polars
    df = pl.read_ndjson(input_filename, schema=schema)
    df.write_delta(delta_table_path, mode="append")


def boe_jsonl_to_csv(input_filename: str, csv_path: str, mode="overwrite"):
    """
    Reads a boe_parser output file (likely ndjson or JSON) and writes it to a CSV using polars.

    Args:
        input_filename (str): Path to the boe_parser output file.
        csv_path (str)      : Path to the CSV file to write to.
        mode(str)           :  How to handle existing data: 'append' or 'overwrite'
    """
    # Read the data with polars
    df = pl.read_ndjson(input_filename, schema=schema)
    if mode == "overwrite":
        df.write_csv(csv_path)
    elif mode == "append":
        with open(csv_path, mode="a") as f:
            df.write_csv(f, include_header=False)

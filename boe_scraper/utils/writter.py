import fsspec
import polars as pl

schema = {
    "occurrence": pl.String,
    "date": pl.Date,
    "reference_id": pl.String,
    "department": pl.String,
}


def fsopen(path: str, mode: str = "w", **kwargs):
    """
    A unified file writer that supports local and cloud storage backends
    (e.g., S3, GCS, Azure) using fsspec.


    Examples
    --------
    >>> with writer.open("s3://my-bucket/data/file.txt") as f:
    ...     f.write("hello world")
    >>> with writer.open("/tmp/output/local.txt") as f:
    ...     f.write("local file")
    """
    fs, _base_path = fsspec.core.url_to_fs(path)

    # ensure parent directory exists (mainly for local FS)
    if "w" in mode or "a" in mode:
        parent = path.rsplit("/", 1)[0]
        if parent:
            fs.makedirs(parent, exist_ok=True)

    return fs.open(path, mode, **kwargs)


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


def boe_jsonl_to_jsonl(input_filename: str, csv_path: str, mode="overwrite"):
    """
    Reads a boe_parser output file (likely ndjson or JSON) and writes it to a JSONL using polars.

    Args:
        input_filename (str): Path to the boe_parser output file.
        csv_path (str)      : Path to the CSV file to write to.
        mode(str)           :  How to handle existing data: 'append' or 'overwrite'
    """
    # Read the data with polars
    df = pl.read_ndjson(input_filename, schema=schema)
    if mode == "overwrite":
        df.write_ndjson(csv_path)
    elif mode == "append":
        with open(csv_path, mode="a") as f:
            df.write_ndjson(f)

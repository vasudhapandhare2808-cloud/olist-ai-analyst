from pathlib import Path
import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "olist.duckdb"


def main():
    con = duckdb.connect(str(DB_PATH))

    csv_files = sorted(DATA_DIR.glob("*.csv"))

    for csv_file in csv_files:
        table_name = csv_file.stem.replace("-", "_")

        print(f"Loading {csv_file.name} -> {table_name}")

        con.execute(
            f"""
            CREATE OR REPLACE TABLE "{table_name}" AS
            SELECT *
            FROM read_csv_auto('{csv_file}')
            """
        )

        row_count = con.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]

        print(f"  {row_count:,} rows")

    con.close()

    print("\nDone. Database created:", DB_PATH)


if __name__ == "__main__":
    main()
import duckdb

DB_PATH = "olist.duckdb"


def get_schema():
    con = duckdb.connect(DB_PATH)

    tables = con.execute("SHOW TABLES").fetchall()

    schema = []

    for (table_name,) in tables:
        columns = con.execute(
            f'DESCRIBE "{table_name}"'
        ).fetchall()

        schema.append(f"Table: {table_name}")

        for column in columns:
            column_name = column[0]
            data_type = column[1]

            schema.append(
                f"  - {column_name}: {data_type}"
            )

        schema.append("")

    con.close()

    return "\n".join(schema)


if __name__ == "__main__":
    print(get_schema())
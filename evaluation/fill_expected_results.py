
import json
import math
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "olist.duckdb"
BENCHMARK_PATH = PROJECT_ROOT / "evaluation" / "benchmark.json"


def values_match(expected, actual):
    """Compare benchmark values, allowing small floating-point differences."""

    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if isinstance(actual, (int, float)) and not isinstance(actual, bool):
            return math.isclose(
                expected,
                actual,
                rel_tol=1e-9,
                abs_tol=1e-9,
            )

    if isinstance(expected, dict) and isinstance(actual, dict):
        if expected.keys() != actual.keys():
            return False

        return all(
            values_match(expected[key], actual[key])
            for key in expected
        )

    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return False

        return all(
            values_match(e, a)
            for e, a in zip(expected, actual)
        )

    return expected == actual


def execute_reference_query(connection, sql):
    """Execute reference SQL and return rows as dictionaries."""

    cursor = connection.execute(sql)

    columns = [description[0] for description in cursor.description]
    results = cursor.fetchall()

    return [
        dict(zip(columns, row))
        for row in results
    ]


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(
            f"Benchmark file not found: {BENCHMARK_PATH}"
        )

    with BENCHMARK_PATH.open("r", encoding="utf-8") as file:
        benchmark = json.load(file)

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    filled_count = 0
    verified_count = 0
    mismatch_count = 0

    try:
        for case in benchmark:
            case_id = case["id"]
            question = case["question"]
            sql = case["expected_sql"]

            print(f"\nBenchmark {case_id}: {question}")

            actual_result = execute_reference_query(
                connection,
                sql,
            )

            if case["expected_result"] is None:
                case["expected_result"] = actual_result
                filled_count += 1

                print("STATUS: EXPECTED RESULT GENERATED")
                print("RESULT:", actual_result)

            elif values_match(
                case["expected_result"],
                actual_result,
            ):
                verified_count += 1
                print("STATUS: EXISTING RESULT VERIFIED")

            else:
                mismatch_count += 1

                print("STATUS: MISMATCH")
                print("STORED:", case["expected_result"])
                print("ACTUAL:", actual_result)

    finally:
        connection.close()

    with BENCHMARK_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            benchmark,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 50)
    print("BENCHMARK PREPARATION SUMMARY")
    print("=" * 50)
    print(f"Total benchmark questions: {len(benchmark)}")
    print(f"New expected results generated: {filled_count}")
    print(f"Existing results verified: {verified_count}")
    print(f"Mismatches found: {mismatch_count}")
    print(f"Updated file: {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()

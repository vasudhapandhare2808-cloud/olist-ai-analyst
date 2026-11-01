import json
import math
import sys
import time
from pathlib import Path
from datetime import date, datetime

import pandas as pd

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.text_to_sql import generate_valid_sql
from src.safe_sql import run_safe_query

BENCHMARK_PATH = PROJECT_ROOT / "evaluation" / "benchmark.json"
REPORT_PATH = PROJECT_ROOT / "evaluation" / "evaluation_report.json"


# --------------------------------------------------
# JSON SERIALIZATION
# --------------------------------------------------

def json_default(obj):
    """Convert Pandas, NumPy and date values into JSON-safe values."""
    if isinstance(obj, (pd.Timestamp, datetime, date)):
        return obj.isoformat()

    if hasattr(obj, "item"):
        return obj.item()

    return str(obj)


# --------------------------------------------------
# RESULT NORMALIZATION
# --------------------------------------------------

def normalize_value(value):
    """Convert NumPy/Pandas scalar values into Python values."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()

    return value


def normalize_rows(rows):
    """
    Convert dictionary-based rows into lists of values.

    Column names are intentionally ignored because generated SQL
    aliases may differ from the benchmark aliases.
    """
    return [
        [normalize_value(value) for value in row.values()]
        for row in rows
    ]


# --------------------------------------------------
# RESULT COMPARISON
# --------------------------------------------------

def values_match(actual, expected):
    """Compare individual values with a small numeric tolerance."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual == expected

    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(
            actual,
            expected,
            rel_tol=1e-9,
            abs_tol=0.01,
        )

    return actual == expected


def rows_match(actual_row, expected_row):
    """Compare two normalized rows."""
    return (
        len(actual_row) == len(expected_row)
        and all(
            values_match(actual_value, expected_value)
            for actual_value, expected_value in zip(actual_row, expected_row)
        )
    )


def compare_results(actual, expected, comparison_mode="unordered"):
    """
    Compare result rows.

    ordered:
        Row positions must match. Use for chronological series and rankings.

    unordered:
        Row order is ignored, but duplicate rows are still counted.
    """
    if len(actual) != len(expected):
        return False

    if comparison_mode == "ordered":
        return all(
            rows_match(actual_row, expected_row)
            for actual_row, expected_row in zip(actual, expected)
        )

    if comparison_mode != "unordered":
        raise ValueError(
            f"Unsupported comparison_mode: {comparison_mode!r}"
        )

    unmatched = list(expected)

    for actual_row in actual:
        match_index = next(
            (
                index
                for index, expected_row in enumerate(unmatched)
                if rows_match(actual_row, expected_row)
            ),
            None,
        )

        if match_index is None:
            return False

        unmatched.pop(match_index)

    return not unmatched


# --------------------------------------------------
# EVALUATE ONE QUESTION
# --------------------------------------------------

def evaluate_case(case):
    comparison_mode = case.get("comparison_mode", "unordered")

    result = {
        "id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "comparison_mode": comparison_mode,
        "generated_sql": None,
        "sql_generation_success": False,
        "execution_success": False,
        "result_correct": False,
        "latency_seconds": None,
        "actual_result": None,
        "expected_result": case["expected_result"],
        "error": None,
    }

    start = time.perf_counter()

    try:
        sql = generate_valid_sql(
            case["question"],
            max_attempts=2,
        )

        result["generated_sql"] = sql
        result["sql_generation_success"] = True

        dataframe = run_safe_query(sql)
        result["execution_success"] = True

        actual = normalize_rows(
            dataframe.to_dict(orient="records")
        )
        expected = normalize_rows(case["expected_result"])

        result["actual_result"] = actual
        result["result_correct"] = compare_results(
            actual,
            expected,
            comparison_mode=comparison_mode,
        )

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    finally:
        result["latency_seconds"] = round(
            time.perf_counter() - start,
            3,
        )

    return result


# --------------------------------------------------
# MAIN EVALUATION
# --------------------------------------------------

def main():
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(
            f"Benchmark not found: {BENCHMARK_PATH}"
        )

    with BENCHMARK_PATH.open("r", encoding="utf-8") as file:
        benchmark = json.load(file)

    if not benchmark:
        raise ValueError("Benchmark dataset is empty.")

    results = []

    print("\n" + "=" * 65)
    print("OLIST AI ANALYST: EVALUATION")
    print("=" * 65)

    for index, case in enumerate(benchmark, start=1):
        print(f"\n[{index}/{len(benchmark)}] {case['question']}")

        result = evaluate_case(case)
        results.append(result)

        if result["result_correct"]:
            status = "CORRECT"
        elif result["execution_success"]:
            status = "INCORRECT RESULT"
        elif result["sql_generation_success"]:
            status = "EXECUTION FAILED"
        else:
            status = "GENERATION FAILED"

        print("Status:", status)
        print("Comparison mode:", result["comparison_mode"])
        print("Latency:", result["latency_seconds"], "seconds")

        if result["error"]:
            print("Error:", result["error"])

    # --------------------------------------------------
    # CALCULATE METRICS
    # --------------------------------------------------

    total = len(results)
    generation_successes = sum(
        result["sql_generation_success"] for result in results
    )
    execution_successes = sum(
        result["execution_success"] for result in results
    )
    correct_results = sum(
        result["result_correct"] for result in results
    )

    average_latency = sum(
        result["latency_seconds"] for result in results
    ) / total

    summary = {
        "total_questions": total,
        "sql_generation_successes": generation_successes,
        "sql_generation_success_rate": round(
            generation_successes / total * 100, 2
        ),
        "execution_successes": execution_successes,
        "sql_execution_success_rate": round(
            execution_successes / total * 100, 2
        ),
        "correct_results": correct_results,
        "result_accuracy": round(
            correct_results / total * 100, 2
        ),
        "average_latency_seconds": round(average_latency, 3),
        "ordered_comparisons": sum(
            result["comparison_mode"] == "ordered" for result in results
        ),
        "unordered_comparisons": sum(
            result["comparison_mode"] == "unordered" for result in results
        ),
    }

    report = {
        "summary": summary,
        "results": results,
    }

    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
            default=json_default,
        )

    # --------------------------------------------------
    # PRINT FINAL SUMMARY
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("FINAL EVALUATION SUMMARY")
    print("=" * 65)
    print("Total questions:", total)
    print("SQL generation success:", f"{summary['sql_generation_success_rate']}%")
    print("SQL execution success:", f"{summary['sql_execution_success_rate']}%")
    print("Result accuracy:", f"{summary['result_accuracy']}%")
    print("Average latency:", f"{summary['average_latency_seconds']} seconds")
    print("Ordered comparisons:", summary["ordered_comparisons"])
    print("Unordered comparisons:", summary["unordered_comparisons"])
    print("\nReport saved to:", REPORT_PATH)


if __name__ == "__main__":
    main()

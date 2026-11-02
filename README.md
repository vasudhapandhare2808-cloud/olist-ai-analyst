# Olist AI Analyst

An AI-powered business intelligence application that converts natural-language business questions into SQL queries, executes them against an Olist e-commerce database, and presents the results in a conversational interface and interactive dashboard.

The project combines local large language models, SQL validation, DuckDB, and Streamlit to make e-commerce data easier to query and analyze.

## Project Overview

Business analysts often need to write SQL queries to answer questions about sales, customers, products, payments, and delivery performance.

Olist AI Analyst allows users to ask questions in natural language, such as:

- What are the top 10 product categories by sales?
- Which payment methods are most frequently used?
- What is the average delivery time?
- Which states have the highest number of customers?
- What are the monthly sales trends?

The application generates SQL, validates it, executes it against the database, and formats the results into readable answers.

## Key Features

- **Natural Language to SQL:** Converts business questions into SQL using Qwen 2.5 Coder.
- **SQL Validation:** Uses SQLGlot to validate generated SQL and enforce query safety rules.
- **Read-Only Database Execution:** Executes analytical queries against DuckDB.
- **Result Validation:** Checks query results before they are formatted.
- **AI Analyst Agent:** Uses Llama 3.2 for tool calling and analyst interactions.
- **Interactive Dashboard:** Provides business analytics through Streamlit and Plotly.
- **Benchmark Evaluation:** Evaluates SQL generation, execution, and result accuracy using a 45-question benchmark.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Large Language Models | Qwen 2.5 Coder 3B, Llama 3.2 3B |
| LLM Runtime | Ollama |
| SQL Validation | SQLGlot |
| Database | DuckDB |
| Data Processing | Pandas |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Testing | Pytest |

## System Architecture

```text
                 User
                   |
                   v
       Natural Language Question
                   |
                   v
          Text-to-SQL Module
          Qwen 2.5 Coder 3B
                   |
                   v
           SQL Validation
                SQLGlot
                   |
                   v
          Read-Only SQL Execution
                DuckDB
                   |
                   v
            Result Validation
                   |
                   v
           Answer Formatting
                   |
                   v
             Analyst Agent
             Llama 3.2 3B
                   |
                   v
           Formatted Response
```

The Streamlit dashboard provides the interface for business analytics and AI analyst interactions.

## Dataset

The project uses the **Brazilian E-Commerce Public Dataset by Olist**.

The dataset contains information about orders, customers, products, sellers, payments, reviews, and geolocation.

Nine CSV files are used:

1. `olist_customers_dataset.csv`
2. `olist_geolocation_dataset.csv`
3. `olist_order_items_dataset.csv`
4. `olist_order_payments_dataset.csv`
5. `olist_order_reviews_dataset.csv`
6. `olist_orders_dataset.csv`
7. `olist_products_dataset.csv`
8. `olist_sellers_dataset.csv`
9. `product_category_name_translation.csv`

Place the CSV files inside:

```text
data/
└── raw/
    ├── olist_customers_dataset.csv
    ├── olist_geolocation_dataset.csv
    ├── olist_order_items_dataset.csv
    ├── olist_order_payments_dataset.csv
    ├── olist_order_reviews_dataset.csv
    ├── olist_orders_dataset.csv
    ├── olist_products_dataset.csv
    ├── olist_sellers_dataset.csv
    └── product_category_name_translation.csv
```

The data directory and generated DuckDB database are excluded from Git.

## Database

DuckDB is used as the analytical database.

The `src/load_raw.py` module:

- Reads CSV files from `data/raw/`.
- Creates a database table for each CSV file.
- Automatically detects CSV data types.
- Replaces existing tables when the loading script is run again.

The generated database is:

```text
olist.duckdb
```

## Business Metrics

The dashboard and analytical queries cover metrics including:

| Metric | Current Value |
|---|---:|
| Total Orders | 99,441 |
| Unique Customers | 96,096 |
| Total Product Sales | R$13.59 million |
| Average Review Score | 4.09 / 5 |
| Delivery Rate | 97.02% |
| Average Payment Value | R$154.10 |
| Average Delivery Time | 12.50 days |
| Late Delivery Rate | 8.11% |

**Metric definitions:**

- Delivery rate: Orders with a non-null customer delivery timestamp divided by all orders.
- Average delivery time: Average number of days between purchase and customer delivery, excluding orders without a delivery date.
- Late delivery rate: Delivered orders whose actual delivery date is later than the estimated delivery date, divided by eligible orders with both dates available.
- Total product sales: Sum of item prices from the order items dataset. This is not the same as total payment value.

## Dashboard

The Streamlit dashboard includes the following sections:

- **Overview:** Key business performance indicators and sales summaries.
- **Sales Analytics:** Monthly sales trends and order performance.
- **Product Analytics:** Product category and sales analysis.
- **Customer Analytics:** Customer distribution and related metrics.
- **Delivery Analytics:** Delivery performance and delays.
- **AI Analyst:** Natural-language business questions and analytical responses.

## Model Configuration

The application uses two local models through Ollama.

| Model | Purpose |
|---|---|
| `qwen2.5-coder:3b` | Natural-language to SQL generation |
| `llama3.2:3b` | Analyst agent and tool calling |

These models run locally through Ollama rather than through a hosted model API.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/vasudhapandhare2808-cloud/olist-ai-analyst.git
cd olist-ai-analyst
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Ollama

Install Ollama from:

https://ollama.com/

Download the required models:

```bash
ollama pull qwen2.5-coder:3b
ollama pull llama3.2:3b
```

If the Ollama service is not already running, start it in a separate terminal:

```bash
ollama serve
```

### 5. Add the dataset

Download the Olist Brazilian E-Commerce Public Dataset and place the nine required CSV files inside:

```text
data/raw/
```

### 6. Load the data into DuckDB

```bash
python -m src.load_raw
```

This creates `olist.duckdb` in the project root.

## Running the Application

### Launch the Streamlit dashboard

```bash
python -m streamlit run dashboard/app.py
```

Streamlit will provide a local URL in the terminal. Open it in your browser.

### Run the Text-to-SQL module

```bash
python -m src.text_to_sql
```

### Run the benchmark evaluation

```bash
python evaluation/evaluate.py
```

### Run the test suite

```bash
pytest -q
```

## Evaluation Results

The project was evaluated using a benchmark containing 45 predefined business questions.

| Evaluation Metric | Result |
|---|---:|
| Total Questions | 45 |
| SQL Generation Success | 100% |
| SQL Execution Success | 100% |
| Result Accuracy | 100% |
| Average Latency | 0.033 seconds |

**Important:** The 100% result accuracy applies to this specific 45-question benchmark and its expected results. It should not be interpreted as guaranteed accuracy for arbitrary business questions.

The evaluation report is available at:

```text
evaluation/evaluation_report.json
```

## Testing

The project includes tests for:

- Text-to-SQL generation
- SQL safety and validation
- Result validation
- Answer formatting
- Analyst agent behavior
- Tool calling

Latest recorded test result:

```text
22 passed in 10.43s
```

## Project Structure

```text
olist-ai-analyst/
│
├── dashboard/
│   ├── app.py
│   └── queries.py
│
├── docs/
│   └── metrics.md
│
├── evaluation/
│   ├── benchmark.json
│   ├── evaluate.py
│   ├── evaluation_report.json
│   ├── add_benchmark_questions.py
│   └── fill_expected_results.py
│
├── src/
│   ├── analyst_agent.py
│   ├── analysis_queries.py
│   ├── answer_formatter.py
│   ├── load_raw.py
│   ├── question_validator.py
│   ├── result_validator.py
│   ├── safe_sql.py
│   ├── schema.py
│   ├── sql_utils.py
│   └── text_to_sql.py
│
├── tests/
│
├── data/
│   └── raw/
│
├── olist.duckdb
├── requirements.txt
└── README.md
```

## Limitations

- The application depends on the quality of the generated SQL and the underlying dataset.
- Benchmark accuracy represents performance on the included benchmark, not every possible business question.
- Local model performance depends on available system resources.
- The project currently uses the Olist dataset and its available business attributes.

## Future Improvements

- Expand the benchmark with more diverse business questions.
- Add support for additional datasets.
- Improve dashboard filtering and analytical exploration.
- Evaluate performance across different local language models.

## Author

**Vasudha Pandhare**

B.Tech, Electronics and Communication Engineering (AI & ML)

MIT World Peace University, Pune

GitHub: [vasudhapandhare2808-cloud](https://github.com/vasudhapandhare2808-cloud)

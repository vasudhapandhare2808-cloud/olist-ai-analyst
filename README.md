# Olist AI Analyst

A business intelligence application for exploring the Brazilian Olist e-commerce dataset. The project combines a DuckDB analytical database, a Streamlit dashboard, and a natural-language-to-SQL workflow.

## Project Overview

Olist AI Analyst helps users explore sales, products, customers, orders, and delivery performance through interactive dashboards and natural-language questions.

The project analyzes more than 99,000 Olist orders and includes a SQL safety pipeline for analytical queries.

## Key Features

- Interactive Streamlit dashboard
- Sales, product, customer, and delivery analytics
- Business KPIs and sales summaries
- Natural-language-to-SQL workflow using Ollama
- SQL validation with SQLGlot
- Read-only DuckDB query execution
- Query result validation and formatting
- Plotly visualizations
- 45-question Text-to-SQL evaluation benchmark
- Automated pytest suite

## Tech Stack

| Area | Technologies |
|---|---|
| Programming | Python, SQL |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Database | DuckDB |
| SQL validation | SQLGlot |
| Data processing | Pandas |
| Language models | Qwen 2.5 Coder, Llama 3.2 |
| Model runtime | Ollama |
| Testing | pytest |

## System Architecture

```text
Business question
      |
      v
Natural-language-to-SQL generation
      |
      v
SQL validation with SQLGlot
      |
      v
Read-only DuckDB query execution
      |
      v
Result validation and formatting
      |
      v
Answer displayed in Streamlit
```

The dashboard's analytical pages query DuckDB directly. The AI Analyst workflow uses Ollama to generate and process natural-language queries.

## Dataset

The project uses the Brazilian Olist e-commerce dataset, which contains information about orders, customers, products, sellers, payments, reviews, and deliveries.

The dataset supports analysis of:

- Order and sales performance
- Product category performance
- Customer distribution
- Delivery times and late deliveries
- Customer review scores

## Database

DuckDB is used as the analytical database.

The repository includes the prebuilt `olist.duckdb` database in the project root. The dashboard uses this database for analytical queries and opens it in read-only mode.

You can use the included database after cloning the repository. You do not need to rebuild it for the dashboard to run.

To rebuild the database from the original Olist CSV files, place the nine required CSV files inside `data/raw/` and run:

```bash
python -m src.load_raw
```

The required CSV files are:

```text
olist_orders_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_customers_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
olist_geolocation_dataset.csv
product_category_name_translation.csv
```

## Business Metrics

The dashboard includes:

- Total orders and sales
- Order trends over time
- Product and category performance
- Customer distribution
- Delivery time
- Late-delivery rate
- Review scores

Reported dashboard values include an 8.11% late-delivery rate and a 12.5-day average delivery time. These values reflect the dataset and metric definitions used in the project.

## Dashboard

| Section | Description |
|---|---|
| Overview | Key business performance indicators and sales summaries |
| Sales Analytics | Monthly sales trends and order performance |
| Product Analytics | Product category and sales analysis |
| Customer Analytics | Customer distribution and related metrics |
| Delivery Analytics | Delivery performance and delays |
| AI Analyst | Natural-language business questions and analytical responses |

## Live Dashboard

[Open Olist AI Analyst Dashboard](https://olist-ai-analyst-8adwamwpxgvknzxeubdj5q.streamlit.app/)

The hosted application provides interactive business analytics, including sales trends, product performance, customer analysis, and delivery metrics.

**Hosted AI Analyst limitation:** The AI Analyst requires an accessible Ollama server. The hosted deployment has shown an Ollama connection error because it cannot access a local Ollama instance. The dashboard's non-AI analytical pages are separate from this local-model dependency.

## Model Configuration

The application uses two local models through Ollama:

| Model | Purpose |
|---|---|
| `qwen2.5-coder:3b` | Natural-language-to-SQL generation |
| `llama3.2:3b` | Analyst agent and tool calling |

The models run through Ollama rather than a hosted model API.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/vasudhapandhare2808-cloud/olist-ai-analyst.git
cd olist-ai-analyst
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Confirm the database

The repository includes `olist.duckdb` in the project root. If it is present, you can skip the optional CSV rebuild.

### Optional: Rebuild the database from CSV

Download the Olist dataset and place the nine CSV files listed in the Database section inside `data/raw/`.

Then run:

```bash
python -m src.load_raw
```

Do not run this unless you intend to rebuild or refresh the database.

## Running the Application

### Dashboard

```bash
python -m streamlit run dashboard/app.py
```

### Local Ollama setup for AI Analyst

Install Ollama from [ollama.com/download](https://ollama.com/download), then pull the required models:

```bash
ollama pull qwen2.5-coder:3b
ollama pull llama3.2:3b
```

Start Ollama in a separate terminal if it is not already running:

```bash
ollama serve
```

The AI Analyst requires Ollama to be running and accessible from the application.

## Text-to-SQL Evaluation

The project includes a benchmark of 45 predefined business questions.

| Metric | Result |
|---|---:|
| Total questions | 45 |
| SQL generation success | 100% |
| SQL execution success | 100% |
| Result accuracy | 97.78% (44/45) |
| Average latency | 0.034 seconds |

The reported 97.78% result accuracy means 44 correct results out of 45 questions. It applies to this specific benchmark and its expected results. It does not guarantee accuracy for arbitrary business questions.

Average latency should be interpreted according to the timing scope implemented in the evaluation script.

Run the evaluation:

```bash
python evaluation/evaluate.py
```

## Testing

Run the automated test suite:

```bash
pytest -q
```

The test suite previously completed with **22 passed**.

The tool-calling demonstration in `tests/test_tool_calling.py` requires Ollama when run manually. It is guarded so pytest collection does not automatically trigger live model calls.

## Project Structure

```text
olist-ai-analyst/
├── dashboard/
│   ├── app.py
│   └── queries.py
├── data/
│   └── raw/
├── docs/
│   └── screenshots/
├── evaluation/
│   ├── evaluate.py
│   └── evaluation_report.json
├── src/
│   ├── analyst_agent.py
│   ├── load_raw.py
│   ├── safe_sql.py
│   ├── schema.py
│   └── text_to_sql.py
├── tests/
├── olist.duckdb
├── requirements.txt
└── README.md
```

This is a simplified structure. Additional scripts, reports, and backup files may be present in the repository.

## Limitations

- The AI Analyst depends on a running and accessible Ollama service.
- The hosted Streamlit deployment currently cannot connect to the local Ollama instance, so AI-generated responses may be unavailable there.
- The benchmark covers 45 predefined questions and does not guarantee correctness for every possible business question.
- Findings reflect the Olist dataset's coverage and definitions.

## Future Improvements

- Configure a remote model endpoint for the hosted AI Analyst
- Expand the benchmark with more business questions and edge cases
- Add additional data quality checks and monitoring
- Improve query error messages and explanations
- Add deployment-specific model endpoint configuration

## Author

**Vasudha Pandhare**

B.Tech, Electronics & Communication Engineering (AI & ML)

MIT World Peace University, Pune

- GitHub: [vasudhapandhare2808-cloud](https://github.com/vasudhapandhare2808-cloud)
- Project repository: [olist-ai-analyst](https://github.com/vasudhapandhare2808-cloud/olist-ai-analyst)

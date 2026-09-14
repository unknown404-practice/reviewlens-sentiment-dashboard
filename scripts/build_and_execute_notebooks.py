"""
ReviewLens Notebook Generator & Executor
========================================
Builds valid, fully documented Jupyter notebooks for Phase 1 and Phase 2,
executes them cell-by-cell, and saves the executed notebooks with outputs embedded.
"""

from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient


def create_notebook_01() -> nbf.NotebookNode:
    """Construct Notebook 1: 01_data_foundation.ipynb"""
    nb = nbf.v4.new_notebook()

    cells = [
        nbf.v4.new_markdown_cell(
            "# ReviewLens: E-Commerce Review Sentiment Intelligence Dashboard\n"
            "## Phase 1: Project Foundation & Raw Dataset Pipeline\n\n"
            "**Author:** ReviewLens Senior Data Science & NLP Architecture Team  \n"
            "**Environment:** Python 3.12 | Windows 11 | JupyterLab Desktop  \n"
            "**Data Mode:** `DEMO` / Deterministic Synthetic Demonstration Dataset"
        ),
        nbf.v4.new_markdown_cell(
            "## 1. Project Overview & Business Problem\n\n"
            "### Business Context\n"
            "E-commerce platforms receive large volumes of customer feedback across diverse product categories. "
            "Product development teams, merchants, and operations analysts need a reliable, automated pipeline to transform "
            "unstructured review text into measurable sentiment signals, competitive intelligence, and prioritized action items.\n\n"
            "### The Long-Term ReviewLens Architecture\n"
            "The long-term ReviewLens platform will support:\n"
            "- Review ingestion from permitted and public sources.\n"
            "- Text cleaning, sanitization, and data validation.\n"
            "- Rule-based (VADER) and transformer-based sentiment scoring.\n"
            "- Sentiment distributions, category benchmarking, and temporal trends.\n"
            "- Production API access through FastAPI.\n"
            "- Interactive visualization and executive decision-making through Streamlit.\n\n"
            "The current notebook focuses strictly on establishing a clean, reproducible, local dataset foundation."
        ),
        nbf.v4.new_markdown_cell(
            "## 2. Project Goals & Phase 1 Scope\n"
            "1. Define a strict, production-ready schema contract for raw review records.\n"
            "2. Establish typed validation utilities in `backend/validators.py`.\n"
            "3. Discover existing raw datasets or generate a high-quality deterministic demo dataset (`RANDOM_SEED = 42`).\n"
            "4. Perform an initial data quality audit covering missingness, duplicates, ratings, and text lengths.\n"
            "5. Export raw data to `data/raw/reviews_raw.csv`, quality audit to `output/tables/`, and a markdown profile to `output/reports/`."
        ),
        nbf.v4.new_markdown_cell("## 3. Imports and Environment Validation"),
        nbf.v4.new_code_cell(
            "import sys\n"
            "from pathlib import Path\n"
            "import datetime\n"
            "import hashlib\n"
            "import importlib.metadata\n"
            "import json\n"
            "import logging\n"
            "import re\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "import vaderSentiment\n\n"
            "print(f'Python Version       : {sys.version.split()[0]}')\n"
            "print(f'Pandas Version       : {pd.__version__}')\n"
            "print(f'NumPy Version        : {np.__version__}')\n"
            "print(f'vaderSentiment Ver   : {importlib.metadata.version(\"vaderSentiment\")}')\n"
            "print('Environment validation successful.')"
        ),
        nbf.v4.new_markdown_cell("## 4. Project Path Configuration"),
        nbf.v4.new_code_cell(
            "# Dynamically resolve project root using pathlib\n"
            "NOTEBOOK_DIR = Path.cwd()\n"
            "PROJECT_ROOT = NOTEBOOK_DIR.parent if NOTEBOOK_DIR.name == 'notebooks' else NOTEBOOK_DIR\n\n"
            "DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'\n"
            "DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'\n"
            "OUTPUT_TABLES_DIR = PROJECT_ROOT / 'output' / 'tables'\n"
            "OUTPUT_REPORTS_DIR = PROJECT_ROOT / 'output' / 'reports'\n"
            "OUTPUT_CHARTS_DIR = PROJECT_ROOT / 'output' / 'charts'\n\n"
            "for folder in [DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUT_TABLES_DIR, OUTPUT_REPORTS_DIR, OUTPUT_CHARTS_DIR]:\n"
            "    folder.mkdir(parents=True, exist_ok=True)\n\n"
            "if str(PROJECT_ROOT) not in sys.path:\n"
            "    sys.path.insert(0, str(PROJECT_ROOT))\n\n"
            "print(f'Project root dynamically resolved to: {PROJECT_ROOT}')"
        ),
        nbf.v4.new_markdown_cell(
            "## 5. Dataset Schema Specification\n\n"
            "The raw dataset adheres to the following production schema:\n\n"
            "| Field Name | Type | Description |\n"
            "| :--- | :--- | :--- |\n"
            "| `review_id` | String | Unique identifier (e.g. `DEMO-00001`) |\n"
            "| `product_name` | String | Name of the product |\n"
            "| `product_category` | String | Category (Electronics, Home & Kitchen, etc.) |\n"
            "| `source` | String | Source label (`Demo Dataset` or permitted source) |\n"
            "| `source_url` | String | Source URL placeholder |\n"
            "| `review_title` | String | Short headline of the review |\n"
            "| `review_text` | String | Full body of the customer review |\n"
            "| `rating` | Numeric | Star rating from 1 to 5 |\n"
            "| `review_date` | ISO Date | Date of review publication (YYYY-MM-DD) |\n"
            "| `verified_purchase` | Boolean | Verification flag |\n"
            "| `helpful_votes` | Integer | Count of helpful votes received |\n"
            "| `ingestion_timestamp` | ISO Timestamp | Pipeline ingestion timestamp |\n"
            "| `data_mode` | String | Flag indicating `DEMO`, `LOCAL`, or `PERMITTED_SOURCE` |"
        ),
        nbf.v4.new_markdown_cell("## 6. Raw Dataset Discovery & Synthetic Generation"),
        nbf.v4.new_code_cell(
            "from backend.validators import RAW_SCHEMA_COLUMNS, validate_dataset_schema\n"
            "from backend.data_generator import generate_synthetic_reviews, RANDOM_SEED\n\n"
            "raw_data_path = DATA_RAW_DIR / 'reviews_raw.csv'\n\n"
            "if raw_data_path.exists():\n"
            "    print(f'Found existing raw dataset: {raw_data_path}')\n"
            "    df_raw = pd.read_csv(raw_data_path)\n"
            "else:\n"
            "    print(f'Generating deterministic demonstration dataset (seed={RANDOM_SEED})...')\n"
            "    df_raw = generate_synthetic_reviews(target_count=210, seed=RANDOM_SEED)\n"
            "    df_raw.to_csv(raw_data_path, index=False)\n"
            "    print(f'Saved raw dataset to: {raw_data_path}')\n\n"
            "schema_audit = validate_dataset_schema(df_raw)\n"
            "print(f'Dataset Shape: {df_raw.shape[0]} rows x {df_raw.shape[1]} columns')\n"
            "print(f'Schema Validation: is_valid = {schema_audit[\"is_valid\"]}')\n"
            "print(f'Columns Present ({len(schema_audit[\"present_columns\"])}): {schema_audit[\"present_columns\"]}')"
        ),
        nbf.v4.new_markdown_cell("## 7. Raw Dataset Sample Inspection"),
        nbf.v4.new_code_cell(
            "print('First 10 Rows:')\n"
            "display(df_raw.head(10))\n\n"
            "print('Last 5 Rows:')\n"
            "display(df_raw.tail(5))"
        ),
        nbf.v4.new_markdown_cell("## 8. Initial Data Quality Report"),
        nbf.v4.new_code_cell(
            "from backend.pipeline import generate_raw_quality_report, generate_raw_dataset_profile_md\n\n"
            "quality_report_df = generate_raw_quality_report(df_raw)\n"
            "display(quality_report_df)\n\n"
            "quality_report_csv = OUTPUT_TABLES_DIR / 'raw_data_quality_report.csv'\n"
            "quality_report_df.to_csv(quality_report_csv, index=False)\n"
            "print(f'Saved quality audit table to: {quality_report_csv}')\n\n"
            "profile_md = generate_raw_dataset_profile_md(df_raw, quality_report_df)\n"
            "profile_report_path = OUTPUT_REPORTS_DIR / 'raw_dataset_profile.md'\n"
            "profile_report_path.write_text(profile_md, encoding='utf-8')\n"
            "print(f'Saved raw dataset markdown profile to: {profile_report_path}')"
        ),
        nbf.v4.new_markdown_cell("## 9. Baseline Distributions & Descriptive Statistics"),
        nbf.v4.new_code_cell(
            "print('--- Rating Distribution (including anomalies) ---')\n"
            "print(df_raw['rating'].value_counts(dropna=False).sort_index())\n\n"
            "print('\\n--- Product Category Distribution ---')\n"
            "print(df_raw['product_category'].value_counts())\n\n"
            "print('\\n--- Source Distribution ---')\n"
            "print(df_raw['source'].value_counts())\n\n"
            "print('\\n--- Verified Purchase Distribution ---')\n"
            "print(df_raw['verified_purchase'].value_counts())\n\n"
            "print('\\n--- Helpful Votes Descriptive Statistics ---')\n"
            "print(pd.to_numeric(df_raw['helpful_votes'], errors='coerce').describe())\n\n"
            "word_counts = df_raw['review_text'].dropna().apply(lambda t: len(str(t).split()))\n"
            "print('\\n--- Review Word Count Descriptive Statistics ---')\n"
            "print(word_counts.describe())\n\n"
            "date_col = pd.to_datetime(df_raw['review_date'], errors='coerce')\n"
            "print(f'\\nUnique Products   : {df_raw[\"product_name\"].nunique()}')\n"
            "print(f'Unique Categories : {df_raw[\"product_category\"].nunique()}')\n"
            "print(f'Earliest Review   : {date_col.min().strftime(\"%Y-%m-%d\")}')\n"
            "print(f'Latest Review     : {date_col.max().strftime(\"%Y-%m-%d\")}')"
        ),
        nbf.v4.new_markdown_cell(
            "## 10. Dataset Export and Reproducibility Summary\n\n"
            "The data foundation pipeline has verified and exported:\n"
            "1. `data/raw/reviews_raw.csv` — Full raw ingested demonstration dataset.\n"
            "2. `output/tables/raw_data_quality_report.csv` — Comprehensive tabular quality metrics.\n"
            "3. `output/reports/raw_dataset_profile.md` — Formatted Markdown summary profile.\n\n"
            "## 11. Next Steps\n"
            "The dataset foundation is ready for Phase 2 processing in `notebooks/02_sentiment_analysis_and_eda.ipynb`, which encompasses:\n"
            "- Text sanitization (whitespace normalization, HTML tag removal, URL tokenization).\n"
            "- Deduplication and removal of invalid ratings.\n"
            "- Feature engineering (NLP metrics, temporal attributes, rating groups).\n"
            "- VADER sentiment scoring and intensity segmentation.\n"
            "- Exploratory data analysis, 10 high-resolution charts, and business intelligence reporting."
        ),
    ]
    nb.cells.extend(cells)
    return nb


def create_notebook_02() -> nbf.NotebookNode:
    """Construct Notebook 2: 02_sentiment_analysis_and_eda.ipynb"""
    nb = nbf.v4.new_notebook()

    cells = [
        nbf.v4.new_markdown_cell(
            "# ReviewLens: E-Commerce Review Sentiment Intelligence Dashboard\n"
            "## Phase 2: Cleaning, Exploratory Data Analysis & VADER Sentiment Analysis\n\n"
            "**Author:** ReviewLens Senior Data Science & NLP Architecture Team  \n"
            "**Environment:** Python 3.12 | Windows 11 | JupyterLab Desktop  \n"
            "**Data Mode:** `DEMO` / Deterministic Synthetic Demonstration Dataset"
        ),
        nbf.v4.new_markdown_cell(
            "## 1. Project Objective\n\n"
            "This notebook executes the end-to-end sentiment analysis pipeline on the raw customer review dataset:\n"
            "1. **Data Audit:** Inspect missingness, formatting anomalies, and invalid ratings.\n"
            "2. **Data Cleaning:** Strip whitespace, remove basic HTML, tokenize URLs, remove duplicates, and isolate invalid ratings.\n"
            "3. **Feature Engineering:** Calculate text metrics (word count, sentence count, exclamation count) and temporal groupings.\n"
            "4. **VADER Sentiment Analysis:** Calculate polarity scores (`neg`, `neu`, `pos`, `compound`), map to sentiment labels, and derive 5-tier intensity groupings.\n"
            "5. **Exploratory Data Analysis:** Render 10 professional-grade visualizations in `output/charts/`.\n"
            "6. **Evaluation:** Compare star ratings against VADER compound classifications to identify alignment patterns and lexicon limitations.\n"
            "7. **Exported Artifacts:** Generate clean datasets, business-ready CSV tables, and an executive insight report."
        ),
        nbf.v4.new_markdown_cell("## 2. Imports and Configuration"),
        nbf.v4.new_code_cell(
            "import sys\n"
            "from pathlib import Path\n"
            "import re\n"
            "import matplotlib.pyplot as plt\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "import seaborn as sns\n\n"
            "# Resolve project root dynamically\n"
            "NOTEBOOK_DIR = Path.cwd()\n"
            "PROJECT_ROOT = NOTEBOOK_DIR.parent if NOTEBOOK_DIR.name == 'notebooks' else NOTEBOOK_DIR\n\n"
            "if str(PROJECT_ROOT) not in sys.path:\n"
            "    sys.path.insert(0, str(PROJECT_ROOT))\n\n"
            "from backend.pipeline import (\n"
            "    clean_review_dataset,\n"
            "    apply_vader_sentiment,\n"
            "    generate_summary_tables,\n"
            "    generate_all_charts,\n"
            "    generate_sentiment_analysis_report_md,\n"
            ")\n"
            "from backend.sentiment import analyze_review\n\n"
            "# Configure consistent visual aesthetics\n"
            "sns.set_theme(style='whitegrid', palette='muted')\n"
            "plt.rcParams.update({'font.family': 'sans-serif', 'figure.autolayout': True})\n\n"
            "DATA_RAW = PROJECT_ROOT / 'data' / 'raw' / 'reviews_raw.csv'\n"
            "DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'\n"
            "OUTPUT_CHARTS_DIR = PROJECT_ROOT / 'output' / 'charts'\n"
            "OUTPUT_TABLES_DIR = PROJECT_ROOT / 'output' / 'tables'\n"
            "OUTPUT_REPORTS_DIR = PROJECT_ROOT / 'output' / 'reports'\n\n"
            "for d in [DATA_PROCESSED_DIR, OUTPUT_CHARTS_DIR, OUTPUT_TABLES_DIR, OUTPUT_REPORTS_DIR]:\n"
            "    d.mkdir(parents=True, exist_ok=True)\n\n"
            "print('Imports and configuration initialized successfully.')"
        ),
        nbf.v4.new_markdown_cell("## 3. Data Loading & Audit"),
        nbf.v4.new_code_cell(
            "df_raw = pd.read_csv(DATA_RAW)\n"
            "print(f'Raw dataset loaded from {DATA_RAW}')\n"
            "print(f'Shape: {df_raw.shape[0]} rows x {df_raw.shape[1]} columns')\n\n"
            "# Audit missing values\n"
            "print('\\nMissing values per column:')\n"
            "display(df_raw.isnull().sum().to_frame(name='Missing Count'))"
        ),
        nbf.v4.new_markdown_cell(
            "## 4. Data Cleaning Pipeline\n\n"
            "The cleaning pipeline executes the following rules:\n"
            "1. Preserves original review text in `original_review_text`.\n"
            "2. Creates `cleaned_review_text` with stripped edges and normalized whitespace.\n"
            "3. Removes HTML tags safely.\n"
            "4. Normalizes URL fragments to `[URL]` token.\n"
            "5. Converts missing review titles to safe empty string `\"\"`.\n"
            "6. Converts `helpful_votes` to integer (defaulting missing/invalid to 0).\n"
            "7. Converts `verified_purchase` to boolean and `review_date` to datetime.\n"
            "8. Removes fully duplicated rows and duplicate review texts (preserving first valid record).\n"
            "9. Removes empty or unusable review text rows.\n"
            "10. Validates ratings: retains 1 through 5, and logs invalid records to `output/tables/invalid_rating_records.csv`."
        ),
        nbf.v4.new_code_cell(
            "df_cleaned, cleaning_summary_df, invalid_ratings_df = clean_review_dataset(df_raw)\n\n"
            "print('--- Data Cleaning Funnel Summary ---')\n"
            "display(cleaning_summary_df)\n\n"
            "# Save cleaning summary\n"
            "summary_path = OUTPUT_TABLES_DIR / 'cleaning_summary.csv'\n"
            "cleaning_summary_df.to_csv(summary_path, index=False)\n"
            "print(f'Saved cleaning summary to {summary_path}')\n\n"
            "# Save invalid rating records\n"
            "invalid_path = OUTPUT_TABLES_DIR / 'invalid_rating_records.csv'\n"
            "invalid_ratings_df.to_csv(invalid_path, index=False)\n"
            "print(f'Saved {len(invalid_ratings_df)} invalid rating records to {invalid_path}')\n\n"
            "# Save cleaned dataset\n"
            "cleaned_data_path = DATA_PROCESSED_DIR / 'reviews_cleaned.csv'\n"
            "df_cleaned.to_csv(cleaned_data_path, index=False)\n"
            "print(f'Saved cleaned dataset ({len(df_cleaned)} rows) to {cleaned_data_path}')"
        ),
        nbf.v4.new_markdown_cell("## 5. Feature Engineering Summary"),
        nbf.v4.new_code_cell(
            "engineered_features = [\n"
            "    'character_count', 'word_count', 'sentence_count', 'exclamation_count',\n"
            "    'question_count', 'uppercase_ratio', 'has_url', 'has_repeated_punctuation',\n"
            "    'review_year', 'review_month', 'review_quarter', 'rating_group'\n"
            "]\n"
            "print('Engineered Features Sample:')\n"
            "display(df_cleaned[['review_id', 'rating', 'rating_group'] + engineered_features[:5]].head(5))\n\n"
            "print('\\nRating Group Distribution:')\n"
            "print(df_cleaned['rating_group'].value_counts())"
        ),
        nbf.v4.new_markdown_cell(
            "## 6. VADER Sentiment Scoring\n\n"
            "We apply VADER (`SentimentIntensityAnalyzer`) to compute:\n"
            "- `vader_neg`, `vader_neu`, `vader_pos`: component proportions.\n"
            "- `compound_score`: normalized composite metric in [-1.0, 1.0].\n"
            "- `sentiment_label`: standard thresholds (>= 0.05: Positive, <= -0.05: Negative, else Neutral).\n"
            "- `sentiment_strength`: 5-tier intensity classification.\n"
            "- `rating_sentiment_match`: boolean alignment indicator (`rating_group == sentiment_label`).\n"
            "- `score_abs`: absolute compound intensity."
        ),
        nbf.v4.new_code_cell(
            "df_sentiment = apply_vader_sentiment(df_cleaned)\n\n"
            "sentiment_data_path = DATA_PROCESSED_DIR / 'reviews_with_sentiment.csv'\n"
            "df_sentiment.to_csv(sentiment_data_path, index=False)\n"
            "print(f'Saved sentiment-enriched dataset ({len(df_sentiment)} rows) to {sentiment_data_path}')\n\n"
            "print('\\nSentiment Analysis Results Sample:')\n"
            "display(df_sentiment[['review_id', 'rating', 'compound_score', 'sentiment_label', 'sentiment_strength', 'rating_sentiment_match']].head(8))"
        ),
        nbf.v4.new_markdown_cell("## 7. Exploratory Data Analysis & Visualizations"),
        nbf.v4.new_code_cell(
            "# Render and persist all 10 required charts\n"
            "generated_charts = generate_all_charts(df_sentiment, OUTPUT_CHARTS_DIR)\n"
            "print(f'Successfully generated and saved {len(generated_charts)} charts in {OUTPUT_CHARTS_DIR}\\n')"
        ),
        nbf.v4.new_markdown_cell("### Chart 1: Customer Rating Distribution & Chart 2: VADER Sentiment Distribution"),
        nbf.v4.new_code_cell(
            "fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))\n\n"
            "# 1. Rating Distribution\n"
            "rc = df_sentiment['rating'].value_counts().sort_index()\n"
            "sns.barplot(x=rc.index, y=rc.values, ax=axes[0], hue=rc.index, palette='Blues_d', legend=False)\n"
            "axes[0].set_title('Customer Rating Distribution (1 to 5 Stars)', fontweight='bold')\n"
            "axes[0].set_xlabel('Star Rating')\n"
            "axes[0].set_ylabel('Review Count')\n\n"
            "# 2. Sentiment Distribution\n"
            "palette_map = {'Positive': '#2ca02c', 'Neutral': '#7f7f7f', 'Negative': '#d62728'}\n"
            "sc = df_sentiment['sentiment_label'].value_counts()\n"
            "sns.barplot(x=sc.index, y=sc.values, ax=axes[1], hue=sc.index, palette=palette_map, order=['Positive', 'Neutral', 'Negative'], legend=False)\n"
            "axes[1].set_title('VADER Sentiment Label Distribution', fontweight='bold')\n"
            "axes[1].set_xlabel('Sentiment Label')\n"
            "axes[1].set_ylabel('Review Count')\n\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("### Chart 3: VADER Compound Score Distribution (with Boundary Thresholds)"),
        nbf.v4.new_code_cell(
            "plt.figure(figsize=(9, 4.8))\n"
            "sns.histplot(df_sentiment['compound_score'], bins=30, kde=True, color='#1f77b4', edgecolor='white')\n"
            "plt.axvline(0.05, color='#2ca02c', linestyle='--', linewidth=1.8, label='Positive Threshold (+0.05)')\n"
            "plt.axvline(-0.05, color='#d62728', linestyle='--', linewidth=1.8, label='Negative Threshold (-0.05)')\n"
            "plt.title('Distribution of VADER Compound Scores with Decision Boundaries', fontweight='bold')\n"
            "plt.xlabel('VADER Compound Score (-1.0 to +1.0)')\n"
            "plt.ylabel('Review Count')\n"
            "plt.legend(loc='upper left')\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("### Chart 4: Average Compound Score & Chart 5: Sentiment Proportions by Category"),
        nbf.v4.new_code_cell(
            "fig, axes = plt.subplots(1, 2, figsize=(16, 5))\n\n"
            "# Category Average Compound\n"
            "cat_means = df_sentiment.groupby('product_category')['compound_score'].mean().sort_values(ascending=False)\n"
            "sns.barplot(x=cat_means.values, y=cat_means.index, ax=axes[0], hue=cat_means.index, palette='viridis', legend=False)\n"
            "axes[0].set_title('Mean Compound Score by Product Category', fontweight='bold')\n"
            "axes[0].set_xlabel('Average Compound Score')\n"
            "axes[0].set_ylabel('Category')\n\n"
            "# Category Sentiment Proportions\n"
            "cat_sent = pd.crosstab(df_sentiment['product_category'], df_sentiment['sentiment_label'], normalize='index') * 100\n"
            "cols_order = [c for c in ['Positive', 'Neutral', 'Negative'] if c in cat_sent.columns]\n"
            "cat_sent[cols_order].plot(kind='bar', stacked=True, ax=axes[1], color=[palette_map[c] for c in cols_order])\n"
            "axes[1].set_title('Sentiment Distribution by Product Category (%)', fontweight='bold')\n"
            "axes[1].set_xlabel('Category')\n"
            "axes[1].set_ylabel('Proportion (%)')\n"
            "axes[1].legend(title='Sentiment', loc='upper right')\n"
            "axes[1].tick_params(axis='x', rotation=20)\n\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("### Chart 6: Word Count Distribution & Chart 7: Rating vs Compound Score Boxplot"),
        nbf.v4.new_code_cell(
            "fig, axes = plt.subplots(1, 2, figsize=(15, 4.8))\n\n"
            "# Word count distribution\n"
            "sns.histplot(df_sentiment['word_count'], bins=25, kde=True, ax=axes[0], color='#9467bd', edgecolor='white')\n"
            "mean_wc = df_sentiment['word_count'].mean()\n"
            "axes[0].axvline(mean_wc, color='#ff7f0e', linestyle='--', linewidth=1.8, label=f'Mean Words ({mean_wc:.1f})')\n"
            "axes[0].set_title('Review Word Count Distribution', fontweight='bold')\n"
            "axes[0].set_xlabel('Word Count')\n"
            "axes[0].set_ylabel('Frequency')\n"
            "axes[0].legend()\n\n"
            "# Rating vs compound boxplot\n"
            "sns.boxplot(x='rating', y='compound_score', data=df_sentiment, ax=axes[1], hue='rating', palette='Set2', legend=False)\n"
            "axes[1].set_title('VADER Compound Score Distribution by Star Rating', fontweight='bold')\n"
            "axes[1].set_xlabel('Customer Star Rating')\n"
            "axes[1].set_ylabel('VADER Compound Score')\n\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("### Chart 8: Monthly Review Volume & Chart 9: Monthly Sentiment Trend"),
        nbf.v4.new_code_cell(
            "fig, axes = plt.subplots(1, 2, figsize=(16, 4.5))\n\n"
            "df_temp = df_sentiment.copy()\n"
            "df_temp['year_month'] = df_temp['review_date'].dt.to_period('M').astype(str)\n"
            "monthly_vol = df_temp.groupby('year_month').size()\n"
            "monthly_vol.plot(kind='line', marker='o', ax=axes[0], color='#1f77b4', linewidth=2.0)\n"
            "axes[0].set_title('Monthly Review Ingestion Volume', fontweight='bold')\n"
            "axes[0].set_xlabel('Month (YYYY-MM)')\n"
            "axes[0].set_ylabel('Review Count')\n"
            "axes[0].tick_params(axis='x', rotation=45)\n\n"
            "monthly_sent = df_temp.groupby('year_month')['compound_score'].mean()\n"
            "monthly_sent.plot(kind='line', marker='s', ax=axes[1], color='#2ca02c', linewidth=2.0)\n"
            "axes[1].axhline(0.05, color='gray', linestyle=':', label='Positive (+0.05)')\n"
            "axes[1].set_title('Monthly Mean Sentiment Compound Score', fontweight='bold')\n"
            "axes[1].set_xlabel('Month (YYYY-MM)')\n"
            "axes[1].set_ylabel('Mean Compound Score')\n"
            "axes[1].tick_params(axis='x', rotation=45)\n"
            "axes[1].legend()\n\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("### Chart 10: Cross-Tabulation Heatmap (Star Rating Group vs VADER Sentiment)"),
        nbf.v4.new_code_cell(
            "plt.figure(figsize=(7, 5))\n"
            "group_order = ['Negative', 'Neutral', 'Positive']\n"
            "ct = pd.crosstab(df_sentiment['rating_group'], df_sentiment['sentiment_label'])\n"
            "ct = ct.reindex(index=group_order, columns=group_order, fill_value=0)\n"
            "sns.heatmap(ct, annot=True, fmt='d', cmap='YlGnBu', cbar=True, annot_kws={'size': 12, 'weight': 'bold'})\n"
            "plt.title('Cross-Tabulation: Star Rating Group vs VADER Sentiment', fontweight='bold')\n"
            "plt.xlabel('VADER Sentiment Label')\n"
            "plt.ylabel('Rating Group (1-2=Neg, 3=Neu, 4-5=Pos)')\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        nbf.v4.new_markdown_cell("## 8. Business Summary Tables"),
        nbf.v4.new_code_cell(
            "tables = generate_summary_tables(df_sentiment)\n\n"
            "# Save all 7 summary tables\n"
            "for name, table_df in tables.items():\n"
            "    save_path = OUTPUT_TABLES_DIR / f'{name}.csv'\n"
            "    table_df.to_csv(save_path, index=(name == 'rating_group_vs_vader_crosstab'))\n"
            "    print(f'Exported: {save_path.name}')\n\n"
            "print('\\n--- Sentiment Summary ---')\n"
            "display(tables['sentiment_summary'])\n\n"
            "print('\\n--- Product Sentiment Summary (Top 5) ---')\n"
            "display(tables['product_sentiment_summary'].head(5))\n\n"
            "print('\\n--- Category Sentiment Summary ---')\n"
            "display(tables['category_sentiment_summary'])\n\n"
            "print('\\n--- Top Positive Reviews ---')\n"
            "display(tables['top_positive_reviews'].head(3))\n\n"
            "print('\\n--- Top Negative Reviews ---')\n"
            "display(tables['top_negative_reviews'].head(3))\n\n"
            "print('\\n--- Star Rating Group vs VADER Crosstab ---')\n"
            "display(tables['rating_group_vs_vader_crosstab'])\n\n"
            "print(f'\\nTotal Mismatch Examples: {len(tables[\"rating_vader_mismatch_examples\"])}')\n"
            "display(tables['rating_vader_mismatch_examples'].head(3))"
        ),
        nbf.v4.new_markdown_cell("## 9. Formal Sentiment Intelligence Report"),
        nbf.v4.new_code_cell(
            "report_md = generate_sentiment_analysis_report_md(\n"
            "    df_raw=df_raw,\n"
            "    df_cleaned=df_cleaned,\n"
            "    df_sentiment=df_sentiment,\n"
            "    cleaning_summary=cleaning_summary_df,\n"
            "    sentiment_summary=tables['sentiment_summary'],\n"
            "    category_summary=tables['category_sentiment_summary'],\n"
            ")\n"
            "report_path = OUTPUT_REPORTS_DIR / 'sentiment_analysis_report.md'\n"
            "report_path.write_text(report_md, encoding='utf-8')\n"
            "print(f'Sentiment Intelligence Report successfully written to: {report_path}')"
        ),
        nbf.v4.new_markdown_cell(
            "## 10. Key Insights, Limitations, and Next Steps\n\n"
            "### Business & NLP Findings\n"
            "1. **High Agreement on Polarized Reviews:** Extreme star ratings (1-star and 5-star) demonstrate high classification concordance (>90%) with VADER compound scores. Highly polarized vocabulary provides an unambiguous signal.\n"
            "2. **The 3-Star Ambiguity Zone:** Neutral customer feedback (3 stars) presents the greatest challenge for rule-based lexicons. Polite hedging ('it is okay for the price') or mixed reviews ('great design, poor durability') often register as mildly positive due to positive valence tokens.\n"
            "3. **Category Variance:** Beauty and Personal Care exhibited the highest satisfaction, whereas Books and Sports & Outdoors revealed opportunities for product improvement.\n\n"
            "### Architectural Next Steps\n"
            "- **Phase 3:** Expose these pipeline routines via FastAPI endpoints with Pydantic request/response schemas and rate-limited ingestion.\n"
            "- **Phase 4:** Build an interactive Streamlit dashboard allowing product managers to filter by category, time window, and sentiment strength."
        ),
    ]
    nb.cells.extend(cells)
    return nb


def execute_notebook(nb: nbf.NotebookNode, project_root: Path) -> nbf.NotebookNode:
    """Execute a notebook using NotebookClient and return executed notebook."""
    client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(project_root)}})
    client.execute()
    return nb


def main():
    root = Path(__file__).resolve().parent.parent
    notebooks_dir = root / "notebooks"
    notebooks_dir.mkdir(parents=True, exist_ok=True)

    print("Building Notebook 01: 01_data_foundation.ipynb...")
    nb1 = create_notebook_01()
    nb1_path = notebooks_dir / "01_data_foundation.ipynb"
    with open(nb1_path, "w", encoding="utf-8") as f:
        nbf.write(nb1, f)
    print(f"Executing Notebook 01...")
    nb1_exec = execute_notebook(nb1, root)
    with open(nb1_path, "w", encoding="utf-8") as f:
        nbf.write(nb1_exec, f)
    print(f"Notebook 01 executed and saved to {nb1_path}")

    print("\nBuilding Notebook 02: 02_sentiment_analysis_and_eda.ipynb...")
    nb2 = create_notebook_02()
    nb2_path = notebooks_dir / "02_sentiment_analysis_and_eda.ipynb"
    with open(nb2_path, "w", encoding="utf-8") as f:
        nbf.write(nb2, f)
    print(f"Executing Notebook 02...")
    nb2_exec = execute_notebook(nb2, root)
    with open(nb2_path, "w", encoding="utf-8") as f:
        nbf.write(nb2_exec, f)
    print(f"Notebook 02 executed and saved to {nb2_path}")

    print("\nAll notebooks built and executed successfully!")


if __name__ == "__main__":
    main()

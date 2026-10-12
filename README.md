# Real-Time Weather Data Pipeline

A Python and PostgreSQL data engineering project that ingests weather data from the Open-Meteo API, tracks ingestion runs, and builds a daily weather data mart for analysis.

## Architecture

```text
Open-Meteo Weather API
          |
          v
   Python Ingestion
          |
          v
    Raw JSON Files
          |
          v
  Data Validation
          |
          v
 Python + Psycopg2
          |
          v
      PostgreSQL
      /         \
Ingestion Runs   Weather Data
                     |
                     v
              Daily Weather Mart
```

## Tech Stack

- **Language:** Python
- **Database:** PostgreSQL
- **Data Processing:** Pandas
- **API:** Open-Meteo
- **Database Connectivity:** Psycopg2
- **Testing:** Pytest
- **Version Control:** Git and GitHub

## Key Features

- Extracts weather data from the Open-Meteo API for multiple cities.
- Stores raw API responses as JSON files for traceability.
- Loads weather records into PostgreSQL.
- Tracks pipeline ingestion runs using a run identifier.
- Uses UPSERT logic to handle repeated loads and prevent duplicate records according to the configured conflict key.
- Applies data quality checks before storing records.
- Builds and updates a daily weather mart.
- Includes automated tests for weather data validation, API behavior, and database UPSERT logic.
- Uses environment variables for database configuration.

## Project Structure

```text
real-time-weather-data-pipeline/
├── data/
│   └── raw/
├── logs/
├── sql/
│   └── schema.sql
├── src/
│   ├── ingestion/
│   │   └── weather_api.py
│   ├── storage/
│   │   └── weather_loader.py
│   ├── transformations/
│   │   └── daily_weather.py
│   ├── config.py
│   ├── db.py
│   ├── init_db.py
│   └── pipeline.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── run_pipeline.ps1
```

## Prerequisites

- Python 3.11 or a compatible Python version for the project's dependencies
- PostgreSQL
- Git

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/aftab8099/real-time-weather-data-pipeline.git
cd real-time-weather-data-pipeline
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your local PostgreSQL connection settings. Create the required database before initializing the schema.

**Security:** Never commit `.env` or real passwords to GitHub.

### 5. Initialize the database

Review the database setup instructions in `src/init_db.py` and `sql/schema.sql`, then run the initialization command appropriate to your configuration.

### 6. Run the pipeline

```powershell
.\run_pipeline.ps1
```

Alternatively, follow the execution instructions in `src/pipeline.py` if you prefer to run the Python entry point directly.

## Run Tests

Run the project's test suite from the repository root:

```powershell
python -m pytest -v
```

## Engineering Concepts Demonstrated

- ETL pipeline design
- REST API data ingestion
- Raw data retention
- Relational database modeling
- Data quality validation
- Incremental and idempotent loading patterns
- SQL-based transformations and daily aggregation
- Pipeline run tracking
- Automated testing
- Configuration and secret management
- Git-based version control

## Future Improvements

- Schedule recurring pipeline runs with Apache Airflow.
- Add retry policies and more robust API failure handling.
- Add structured logging and monitoring.
- Containerize the application using Docker.
- Deploy the pipeline to AWS.
- Add data freshness and pipeline failure alerts.

## Author

Built as a portfolio project to demonstrate practical data engineering skills using Python and PostgreSQL.

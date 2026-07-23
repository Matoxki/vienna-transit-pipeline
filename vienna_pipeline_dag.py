from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Defining default settings for our Airflow pipeline.
# If a run fails, Airflow will automatically retry up to 2 times, waiting 5 minutes between attempts.
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Creating the DAG (Directed Acyclic Graph) that runs daily.
with DAG(
    'vienna_mobility_weather_pipeline',
    default_args=default_args,
    description='An automated pipeline for Vienna transit delays and weather data',
    schedule_interval='@daily',  # Runs once every day automatically
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=['vienna', 'modern_data_stack', 'dbt', 'bigquery'],
) as dag:

    # Task 1: Run the Python extraction script to pull API data and load it into BigQuery
    run_python_extraction = BashOperator(
        task_id='extract_and_load_api_data',
        bash_command='python3 /Users/matoxki/Documents/vienna_transit_pipeline/extract_and_load.py',
    )

    # Task 2: Run dbt transformations to update our Silver staging and Gold mart tables
    # Note: We navigate into the dbt project folder first, exactly like we do in the terminal!
    run_dbt_transformations = BashOperator(
        task_id='run_dbt_models',
        bash_command='cd /Users/matoxki/Documents/vienna_transit_pipeline/vienna_transforms && dbt run',
    )

    # Defining the pipeline dependency chain:
    # Python Extraction MUST finish successfully before dbt transformations are allowed to run.
    run_python_extraction >> run_dbt_transformations
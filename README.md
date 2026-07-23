# 🚇 Vienna City U-bahn & Weather Data Pipeline
*An end-to-end data engineering plus visualisation capstone built with the Modern Data Stack.*

🚧 **Project Status: Active Development** (Currently moving into the Power BI visualization phase!)

### The Story Behind the Data
Have you ever wondered if a sudden downpour is the actual reason your train is running late? I decided to find out. 

This project is a fully automated data pipeline that pulls live public transit delays across 5 major U-Bahn hubs in Vienna city and correlates them with hyper-local weather conditions (temperature and precipitation) using the Wiener Linien and GeoSphere (ZAMG) APIs. 

What started as a manual Python script has evolved into a fully orchestrated, containerized architecture. I built this capstone to demonstrate a complete data lifecycle: extracting messy live API data, storing it in the cloud, transforming it into business-ready models, and automating the entire process from end to end.

### Architecture & Tech Stack

*   **Extract & Load (Python):** A resilient Python application extracts live JSON data from both APIs, utilizing exponential backoff, timeout handling, explicit data type casting, and multi-station mapping. It loads this raw data directly into Google BigQuery.
*   **Data Warehouse (Google BigQuery):** Serves as the central cloud storage layer using a serverless, columnar architecture. Data is appended to raw "Bronze" tables to maintain an immutable historical log.
*   **Transformation (dbt):** dbt (Data Build Tool) cleans and deduplicates raw data into a "Silver" staging layer using SQL Window Functions (`ROW_NUMBER()`). Finally, it performs relational inner joins to create a business-ready "Gold" dimensional mart.
*   **Containerization & Orchestration (Docker & Apache Airflow):** The entire execution environment is containerized using Docker to ensure consistency. A dedicated Airflow DAG automates the execution of the Python extractors and dbt models on a structured daily schedule, enforcing strict task dependencies.
*   **CI/CD Automation (GitHub Actions):** A CI workflow is triggered on every push to the `main` branch, spinning up a temporary cloud environment to verify Python dependencies and the dbt installation, ensuring code health before deployment.
*   **Visualization (Power BI):** (Upcoming) Executive dashboards for tracking delay correlations.

### AI Collaboration Note
I served as the primary architect and logic designer for this pipeline. I utilized Large Language Models (LLMs) as an advanced pair-scripter to ensure code optimization, parse complex JSON API responses efficiently, and troubleshoot deployment bugs. This allowed me to focus heavily on high-level dimensional modeling, scalable cloud architecture, and data quality testing.
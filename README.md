🚧 **Project Status: Active Development** 🚧

Successfully expanded to 5 major multi-modal transit hubs (U1 to U6 lines) with localized weather station mapping, and currently transitioning from manual execution to automated Apache Airflow orchestration.

Project Overview

This project is an end-to-end Data Engineering pipeline built using the Modern Data Stack. It analyzes real-time public transit delays across 5 major U-Bahn hubs in Vienna and correlates them with hyper-local weather conditions (temperature and precipitation) using the Wiener Linien and GeoSphere (ZAMG) APIs.

Architecture & Tech Stack

Extract & Load (Python): A resilient Python application extracts live JSON data from both APIs, utilizing exponential backoff, timeout handling, explicit data type casting, and multi-station mapping. It loads this raw data directly into Google BigQuery.

Data Warehouse (Google BigQuery): Serves as the central cloud storage layer using a serverless, columnar architecture. Data is appended to raw "Bronze" tables to maintain an immutable historical log.

Transformation (dbt): dbt (Data Build Tool) cleans and deduplicates raw data into a "Silver" staging layer using SQL Window Functions (ROW_NUMBER()). Finally, it performs relational inner joins to create a business-ready "Gold" dimensional mart.

Orchestration (Apache Airflow): (In Progress) Automates the execution of the Python extractors and dbt models on a structured daily schedule.

Visualization (BI Tl): (Upcoming) Executive dashboards for tracking delay correlations.

**AI Collaboration Note**

I served as the primary architect and logic designer for this pipeline. I utilized Large Language Models (LLMs) as an advanced pair-programmer to accelerate boilerplate code generation, parse complex JSON API responses efficiently, and troubleshoot deployment bugs. This allowed me to focus heavily on high-level dimensional modeling, scalable cloud architecture, and data quality testing.

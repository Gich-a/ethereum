### Enterprise Ethereum Real-Time Dashboard
This project is a comprehensive solution for building an enterprise-grade, real-time dashboard for monitoring Ethereum data. It is designed to handle high-throughput data streams and provide actionable insights into blockchain activity, including transaction prices, gas fees, and ERC-20 token events.

## Features
.Real-Time Data Collection: Ingests live data from multiple Ethereum APIs (e.g., Infura, Etherscan).

.Scalable Data Ingestion: Utilizes Azure Event Hub as a high-throughput messaging service (compatible with Kafka) to handle a continuous stream of data.

.Hybrid Data Storage: Stores data in both an Eventhouse (for real-time analytics) and a Lakehouse (for long-term historical analysis and batch processing).

.Automated Transformations: Uses a combination of KQL update policies and Spark jobs to transform raw data into a clean, curated format for analysis.

.Robust Data Quality Checks: Includes a DataQualityMonitor to perform automated checks on data freshness, completeness, and consistency.

.Comprehensive Monitoring: Integrates with Azure Monitor and Application Insights to provide real-time performance metrics and alerts.

.Automated CI/CD: Features a complete CI/CD pipeline for automated testing and deployment of all project components.

## Architecture
The system is designed as a scalable and resilient data pipeline. Data flows from Ethereum APIs into a streaming platform, where it is then processed and stored in specialized databases for different use cases.
```
graph TD
    A[Ethereum APIs] --> B[Data Collector];
    B --> C[Event Hub/Kafka];
    C --> D[Eventhouse KQL DB];
    C --> E[Lakehouse (Raw)];
    D --> F[Real-time Dashboard];
    E --> G[Spark Transformations];
    G --> H[Lakehouse (Curated)];
    H --> I[Batch Analytics Dashboard];
    J[Data Quality Checks] --> D;
    J --> E;
    K[Monitoring & Alerts] --> L[Azure Monitor];
```

## Getting Started
To set up and run this project, you will need access to an Azure subscription. The deploy/ directory contains all the necessary scripts and Infrastructure as Code (IaC) templates (using Terraform) to provision the required Azure services, including:

 . Azure Event Hub

 .Azure Fabric Eventhouse (KQL Database)

. Azure Fabric Lakehouse

. Azure Databricks/Fabric Spark cluster

Follow the detailed instructions in the docs/ folder (not yet implemented) for a step-by-step guide to deployment.

### Project Structure
This project follows a modular structure to keep components organized and maintainable.
```
ethereum/
├── .azure-pipelines/
│   ├── build.yml
│   └── deploy.yml
├── data-collector/
│   ├── collector.py
│   └── config.json
├── lakehouse/
│   ├── notebooks/
│   │   ├── transform_gas_data.ipynb
│   │   └── transform_erc20_data.ipynb
│   └── tables/
│       ├── raw/
│       ├── curated/
│       └── aggregated/
├── kql/
│   ├── functions/
│   │   ├── get_latest_price.kql
│   │   └── calculate_gas_average.kql
│   └── update_policies/
│       ├── eth_price_policy.kql
│       └── eth_gas_policy.kql
├── dashboard/
│   ├── real_time_queries.kql
│   └── batch_queries.kql
├── tests/
│   ├── unit/
│   │   └── test_collector.py
│   ├── integration/
│   │   └── test_ingestion.py
│   └── performance/
│       └── test_spark_job.py
├── deploy/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── scripts/
│       ├── setup_eventhouse.py
│       └── setup_lakehouse.py
├── monitor/
│   ├── quality_monitor.py
│   └── setup_alerts.py
├── .venv/                  # Virtual environment for the project
├── .github/                # Added for GitHub Actions (alternative to Azure Pipelines)
│   └── workflows/
│       └── ci-cd.yml
├── requirements.txt        # Base dependencies
├── requirements-dev.txt    # Development dependencies
├── requirements-prod.txt   # Production dependencies
├── pyproject.toml          # Project metadata and build configuration
├── setup.py                # For backward compatibility with older tools
└── README.md

```
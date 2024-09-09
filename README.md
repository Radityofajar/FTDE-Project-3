# Session 18 - Project 3: Batch Processing Using Airflow and Spark

## Overview

This project demonstrates how to integrate data from a data warehouse to a product via API. Specifically, it involves processing and analyzing data to determine:
- Top Country Based on User
- Total Film Based on Category

The tools used include Apache Airflow for workflow management and Apache Spark for data processing.

## Tools & Setup

### Prerequisites

- [Visual Studio Code](https://code.visualstudio.com/)
- [DBeaver](https://dbeaver.io/)
- [Postman](https://www.postman.com/)
- [Docker](https://www.docker.com/)

### Docker Setup

1. Pull the required Docker images:
    ```bash
    docker pull apache/airflow:2.10.0
    docker pull postgres:13
    ```

2. Clone the Airflow Docker repository:
    ```bash
    git clone https://github.com/MSinggihP/airflow-docker
    cd airflow-docker
    ```

3. Build the Airflow Docker image:
    ```bash
    docker build -t my-airflow .
    ```

4. Start the Docker containers:
    ```bash
    docker compose up -d
    ```

### Dataset

- [Pagila PostgreSQL Sample Database](https://www.kaggle.com/datasets/kapturovalexander/pagila-postgresql-sample-database)

## Project Flow

![Project Flow Diagram](https://prod-files-secure.s3.us-west-2.amazonaws.com/01b24fa3-f906-4bbc-ae9a-eae8c32be7d8/32c7269a-4849-4425-bf0d-a7c1fb667885/image.png)

## Step-by-Step Instructions

### 1. Check Database Connections

- **Postgres**
- **TiDB**: For secure connections, refer to the [TiDB documentation](https://docs.pingcap.com/tidbcloud/secure-connections-to-serverless-clusters).

### 2. Configure Airflow

1. **Create `requirements.txt`**:

    ```txt
    pyspark==3.5.2
    psycopg2-binary==2.9.9
    mysql-connector-python==9.0.0
    pandas
    ```

2. **Create `Dockerfile`**:

    ```dockerfile
    FROM apache/airflow:2.10.0
    COPY requirements.txt /
    RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
    ```

3. **Build the Docker image**:

    ```bash
    docker build -t my-airflow .
    ```

4. **Create `docker-compose.yaml`**:

    ```yaml
    version: '3.4'
    
    services:
      postgres:
        image: postgres:13
        container_name: postgres
        ports:
          - "5434:5432"
        healthcheck:
          test: ["CMD", "pg_isready", "-U", "airflow"]
          interval: 5s
          retries: 5
        env_file:
          - .env
        volumes:
          - postgres_airflow:/var/lib/postgresql/data
    
      scheduler:
        image: my-airflow
        user: "${AIRFLOW_UID}:0"
        env_file: 
          - .env
        volumes:
          - ./dags:/opt/airflow/dags
          - ./logs:/opt/airflow/logs
          - ./plugins:/opt/airflow/plugins
          - /var/run/docker.sock:/var/run/docker.sock
        depends_on:
          postgres:
            condition: service_healthy
          airflow-init:
            condition: service_completed_successfully
        container_name: airflow-scheduler
        command: scheduler
        restart: on-failure
        ports:
          - "8793:8793"
    
      webserver:
        image: my-airflow
        user: "${AIRFLOW_UID}:0"
        env_file: 
          - .env
        volumes:
          - ./dags:/opt/airflow/dags
          - ./logs:/opt/airflow/logs
          - ./plugins:/opt/airflow/plugins
          - /var/run/docker.sock:/var/run/docker.sock
        depends_on:
          postgres:
            condition: service_healthy
          airflow-init:
            condition: service_completed_successfully
        container_name: airflow-webserver
        restart: always
        command: webserver
        ports:
          - "8080:8080"
        healthcheck:
          test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
          interval: 30s
          timeout: 30s
          retries: 5
      
      airflow-init:
        image: my-airflow
        user: "${AIRFLOW_UID}:0"
        env_file: 
          - .env
        volumes:
          - ./dags:/opt/airflow/dags
          - ./logs:/opt/airflow/logs
          - ./plugins:/opt/airflow/plugins
          - /var/run/docker.sock:/var/run/docker.sock
        container_name: airflow-init
        entrypoint: /bin/bash
        command:
          - -c
          - |
            mkdir -p /sources/logs /sources/dags /sources/plugins
            chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
            exec /entrypoint airflow version
    volumes:
      postgres_airflow:
          external: true
    ```

5. **Set up connections in Airflow**:
    - Add connections for Postgres and TiDB.

### 3. Extract, Transform, and Load (ETL)

1. **Extract**:
    - Create a module to connect to Postgres.
    - Create a module to fetch data from Postgres.

2. **Transform**:
    - Write a script to transform data using Apache Spark.

3. **Load**:
    - Create a module to connect to Hadoop.
    - Load the transformed data into Hadoop.

## Notes

- **TiDB**: TiDB is an open-source NewSQL database that supports Hybrid Transactional and Analytical Processing workloads.


import os
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

import psycopg2
from sqlalchemy import create_engine
import pandas as pd

from datetime import datetime

import json
# Load config from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Extract details from JSON config
db_url = config["database"]["url"]
db_username = config["database"]["username"]
db_password = config["database"]["password"]

def fun_top_countries_get_data(**kwargs):
    spark = SparkSession.builder \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.0") \
        .master("local").appName("PySpark_Postgres").getOrCreate()
    
    df_country = spark.read.format("jdbc")\
        .option("url",db_url) \
        .option("driver", "org.postgresql.Driver") \
        .option("dbtable", "country") \
        .option("user", db_username) \
        .option("password", db_password) \
        .load()
    df_country.createOrReplaceTempView("country")

    df_city = spark.read.format("jdbc")\
        .option("url",db_url) \
        .option("driver", "org.postgresql.Driver") \
        .option("dbtable", "city") \
        .option("user", db_username) \
        .option("password", db_password) \
        .load()
    df_city.createOrReplaceTempView("city")

    df_result = spark.sql('''
        SELECT
            country,
            count(country) as total,
            current_date() as date
        from country as co
        inner join city as ci
            on ci.country_id = co.country_id
        group by 1
    ''')

    df_result.write.mode('append').partitionBy('date') \
        .option('compression','snappy') \
        .save('data_result_task_1')

def fun_top_countries_load_data(**kwargs):
    df = pd.read_parquet('data_result_task_1')
    engine = create_engine(
        'mysql+mysqlconnector://4FFFhK9fXu6JayE.root:9v07S0pKe4ZYCkjE@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test',
        echo=False)
    df.to_sql(name='top_country_prisqia_a',con=engine)

def fun_total_film_get_data(**kwargs):
    spark = SparkSession.builder \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.0") \
        .master("local").appName("PySpark_Postgres").getOrCreate()
    
    df_film = spark.read.format("jdbc")\
        .option("url",db_url) \
        .option("driver", "org.postgresql.Driver") \
        .option("dbtable", "film") \
        .option("user", db_username) \
        .option("password", db_password) \
        .load()
    df_film.createOrReplaceTempView("film")

    df_film_category = spark.read.format("jdbc")\
        .option("url",db_url) \
        .option("driver", "org.postgresql.Driver") \
        .option("dbtable", "film_category") \
        .option("user", db_username) \
        .option("password", db_password) \
        .load()
    df_film_category.createOrReplaceTempView("film_category")

    df_category = spark.read.format("jdbc")\
        .option("url",db_url) \
        .option("driver", "org.postgresql.Driver") \
        .option("dbtable", "category") \
        .option("user", db_username) \
        .option("password", db_password) \
        .load()
    df_category.createOrReplaceTempView("category")    

    df_result = spark.sql('''
        SELECT
            name,
            COUNT(name) as total,
            current_date() as date
        FROM (
            SELECT * FROM film AS f
            JOIN film_category as fc
            ON f.film_id = fc.film_id) AS j
        JOIN category AS c ON j.category_id = c.category_id
        GROUP BY name ORDER BY COUNT(name) DESC
    ''')

    df_result.write.mode('append').partitionBy('date') \
        .option('compression','snappy') \
        .save('data_result_task_2')

def fun_total_film_load_data(**kwargs):
    df = pd.read_parquet('data_result_task_2')
    engine = create_engine(
        'mysql+mysqlconnector://4FFFhK9fXu6JayE.root:9v07S0pKe4ZYCkjE@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test',
        echo=False)
    df.to_sql(name='total_film_category_prisqia_a',con=engine)


with DAG(
    dag_id='d_1_batch_processing_spark',
    start_date=datetime(2022, 5, 28),
    schedule_interval='00 23 * * *',
    catchup=False
) as dag:

    start_task = EmptyOperator(
        task_id='start'
    )

    op_top_countries_get_data = PythonOperator(
        task_id='top_countries_get_data',
        python_callable=fun_top_countries_get_data
    )

    op_top_countries_load_data = PythonOperator(
        task_id='top_countries_load_data',
        python_callable=fun_top_countries_load_data
    )

    op_total_film_get_data = PythonOperator(
        task_id='total_film_get_data',
        python_callable=fun_total_film_get_data
    )

    op_total_film_load_data = PythonOperator(
        task_id='total_film_load_data',
        python_callable=fun_total_film_load_data
    )

    end_task = EmptyOperator(
        task_id='end'
    )

    start_task >> op_top_countries_get_data >> op_top_countries_load_data >> end_task
    start_task >> op_total_film_get_data >> op_total_film_load_data >> end_task

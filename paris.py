from airflow import DAG
from datetime import timedelta, datetime
from airflow.operators.python import PythonOperator
import pandas as pd
import json
import os
import boto3
from botocore.exceptions import NoCredentialsError
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.task_group import TaskGroup


import requests
import pandas as pd

# 現在のファイルのディレクトリパスを取得
current_directory = os.path.dirname(__file__)
# 親ディレクトリへのパスを取得
parent_directory = os.path.dirname(current_directory)
# config.jsonのフルパスを構築
config_path = os.path.join(parent_directory, 'config.json')

#認証情報を別ファイルに保管
with open(config_path, 'r') as config_file:
    config = json.load(config_file)
    aws_key = config['aws_key']
    aws_secret= config['aws_secret']
    aws_token= config['aws_token']
    weathermap_api_key = config['weathermap_api_key']
    email = config['email_address']

default_args = {
    'owner':'airflow',
    'depends_on_past':False,
    'start_date':datetime(2024,8,3),
    'email':email,
    'email_on_failure':False,
    'email_on_retry':False,
    'retries':3,
    'retry_delay':timedelta(minutes=2)
}

def check_connection():
    response = requests.get('https://apis.codante.io/olympic-games/events')
    if response.status_code != 200:
        raise Exception('API接続失敗')
    
def extract_data():
    base_url = "https://apis.codante.io/olympic-games"
    events_url = f"{base_url}/events"
    params = {"discipline": "BKB"}

    response = requests.get(events_url, params=params)
    json_data = response.json()

    events_data = []
    for event in json_data['data']:
        for competitor in event['competitors']:
            events_data.append({
                'Event ID': event['id'],
                'Date': event['day'],
                'Discipline': event['discipline_name'],
                'Venue': event['venue_name'],
                'Event Name': event['event_name'],
                'Detailed Event Name': event['detailed_event_name'],
                'Start Date': event['start_date'],
                'End Date': event['end_date'],
                'Status': event['status'],
                'Is Medal Event': event['is_medal_event'],
                'Competitor Country': competitor['country_id'],
                'Competitor Name': competitor['competitor_name'],
                'Result (W/L)': competitor['result_winnerLoserTie'],
                'Score': competitor['result_mark']
            })

    df = pd.DataFrame(events_data)
    df.to_csv('/tmp/paris_olympic_basketball.csv', index=False)
    
def upload_to_s3(**kwargs):
    now = datetime.now()
    dt_string = 'paris_olympic_basketball_' + now.strftime("%d%m%Y%H%M%S") + '.csv'
    s3 = boto3.client('s3',
                        aws_access_key_id=aws_key,
                        aws_secret_access_key=aws_secret,
                        aws_session_token=aws_token)

    try:
        s3.upload_file('/tmp/paris_olympic_basketball.csv', 'wheatherapiairflowetl-yml', dt_string)
        print(f"成功: {dt_string}")
        # XComにファイル名をプッシュ
        kwargs['ti'].xcom_push(key='s3_file_name', value=dt_string)
    except FileNotFoundError:
        print("ファイルが見つかりません")
    except NoCredentialsError:
        print("S3認証失敗")

with DAG('paris_olympic_basketball',
        default_args=default_args,
        schedule_interval = '@daily',
        catchup=False) as dag:
    
    check_connection_to_api = PythonOperator(
        task_id='check_connection_to_api',
        python_callable=check_connection,
    )

    extract_basketball_result = PythonOperator(
        task_id='extract_basketball_result',
        python_callable=extract_data,
    )

    transform_s3 = PythonOperator(
        task_id='transform_s3',
        python_callable=upload_to_s3,
    )

    with TaskGroup(group_id = "transform_postgres",tooltip="extract_from_s3") as transform_postgres:
        create_table_1 = PostgresOperator(
                task_id = "tsk_create_table_1",
                postgres_conn_id = "postgres_conn",
                sql = '''
                create table if not exists basketball_events (
                    event_id INT,
                    event_date DATE,
                    discipline TEXT,
                    venue TEXT,
                    event_name TEXT,
                    detailed_event_name TEXT,
                    start_date TIMESTAMPTZ,
                    end_date TIMESTAMPTZ,
                    status TEXT,
                    is_medal_event BOOLEAN,
                    competitor_country TEXT,
                    competitor_name TEXT,
                    result TEXT,
                    score INT
                );
                '''
        )
        truncate_table = PostgresOperator(
                task_id = 'tsk_truncate_table',
                postgres_conn_id = "postgres_conn",
                sql = '''
                    TRUNCATE TABLE basketball_events;
                    '''
        )

        uploadS3_to_postgres = PostgresOperator(
                task_id = 'tsk_uploadS3_to_postgres',
                postgres_conn_id = "postgres_conn",
                sql="""
                    SELECT aws_s3.table_import_from_s3(
                        'basketball_events', 
                        '', 
                        '(format csv, DELIMITER '','', HEADER true)', 
                        'wheatherapiairflowetl-yml', 
                        '{{ task_instance.xcom_pull(task_ids="transform_s3", key="s3_file_name") }}', 
                        'ap-northeast-1'
                    );                
                """
                # xcomでファイル名を受け渡し
                )
        
        create_table_1 >> truncate_table >> uploadS3_to_postgres
    check_connection_to_api >> extract_basketball_result >> transform_s3 >> transform_postgres
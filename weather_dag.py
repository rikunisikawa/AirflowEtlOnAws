from airflow import DAG
from datetime import timedelta, datetime
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
import pandas as pd
import json
import os

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

def kelvin_to_faherenheit(temp_in_kelvin):
        temp_in_fahrenhit = (temp_in_kelvin - 273.15) * (9/5) * 32
        return temp_in_fahrenhit

def transform_load_data(task_instance):
        data = task_instance.xcom_pull(task_ids = "extract_weather_data")
        city = data["name"]
        weather_description = data["weather"][0]['description']
        temp_farenheit = kelvin_to_faherenheit(data["main"]["temp"])
        feels_like_farenheit = kelvin_to_faherenheit(data["main"]["feels_like"])
        min_temp_farenheit = kelvin_to_faherenheit(data["main"]["temp_min"])
        max_temp_farenheit = kelvin_to_faherenheit(data["main"]["temp_max"])
        pressure = data["main"]["pressure"]
        humidity = data["main"]["humidity"]
        wind_speed =data["wind"]["speed"]
        time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
        sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data['timezone'])
        sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data['timezone'])

        transformed_data = {"City":city,
                            "Description":weather_description,
                            "Temperature(F)":temp_farenheit,
                            "Feels Like(F)":feels_like_farenheit,
                            "Minimum Temp(F)":min_temp_farenheit,
                            "Maximum Temp(F)":max_temp_farenheit,
                            "Pressure":pressure,
                            "Humidity":humidity,
                            "Wind Speed":wind_speed,
                            "Time of Record":time_of_record,
                            "Sunrise (Local Time)":sunrise_time,
                            "Sunset (Local Time)":sunset_time,
                            }
        print(config)

        transformed_data_list = [transformed_data]
        df_data = pd.DataFrame(transformed_data_list)
        aws_credentials = {"key": aws_key,
        "secret": aws_secret,
        "token": aws_token}

        print(aws_credentials)

        now = datetime.now()
        dt_string = now.strftime("%d%m%Y%H%M%S")
        dt_string = 'current_weather_data_japan_' + dt_string
        print(dt_string)
        df_data.to_csv(f"s3://wheatherapiairflowetl-yml/{dt_string}.csv", index=False, storage_options=aws_credentials)

default_args = {
    'owner':'airflow',
    'depends_on_past':False,
    'start_date':datetime(2024,3,22),
    'email':email,
    'email_on_failure':False,
    'email_on_retry':False,
    'retries':2,
    'retry_delay':timedelta(minutes=2)
}

with DAG('weather_dag',
        default_args=default_args,
        schedule_interval = '@daily',
        catchup=False) as dag:

        is_weather_api_ready = HttpSensor(
        task_id = 'is_weather_api_ready',
        http_conn_id='weathermap_api',
        endpoint='/data/2.5/weather?q=Portland&appid={}'.format(weathermap_api_key)
    )
        
        extract_weather_data = SimpleHttpOperator(
        task_id = 'extract_weather_data',
        http_conn_id = 'weathermap_api',
        endpoint='/data/2.5/weather?q=Portland&appid={}'.format(weathermap_api_key),
        method='GET',
        response_filter = lambda r:json.loads(r.text),
        log_response=True
    )
        transform_load_weather_data = PythonOperator(
                task_id = 'transform_load_weather_data',
                python_callable=transform_load_data
        )

        is_weather_api_ready >> extract_weather_data >> transform_load_weather_data

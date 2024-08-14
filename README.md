# AirflowEtlOnAws
AirflowEtlOnAws


# postgresqlに接続するために必要
sudo pip install apache-airflow-providers-postgres

# postgresqlのApt設定
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

sudo apt update
sudo apt -y install postgresql

# S3とpostgresqlを接続する設定
EC2でpostgresに接続後
CREATE EXTENSION aws_s3 CASCADE;

# 構成図
![構成図](https://github.com/rikunisikawa/AirflowEtlOnAws/blob/main/diagram.png)

# 内容
AWS上でairflowを用いたETLパイプラインの作成

# postgresqlに接続するために必要
''' 
sudo pip install apache-airflow-providers-postgres
'''

# postgresqlのApt設定（ubuntuで使えるように）
https://www.postgresql.org/download/linux/ubuntu/　　
'''
sudo apt install -y postgresql-common　　
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh　　
sudo apt update　　
sudo apt -y install postgresql　　
'''
# S3とpostgresqlを接続する設定
https://docs.aws.amazon.com/ja_jp/AmazonRDS/latest/UserGuide/USER_PostgreSQL.S3Import.html　　
EC2でpostgresに接続後　　
''' 
CREATE EXTENSION aws_s3 CASCADE;
'''
# IAMポリシー作成
'''
aws iam create-policy \
   --policy-name postgress3Policy-yml-4 \
   --policy-document '{
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "s3import",
         "Action": [
           "s3:GetObject",
           "s3:ListBucket"
         ],
         "Effect": "Allow",
         "Resource": [
           "arn:aws:s3:::wheatherapiairflowetl-yml", 
           "arn:aws:s3:::wheatherapiairflowetl-yml/*"
         ] 
       }
     ] 
   }'    
'''

# IAMロールの作成
'''
aws iam create-role \
   --role-name postgres-S3-Role-yml \
   --assume-role-policy-document '{
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
            "Service": "rds.amazonaws.com"
          },
         "Action": "sts:AssumeRole"
         
       }
     ] 
   }'
ARN
role
weather-etl-weathermap-yml                

 aws iam attach-role-policy \
   --policy-arn arn:aws:iam::143944071087:policy/postgress3Policy-yml-4 \
   --role-name postgres-S3-Role-yml
'''
# CLI を使用して PostgreSQL DB インスタンスの IAM ロールを追加する
'''
aws rds add-role-to-db-instance \
   --db-instance-identifier postgres \
   --feature-name s3Import \
   --role-arn arn:aws:iam::143944071087:role/postgres-S3-Role-yml \
   --region ap-northeast-1
'''

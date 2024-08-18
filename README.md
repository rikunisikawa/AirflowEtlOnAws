# 構成図
![構成図](https://github.com/rikunisikawa/AirflowEtlOnAws/blob/main/diagram.png)
![AirflowDag](https://github.com/rikunisikawa/AirflowEtlOnAws/blob/main/dag.png)
# 内容
AWS上でairflowを用いたETLパイプラインの作成

# PostgreSQLに接続するための手順
## Airflowでpostgresqlに接続するために必要
```
sudo pip install apache-airflow-providers-postgres
```

## PostgreSQLのインストールと設定（Ubuntu）
https://www.postgresql.org/download/linux/ubuntu/　　
```
sudo apt install -y postgresql-common　　
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh　　
sudo apt update　　
sudo apt -y install postgresql　　
```
## S3とpostgresqlを接続する設定
https://docs.aws.amazon.com/ja_jp/AmazonRDS/latest/UserGuide/USER_PostgreSQL.S3Import.html　　
EC2でpostgresに接続後　　
```
CREATE EXTENSION aws_s3 CASCADE;
```
## IAMポリシー作成
```
aws iam create-policy \
   --policy-name <YOUR-POLICY-NAME> \
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
           "arn:aws:s3:::<YOUR-S3-BUCKET-NAME>", 
           "arn:aws:s3:::<YOUR-S3-BUCKET-NAME>/*"
         ] 
       }
     ] 
   }'
```

## IAMロールの作成
```
aws iam create-role \
   --role-name <YOUR-ROLE-NAME> \
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

aws iam attach-role-policy \
   --policy-arn arn:aws:iam::<YOUR-AWS-ACCOUNT-ID>:policy/<YOUR-POLICY-NAME> \
   --role-name <YOUR-ROLE-NAME>
```
## PostgreSQL DB インスタンスへのIAMロールの追加
```
aws rds add-role-to-db-instance \
   --db-instance-identifier <YOUR-DB-INSTANCE-ID> \
   --feature-name s3Import \
   --role-arn arn:aws:iam::<YOUR-AWS-ACCOUNT-ID>:role/<YOUR-ROLE-NAME> \
   --region <YOUR-REGION>
```

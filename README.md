# 内容
パリオリンピック バスケットボール ETLパイプライン  
AWS上でairflowを用いたETLパイプラインの作成  

# 構成図
## AWS
![構成図](https://github.com/rikunisikawa/AirflowEtlOnAws/blob/main/diagram.png)
## Airflow ETL
![AirflowDag](https://github.com/rikunisikawa/AirflowEtlOnAws/blob/main/dag.png)

# ETLパイプライン概要
タスクID: check_connection_to_api  
- API（https://apis.codante.io/olympic-games/events）への接続を確認

タスクID: extract_basketball_result
- オリンピックのAPIからバスケットボールイベントのデータを抽出
- CSVファイルとして保存します。
- S3へのアップロード

タスクID: transform_s3  
- 生成されたCSVファイルをS3バケットにアップロード  
- S3ファイル名はXComを介して次の処理で使用する  
PostgreSQLへの変換とロード  

タスクグループID: transform_postgres  
テーブルの作成:  
- タスクID: tsk_create_table_1  
- テーブルが存在しない場合は作成  
テーブルのクリア:  
- タスクID: tsk_truncate_table
- 新しいデータをロードする準備のため、既存のテーブルをクリア（トランケート）
S3からPostgreSQLへのデータロード:
- タスクID: tsk_uploadS3_to_postgres
- S3に保存されたCSVファイルからPostgreSQLテーブルにデータをロード
- aws_s3.table_import_from_s3関数を使用してデータをインポート

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

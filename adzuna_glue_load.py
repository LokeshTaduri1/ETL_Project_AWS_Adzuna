import boto3
import json
from datetime import datetime
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql import Row
from pyspark.sql.functions import to_timestamp, col
import psycopg2

# === CONFIGURATION ===
raw_bucket = "YOUR-RAW_BUCKET"
raw_key = "RAW-KEY"
destination_bucket = "DESTINATION=BUCKET"
secret_name = "redshift/adzuna"
region_name = "us-east-1"
redshift_iam_role = "arn:aws:iam::<your-account-id>:role/<RedshiftRoleWithS3Access>"
table_name = "adzuna_jobs"

# === STEP 1: Initialize Spark and Glue ===
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# === STEP 2: Load credentials from Secrets Manager ===
secrets_client = boto3.client('secretsmanager', region_name=region_name)
secret = json.loads(secrets_client.get_secret_value(SecretId=secret_name)['SecretString'])
redshift_host = secret['host']
redshift_port = secret['port']
redshift_db = secret['dbname']
redshift_user = secret['username']
redshift_password = secret['password']

# === STEP 3: Get the max job_created from Redshift ===
conn = psycopg2.connect(
    dbname=redshift_db,
    user=redshift_user,
    password=redshift_password,
    host=redshift_host,
    port=redshift_port
)
cursor = conn.cursor()

cursor.execute(f"SELECT MAX(job_created) FROM {table_name};")
max_created_result = cursor.fetchone()
max_created = max_created_result[0] if max_created_result[0] else datetime.min
print(f"Latest job_created in Redshift: {max_created}")
cursor.close()
conn.close()

# === STEP 4: Load raw JSON from S3 ===
s3 = boto3.client('s3')
response = s3.get_object(Bucket=raw_bucket, Key=raw_key)
raw_json = json.loads(response['Body'].read())

# === STEP 5: Parse and filter new records only ===
def parse_job(job):
    return Row(
        job_id=job.get('id'),
        job_title=job.get('title'),
        job_location=job.get('location', {}).get('display_name'),
        job_company=job.get('company', {}).get('display_name'),
        job_category=job.get('category', {}).get('label'),
        job_description=job.get('description'),
        job_url=job.get('redirect_url'),
        job_created=job.get('created')
    )

parsed_rows = [parse_job(job) for job in raw_json]
df = spark.createDataFrame(parsed_rows)
df = df.withColumn("job_created", to_timestamp("job_created"))

# === STEP 6: Filter out old data (incremental logic) ===
filtered_df = df.filter(col("job_created") > to_timestamp(lit(max_created.isoformat())))
new_count = filtered_df.count()
print(f"New jobs to load: {new_count}")

if new_count > 0:
    # === STEP 7: Write new records to S3 as CSV ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_prefix = f"adzuna_incremental/{timestamp}/"
    output_path = f"s3://{destination_bucket}/{output_prefix}"
    filtered_df.coalesce(1).write.option("header", True).option("quoteAll", True).mode("overwrite").csv(output_path)

    # === STEP 8: Load into Redshift (Append only, no UPSERT) ===
    conn = psycopg2.connect(
        dbname=redshift_db,
        user=redshift_user,
        password=redshift_password,
        host=redshift_host,
        port=redshift_port
    )
    cursor = conn.cursor()

    # Ensure target table exists
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        job_id VARCHAR PRIMARY KEY,
        job_title VARCHAR,
        job_location VARCHAR,
        job_company VARCHAR,
        job_category VARCHAR,
        job_description VARCHAR(MAX),
        job_url VARCHAR,
        job_created TIMESTAMP
    );
    """)

    # Append-only COPY command
    copy_sql = f"""
    COPY {table_name}
    FROM 's3://{destination_bucket}/{output_prefix}'
    IAM_ROLE '{redshift_iam_role}'
    FORMAT AS CSV
    IGNOREHEADER 1
    TIMEFORMAT 'auto'
    REMOVEQUOTES;
    """
    cursor.execute(copy_sql)
    conn.commit()
    cursor.close()
    conn.close()

    print(f"{new_count} new records loaded to Redshift.")

else:
    print("No new data to load. Skipping Redshift COPY.")

# === STEP 9: Optional Cleanup ===
s3.delete_object(Bucket=raw_bucket, Key=raw_key)

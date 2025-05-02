import boto3
import json
from datetime import datetime
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql import Row
from pyspark.sql.functions import to_timestamp

# Initialize Spark and Glue contexts
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Initialize S3 client
s3 = boto3.client('s3')

# === CONFIGURATION ===
raw_bucket = "test-bucket-lokesh12"
raw_key = "adzuna_raw_data_20250429_214724.json"  # <- Your JSON file inside the root of the bucket
destination_bucket = "destination-jsontocsv"

# Step 1: Load raw JSON from S3
response = s3.get_object(Bucket=raw_bucket, Key=raw_key)
raw_json = json.loads(response['Body'].read())

# Step 2: Parse raw JSON into structured rows
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

# Step 3: Write transformed data to destination bucket as CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_key = f"adzuna_transformed_data_{timestamp}.csv"
output_path = f"s3://{destination_bucket}/{output_key}"

df.coalesce(1).write.option("header", True).option("quoteAll", True).mode("overwrite").csv(output_path)


# Step 4: Delete the original raw file (optional cleanup)
s3.delete_object(Bucket=raw_bucket, Key=raw_key)

print(f"Transformed CSV written to: {output_path}")

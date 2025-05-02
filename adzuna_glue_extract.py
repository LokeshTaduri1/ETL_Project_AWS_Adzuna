import json
import requests
import math
from datetime import datetime
import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# === Adzuna API Credentials ===
# You can pass these via Glue job parameters for security and flexibility
ADZUNA_APP_ID = "ADZUNA_APP_ID"     # <-- Replace with your actual App ID
ADZUNA_APP_KEY = "ADZUNA_APP_KEY"   # <-- Replace with your actual App Key

# S3 destination
BUCKET = "adzuna-extract-data"

# API configuration
url = "https://api.adzuna.com/v1/api/jobs/ca/search/"
base_params = {
    'app_id': ADZUNA_APP_ID,
    'app_key': ADZUNA_APP_KEY,
    'results_per_page': 50,
    'what_phrase': "data engineer",
    'max_days_old': 2,
    'sort_by': "date"
}

def main():
    all_job_postings = []

    logger.info("Requesting first page to calculate total number of pages")
    response = requests.get(f"{url}1", params=base_params)

    if response.status_code == 200:
        data = response.json()
        total_results = data.get('count', 0)
        total_pages = math.ceil(total_results / base_params['results_per_page'])
        logger.info(f"Total pages to retrieve: {total_pages}")
        all_job_postings.extend(data.get('results', []))

        for page in range(2, total_pages + 1):
            logger.info(f"Fetching page {page}")
            response = requests.get(f"{url}{page}", params=base_params)
            if response.status_code == 200:
                page_data = response.json()
                all_job_postings.extend(page_data.get('results', []))
            else:
                logger.warning(f"Failed to fetch page {page}: {response.status_code}, {response.text}")
    else:
        logger.error(f"Initial request failed: {response.status_code}, {response.text}")
        return

    logger.info(f"Total job postings retrieved: {len(all_job_postings)}")

    if not all_job_postings:
        logger.warning("No job postings found. Skipping S3 upload.")
        return

    # Generate output file name
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"adzuna_raw_data_{current_timestamp}.json"
    file_key = f"raw_data/{file_name}"

    # Upload to S3
    logger.info(f"Uploading results to s3://{BUCKET}/{file_key}")
    s3 = boto3.client('s3')

    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=file_key,
            Body=json.dumps(all_job_postings)
        )
        logger.info(f"Successfully uploaded file to {BUCKET}/{file_key}")
    except Exception as e:
        logger.error(f"Failed to upload to S3: {str(e)}")

if __name__ == "__main__":
    main()

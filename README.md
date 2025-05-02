# From API to Dashboard: Building a Complete ETL Pipeline on AWS


This project explains how to build a complete end-to-end data pipeline using **AWS services**. It starts with collecting real-time job listings for Data Engineering roles in Canada using the **Adzuna API**, then processes the data using **AWS Glue**, stores it in **Amazon S3**, loads it into **Amazon Redshift Serverless**, and finally presents it in a clean and interactive dashboard built with **Looker Studio**.

While this project focuses on jobs in Canada, the same setup can be used to collect job listings from any other country — you just need to change the country code while calling the Adzuna API. This makes the pipeline flexible and reusable for different regions or job roles.


The main goal of this pipeline is to show how we can automate data collection, transformation, and reporting — all without managing servers. This kind of setup is very useful for building data workflows that run on a schedule, can handle changes in data automatically, and help businesses make decisions by showing useful insights in dashboards.

I have also used **AWS Step Functions** to manage and control the flow of each step in the pipeline and **Amazon EventBridge** to schedule when the pipeline should run (like daily or weekly). This makes the whole process automatic and serverless..

![Project Workflow](workflows/project_workflow.png)

## 🧭 Project Flow

This project follows these main steps:

### Step 1: Extract Data  
- I'have used **AWS Glue (Python Shell Job)** to collect job listing data from the Adzuna API.
- The raw data is saved in **Amazon S3**.

### Step 2: Transform Data  
- The raw data is cleaned and formatted using **AWS Glue PySpark Job**.
- The transformed data is stored again in S3.

### Step 3: Load Data  
- The final data is loaded from S3 into **Amazon Redshift Serverless**.
- A Redshift schema is defined using SQL scripts.

### Step 4: Visualize Data  
- The Redshift database is connected to **Looker Studio** (Google’s BI tool).
- Dashboards are created to show job trends, salaries, and top hiring cities for Data Engineers in Canada.

---

## ⚙️ Services Used

- **AWS Glue** (Python Shell + Spark Jobs)
- **Amazon S3** (To store raw, stagging and processed data)
- **Amazon Redshift Serverless**(Data Warehouse)
- **AWS Step Functions** (to orchestrate the ETL flow)
- **Amazon EventBridge** (to schedule jobs)
- **IAM (Identity Access Management to manage roles,permissions, security policies)
- **Looker Studio** (for reporting and dashboards)
- **Python**
- **Adzuna Job Search API** (to get the data)

---

## 🖼️ Visual Walkthrough

Below are some visuals to understand the process better:

- **Step Function Workflow**  
  <img src="workflows/step_functions_workflow.png" width="60%">

- **Execution Success Example**  
  <img src="workflows/step_functions_success.png" width="60%">

- **Data Loaded in Redshift**  
  <img src="workflows/redshift.png" width="60%">

- **Final Looker Studio Dashboard**  
  <img src="workflows/looker_job_dashboard.png" width="60%">

---

## 🚀 How to Run This Project

### 1. Clone This Repository

```bash
git clone https://github.com/your-username/aws-etl-project.git
cd aws-etl-project

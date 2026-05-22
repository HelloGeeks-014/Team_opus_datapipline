Welcome to the **Sigma QuickMart Data Pipeline**! Follow these steps to get the full pipeline running on your own AWS account.

---

#### Step 1 — Prerequisites
Make sure you have the following before you begin:
- **Python 3.9+** installed locally
- **An AWS account** with Admin or PowerUser-level access
- **AWS CLI** configured (`aws configure`) — *or* enter credentials in the sidebar
- The following Python packages installed:
  ```
  pip install streamlit boto3 pandas
  ```

---

#### Step 2 — Clone the Repository
```bash
git clone https://github.com/<your-username>/sigma-opus-pipeline.git
cd sigma-opus-pipeline
```

---

#### Step 3 — Upload Your Data Folder
Place your own data files inside the `data/` folder of the cloned repository:
```
sigma-opus-pipeline/
└── data/
    ├── customers.csv
    ├── products.csv
    ├── orders_day1.csv
    ├── orders_day2.csv
    ├── orders_day3.csv
    ├── orders_day4.csv
    └── orders_day5.csv
```
> **💡 Tip:** Your CSV files must match the expected column structure. Refer to the table schemas in the **🔍 Ask Your Data** tab for the required fields.

---

#### Step 4 — Configure AWS Credentials
Use **one** of these methods:

| Method | How |
|---|---|
| **Sidebar (recommended for quick testing)** | Enter your *Access Key ID* & *Secret Access Key* in the **🔑 AWS Credentials** section on the left sidebar. |
| **AWS CLI profile** | Run `aws configure` and set your default region to `us-east-1`. |
| **Environment variables** | Export `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your terminal. |

---

#### Step 5 — Launch the Dashboard
```bash
streamlit run app.py
```
The app will open at **http://localhost:8501**. Configure settings in the sidebar as needed.

---

#### Step 6 — Deploy the Pipeline (this tab!)
1. Set your desired **S3 Bucket Name** in the sidebar (must be globally unique).
2. Verify the **Glue Job Name**, **IAM Role**, and **Athena Database** values.
3. Click **🚀 Deploy Pipeline** below.

This will automatically:
- Create the S3 bucket
- Upload the Glue ETL script
- Upload reference datasets (customers, products)
- Provision the AWS Glue Python Shell job
- Create the Athena database and register all tables

---

#### Step 7 — Run Daily ETL Loads
Switch to the **📦 Daily Load** tab and select a day to ingest:
1. Choose a partition day (Day 1 → Day 5).
2. Click **▶️ Run ETL** — this uploads raw CSV to S3, triggers the Glue job, and shows progress.
3. After completion, an AI-powered quality assessment is generated automatically.

---

#### Step 8 — Query Your Data
Go to the **🔍 Ask Your Data** tab:
- Pick a quick question or type your own in natural language.
- The AI assistant converts your question into SQL, runs it on Athena, and returns results.

---

#### Step 9 — Monitor Pipeline Health
The **📊 Pipeline Health** tab shows:
- Total rows, revenue, and average order value across all loaded partitions.
- An AI-generated executive health summary.

---

> **💡 Tip:** All AWS resource names can be customized from the sidebar. If you hit a *403 Forbidden* error on S3, your bucket name is already taken — just append a unique suffix.
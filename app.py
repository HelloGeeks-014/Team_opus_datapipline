import time
import json
import io
import re
import boto3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Sigma QuickMart Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply premium dark dashboard aesthetic via a single CSS injection block
st.markdown("""
<style>
:root {
    --accent:         #E63946;   /* QuickMart red — primary CTA, active states    */
    --accent-hover:   #FF6B7A;   /* lighter red — hover glow                      */
    --accent-muted:   rgba(230, 57, 70, 0.12);  /* soft tint for cards/backgrounds */
    --accent-border:  rgba(230, 57, 70, 0.35);  /* subtle accent borders           */
    --surface:        #1a1a2e;   /* card / panel background                        */
    --surface-raise:  #16213e;   /* slightly elevated surface                      */
    --page-bg:        #0f0f1a;   /* overall page background                        */
    --text-primary:   #f0f0f0;
    --text-secondary: #a0a0b0;
    --text-muted:     #606070;
    --success:        #2dc653;
    --warning:        #f4a261;
    --danger:         #e63946;
    --border:         rgba(255, 255, 255, 0.07);
}

/* Page background */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: var(--page-bg) !important;
}
[data-testid="stHeader"] {
    background-color: var(--page-bg) !important;
    border-bottom: 1px solid var(--border);
}
[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
}

/* Typography — minimum 16px everywhere */
html, body, [class*="css"] {
    font-size: 16px !important;
    color: var(--text-primary) !important;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}
h1 { font-size: 2.2rem !important; font-weight: 700 !important;
     color: var(--accent) !important; letter-spacing: -0.5px; margin-bottom: 1.5rem !important; }
h2 { font-size: 1.6rem !important; font-weight: 600 !important;
     color: var(--text-primary) !important; margin-top: 1rem !important; }
h3 { font-size: 1.25rem !important; font-weight: 600 !important;
     color: var(--accent-hover) !important; }

/* Tabs — glowing active indicator */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: var(--accent-muted) !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    box-shadow: 0 0 16px var(--accent-muted) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--accent-hover) !important;
    background: var(--accent-muted) !important;
}

/* Buttons — solid accent with hover glow */
.stButton > button {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: var(--accent-hover) !important;
    box-shadow: 0 4px 20px rgba(230, 57, 70, 0.4) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* Metric Cards — glowing accent labels */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--accent-border) !important;
    border-radius: 12px !important;
    padding: 18px 20px !important;
}
[data-testid="stMetricLabel"] {
    color: var(--accent) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 13px !important;
}

/* Dataframes & Tables */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] th {
    background: var(--surface-raise) !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
[data-testid="stDataFrame"] td {
    color: var(--text-primary) !important;
    font-size: 14px !important;
}
[data-testid="stDataFrame"] tr:hover td {
    background: var(--accent-muted) !important;
}

/* Progress Bar — accent colored */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent-hover)) !important;
    border-radius: 4px !important;
}
[data-testid="stProgressBar"] {
    background: var(--surface) !important;
    border-radius: 4px !important;
}

/* Selectbox & Text Input */
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-size: 15px !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stTextInput"] > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-muted) !important;
}

/* Alert / Notification Banners */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left: 4px solid !important;
    font-size: 15px !important;
}
.stSuccess  { border-left-color: var(--success) !important; background: rgba(45,198,83,0.08) !important; }
.stWarning  { border-left-color: var(--warning) !important; background: rgba(244,162,97,0.08) !important; }
.stError    { border-left-color: var(--danger)  !important; background: rgba(230,57,70,0.08)  !important; }
.stInfo     { border-left-color: #38beff        !important; background: rgba(56,190,255,0.08) !important; }

/* Code Blocks */
[data-testid="stCode"] {
    background: var(--surface-raise) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-size: 13px !important;
}

/* Charts — override default Streamlit chart container */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
    background: var(--surface) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    border: 1px solid var(--border) !important;
}

/* Dividers */
hr {
    border-color: var(--border) !important;
    margin: 1.5rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# Sidebar — AWS Configuration Panel
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:8px 0 4px;">
        <span style="font-size:1.5rem;font-weight:700;color:#E63946;">⚙️ AWS Configuration</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # — Credentials —
    st.markdown("##### 🔑 AWS Credentials")
    AWS_ACCESS_KEY = st.text_input(
        "Access Key ID",
        value="",
        type="password",
        help="Your AWS IAM Access Key ID. Leave blank to use environment / instance-profile credentials.",
    )
    AWS_SECRET_KEY = st.text_input(
        "Secret Access Key",
        value="",
        type="password",
        help="Your AWS IAM Secret Access Key. Leave blank to use environment / instance-profile credentials.",
    )

    st.markdown("---")

    # — Region —
    st.markdown("##### 🌍 Region")
    REGION = st.selectbox(
        "AWS Region",
        options=[
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-south-1", "ap-southeast-1", "ap-northeast-1",
        ],
        index=0,
        help="The AWS region where all resources will be provisioned.",
    )

    st.markdown("---")

    # — S3 —
    st.markdown("##### 🪣 Amazon S3")
    BUCKET_NAME = st.text_input(
        "S3 Bucket Name",
        value="sigma-opus-bucket",
        help="S3 bucket names must be globally unique. If the default is taken, append a unique suffix (e.g. '-yourname').",
    )

    st.markdown("---")

    # — AWS Glue —
    st.markdown("##### 🔧 AWS Glue")
    GLUE_JOB = st.text_input(
        "Glue Job Name",
        value="sigma-opus-etl",
        help="Name of the Glue Python Shell ETL job.",
    )
    GLUE_ROLE = st.text_input(
        "Glue IAM Role",
        value="SigmaGlueServiceRole",
        help="IAM role ARN or name that Glue assumes for execution.",
    )

    st.markdown("---")

    # — Athena —
    st.markdown("##### 🔎 Amazon Athena")
    ATHENA_DB = st.text_input(
        "Athena Database",
        value="sigma_opus_db",
        help="Athena/Glue Catalog database that stores the table definitions.",
    )

    st.markdown("---")

    # — Bedrock —
    st.markdown("##### 🤖 Amazon Bedrock")
    BEDROCK_MODEL = st.selectbox(
        "Bedrock Model",
        options=[
            "us.amazon.nova-lite-v1:0",
            "us.amazon.nova-pro-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
        ],
        index=0,
        help="Foundation model used for AI-powered analytics and query generation.",
    )

    st.markdown("---")

    # — Connection status indicator —
    st.markdown("##### 🔗 Connection Status")

    st.markdown("---")

    # — Cost Analysis —
    st.markdown("##### 💰 Estimated AWS Costs")

    # Initialize session-state usage counters
    if "usage_glue_runs" not in st.session_state:
        st.session_state.usage_glue_runs = 0
    if "usage_athena_queries" not in st.session_state:
        st.session_state.usage_athena_queries = 0
    if "usage_athena_data_mb" not in st.session_state:
        st.session_state.usage_athena_data_mb = 0.0
    if "usage_bedrock_calls" not in st.session_state:
        st.session_state.usage_bedrock_calls = 0
    if "usage_s3_puts" not in st.session_state:
        st.session_state.usage_s3_puts = 0

    # ── Per-service cost rates (US-East-1 pricing) ──
    # Glue Python Shell: $0.44/DPU-hour, 0.0625 DPU, avg ~2 min run
    GLUE_COST_PER_RUN = 0.44 * 0.0625 * (2 / 60)  # ~$0.0009/run
    # Athena: $5.00 per TB scanned, min 10 MB per query
    ATHENA_COST_PER_MB = 5.00 / (1024 * 1024)       # per MB
    ATHENA_MIN_MB = 10.0
    # Bedrock Nova Lite: ~$0.00006 per 1K input tokens, assume avg 500 tokens
    BEDROCK_COST_PER_CALL = 0.00006 * 0.5            # ~$0.00003/call
    # S3: $0.005 per 1,000 PUT requests
    S3_COST_PER_PUT = 0.005 / 1000                    # $0.000005/put

    # Calculate costs
    glue_cost = st.session_state.usage_glue_runs * GLUE_COST_PER_RUN
    athena_data = max(st.session_state.usage_athena_data_mb, st.session_state.usage_athena_queries * ATHENA_MIN_MB)
    athena_cost = athena_data * ATHENA_COST_PER_MB
    bedrock_cost = st.session_state.usage_bedrock_calls * BEDROCK_COST_PER_CALL
    s3_cost = st.session_state.usage_s3_puts * S3_COST_PER_PUT
    total_cost = glue_cost + athena_cost + bedrock_cost + s3_cost

    # Display cost breakdown
    st.markdown(f"""
    <div style="background:#16213e;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:14px 16px;font-size:13px;line-height:1.8;">
        <div style="display:flex;justify-content:space-between;">
            <span>🔧 Glue Jobs ({st.session_state.usage_glue_runs} runs)</span>
            <span style="color:#2dc653;">${glue_cost:.4f}</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span>🔎 Athena ({st.session_state.usage_athena_queries} queries)</span>
            <span style="color:#2dc653;">${athena_cost:.4f}</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span>🤖 Bedrock ({st.session_state.usage_bedrock_calls} calls)</span>
            <span style="color:#2dc653;">${bedrock_cost:.6f}</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span>🪣 S3 PUTs ({st.session_state.usage_s3_puts} ops)</span>
            <span style="color:#2dc653;">${s3_cost:.6f}</span>
        </div>
        <hr style="border-color:rgba(255,255,255,0.1);margin:8px 0;">
        <div style="display:flex;justify-content:space-between;font-weight:700;font-size:15px;">
            <span>Total (this session)</span>
            <span style="color:#E63946;">${total_cost:.4f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("💡 Estimates based on us-east-1 on-demand pricing. Actual charges may vary.")

# AWS Client Initializations
try:
    _session_kwargs = {"region_name": REGION}
    if AWS_ACCESS_KEY and AWS_SECRET_KEY:
        _session_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY
        _session_kwargs["aws_secret_access_key"] = AWS_SECRET_KEY
    s3 = boto3.client("s3", **_session_kwargs)
    glue = boto3.client("glue", **_session_kwargs)
    athena = boto3.client("athena", **_session_kwargs)
    bedrock = boto3.client("bedrock-runtime", **_session_kwargs)
except Exception as e:
    st.error(f"Error initializing AWS Boto3 Clients: {str(e)}")

# Bedrock converse() Helper
def ask_bedrock(prompt):
    try:
        response = bedrock.converse(
            modelId=BEDROCK_MODEL,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 500, "temperature": 0.0}
        )
        return response["output"]["message"]["content"][0]["text"].strip()
    except Exception as e:
        return f"Bedrock error: {str(e)}"

# Athena Helper — uses start_query_execution and polls
def run_athena_query(query, database="default"):
    try:
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": database},
            ResultConfiguration={"OutputLocation": f"s3://{BUCKET_NAME}/athena-results/"}
        )
        query_execution_id = response["QueryExecutionId"]
        
        while True:
            status_response = athena.get_query_execution(QueryExecutionId=query_execution_id)
            state = status_response["QueryExecution"]["Status"]["State"]
            
            if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                if state == "FAILED":
                    reason = status_response["QueryExecution"]["Status"].get("StateChangeReason", "Unknown Athena error")
                    raise Exception(f"Athena query execution failed: {reason}")
                elif state == "CANCELLED":
                    raise Exception("Athena query was cancelled.")
                break
            time.sleep(2)
            
        results = athena.get_query_results(QueryExecutionId=query_execution_id)
        # Safely extract columns; some DDL/metadata queries return no columns
        column_info = results.get("ResultSet", {}).get("ResultSetMetadata", {}).get("ColumnInfo", [])
        cols = [c["Label"] for c in column_info] if column_info else []
        all_rows = results.get("ResultSet", {}).get("Rows", []) or []

        # Skip header row if it matches column names
        if cols and all_rows:
            header_vals = [f.get("VarCharValue", "") for f in all_rows[0].get("Data", [])]
            if header_vals == cols:
                all_rows = all_rows[1:]

        # Parse rows into a DataFrame safely
        data = [[field.get("VarCharValue", "") for field in row.get("Data", [])] for row in all_rows]
        return pd.DataFrame(data, columns=cols) if cols else pd.DataFrame()
    except Exception as e:
        raise Exception(f"Athena Helper failed: {str(e)}")

# DDL definitions for Tab 1 Setup
ORDERS_DDL = f"""
CREATE EXTERNAL TABLE IF NOT EXISTS {ATHENA_DB}.sigma_opus_orders (
    order_id STRING,
    customer_id STRING,
    product_id STRING,
    quantity INT,
    amount DOUBLE,
    status STRING,
    payment_method STRING,
    city STRING,
    created_at STRING,
    processed_at STRING,
    is_high_value STRING
)
PARTITIONED BY (date STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://{BUCKET_NAME}/processed/orders/'
TBLPROPERTIES ('skip.header.line.count'='1')
"""

CUSTOMERS_DDL = f"""
CREATE EXTERNAL TABLE {ATHENA_DB}.sigma_opus_customers (
    customer_id STRING,
    name STRING,
    email STRING,
    phone STRING,
    city STRING,
    tier STRING,
    signup_date STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://{BUCKET_NAME}/processed/customers/'
TBLPROPERTIES ('skip.header.line.count'='1')
"""

PRODUCTS_DDL = f"""
CREATE EXTERNAL TABLE {ATHENA_DB}.sigma_opus_products (
    product_id STRING,
    name STRING,
    category STRING,
    price DOUBLE,
    stock_quantity INT,
    is_active STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://{BUCKET_NAME}/processed/products/'
TBLPROPERTIES ('skip.header.line.count'='1')
"""

# App Layout
st.markdown("<h1>🛍️ QuickMart AI Data Pipeline Portal</h1>", unsafe_allow_html=True)

# Sidebar info
with st.sidebar:
    st.markdown("### 📊 Pipeline Architecture")
    st.info("AI-powered orchestration dashboard connected to S3 Lakehouse, AWS Glue jobs, Amazon Athena, and Bedrock.")
    st.markdown("---")
    st.markdown("**Infrastructure Parameters:**")
    st.markdown(f"- S3 Bucket: `{BUCKET_NAME}`")
    st.markdown(f"- Glue Job: `{GLUE_JOB}`")
    st.markdown(f"- Database: `{ATHENA_DB}`")
    st.markdown(f"- Bedrock Model: `us.amazon.nova-lite-v1:0`")

# Render 4 Tabs
tab_setup, tab_load, tab_ask, tab_health, tab_about = st.tabs([
    "🔧 Setup Pipeline",
    "📦 Daily Load",
    "🔍 Ask Your Data",
    "📊 Pipeline Health",
    "ℹ️ About QuickMart"
])

# ==================== TAB 1: Setup Pipeline ====================
with tab_setup:
    st.markdown("### 🔧 AWS Configuration Guide")

    st.markdown("""
    Fill in the following fields in the **⚙️ AWS Configuration** sidebar before deploying:

    | Field | Example Value |
    |---|---|
    | **Access Key ID** | `AKIAIOSFODNN7EXAMPLE` |
    | **Secret Access Key** | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
    | **AWS Region** | `us-east-1` |
    | **S3 Bucket Name** | `sigma-opus-bucket-yourname` |
    | **Glue Job Name** | `sigma-opus-etl` |
    | **Glue IAM Role** | `SigmaGlueServiceRole` |
    | **Athena Database** | `sigma_opus_db` |
    | **Bedrock Model** | `us.amazon.nova-lite-v1:0` |
    """)

    st.markdown("---")
    st.write("When you're ready, hit the button below to provision all AWS resources in one click.")
    
    if st.button("🚀 Deploy Pipeline"):
        status_cols = [st.empty() for _ in range(8)]
        for i, step in enumerate([
            "1. S3 bucket creation",
            "2. Upload Glue script",
            "3. Upload reference datasets (customers, products)",
            "4. Provision/Recreate AWS Glue Python Shell job",
            "5. Athena database schema creation",
            "6. Register Athena orders partition table",
            "7. Drop and register customers table",
            "8. Drop and register products table"
        ]):
            status_cols[i].markdown(f"⏳ **{step}...**")
            
        try:
            # 1. Create S3 Bucket
            try:
                s3.head_bucket(Bucket=BUCKET_NAME)
            except s3.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['404', 'NoSuchBucket']:
                    s3.create_bucket(Bucket=BUCKET_NAME)
                elif error_code == '403':
                    raise Exception(
                        f"Access Denied (403) to S3 bucket '{BUCKET_NAME}'. "
                        "S3 bucket names must be globally unique across all AWS accounts. "
                        "This name is likely owned by another AWS customer. "
                        "Please change the S3 Bucket Name in the sidebar (e.g., append a unique suffix like '-yourname') and deploy again."
                    )
                else:
                    raise
            status_cols[0].success(f"✅ 1. S3 Bucket ready ('{BUCKET_NAME}')")
            
            # 2. Upload Glue Script
            with open("glue_scripts/etl.py", "rb") as f:
                s3.put_object(Bucket=BUCKET_NAME, Key="glue-scripts/etl.py", Body=f.read())
            status_cols[1].success("✅ 2. Glue Python Shell script uploaded to S3")
            
            # 3. Upload Customers & Products
            with open("data/customers.csv", "rb") as f:
                cust_bytes = f.read()
                s3.put_object(Bucket=BUCKET_NAME, Key="raw/customers.csv", Body=cust_bytes)
                s3.put_object(Bucket=BUCKET_NAME, Key="processed/customers/customers.csv", Body=cust_bytes)
                
            with open("data/products.csv", "rb") as f:
                prod_bytes = f.read()
                s3.put_object(Bucket=BUCKET_NAME, Key="raw/products.csv", Body=prod_bytes)
                s3.put_object(Bucket=BUCKET_NAME, Key="processed/products/products.csv", Body=prod_bytes)
            status_cols[2].success("✅ 3. Customer & Product datasets registered in raw and processed zones")
            
            # 4. Create/Recreate Glue Job (GlueVersion 1.0)
            existing_jobs = glue.list_jobs()["JobNames"]
            if GLUE_JOB in existing_jobs:
                glue.delete_job(JobName=GLUE_JOB)
                
            glue.create_job(
                Name=GLUE_JOB,
                Description="Sigma QuickMart ETL Pipeline",
                Role=GLUE_ROLE,
                ExecutionProperty={"MaxConcurrentRuns": 5},
                Command={
                    "Name": "pythonshell",
                    "ScriptLocation": f"s3://{BUCKET_NAME}/glue-scripts/etl.py",
                    "PythonVersion": "3.9"
                },
                DefaultArguments={
                    "--additional-python-modules": "pandas"
                },
                MaxRetries=0,
                Timeout=10,
                MaxCapacity=0.0625,
                GlueVersion="1.0"
            )
            status_cols[3].success("✅ 4. Glue Python Shell job created (GlueVersion 1.0, MaxCapacity 0.0625)")
            
            # 5. Create Database
            run_athena_query(f"CREATE DATABASE IF NOT EXISTS {ATHENA_DB}", database="default")
            status_cols[4].success(f"✅ 5. Athena metastore '{ATHENA_DB}' database created")
            
            # 6. Create Orders Table
            run_athena_query(ORDERS_DDL, database="default")
            status_cols[5].success("✅ 6. External orders partition table registered")
            
            # 7. Create Customers Table
            run_athena_query(f"DROP TABLE IF EXISTS {ATHENA_DB}.sigma_opus_customers", database="default")
            run_athena_query(CUSTOMERS_DDL, database="default")
            status_cols[6].success("✅ 7. Reference customers table drop-recreated successfully")
            
            # 8. Create Products Table
            run_athena_query(f"DROP TABLE IF EXISTS {ATHENA_DB}.sigma_opus_products", database="default")
            run_athena_query(PRODUCTS_DDL, database="default")
            status_cols[7].success("✅ 8. Reference products table drop-recreated successfully")
            
            st.success("🎉 **Pipeline setup completed! QuickMart S3 lakehouse and Athena schema are fully provisioned.**")
        except Exception as e:
            st.error(f"❌ **Setup Pipeline failed**: {str(e)}")

# ==================== TAB 2: Daily Load ====================
DAYS_MAPPING = {
    "Day 1 — 2026-05-01": ("2026-05-01", "orders_day1.csv"),
    "Day 2 — 2026-05-02": ("2026-05-02", "orders_day2.csv"),
    "Day 3 — 2026-05-03": ("2026-05-03", "orders_day3.csv"),
    "Day 4 — 2026-05-04": ("2026-05-04", "orders_day4.csv"),
    "Day 5 — 2026-05-05": ("2026-05-05", "orders_day5.csv")
}

with tab_load:
    st.markdown("### 📦 Daily Data Ingestion & ETL Job Runs")
    selected_day = st.selectbox("Select partition day load:", list(DAYS_MAPPING.keys()))
    date_partition, local_filename = DAYS_MAPPING[selected_day]
    
    if st.button(f"▶️ Run ETL for {selected_day}"):
        try:
            # 1. Upload Raw Daily CSV
            st.write(f"Ingesting raw dataset `data/{local_filename}` into raw lakehouse zone...")
            with open(f"data/{local_filename}", "rb") as f:
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=f"raw/orders/date={date_partition}/orders.csv",
                    Body=f.read()
                )
            st.success("Raw CSV file ingested to S3 successfully.")
            
            # 2. Trigger Glue Job
            st.write("Triggering Glue ETL Python Shell job execution...")
            run_response = glue.start_job_run(
                JobName=GLUE_JOB,
                Arguments={
                    "--job_type": "orders",
                    "--bucket_name": BUCKET_NAME,
                    "--date_partition": date_partition
                }
            )
            job_run_id = run_response["JobRunId"]
            st.write(f"Glue job run spawned (Run ID: `{job_run_id}`)")
            
            # 3. Poll Glue job status
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            job_state = "STARTING"
            for poll in range(1, 41):
                progress_val = min(float(poll) / 40.0, 1.0)
                progress_bar.progress(progress_val)
                
                state_resp = glue.get_job_run(JobName=GLUE_JOB, RunId=job_run_id)
                job_state = state_resp["JobRun"]["JobRunState"]
                status_text.markdown(f"⏳ **Glue Job Run Status: {job_state}** (Check {poll}/40)")
                
                if job_state in ["SUCCEEDED", "FAILED", "STOPPED", "TIMEOUT"]:
                    break
                time.sleep(3)
                
            if job_state == "FAILED":
                err_resp = glue.get_job_run(JobName=GLUE_JOB, RunId=job_run_id)
                err_msg = err_resp["JobRun"].get("ErrorMessage", "No explicit error details provided.")
                st.error(f"❌ **Ingestion pipeline failed**: {err_msg}")
            elif job_state != "SUCCEEDED":
                st.error(f"❌ **Ingestion timeout reached. Job remaining state: {job_state}**")
            else:
                progress_bar.progress(1.0)
                status_text.markdown("✅ **Ingestion Pipeline Succeeded!**")
                
                # 5. MSCK Repair Table
                with st.spinner("Synchronizing partitions to Athena catalog..."):
                    run_athena_query(f"MSCK REPAIR TABLE {ATHENA_DB}.sigma_opus_orders", database="default")
                st.success("Partition registered on Athena table catalog successfully.")
                
                # 6. Read S3 Quality Report JSON
                report_key = f"reports/quality_report_{date_partition}.json"
                report_resp = s3.get_object(Bucket=BUCKET_NAME, Key=report_key)
                report_json = json.loads(report_resp["Body"].read().decode("utf-8"))
                
                # 7. Render Metric Cards
                st.markdown("#### Data Quality Performance")
                c1, c2, c3 = st.columns(3)
                c1.metric("Raw Rows", report_json["input_rows"])
                c2.metric("Cleaned Rows", report_json["output_rows"])
                c3.metric("Anomalous Rows Dropped", report_json["rows_dropped"], delta=-int(report_json["rows_dropped"]), delta_color="inverse")
                
                c4, c5, c6 = st.columns(3)
                c4.metric("Null Customer IDs", report_json["null_customer_ids"])
                c5.metric("Negative Amounts Corrected", report_json["negative_amounts"])
                c6.metric("Duplicate Order IDs Dropped", report_json["duplicate_order_ids"])
                
                # 8. Warn on quality issues
                total_issues = report_json["null_customer_ids"] + report_json["negative_amounts"] + report_json["duplicate_order_ids"]
                if total_issues > 0:
                    st.warning("⚠️ Data quality issues detected")
                    
                # 9. Call Bedrock
                with st.spinner("AI assessing raw ingestion quality report..."):
                    bedrock_prompt = f"""
                    Analyze this AWS Glue data quality report for the date partition {report_json['date']}:
                    {json.dumps(report_json, indent=2)}
                    
                    You must return:
                    1. Overall pipeline health status: HEALTHY (if no issues), WARNING (if minor issues, < 10% rows dropped), or CRITICAL (if major issues, >= 10% rows dropped or zero output).
                    2. Exactly one clear data engineering recommendation (max 80 words).
                    
                    Format your response clearly. Keep it extremely concise and direct.
                    """
                    assessment = ask_bedrock(bedrock_prompt)
                    st.subheader("💡 AI Quality Assessment")
                    st.info(assessment)
        except Exception as e:
            st.error(f"❌ **ETL execution failed**: {str(e)}")

# ==================== TAB 3: Ask Your Data ====================
QUICK_QUESTIONS = [
    "Top 5 cities by revenue",
    "Daily order trend",
    "High value orders per day",
    "Top 3 payment methods by order count",
    "Average order amount by city"
]

with tab_ask:
    st.markdown("### 🔍 Ask Your Data (Natural Language SQL Assistant)")
    st.write("Ask natural language business questions. Bedrock automatically builds highly optimized Athena query structures.")
    
    # Session State staging pattern
    if "_qq_value" in st.session_state:
        st.session_state["nl_question_input"] = st.session_state.pop("_qq_value")
        
    # Show quick-question buttons in columns
    st.markdown("#### Quick Templates:")
    cols = st.columns(5)
    for idx, qq in enumerate(QUICK_QUESTIONS):
        if cols[idx].button(qq, key=f"qq_{idx}"):
            st.session_state["_qq_value"] = qq
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()
                
    # Text input — key= is mandatory to persist across renders
    user_question = st.text_input("Enter your business query:", key="nl_question_input")
    
    if user_question:
        with st.spinner("AI formulating Athena SQL query structure..."):
            sql_prompt = f"""
            You are an expert AI SQL Generator. Generate an Amazon Athena SQL query for the following natural language request: "{user_question}"
            
            Table Schemas:
            1. Orders Table: `sigma_opus_db.sigma_opus_orders`
            Columns:
            - order_id STRING
            - customer_id STRING
            - product_id STRING
            - quantity INT
            - amount DOUBLE
            - status STRING
            - payment_method STRING
            - city STRING
            - created_at STRING
            - processed_at STRING
            - is_high_value STRING
            - date STRING (Partition Key)
            
            2. Customers Table: `sigma_opus_db.sigma_opus_customers`
            Columns:
            - customer_id STRING
            - name STRING
            - email STRING
            - phone STRING
            - city STRING
            - tier STRING
            - signup_date STRING
            
            3. Products Table: `sigma_opus_db.sigma_opus_products`
            Columns:
            - product_id STRING
            - name STRING
            - category STRING
            - price DOUBLE
            - stock_quantity INT
            - is_active STRING
            
            Rules for generating the query:
            1. For SELECT queries that do not use aggregations, always append a LIMIT of 100.
            2. For aggregation queries (e.g. using GROUP BY, SUM, COUNT), do NOT append a LIMIT.
            3. For SHOW, DESCRIBE, or DDL queries, NEVER append a LIMIT (this is critical to prevent errors).
            4. Always wrap monetary aggregations like SUM(amount) or AVG(amount) in CAST(ROUND(<expression>) AS BIGINT) to avoid scientific notation (e.g. 2.94E8) in the output.
            5. Return ONLY the raw SQL query. Do not include markdown fences, backticks, comments, or any conversational text.
            """
            generated_sql = ask_bedrock(sql_prompt)
            
            # Post-process backticks/fences out of Bedrock's response
            generated_sql = re.sub(r'^```sql\s*', '', generated_sql, flags=re.IGNORECASE)
            generated_sql = re.sub(r'^```\s*', '', generated_sql)
            generated_sql = re.sub(r'```$', '', generated_sql)
            generated_sql = generated_sql.strip()
            
            # Strip LIMIT from non-SELECT queries
            first_word = generated_sql.split()[0].upper() if generated_sql.split() else ""
            if first_word != "SELECT":
                generated_sql = re.sub(r'\bLIMIT\s+\d+\b', '', generated_sql, flags=re.IGNORECASE).strip()
                
        st.markdown("#### Generated SQL Structure:")
        st.code(generated_sql, language="sql")
        
        # Execute button
        if st.button("▶️ Run on Athena"):
            with st.spinner("Running execution against lakehouse metastore..."):
                try:
                    res_df = run_athena_query(generated_sql, database=ATHENA_DB)
                    
                    if res_df.empty:
                        st.info("Metastore returned zero matching records.")
                    else:
                        # Format monetary columns
                        for col in res_df.columns:
                            col_lower = col.lower()
                            if any(kw in col_lower for kw in ['amount', 'revenue', 'total_sales', 'avg_amount', 'total_revenue', 'sales', 'price', 'cost']):
                                try:
                                    res_df[col] = res_df[col].apply(lambda val: f"₹{int(round(float(val))):,}" if val and str(val).strip() != "" else "")
                                except Exception:
                                    pass
                                    
                        st.markdown("#### Query Execution Results:")
                        st.dataframe(res_df, use_container_width=True)
                        
                        # Generate bedrock interpretation
                        with st.spinner("Formulating AI executive explanation..."):
                            explain_prompt = f"Explain these Athena query results in one plain-English sentence: {res_df.head(5).to_json(orient='records')}"
                            explanation = ask_bedrock(explain_prompt)
                            st.subheader("💡 AI Explanation")
                            st.info(explanation)
                except Exception as ex:
                    st.error(f"❌ **Athena execution error**: {str(ex)}")

# ==================== TAB 4: Pipeline Health ====================
with tab_health:
    st.markdown("### 📊 Operational Pipeline & Business Metrics")
    st.write("Query real-time daily partition ingestion status and operational summaries via Athena metadata.")
    
    if st.button("🔄 Load Health Dashboard"):
        with st.spinner("Aggregating lakehouse partition health statistics..."):
            try:

# About tab moved below (fixed indentation)

                health_query = f"""
                SELECT date, COUNT(*) AS orders, CAST(ROUND(SUM(amount)) AS BIGINT) AS revenue 
                FROM {ATHENA_DB}.sigma_opus_orders 
                GROUP BY date 
                ORDER BY date
                """
                health_df = run_athena_query(health_query, database=ATHENA_DB)
                
                if health_df.empty:
                    st.warning("No ingested orders partitions discovered in Athena metastore! Please load orders via Tab 2 first.")
                else:
                    health_df['orders'] = health_df['orders'].astype(int)
                    health_df['revenue'] = health_df['revenue'].astype(float)
                    
                    # 3 Metric KPI Cards
                    t_orders = health_df['orders'].sum()
                    t_rev = health_df['revenue'].sum()
                    d_loaded = len(health_df)
                    
                    st.markdown("#### Operational Highlights")
                    hc1, hc2, hc3 = st.columns(3)
                    hc1.metric("Total Cleaned Orders", f"{t_orders:,}")
                    hc2.metric("Total Gained Revenue", f"₹{int(t_rev):,}")
                    hc3.metric("Monitored Date Partitions", f"{d_loaded} / 5")
                    
                    st.markdown("---")
                    
                    # Layout Trends
                    t_col1, t_col2 = st.columns(2)
                    with t_col1:
                        st.subheader("📈 Revenue Growth Trend")
                        rev_chart_df = health_df.set_index("date")[["revenue"]]
                        st.bar_chart(rev_chart_df)
                        
                    with t_col2:
                        st.subheader("📦 Order Quantity Volumetrics")
                        vol_chart_df = health_df.set_index("date")[["orders"]]
                        st.bar_chart(vol_chart_df)
                        
                    st.markdown("---")
                    
                    # Executive summary call to Bedrock
                    with st.spinner("AI compiling executive health summary..."):
                        exec_prompt = f"""
                        Synthesize a 3-sentence executive summary of the pipeline health and business performance based on the following daily aggregations:
                        {health_df.to_json(orient='records')}
                        
                        Include:
                        1. Total orders volume and revenue generated.
                        2. Any trend observation.
                        3. A quick forward-looking technical note.
                        Ensure it is exactly 3 sentences.
                        """
                        exec_summary = ask_bedrock(exec_prompt)
                        st.subheader("📋 Executive Health Summary")
                        st.info(exec_summary)
            except Exception as e_health:
                st.error(f"❌ **Failed to retrieve health metrics**: {str(e_health)}")
with tab_about:
    st.markdown("## About QuickMart")
    st.write("""Here is an expanded, production-ready version of the dummy data for QuickMart. I have fleshed out the company profile, core business model, technical data ecosystem, and a mock transactional log schema to give you plenty of realistic material for system documentation, testing, or pipeline architecture design.

🛒 QuickMart: Corporate & Data Ecosystem Profile
1. Executive Summary
Founded in 2024, QuickMart is a hyper-growth, fictional retail startup specializing in omni-channel grocery delivery and smart convenience commerce. Operating across 12 major metropolitan areas, QuickMart utilizes an asset-light model by partnering with local neighborhood micro-warehouses (dark stores) to fulfill customer orders via an app-based marketplace. The company prides itself on its predictive inventory management system and a guaranteed 20-minute "click-to-curb" delivery window.

As a tech-first retail platform, QuickMart generates vast volumes of streaming data from user interactions, transactional checkouts, real-time logistics tracking, and dynamic pricing engines.

2. Business Architecture & Revenue Streams
QuickMart operates on a three-pronged monetization strategy:

Direct Marketplace Sales: Standard retail margins on groceries, fresh produce, and exclusive white-label QuickMart everyday essentials.

QuickMart+ Subscription Tier: A premium loyalty program charging users $9.99/month for unlimited free deliveries, reduced service fees, and priority scheduling during peak hours.

Retail Media Network (RMN): Sponsored product placements and targeted in-app advertisements powered by first-party consumer behavior data, allowing consumer packaged goods (CPG) brands to bid on keyword visibility.

3. Data Infrastructure Overview
To support real-time operations and downstream business intelligence, QuickMart utilizes a modern, cloud-native data architecture designed to scale seamlessly with transaction spikes (e.g., during major sporting events or holiday rushes).

[ App / Web Event Streams ] ---> [ Real-time Ingestion Layer ] ---> [ Medallion Architecture ] ---> [ Analytics & ML ]
Ingestion Layer: Raw API clicks, cart modifications, and GPS telemetry are captured via high-throughput streaming queues.

Storage & Processing Layer: Data is written directly into cloud object storage buckets before being processed via distributed compute engines using a multi-layered storage strategy (Bronze, Silver, and Gold data layers).

Orchestration: Data transformation pipelines, data quality checks, and automated aggregate updates are managed programmatically using programmatic scheduling frameworks to ensure complete execution lineage.""")
    st.image(
        "/Users/as-mac-1325/.gemini/antigravity-ide/brain/8614ea28-1e08-4716-b474-28716d044ee7/quickmart_logo_1779354377453.png",
        caption="QuickMart – Retail Innovation",
        width='stretch'
    )

import sys
import json
import datetime
import io
import logging
import argparse
import boto3
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting Glue Python Shell ETL job")
    
    try:
        # Parse arguments from sys.argv using argparse parse_known_args to handle Glue environment arguments
        logging.info("Parsing command line arguments")
        parser = argparse.ArgumentParser()
        parser.add_argument('--bucket_name', required=True)
        parser.add_argument('--date_partition', required=False)
        parser.add_argument('--job_type', required=True)
        
        args, unknown = parser.parse_known_args()
        bucket_name = args.bucket_name
        date_partition = args.date_partition
        job_type = args.job_type
        
        logging.info(f"Arguments parsed - bucket_name: {bucket_name}, job_type: {job_type}, date_partition: {date_partition}")
        
        s3_client = boto3.client('s3')
        
        if job_type == "orders":
            if not date_partition:
                raise ValueError("date_partition is required when job_type is 'orders'")
                
            input_key = f"raw/orders/date={date_partition}/orders.csv"
            output_key = f"processed/orders/date={date_partition}/orders.csv"
            report_key = f"reports/quality_report_{date_partition}.json"
            
            logging.info(f"Reading orders raw file from S3: s3://{bucket_name}/{input_key}")
            response = s3_client.get_object(Bucket=bucket_name, Key=input_key)
            csv_content = response['Body'].read().decode('utf-8')
            
            logging.info("Loading data into Pandas DataFrame")
            df = pd.read_csv(io.StringIO(csv_content))
            
            input_rows = len(df)
            logging.info(f"Input row count: {input_rows}")
            
            logging.info("Counting quality issues")
            null_customer_ids = int(df['customer_id'].isnull().sum())
            negative_amounts = int((df['amount'] < 0).sum())
            duplicate_order_ids = int(df.duplicated(subset=['order_id'], keep='first').sum())
            
            logging.info(f"Quality issues found - null customer_ids: {null_customer_ids}, negative amounts: {negative_amounts}, duplicate order_ids: {duplicate_order_ids}")
            
            logging.info("Applying fixes and transformations")
            # Drop null customer_ids
            df_cleaned = df.dropna(subset=['customer_id']).copy()
            # Absolute negative amounts
            df_cleaned['amount'] = df_cleaned['amount'].abs()
            # Drop duplicates keeping first
            df_cleaned = df_cleaned.drop_duplicates(subset=['order_id'], keep='first')
            
            output_rows = len(df_cleaned)
            rows_dropped = input_rows - output_rows
            logging.info(f"Output row count: {output_rows}, Rows dropped: {rows_dropped}")
            
            # Add columns
            processed_at_val = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            df_cleaned['processed_at'] = processed_at_val
            df_cleaned['is_high_value'] = (df_cleaned['amount'] > 10000).astype(str)
            
            logging.info("Writing cleaned data to S3")
            csv_bytes = df_cleaned.to_csv(index=False).encode("utf-8")
            s3_client.put_object(
                Bucket=bucket_name,
                Key=output_key,
                Body=csv_bytes
            )
            logging.info(f"Cleaned orders file written to S3: s3://{bucket_name}/{output_key}")
            
            logging.info("Writing quality report to S3")
            quality_report = {
                "date": date_partition,
                "input_rows": input_rows,
                "output_rows": output_rows,
                "null_customer_ids": null_customer_ids,
                "negative_amounts": negative_amounts,
                "duplicate_order_ids": duplicate_order_ids,
                "rows_dropped": rows_dropped,
                "status": "SUCCESS"
            }
            s3_client.put_object(
                Bucket=bucket_name,
                Key=report_key,
                Body=json.dumps(quality_report, indent=4)
            )
            logging.info(f"Quality report written to S3: s3://{bucket_name}/{report_key}")
            
        elif job_type == "reference":
            logging.info("Copying customers.csv from raw to processed")
            s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': f'{bucket_name}/raw/customers.csv'},
                Key='processed/customers.csv'
            )
            logging.info("Copying products.csv from raw to processed")
            s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': f'{bucket_name}/raw/products.csv'},
                Key='processed/products.csv'
            )
            logging.info("Reference data copy completed successfully")
            
        else:
            raise ValueError(f"Unknown job_type: {job_type}")
            
        logging.info("Glue Python Shell ETL job completed successfully")
        
    except Exception as e:
        logging.error(f"Job failed with error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

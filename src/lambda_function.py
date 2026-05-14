import os
import json
import boto3
import pymysql
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

# Environment Variables
RDS_HOST = os.environ.get('RDS_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASS = os.environ.get('DB_PASS', 'password')
DB_NAME = os.environ.get('DB_NAME', 'turnstile_db')
S3_BUCKET = os.environ.get('S3_LOG_BUCKET', 'turnstile-audit-logs')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:1234567890:AdminAlerts')
MAX_LIMIT = int(os.environ.get('MAX_EVENT_CAPACITY', '100'))

def lambda_handler(event, context):
    """
    AWS Lambda entry point triggered by API Gateway.
    Payload expected: { "student_id": "STU-123", "event_id": "EVT-2026" }
    """
    try:
        # Parse incoming request body
        body = json.loads(event.get('body', '{}'))
        student_id = body.get('student_id')
        event_id = body.get('event_id')

        if not student_id or not event_id:
            return build_response(400, "Missing student_id or event_id")

        # Connect to RDS
        conn = pymysql.connect(host=RDS_HOST, user=DB_USER, password=DB_PASS, db=DB_NAME)
        cursor = conn.cursor()

        # 1. Validate Student
        cursor.execute("SELECT is_active FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()

        if not student or not student[0]:
            trigger_alert(f"Invalid or Inactive Student ID Scanned: {student_id}")
            log_to_s3(student_id, event_id, "DENIED - INVALID_ID")
            return build_response(403, "Access Denied: Invalid ID")

        # 2. Check Event Capacity Limit
        cursor.execute("SELECT count FROM event_attendance WHERE event_id = %s", (event_id,))
        attendance = cursor.fetchone()
        current_count = attendance[0] if attendance else 0

        if current_count >= MAX_LIMIT:
            trigger_alert(f"Event {event_id} Capacity Reached! Turnstile locked for {student_id}")
            log_to_s3(student_id, event_id, "DENIED - CAPACITY_FULL")
            return build_response(403, "Access Denied: Event Full")

        # 3. Grant Access & Update DB
        cursor.execute("UPDATE event_attendance SET count = count + 1 WHERE event_id = %s", (event_id,))
        cursor.execute("INSERT INTO scan_history (student_id, event_id, status) VALUES (%s, %s, 'GRANTED')", (student_id, event_id))
        conn.commit()

        # 4. Save Audit Log to S3
        log_to_s3(student_id, event_id, "GRANTED")

        return build_response(200, "Access Granted")

    except Exception as e:
        trigger_alert(f"System Error: {str(e)}")
        return build_response(500, "Internal Server Error")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

def log_to_s3(student_id, event_id, status):
    """Saves a timestamped JSON log to S3 for auditing."""
    timestamp = datetime.utcnow().isoformat()
    log_data = {
        "student_id": student_id,
        "event_id": event_id,
        "timestamp": timestamp,
        "status": status
    }
    file_key = f"logs/{event_id}/{student_id}_{timestamp}.json"
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=file_key,
        Body=json.dumps(log_data),
        ContentType='application/json'
    )

def trigger_alert(message):
    """Triggers an SNS notification to administrators."""
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject="Turnstile System Alert"
    )

def build_response(status_code, message):
    """Helper to build API Gateway compatible response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": message})
    }

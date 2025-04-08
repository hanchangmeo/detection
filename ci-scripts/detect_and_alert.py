import os
import json
import time
from datetime import datetime, timedelta

from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch.elasticsearch_elastalert import ElastalertBackend
from sigma.configuration import SigmaConfiguration

from elasticsearch import Elasticsearch
import requests
import smtplib
from email.mime.text import MIMEText

# === CẤU HÌNH ===

ELASTIC_URL = os.getenv("ELASTIC_URL")  # VD: https://xxxx.es.us-central1.gcp.cloud.es.io
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")  # App Password của Gmail

FROM_EMAIL = "hanchiangzo@gmail.com"
TO_EMAIL = "hanchiangzo@gmail.com"

RULES_DIR = "rules"

# === KHỞI TẠO KẾT NỐI ===

es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

# === CÁC HÀM XỬ LÝ ===

def send_email_alert(subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(FROM_EMAIL, EMAIL_APP_PASSWORD)
            server.send_message(msg)
            print(f"Email alert sent to {TO_EMAIL}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def load_sigma_rules():
    for rule_file in os.listdir(RULES_DIR):
        if rule_file.endswith(".yml"):
            path = os.path.join(RULES_DIR, rule_file)
            with open(path, "r", encoding="utf-8") as f:
                yield rule_file, SigmaCollection.from_yaml(f.read())

def convert_to_query(collection):
    config = SigmaConfiguration()
    backend = ElastalertBackend(config)
    return backend.convert(collection)[0]

def query_elasticsearch(query_string, index="logs-*", timeframe_minutes=5):
    now = datetime.utcnow()
    start = now - timedelta(minutes=timeframe_minutes)

    query = {
        "query": {
            "bool": {
                "must": [
                    {"query_string": {"query": query_string}},
                    {"range": {"@timestamp": {
                        "gte": start.isoformat(),
                        "lte": now.isoformat()
                    }}}
                ]
            }
        }
    }

    res = es.search(index=index, body=query, size=10)
    return res.get("hits", {}).get("hits", [])

def main():
    print("Detection-as-Code service with Email Alert")

    for rule_name, collection in load_sigma_rules():
        try:
            query_string = convert_to_query(collection)
            print(f"Converted {rule_name} to query: {query_string}")

            results = query_elasticsearch(query_string)
            if results:
                print(f"MATCH: {rule_name}")
                log_sample = json.dumps(results[0]["_source"], indent=2)
                subject = f"[Detection] Rule matched: {rule_name}"
                body = f"Matched log:\n\n{log_sample}"
                send_email_alert(subject, body)
            else:
                print(f"No match: {rule_name}")

        except Exception as e:
            print(f"Error with {rule_name}: {e}")

if __name__ == "__main__":
    if not ELASTIC_URL or not ELASTIC_API_KEY or not EMAIL_APP_PASSWORD:
        print("Missing environment variables!")
        print("Cần ELASTIC_URL, ELASTIC_API_KEY và EMAIL_APP_PASSWORD")
        exit(1)
    main()

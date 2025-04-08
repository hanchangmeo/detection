import os
import json
from datetime import datetime, timedelta
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch.elasticsearch import ElasticsearchBackend
from sigma.configuration import default_configuration

from elasticsearch import Elasticsearch
import smtplib
from email.mime.text import MIMEText

# === CẤU HÌNH ===
ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

FROM_EMAIL = "hanchiangzo@gmail.com"
TO_EMAIL = "hanchiangzo@gmail.com"

INDEX_PATTERN = os.getenv("INDEX_PATTERN", "logs-*")
RULES_DIR = "rules"
MAX_ALERT_LOGS = 3

# === KẾT NỐI ES 8 ===
es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

def send_email_alert(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(FROM_EMAIL, EMAIL_APP_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {TO_EMAIL}")
    except Exception as e:
        print(f" Email failed: {e}")

def load_sigma_rules():
    for file in os.listdir(RULES_DIR):
        if file.endswith(".yml") or file.endswith(".yaml"):
            with open(os.path.join(RULES_DIR, file), "r") as f:
                yield file, SigmaCollection.from_yaml(f.read())

def convert_to_query(collection):
    backend = ElasticsearchBackend(default_configuration)
    return backend.convert(collection)[0]

def query_elasticsearch(query_string, timeframe_minutes=5):
    now = datetime.utcnow()
    start = now - timedelta(minutes=timeframe_minutes)

    query = {
        "query": {
            "bool": {
                "must": [
                    {"query_string": {"query": query_string}},
                    {"range": {
                        "@timestamp": {
                            "gte": start.isoformat(),
                            "lte": now.isoformat()
                        }
                    }}
                ]
            }
        }
    }

    res = es.search(index=INDEX_PATTERN, body=query, size=MAX_ALERT_LOGS)
    return res.get("hits", {}).get("hits", [])

def main():
    print(" Running Detection-as-Code...")

    for rule_name, collection in load_sigma_rules():
        try:
            query_string = convert_to_query(collection)
            print(f" Rule: {rule_name} → {query_string}")

            results = query_elasticsearch(query_string)
            if results:
                print(f" MATCH: {rule_name}")
                logs = "\n---\n".join(json.dumps(hit["_source"], indent=2) for hit in results)
                send_email_alert(f"[Detection] {rule_name} matched", logs)
            else:
                print(f" No match: {rule_name}")
        except Exception as e:
            print(f" Error in {rule_name}: {e}")

if __name__ == "__main__":
    if not ELASTIC_URL or not ELASTIC_API_KEY or not EMAIL_APP_PASSWORD:
        print(" Missing environment variables!")
        exit(1)
    main()

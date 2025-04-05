import os
import json
import random
import time
from datetime import datetime, timedelta

from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch.elasticsearch_elastalert import ElastalertBackend
from sigma.configuration import SigmaConfiguration

from elasticsearch import Elasticsearch
import requests

# === CẤU HÌNH ===

ELASTIC_URL = os.getenv("ELASTIC_URL")  # VD: https://xxxx.es.us-central1.gcp.cloud.es.io
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")  # lấy từ Elastic Cloud
RULES_DIR = "rules"
ALERT_TYPE = random.choice(["slack", "webhook", "email"])  # GPT chọn ngẫu nhiên

# === CẤU HÌNH CẢNH BÁO ===

ALERT_ENDPOINTS = {
    "slack": "https://hooks.slack.com/services/your/slack/webhook",
    "webhook": "https://your-webhook-url.com/receive",
    "email": "https://api.your-email-service.com/send"  # placeholder
}

HEADERS = {
    "Authorization": f"ApiKey {ELASTIC_API_KEY}"
}

es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

def load_sigma_rules():
    for rule_file in os.listdir(RULES_DIR):
        if rule_file.endswith(".yml"):
            path = os.path.join(RULES_DIR, rule_file)
            with open(path, "r", encoding="utf-8") as f:
                yield rule_file, SigmaCollection.from_yaml(f.read())

def convert_to_query(collection):
    config = SigmaConfiguration()
    backend = ElastalertBackend(config)
    return backend.convert(collection)[0]  # Chỉ lấy rule đầu tiên

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

def send_alert(rule_name, log_sample):
    message = f" Rule matched: *{rule_name}*\n\nSample log:\n```json\n{json.dumps(log_sample, indent=2)}```"
    
    if ALERT_TYPE == "slack":
        requests.post(ALERT_ENDPOINTS["slack"], json={"text": message})
    elif ALERT_TYPE == "webhook":
        requests.post(ALERT_ENDPOINTS["webhook"], json={"rule": rule_name, "log": log_sample})
    elif ALERT_TYPE == "email":
        print(" Pretend sending email:\n", message)
    else:
        print(" No valid alert type configured.")

def main():
    print(f" Running Detection-as-Code with alert via: {ALERT_TYPE}")

    for rule_name, collection in load_sigma_rules():
        try:
            rule_text = convert_to_query(collection)
            print(f" Converted {rule_name} to query:\n{rule_text}")

            results = query_elasticsearch(rule_text)
            if results:
                print(f" Match found for {rule_name}!")
                send_alert(rule_name, results[0]["_source"])
            else:
                print(f" No match for {rule_name}")

        except Exception as e:
            print(f" Error with rule {rule_name}: {e}")

if __name__ == "__main__":
    if not ELASTIC_URL or not ELASTIC_API_KEY:
        print(" Missing ELASTIC_URL or ELASTIC_API_KEY environment variables.")
        exit(1)
    main()

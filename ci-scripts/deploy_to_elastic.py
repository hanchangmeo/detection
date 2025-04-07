import os
import json
import requests
from sigma.collection import SigmaCollection
from sigma.resolver import BackendResolver

KIBANA_URL = os.getenv("ELASTIC_URL")  # Ví dụ: https://your-deployment.kb.us-central1.gcp.cloud.es.io
KIBANA_TOKEN = os.getenv("ELASTIC_API_KEY")  # Elastic Cloud API Key
RULES_DIR = "rules"
PASSED_RULES_FILE = "passed_rules.txt"

HEADERS = {
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
    "Authorization": f"ApiKey {KIBANA_TOKEN}"
}

def parse_metadata(rule_dict, rule_path):
    return {
        "name": rule_dict.get("title", os.path.basename(rule_path)),
        "description": rule_dict.get("description", "No description."),
        "risk_score": int(rule_dict.get("risk_score", 50)),
        "severity": rule_dict.get("level", "low"),
        "rule_id": rule_dict.get("id", os.path.basename(rule_path).replace(".yml", "")),
        "tags": rule_dict.get("tags", []) + ["stage:production"]
    }

def deploy_rule(rule_path):
    with open(rule_path, "r", encoding="utf-8") as f:
        rule_yaml = f.read()

    # Parse rule Sigma từ file YAML
    collection = SigmaCollection.from_yaml(rule_yaml)
    # Sử dụng BackendResolver để lấy backend chuyển Sigma thành query cho Elastic (KQL)
    resolver = BackendResolver.default()
    backend = resolver.resolve("elasticsearch/kibana")
    queries = list(collection.to_query(backend))

    if not queries:
        print(f"Không tạo được query cho {rule_path}")
        return

    query = queries[0]
    rule = collection.parsedyaml[0]
    metadata = parse_metadata(rule, rule_path)

    payload = {
        **metadata,
        "type": "query",
        "index": ["logs-*"],
        "language": "kuery",
        "query": query,
        "interval": "5m",
        "from": "now-6m",
        "enabled": True
    }

    url = f"{KIBANA_URL}/api/detection_engine/rules"
    response = requests.post(url, headers=HEADERS, json=payload)

    if response.status_code in [200, 201]:
        print(f"Đã deploy rule: {metadata['name']}")
    else:
        print(f"Lỗi khi deploy {rule_path}:\n{response.status_code} - {response.text}")

def main():
    if not os.path.exists(PASSED_RULES_FILE):
        print("Không tìm thấy passed_rules.txt")
        return

    with open(PASSED_RULES_FILE, "r") as f:
        rule_list = [line.strip() for line in f if line.strip()]

    for rule in rule_list:
        rule_path = os.path.join(RULES_DIR, rule)
        if os.path.exists(rule_path):
            deploy_rule(rule_path)
        else:
            print(f"Không tìm thấy rule: {rule_path}")

if __name__ == "__main__":
    if not KIBANA_URL or not KIBANA_TOKEN:
        print("Thiếu biến ELASTIC_URL hoặc ELASTIC_API_KEY")
        exit(1)
    main()

import os
import json
import requests
from sigma.parser.collection import SigmaCollection
from sigma.backends.kibana import KibanaQueryBackend

# Config từ biến môi trường
KIBANA_URL = os.getenv("ELASTIC_URL")
KIBANA_TOKEN = os.getenv("ELASTIC_API_KEY")
RULES_DIR = "rules"
PASSED_RULES_FILE = "passed_rules.txt"

HEADERS = {
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
    "Authorization": f"ApiKey {KIBANA_TOKEN}"
}

def parse_rule_metadata(rule_dict, rule_path):
    return {
        "name": rule_dict.get("title", os.path.basename(rule_path)),
        "description": rule_dict.get("description", "No description."),
        "risk_score": int(rule_dict.get("risk_score", 50)),
        "severity": rule_dict.get("level", "low"),
        "rule_id": rule_dict.get("id", os.path.basename(rule_path).replace(".yml", "")),
        "tags": rule_dict.get("tags", []) + ["stage:testing"]
    }

def deploy_rule(rule_path):
    with open(rule_path, "r", encoding="utf-8") as f:
        rule_yaml = f.read()

    collection = SigmaCollection.from_yaml(rule_yaml)
    backend = KibanaQueryBackend()
    queries = list(collection.to_query(backend))

    if not queries:
        print(f"[\u274c] Không tạo được query cho {rule_path}")
        return

    query = queries[0]
    rule = collection.parsedyaml[0]
    metadata = parse_rule_metadata(rule, rule_path)

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

    response = requests.post(f"{KIBANA_URL}/api/detection_engine/rules", headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"[\u2705] Đã deploy rule: {metadata['name']}")
    else:
        print(f"[\u274c] Lỗi với rule: {rule_path}")
        print(response.text)

def main():
    if not os.path.exists(PASSED_RULES_FILE):
        print("[\u26a0\ufe0f] Không tìm thấy passed_rules.txt")
        return

    with open(PASSED_RULES_FILE, "r") as f:
        rule_list = [line.strip() for line in f if line.strip()]

    for rule in rule_list:
        rule_path = os.path.join(RULES_DIR, rule)
        if os.path.exists(rule_path):
            deploy_rule(rule_path)
        else:
            print(f"[\u26a0\ufe0f] Không tìm thấy file: {rule_path}")

if __name__ == "__main__":
    if not KIBANA_URL or not KIBANA_TOKEN:
        print("[\u274c] Thiếu biến môi trường: ELASTIC_URL hoặc ELASTIC_API_KEY")
        exit(1)
    main()

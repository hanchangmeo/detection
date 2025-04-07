import os
import json
import requests
from sigma.parser.collection import SigmaCollection
from sigma.backends.elasticsearch import LuceneBackend

# Lấy biến môi trường Elastic (Kibana) URL và API Key
KIBANA_URL = os.getenv("ELASTIC_URL")      # Ví dụ: https://your-deployment.kb.us-central1.gcp.cloud.es.io
KIBANA_TOKEN = os.getenv("ELASTIC_API_KEY")  # Elastic Cloud API Key
RULES_DIR = "rules"
PASSED_RULES_FILE = "passed_rules.txt"

# Header dùng để gọi API Kibana Detection Engine
HEADERS = {
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
    "Authorization": f"ApiKey {KIBANA_TOKEN}"
}

def parse_metadata(rule_dict, rule_path):
    """
    Lấy thông tin metadata từ rule Sigma (dạng dictionary) và file path,
    trả về dictionary chứa metadata cần thiết cho Elastic Detection rule.
    """
    return {
        "name": rule_dict.get("title", os.path.basename(rule_path)),
        "description": rule_dict.get("description", "No description."),
        "risk_score": int(rule_dict.get("risk_score", 50)),
        "severity": rule_dict.get("level", "low"),
        "rule_id": rule_dict.get("id", os.path.basename(rule_path).replace(".yml", "")),
        "tags": rule_dict.get("tags", []) + ["stage:production"]
    }

def deploy_rule(rule_path):
    """
    - Đọc file rule Sigma từ rule_path.
    - Chuyển đổi rule Sigma sang câu truy vấn Lucene dùng LuceneBackend.
    - Tạo payload theo định dạng Elastic Detection rule.
    - Gọi API của Kibana để deploy rule.
    """
    with open(rule_path, "r", encoding="utf-8") as f:
        rule_yaml = f.read()

    # Parse rule Sigma từ YAML
    collection = SigmaCollection.from_yaml(rule_yaml)
    
    # Sử dụng LuceneBackend để chuyển rule Sigma sang Lucene query
    backend = LuceneBackend()  # Default output là Lucene queries
    queries = list(collection.convert(backend))
    
    if not queries:
        print(f"Không tạo được query cho {rule_path}")
        return

    query = queries[0]
    # Lấy rule dictionary đã được parse
    rule = collection.parsedyaml[0]
    metadata = parse_metadata(rule, rule_path)

    # Tạo payload cho API của Kibana Detection Engine
    payload = {
        **metadata,
        "type": "query",
        "index": ["logs-*"],
        "language": "lucene",  # Dùng ngôn ngữ lucene
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

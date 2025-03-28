import os
import json
import requests

def test_rule(rule_file, elastic_url, api_key):
    with open(rule_file, 'r') as f:
        query = json.load(f)

    headers = {
        "Authorization": f"ApiKey {api_key}",
        "Content-Type": "application/json"
    }

    # Gửi query tới Elasticsearch
    response = requests.post(f"{elastic_url}/_search", headers=headers, json=query)

    if response.status_code == 200:
        result = response.json()
        total_hits = result['hits']['total']['value']
        print(f"Rule: {rule_file} - Hits: {total_hits}")
        return total_hits
    else:
        print(f"Error testing {rule_file}: {response.text}")
        return None

def main():
    # Lấy URL và API key từ biến môi trường
    elastic_url = os.getenv("ELASTIC_URL")
    api_key = os.getenv("ELASTIC_API_KEY")
    
    if not elastic_url or not api_key:
        print("Error: Missing ELASTIC_URL or ELASTIC_API_KEY environment variables.")
        exit(1)

    rules_dir = "./converted-rules"
    for rule_file in os.listdir(rules_dir):
        if rule_file.endswith(".json"):
            test_rule(os.path.join(rules_dir, rule_file), elastic_url, api_key)

if __name__ == "__main__":
    main()


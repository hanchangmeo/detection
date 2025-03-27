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
    elastic_url = "https://<your-elastic-url>"
    api_key = "<your-api-key>"
    rules_dir = "./converted-rules"
    for rule_file in os.listdir(rules_dir):
        if rule_file.endswith(".json"):
            test_rule(os.path.join(rules_dir, rule_file), elastic_url, api_key)

if __name__ == "__main__":
    main()


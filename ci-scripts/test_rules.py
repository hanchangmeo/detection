import os
import sys
import requests

def test_rule(rule_file, elastic_url, api_key):
    try:
        with open(rule_file, 'r') as f:
            query_str = f.read().strip()

        search_query = {"query": {"query_string": {"query": query_str}}}
        headers = {"Authorization": f"ApiKey {api_key}", "Content-Type": "application/json"}

        response = requests.post(f"{elastic_url}/_search", headers=headers, json=search_query, timeout=10)
        response.raise_for_status()  # Ném lỗi nếu không phải 200

        total_hits = response.json()['hits']['total']['value']
        print(f"Rule: {rule_file} - Hits: {total_hits}")
        return total_hits > 0
    except Exception as e:
        print(f"Error testing {rule_file}: {e}")
        return False

def main():
    elastic_url = os.getenv("ELASTIC_URL")
    api_key = os.getenv("ELASTIC_API_KEY")
    
    if not elastic_url or not api_key:
        print("Error: Missing ELASTIC_URL or ELASTIC_API_KEY.")
        sys.exit(1)

    rules_dir = "./converted_rules"
    if not os.path.exists(rules_dir):
        print(f"Error: Directory {rules_dir} not found.")
        sys.exit(1)

    all_passed = True
    for rule_file in os.listdir(rules_dir):
        if rule_file.endswith(".json"):
            result = test_rule(os.path.join(rules_dir, rule_file), elastic_url, api_key)
            if not result:
                all_passed = False

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()

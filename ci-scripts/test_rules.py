import os
import json
import requests

def test_rule(rule_file, elastic_url, api_key):
    with open(rule_file, 'r') as f:
        query_str = f.read().strip()  # Đọc chuỗi query DSL từ sigmac

    # Tạo truy vấn _search đơn giản để test
    search_query = {
        "query": {
            "query_string": {
                "query": query_str
            }
        }
    }

    headers = {
        "Authorization": f"ApiKey {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(f"{elastic_url}/_search", headers=headers, json=search_query)
    if response.status_code == 200:
        result = response.json()
        total_hits = result['hits']['total']['value']
        print(f"Rule: {rule_file} - Hits: {total_hits}")
        return total_hits > 0  # Trả về True nếu có kết quả khớp
    else:
        print(f"Error testing {rule_file}: {response.text}")
        return False

def main():
    elastic_url = os.getenv("ELASTIC_URL")
    api_key = os.getenv("ELASTIC_API_KEY")
    
    if not elastic_url or not api_key:
        print("Error: Missing ELASTIC_URL or ELASTIC_API_KEY.")
        sys.exit(1)

    rules_dir = "./converted_rules"  # Đồng bộ với convert_sigma.py
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

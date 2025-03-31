import os
import sys
import json
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch.elasticsearch import ElasticsearchBackend  # Import sửa lại

# Đường dẫn đầu vào
rules_dir = sys.argv[1]  # rules/
logs_dir = sys.argv[2]  # test/

# Backend Elasticsearch
backend = ElasticsearchBackend()  # Dùng ElasticsearchBackend thay vì ElasticsearchQuerystringBackend

# Hàm đọc log từ file
def load_logs(log_file_path):
    logs = []
    with open(log_file_path, 'r') as f:
        content = f.read().strip()
        try:
            logs_data = json.loads(content)
            if isinstance(logs_data, list):
                logs.extend(logs_data)
            else:
                logs.append(logs_data)
        except json.JSONDecodeError:
            f.seek(0)
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line in {log_file_path}: {e}")
                        sys.exit(1)
    return logs

# Hàm kiểm tra log có khớp với query không
def matches_query(log, query):
    for condition in query.split(" AND "):
        if ":" in condition:
            key, value = condition.split(":")
            if key not in log or log[key] != value.strip('"'):
                return False
    return True

# Kiểm tra từng rule với log tương ứng
passed_rules = []
for rule_file in os.listdir(rules_dir):
    if rule_file.endswith('.yml'):
        rule_name = rule_file.replace('.yml', '')  # Ví dụ: T1059
        log_file = os.path.join(logs_dir, f"{rule_name}-log.json")  # T1059-log.json
        
        if not os.path.exists(log_file):
            print(f"No corresponding log file found for {rule_file} (expected {log_file})")
            sys.exit(1)
        
        # Đọc log từ file tương ứng
        logs = load_logs(log_file)
        
        # Đọc và chuyển đổi Sigma rule thành query
        with open(os.path.join(rules_dir, rule_file), 'r') as f:
            rule_content = f.read()
        sigma_collection = SigmaCollection.from_yaml(rule_content)
        query = backend.convert(sigma_collection)[0]  # Query Elasticsearch
        
        # Kiểm tra với log
        for log in logs:
            if matches_query(log, query):
                print(f"Rule {rule_file} passed with sample log in {log_file} (Query: {query})!")
                passed_rules.append(rule_file)
                break
        else:
            print(f"Rule {rule_file} failed: No match found in {log_file}!")

if not passed_rules:
    print("No rules passed the test!")
    sys.exit(1)

print(f"Passed rules: {passed_rules}")

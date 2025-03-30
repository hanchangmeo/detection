import json
import os
import sys

# Đường dẫn đầu vào
queries_dir = sys.argv[1]  # queries/
logs_dir = sys.argv[2]    # test/

# Đọc tất cả log mẫu
logs = []
for log_file in os.listdir(logs_dir):
    if log_file.endswith('.json'):
        with open(os.path.join(logs_dir, log_file), 'r') as f:
            logs.extend([json.loads(line) for line in f])

# Hàm kiểm tra log có khớp với query không
def matches_query(log, query):
    for condition in query.split(" AND "):
        if ":" in condition:
            key, value = condition.split(":")
            if key not in log or log[key] != value.strip('"'):
                return False
    return True

# Kiểm tra từng query
passed_rules = []
for query_file in os.listdir(queries_dir):
    if query_file.endswith('.json'):
        with open(os.path.join(queries_dir, query_file), 'r') as f:
            query_data = json.load(f)
            query = query_data["query"]
        
        # Kiểm tra với tất cả log
        for log in logs:
            if matches_query(log, query):
                print(f"Rule {query_file} passed with sample log!")
                passed_rules.append(query_file)
                break
        else:
            print(f"Rule {query_file} failed: No match found in sample logs!")

if not passed_rules:
    print("No rules passed the test!")
    sys.exit(1)

print(f"Passed rules: {passed_rules}")

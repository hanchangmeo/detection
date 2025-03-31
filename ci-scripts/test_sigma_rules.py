import os
import sys
import json
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch import LuceneBackend

# Đường dẫn đầu vào
rules_dir = sys.argv[1]  # rules/
logs_dir = sys.argv[2]  # test/

# Backend Elasticsearch
backend = LuceneBackend()

# Hàm đọc log từ file
def load_logs(log_file_path):
    logs = []
    with open(log_file_path, 'r') as f:
        try:
            logs_data = json.load(f)
            if isinstance(logs_data, list):
                return logs_data
            else:
                return [logs_data]
        except json.JSONDecodeError:
            f.seek(0)  # Nếu file không phải JSON list, đọc từng dòng
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"Error parsing {log_file_path}: {e}")
                    return []
    print(f"Loaded {len(logs)} log entries from {log_file_path}")
    return logs

# Hàm lấy giá trị từ field lồng trong log
def get_nested_value(log, field):
    keys = field.split(".")
    value = log
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None  # Trả về None nếu field không tồn tại
    return str(value) if value is not None else None

# Hàm kiểm tra log có khớp với query không
def matches_query(log, query):
    and_conditions = query.split(" AND ")
    for condition in and_conditions:
        if "(" in condition and ")" in condition:
            or_part = condition[condition.index("(") + 1 : condition.index(")")]
            field = condition.split(":")[0].strip()
            or_values = [v.strip().strip('"') for v in or_part.split(" OR ")]
            log_value = get_nested_value(log, field)
            if log_value is None:
                return False
            if not any(value in log_value if "*" in value else value == log_value for value in or_values):
                return False
        elif ":" in condition:
            key, value = condition.split(":")
            value = value.strip('"')
            log_value = get_nested_value(log, key)
            if log_value is None or ("*" not in value and log_value != value) or ("*" in value and value.replace("*", "") not in log_value):
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
            continue
        
        logs = load_logs(log_file)
        if not logs:
            print(f"Log file {log_file} is empty or could not be parsed!")
            continue

        with open(os.path.join(rules_dir, rule_file), 'r') as f:
            rule_content = f.read()
        sigma_collection = SigmaCollection.from_yaml(rule_content)
        queries = backend.convert(sigma_collection)
        if not queries:
            print(f"No query generated for {rule_file}, skipping...")
            continue
        
        print(f"Generated {len(queries)} queries for {rule_file}")
        matched = False
        for query in queries:
            for log in logs:
                if matches_query(log, query):
                    print(f"Rule {rule_file} passed with sample log in {log_file}!")
                    passed_rules.append(rule_file)
                    matched = True
                    break
            if matched:
                break  # Nếu đã match, dừng kiểm tra rule này
        
        if not matched:
            print(f"Rule {rule_file} failed: No match found in {log_file}!")
            print("--- Debugging Info ---")
            for query in queries:
                print(f"Query: {query}")
            print("Sample Logs:")
            for log in logs[:5]:  # Chỉ in 5 log đầu tiên
                print(json.dumps(log, indent=4))
            print("----------------------")

if not passed_rules:
    print("No rules passed the test!")
    sys.exit(1)

print(f"Passed rules: {passed_rules}")

# Ghi danh sách rule pass vào file
with open("passed_rules.txt", "a") as f:
    for rule in set(passed_rules):
        f.write(f"{rule}\n")

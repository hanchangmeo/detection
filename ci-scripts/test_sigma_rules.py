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
    print(f"Loaded {len(logs)} log entries from {log_file_path}")
    return logs

# Hàm lấy giá trị từ field lồng trong log
def get_nested_value(log, field):
    keys = field.split(".")
    value = log
    for key in keys:
        try:
            value = value[key]
        except (KeyError, TypeError):
            print(f"Field '{field}' not found in log: {log}")
            return None
    return str(value) if value is not None else None

# Hàm kiểm tra log có khớp với query không
def matches_query(log, query):
    and_conditions = query.split(" AND ")
    for condition in and_conditions:
        if "(" in condition and ")" in condition:
            or_part = condition[condition.index("(")+1:condition.index(")")]
            field = condition.split(":")[0].strip()
            or_values = [v.strip() for v in or_part.split(" OR ")]
            log_value = get_nested_value(log, field)
            if log_value is None:
                return False
            matched = False
            for value in or_values:
                value = value.strip('"')
                if "*" in value:
                    value = value.replace("*", "")
                    if value in log_value:
                        matched = True
                        break
                elif value == log_value:
                    matched = True
                    break
            if not matched:
                print(f"No match for OR condition '{field}:({or_part})' in log value '{log_value}'")
                return False
        elif ":" in condition:
            key, value = condition.split(":")
            value = value.strip('"')
            log_value = get_nested_value(log, key)
            if log_value is None:
                return False
            if "*" in value:
                value = value.replace("*", "")
                if value not in log_value:
                    print(f"Value '{value}' not in log value '{log_value}' for field '{key}'")
                    return False
            elif log_value != value:
                print(f"Log value '{log_value}' does not match query value '{value}' for field '{key}'")
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
        
        logs = load_logs(log_file)
        with open(os.path.join(rules_dir, rule_file), 'r') as f:
            rule_content = f.read()
        sigma_collection = SigmaCollection.from_yaml(rule_content)
        query = backend.convert(sigma_collection)[0]
        print(f"Generated query for {rule_file}: {query}")
        
        for log in logs:
            if matches_query(log, query):
                print(f"Rule {rule_file} passed with sample log in {log_file}!")
                passed_rules.append(rule_file)
                break
        else:
            print(f"Rule {rule_file} failed: No match found in {log_file}!")

if not passed_rules:
    print("No rules passed the test!")
    sys.exit(1)

print(f"Passed rules: {passed_rules}")

# Ghi danh sách rule pass vào file
with open("passed_rules.txt", "w") as f:
    for rule in passed_rules:
        f.write(f"{rule}\n")

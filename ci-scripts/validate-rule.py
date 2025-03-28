import os
import sys
import yaml

def validate_rule(file_path):
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)  # Đọc file .yml
        required_fields = ["title", "description", "logsource", "detection", "level"]
        for field in required_fields:
            if field not in data:
                print(f"Error: Missing field '{field}' in {file_path}")
                return False
        print(f"PASSED: {file_path}")
        return True
    except yaml.YAMLError as e:
        print(f"FAILED: {file_path} - Invalid YAML format: {e}")
        return False

def main():
    rules_dir = "./rules"
    if not os.path.exists(rules_dir):
        print(f"Error: Directory {rules_dir} not found.")
        sys.exit(1)

    failed_rules = []
    for rule_file in os.listdir(rules_dir):
        if rule_file.endswith(".yml"):
            file_path = os.path.join(rules_dir, rule_file)
            if not validate_rule(file_path):
                failed_rules.append(file_path)

    if failed_rules:
        print("Failed rules:")
        for rule in failed_rules:
            print(f"- {rule}")
        sys.exit(1)
    else:
        print("All rules passed validation!")

if __name__ == "__main__":
    main()

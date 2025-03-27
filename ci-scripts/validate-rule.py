import os
import json

def validate_rule(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)  # Kiểm tra định dạng JSON
        required_fields = ["rule_name", "query", "description", "tags", "level"]
        for field in required_fields:
            if field not in data:
                print(f"Error: Missing field '{field}' in {file_path}")
                return False
        print(f"PASSED: {file_path}")
        return True
    except json.JSONDecodeError:
        print(f"FAILED: {file_path} - Invalid JSON format")
        return False

def main():
    rules_dir = "./rules"
    failed_rules = []

    for root, _, files in os.walk(rules_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                if not validate_rule(file_path):
                    failed_rules.append(file_path)

    if failed_rules:
        print("The following rules failed validation:")
        for rule in failed_rules:
            print(f"- {rule}")
        exit(1)
    else:
        print("All rules passed validation!")

if __name__ == "__main__":
    main()


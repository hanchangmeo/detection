import os
import sys
from sigma.collection import SigmaCollection

def validate_rule(file_path):
    try:
        # Dùng pySigma để parse và validate file .yml
        with open(file_path, 'r') as f:
            SigmaCollection.from_yaml(f)  # Nếu parse được thì rule hợp lệ
        print(f"PASSED: {file_path}")
        return True
    except Exception as e:
        print(f"FAILED: {file_path} - Invalid Sigma rule: {e}")
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

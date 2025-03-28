import os
import subprocess
import sys

def convert_sigma_to_elasticsearch(sigma_rule_path, output_path):
    try:
        # Dùng lệnh sigmac trực tiếp (cài qua pip)
        result = subprocess.run(
            ["sigmac", "-t", "es-qs", sigma_rule_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Error in Sigma conversion: {result.stderr}")

        output_file = os.path.join(output_path, os.path.basename(sigma_rule_path).replace(".yml", ".json"))
        with open(output_file, "w") as f:
            f.write(result.stdout)
        print(f"Converted {sigma_rule_path} to {output_file}")
        return True
    except Exception as e:
        print(f"Failed to convert {sigma_rule_path}: {e}")
        return False

def main():
    rules_dir = "./rules"
    output_dir = "./converted_rules"
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(rules_dir) or not any(f.endswith(".yml") for f in os.listdir(rules_dir)):
        print(f"No Sigma rules (.yml) found in {rules_dir}. Exiting.")
        sys.exit(1)

    for rule_file in os.listdir(rules_dir):
        if rule_file.endswith(".yml"):
            rule_path = os.path.join(rules_dir, rule_file)
            convert_sigma_to_elasticsearch(rule_path, output_dir)

if __name__ == "__main__":
    main()

import os
import subprocess
import sys

def convert_sigma_to_elasticsearch(sigma_rule_path, output_path):
    """
    Convert Sigma rules to Elasticsearch Query DSL using Sigma CLI.
    """
    try:
        # Ensure Sigma CLI tool exists
        sigmac_path = os.path.join("sigma", "tools", "sigmac")  # Điều chỉnh đường dẫn nếu Sigma được clone
        if not os.path.exists(sigmac_path):
            raise FileNotFoundError(f"Sigma CLI tool not found at {sigmac_path}. Ensure Sigma is installed.")

        # Run Sigma conversion
        result = subprocess.run(
            ["python3", sigmac_path, "-t", "es-qs", sigma_rule_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Error in Sigma conversion: {result.stderr}")

        # Write converted rule to output file
        output_file = os.path.join(output_path, os.path.basename(sigma_rule_path).replace(".yml", ".json"))
        with open(output_file, "w") as f:
            f.write(result.stdout)
        print(f"Converted {sigma_rule_path} to {output_file}")
        return True
    except Exception as e:
        print(f"Failed to convert {sigma_rule_path}: {e}")
        return False

def main():
    # Define input and output directories
    rules_dir = "./rules"  # Thư mục chứa rules Sigma gốc
    output_dir = "./converted_rules"  # Đồng bộ với deploy.yml (dùng _ thay vì -)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Check if rules directory exists and has .yml files
    if not os.path.exists(rules_dir) or not any(f.endswith(".yml") for f in os.listdir(rules_dir)):
        print(f"No Sigma rules (.yml) found in {rules_dir}. Exiting.")
        sys.exit(1)

    # Convert each Sigma rule
    for rule_file in os.listdir(rules_dir):
        if rule_file.endswith(".yml"):
            rule_path = os.path.join(rules_dir, rule_file)
            success = convert_sigma_to_elasticsearch(rule_path, output_dir)
            if not success:
                print(f"Conversion failed for {rule_path}. Continuing with next rule.")

if __name__ == "__main__":
    main()

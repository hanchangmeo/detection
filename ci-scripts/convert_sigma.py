import os
import subprocess

def convert_sigma_to_elasticsearch(sigma_rule_path, output_path):
    """
    Convert Sigma rules to Elasticsearch Query DSL using Sigma CLI.
    """
    try:
        # Check if Sigma CLI is available
        result = subprocess.run(
            ["python3", "tools/sigmac", "-t", "es-qs", sigma_rule_path],
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
    rules_dir = "./rules"
    output_dir = "./converted-rules"
    os.makedirs(output_dir, exist_ok=True)

    for rule_file in os.listdir(rules_dir):
        if rule_file.endswith(".yml"):
            rule_path = os.path.join(rules_dir, rule_file)
            convert_sigma_to_elasticsearch(rule_path, output_dir)

if __name__ == "__main__":
    main()


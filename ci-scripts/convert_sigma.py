import os
import sys
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch import ElasticsearchQuerystringBackend
from sigma.pipelines.elasticsearch import ElasticsearchPipeline

def convert_sigma_to_elasticsearch(sigma_rule_path, output_path):
    try:
        # Đọc rule từ file YAML
        with open(sigma_rule_path, 'r') as f:
            sigma_rule = f.read()

        # Parse rule
        sigma_collection = SigmaCollection.from_yaml(sigma_rule)

        # Khởi tạo backend với pipeline
        pipeline = ElasticsearchPipeline()
        backend = ElasticsearchQuerystringBackend(pipeline=pipeline)
        
        # Chuyển đổi rule
        queries = backend.convert(sigma_collection)

        # Ghi kết quả ra file JSON
        output_file = os.path.join(output_path, os.path.basename(sigma_rule_path).replace(".yml", ".json"))
        with open(output_file, "w") as f:
            f.write(queries[0])  # Lấy query đầu tiên

        print(f" Converted {sigma_rule_path} → {output_file}")
        return True
    except Exception as e:
        print(f" Failed to convert {sigma_rule_path}: {e}")
        return False

def main():
    rules_dir = "./rules"
    output_dir = "./converted_rules"
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(rules_dir) or not any(f.endswith(".yml") for f in os.listdir(rules_dir)):
        print(f" No Sigma rules (.yml) found in {rules_dir}. Exiting.")
        sys.exit(1)

    for rule_file in os.listdir(rules_dir):
        if rule_file.endswith(".yml"):
            rule_path = os.path.join(rules_dir, rule_file)
            convert_sigma_to_elasticsearch(rule_path, output_dir)

if __name__ == "__main__":
    main()

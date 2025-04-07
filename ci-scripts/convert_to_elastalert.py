import os
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch.elasticsearch_elastalert import ElastalertBackend

RULES_DIR = "rules"
OUTPUT_DIR = "converted_rules"

def convert_sigma_to_elastalert(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        rule_content = f.read()

    try:
        collection = SigmaCollection.from_yaml(rule_content)
        backend = ElastalertBackend()
        converted_rules = backend.convert(collection)

        if not converted_rules:
            print(f" Không có rule nào được tạo từ {input_file}")
            return

        with open(output_file, "w", encoding="utf-8") as out:
            out.write(converted_rules[0])  # Mỗi rule Sigma thường sinh ra 1 rule ElastAlert
            print(f" Converted: {input_file} ➜ {output_file}")

    except Exception as e:
        print(f" Error converting {input_file}: {e}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for root, _, files in os.walk(RULES_DIR):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(input_path, RULES_DIR)
                output_file_name = rel_path.replace(os.sep, "_").replace(".yml", ".yaml").replace(".yaml", ".yaml")
                output_path = os.path.join(OUTPUT_DIR, output_file_name)

                convert_sigma_to_elastalert(input_path, output_path)

if __name__ == "__main__":
    main()

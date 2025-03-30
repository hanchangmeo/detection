import os
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch.elasticsearch import LuceneBackend
import yaml

def validate_sigma_rules(rules_dir="rules"):
    backend = ElasticsearchQueryBackend()
    success = True
    for root, _, files in os.walk(rules_dir):
        for file in files:
            if file.endswith(".yml"):
                rule_path = os.path.join(root, file)
                print(f"Validating: {rule_path}")
                try:
                    with open(rule_path, 'r') as f:
                        rule_content = yaml.safe_load(f)
                    sigma_rule = SigmaCollection.from_yaml(rule_content)
                    query = backend.convert(sigma_rule)
                    print(f"Query generated: {query}")
                except Exception as e:
                    print(f"Validation failed for {rule_path}: {e}")
                    success = False
    if not success:
        exit(1)

if __name__ == "__main__":
    validate_sigma_rules()

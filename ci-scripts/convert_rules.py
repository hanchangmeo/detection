import os
import sys
import json
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch import LuceneBackend

# Đường dẫn đầu vào và đầu ra
rules_dir = sys.argv[1]  # rules/
logs_dir = sys.argv[2]   # test/
output_dir = sys.argv[3] # queries/

# Tạo thư mục đầu ra nếu chưa có
os.makedirs(output_dir, exist_ok=True)

# Backend Elasticsearch
backend = LuceneBackend()

# Duyệt qua tất Deed tất cả file .yml trong rules/
for rule_file in os.listdir(rules_dir):
    if rule_file.endswith('.yml'):
        rule_path = os.path.join(rules_dir, rule_file)
        with open(rule_path, 'r') as f:
            rule_content = f.read()
        
        # Chuyển đổi Sigma rule thành query
        sigma_collection = SigmaCollection.from_yaml(rule_content)
        queries = backend.convert(sigma_collection)
        
        # Lưu query vào file
        query_file = os.path.join(output_dir, rule_file.replace('.yml', '.json'))
        with open(query_file, 'w') as f:
            json.dump({"query": queries[0]}, f)

print(f"Converted all Sigma rules to queries in {output_dir}")

import os
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch.elasticsearch import LuceneBackend

def validate_sigma_rules(rules_dir="rules"):
    # Khởi tạo backend Lucene cho Elasticsearch
    backend = LuceneBackend()
    success = True
    
    # Duyệt qua tất cả file .yml trong thư mục rules
    for root, _, files in os.walk(rules_dir):
        for file in files:
            if file.endswith(".yml"):
                rule_path = os.path.join(root, file)
                print(f"Validating: {rule_path}")
                try:
                    # Đọc nội dung file YAML dưới dạng chuỗi
                    with open(rule_path, 'r') as f:
                        rule_content = f.read()  # Lấy chuỗi YAML thô
                    
                    # Tạo SigmaCollection từ chuỗi YAML
                    sigma_rule = SigmaCollection.from_yaml(rule_content)
                    
                    # Chuyển đổi rule thành query Lucene
                    query = backend.convert(sigma_rule)
                    print(f"Query generated: {query}")
                except Exception as e:
                    print(f"Validation failed for {rule_path}: {e}")
                    success = False
    
    # Thoát với mã lỗi nếu có rule không hợp lệ
    if not success:
        exit(1)

if __name__ == "__main__":
    validate_sigma_rules()

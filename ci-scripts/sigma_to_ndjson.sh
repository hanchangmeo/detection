#!/bin/bash
set -e

# Tạo thư mục "kibana" nếu chưa tồn tại
mkdir -p kibana

# Nếu bạn lưu file pipeline "lucene-kibana-siemrule.yml" tại thư mục "pipeline",
# điều chỉnh đường dẫn tương ứng (ví dụ: pipeline/lucene-kibana-siemrule.yml)
PIPELINE_PATH="pipeline/lucene-kibana-siemrule.yml"

# Duyệt qua các file rule trong thư mục rules (chỉ các file .yml)
for rule in ./rules/*.yml; do
    filename=$(basename "$rule" .yml)
    echo "Chuyển đổi rule: $filename.yml"
    
    # Gọi lệnh sigma convert cho file rule này, tạo file NDJSON riêng
    sigma convert -t lucene -p "$PIPELINE_PATH" -o kibana/"${filename}.ndjson" "$rule"
done

echo "Chuyển đổi hoàn tất. Các file NDJSON được lưu trong thư mục kibana."

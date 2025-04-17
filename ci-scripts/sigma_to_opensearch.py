import os
import sys
import yaml
import json

# Thêm đường dẫn của repo pySigma-backend-opensearch vào sys.path để import các module cần thiết
sys.path.insert(0, os.path.join(os.getcwd(), 'pySigma-backend-opensearch'))

# Import các module từ pySigma-backend-opensearch
from sigma.backends.opensearch import OpensearchLuceneBackend
from sigma.collection import SigmaCollection
from sigma.processing.resolver import ProcessingPipelineResolver
from sigma.pipelines.sysmon import sysmon_pipeline
from sigma.pipelines.elasticsearch.windows import ecs_windows

def setup_backend():
    # Khởi tạo resolver cho các pipelines cần thiết
    piperesolver = ProcessingPipelineResolver()
    piperesolver.add_pipeline_class(ecs_windows())
    piperesolver.add_pipeline_class(sysmon_pipeline())
    resolved_pipeline = piperesolver.resolve(piperesolver.pipelines)

    # Khởi tạo backend với các thông số mẫu (chỉnh sửa theo môi trường của bạn nếu cần)
    backend = OpensearchLuceneBackend(
        resolved_pipeline,
        index_names=['logs-*-*', 'beats-*'],
        monitor_interval=10,
        monitor_interval_unit="MINUTES"
    )
    return backend

def convert_rule(input_path, output_path, backend):
    # Đọc file Sigma rule gốc (định dạng YAML)
    with open(input_path, 'r') as f:
        sigma_yaml = f.read()

    # Tạo đối tượng SigmaCollection từ nội dung YAML
    rules = SigmaCollection.from_yaml(sigma_yaml)
    
    # Chuyển đổi rule sang định dạng "monitor_rule" (đầu ra là một chuỗi JSON)
    monitor_rule_json = backend.convert(rules, output_format="monitor_rule")

    # Ghi đầu ra vào file (sử dụng đuôi .json)
    with open(output_path, 'w') as out:
        json.dump(json.loads(monitor_rule_json), out, indent=2)
    print(f"Converted {input_path} -> {output_path}")

def main():
    rules_dir = "rules"
    output_dir = "opensearch"
    
    backend = setup_backend()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Duyệt qua các file có định dạng .yml hoặc .yaml trong thư mục rules/
    for filename in os.listdir(rules_dir):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            input_file = os.path.join(rules_dir, filename)
            # Đổi tên file output sang .json để lưu định dạng monitor_rule
            output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.json")
            try:
                convert_rule(input_file, output_file, backend)
            except Exception as e:
                print(f"Lỗi khi chuyển đổi file {filename}: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import json

# Nếu bạn đã pip install pysigma-backend-opensearch, pysigma-backend-elasticsearch,
# pysigma-pipeline-sysmon thì không cần sys.path hack.
# sys.path.insert(0, os.path.join(os.getcwd(), 'pySigma-backend-opensearch'))

from sigma.backends.opensearch import OpensearchLuceneBackend
from sigma.collection import SigmaCollection
from sigma.processing.resolver import ProcessingPipelineResolver
from sigma.pipelines.sysmon import sysmon_pipeline
from sigma.pipelines.elasticsearch.windows import ecs_windows

def setup_backend():
    """Khởi tạo và trả về một OpensearchLuceneBackend đã config sẵn."""
    resolver = ProcessingPipelineResolver()
    # Nếu rule Windows/Sysmon: cần 2 pipeline
    resolver.add_pipeline_class(ecs_windows())
    resolver.add_pipeline_class(sysmon_pipeline())
    pipeline = resolver.resolve(resolver.pipelines)

    return OpensearchLuceneBackend(
        pipeline,
        index_names=['logs-*-*', 'beats-*'],
        monitor_interval=10,
        monitor_interval_unit="MINUTES"
    )

def convert_rule(input_path, output_path, backend):
    """Chuyển một file Sigma YAML sang JSON monitor_rule của OpenSearch."""
    with open(input_path, 'r', encoding='utf-8') as f:
        sigma_yaml = f.read()

    rules = SigmaCollection.from_yaml(sigma_yaml)

    # Kết quả thường là list (mỗi phần tử dict), hoặc dict nếu chỉ 1 rule
    monitor_rules = backend.convert(rules, output_format="monitor_rule")

    # Nếu list và chỉ muốn export từng rule riêng:
    # here we take first element
    data = monitor_rules[0] if isinstance(monitor_rules, list) else monitor_rules

    # Ghi JSON ra file
    with open(output_path, 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2, ensure_ascii=False)

    print(f"✔ Converted: {input_path} → {output_path}")

def main():
    rules_dir   = "rules"
    output_dir  = "opensearch"

    backend = setup_backend()

    os.makedirs(output_dir, exist_ok=True)

    for fname in os.listdir(rules_dir):
        if not (fname.endswith(".yml") or fname.endswith(".yaml")):
            continue

        in_path  = os.path.join(rules_dir,  fname)
        out_name = os.path.splitext(fname)[0] + ".json"
        out_path = os.path.join(output_dir, out_name)

        try:
            convert_rule(in_path, out_path, backend)
        except Exception as e:
            print(f"✖ Error converting {fname}: {e}")

if __name__ == "__main__":
    main()

import os
import sys
import json

# Thêm đường dẫn của repo pySigma-backend-opensearch vào sys.path
REPO_DIR = os.path.join(os.path.dirname(__file__), '..', 'pySigma-backend-opensearch')
sys.path.insert(0, os.path.abspath(REPO_DIR))

from sigma.backends.opensearch import OpensearchLuceneBackend
from sigma.collection import SigmaCollection
from sigma.processing.resolver import ProcessingPipelineResolver
from sigma.pipelines.sysmon import sysmon_pipeline
from sigma.pipelines.elasticsearch.windows import ecs_windows


def setup_backend(index_patterns=None, interval=10, unit="MINUTES"):
    """
    Khởi tạo và trả về OpensearchLuceneBackend với pipeline được cấu hình sẵn.
    """
    resolver = ProcessingPipelineResolver()
    resolver.add_pipeline_class(ecs_windows())
    resolver.add_pipeline_class(sysmon_pipeline())
    resolved = resolver.resolve(resolver.pipelines)

    backend = OpensearchLuceneBackend(
        resolved,
        index_names=index_patterns or ['logs-*-*', 'beats-*'],
        monitor_interval=interval,
        monitor_interval_unit=unit
    )
    return backend


def convert_directory(rules_dir='rules', output_dir='opensearch', **backend_kwargs):
    """
    Duyệt qua các file rule trong `rules_dir`, convert và xuất file JSON sang `output_dir`.
    """
    backend = setup_backend(**backend_kwargs)

    os.makedirs(output_dir, exist_ok=True)

    for fname in os.listdir(rules_dir):
        if not fname.lower().endswith(('.yml', '.yaml')):
            continue
        src = os.path.join(rules_dir, fname)
        dst = os.path.join(output_dir, f"{os.path.splitext(fname)[0]}.json")
        try:
            with open(src, 'r', encoding='utf-8') as f:
                yaml_text = f.read()

            rules = SigmaCollection.from_yaml(yaml_text)
            monitor_rules = backend.convert(rules, output_format="monitor_rule")

            # Chuyển đổi thành list các dict
            objs = []
            for mr in monitor_rules:
                if isinstance(mr, str):
                    objs.append(json.loads(mr))
                else:
                    objs.append(mr)

            # Ghi kết quả: nếu chỉ có 1 monitor, unwrap thành object, ngược lại giữ list
            output_data = objs[0] if len(objs) == 1 else objs
            with open(dst, 'w', encoding='utf-8') as out:
                json.dump(output_data, out, indent=2)

            print(f"[OK] Converted {fname} -> {os.path.basename(dst)}")
        except Exception as ex:
            print(f"[ERROR] Khi convert {fname}: {ex}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert Sigma rules to OpenSearch monitor JSON files")
    parser.add_argument('-i', '--input', default='rules', help='Thư mục chứa các file rule (.yml/.yaml)')
    parser.add_argument('-o', '--output', default='opensearch', help='Thư mục đích lưu JSON monitor')
    parser.add_argument('--indices', nargs='+', default=['logs-*-*', 'beats-*'], help='Index patterns cho monitor')
    parser.add_argument('--interval', type=int, default=10, help='Interval cho monitor')
    parser.add_argument('--unit', choices=['MINUTES','HOURS','SECONDS'], default='MINUTES', help='Đơn vị thời gian')

    args = parser.parse_args()
    convert_directory(
        rules_dir=args.input,
        output_dir=args.output,
        index_patterns=args.indices,
        interval=args.interval,
        unit=args.unit
    )

if __name__ == '__main__':
    main()

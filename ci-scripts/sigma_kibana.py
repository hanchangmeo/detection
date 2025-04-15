#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import shutil
import glob
import yaml

# Cấu hình đường dẫn – chỉnh sửa cho phù hợp
RULE_PATH = "./rules"         # Thư mục chứa các rule YAML
PARSER = "./elastic-agent-parser.yml"         # File parser của sigma
SIGMA_SOURCE = "./sigma"                      # (Nếu cần sử dụng)
OUTPUT_DIR = "./kibanandj"                     # Thư mục đích lưu file ndjson
BACKEND = "es-qs"                             # Backend dùng cho sigma
LOG_FILE = "./sigma2elastic.log"              # File log

# Hàm ghi log (append vào file)
def write_log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)

# Hàm chạy lệnh sigma convert với tham số truyền vào và trả về stdout
def run_sigma_convert(rule_fullpath, backend, parser, extra_options):
    # Xây dựng lệnh
    command = ["python3", "./sigma/tools/sigmac", "-t", backend, "-c", parser]
    # Thêm các tùy chọn --backend-option từ danh sách extra_options
    for opt in extra_options:
        command.extend(["--backend-option", opt])
    # Cuối cùng thêm đường dẫn rule
    command.append(rule_fullpath)
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        write_log(f"Error executing sigma convert on {rule_fullpath}: {e.stderr.strip()}")
        return None

def calculate_risk(level):
    level = level.lower() if level else ""
    if level == "low":
        return 21
    elif level == "medium":
        return 47
    elif level == "high":
        return 73
    elif level == "critical":
        return 99
    else:
        return 0

def main():
    # Xoá file log nếu tồn tại
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    # Tạo thư mục OUTPUT_DIR nếu chưa tồn tại
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Lấy danh sách file rule YAML (đệ quy)
    rule_files = glob.glob(os.path.join(RULE_PATH, "**/*.yml"), recursive=True)
    if not rule_files:
        write_log("Không tìm thấy file rule trong thư mục " + RULE_PATH)
        sys.exit(1)
    
    for rule_path in rule_files:
        rule_name = os.path.basename(rule_path)
        write_log(f"Chuyển đổi rule: {rule_name}")
        
        # Bước 1: Chạy sigma convert để lấy queryNoRegex (không dùng case_insensitive_whitelist)
        extra_options_no_regex = [
            'keyword_base_fields="*"',
            'analyzed_sub_field_name=".text"',
            'keyword_whitelist="winlog.channel,winlog.event_id"',
            'analyzed_sub_fields="TargetUserName, SourceUserName, TargetHostName, CommandLine, ProcessName, ParentProcessName, ParentImage, Image"',
            'keyword_base_fields="*"'
        ]
        query_no_regex = run_sigma_convert(rule_path, BACKEND, PARSER, extra_options_no_regex)
        if not query_no_regex:
            write_log(f"Problem translating {rule_name}")
            continue  # Bỏ qua rule này nếu không chuyển được
        
        # Bước 2: Chạy sigma convert để lấy query chính với case_insensitive_whitelist
        extra_options = [
            'keyword_base_fields="*"',
            'analyzed_sub_field_name=".text"',
            'keyword_whitelist="winlog.channel,winlog.event_id"',
            'case_insensitive_whitelist="*"',
            'analyzed_sub_fields="TargetUserName, SourceUserName, TargetHostName, CommandLine, ProcessName, ParentProcessName, ParentImage, Image"',
            'keyword_base_fields="*"'
        ]
        query_final = run_sigma_convert(rule_path, BACKEND, PARSER, extra_options)
        if not query_final:
            write_log(f"Problem translating (with regex) {rule_name}")
            continue
        
        # Đọc nội dung YAML của rule
        try:
            with open(rule_path, "r", encoding="utf-8") as f:
                rule_info = yaml.safe_load(f)
        except Exception as e:
            write_log(f"Lỗi đọc file YAML {rule_name}: {str(e)}")
            continue
        
        # Tính risk dựa vào rule_info.level
        level_value = rule_info.get("level", "")
        risk = calculate_risk(level_value)
        
        # Tạo đối tượng rule cuối cùng (theo cấu trúc Detection Rule)
        # Lưu ý: Trong PowerShell, trường "id" và "rule_id" dùng giá trị từ $ruleinfo.id.
        # Bạn cần đảm bảo rằng file YAML có trường "id". Nếu không, bạn có thể tạo một ID tự động.
        rule_id = rule_info.get("id", "")
        final_rule = {
            "id": rule_id,
            "created_by": rule_info.get("author"),
            "name": rule_info.get("title"),
            "tags": rule_info.get("tags"),
            "interval": "5m",
            "description": rule_info.get("description"),
            "risk_score": risk,
            "enabled": True,
            "severity": level_value,
            "false_positives": rule_info.get("falsepositives"),
            "from": "now-720s",  # Có thể điều chỉnh: ở PowerShell dùng now-720s
            "type": "query",
            "language": "lucene",
            "index": ["winlogbeat-*","logs-*"],
            "query": query_final,
            "rule_id": rule_id,
            "timestamp_override": "event.ingested",
            "references": rule_info.get("references"),
            "note": f"**Detection Rule without Regex for better understanding. Be careful, this way is case sensitive:** `{query_no_regex}`"
        }
        
        # Chuyển đổi đối tượng thành JSON nén (không phân cách)
        rule_json = json.dumps(final_rule, separators=(",", ":"))
        
        # Tạo tên file ndjson (sử dụng tên rule ban đầu cộng .ndjson)
        base_name = os.path.splitext(rule_name)[0]
        output_file = os.path.join(OUTPUT_DIR, base_name + ".ndjson")
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rule_json)
            write_log(f"Rule {base_name}.ndjson has been translated successfully")
        except Exception as e:
            write_log(f"Lỗi ghi file {output_file}: {str(e)}")
    
if __name__ == "__main__":
    main()

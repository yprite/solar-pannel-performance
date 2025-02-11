import csv
import json
import time
import os
import shutil

def csv_to_json(csv_file_path, json_file_path, backup_path):
    try:
        last_line_count = 0
        existing_data = []
        
        # 기존 JS 파일에서 데이터 로드
        if os.path.exists(json_file_path):
            with open(json_file_path, mode='r', encoding='utf-8') as js_file:
                try:
                    js_content = js_file.read().strip()
                    if js_content.startswith("var solarData = "):
                        js_content = js_content.replace("var solarData = ", "", 1).strip()
                    existing_data = json.loads(js_content)
                    if not isinstance(existing_data, list):
                        existing_data = []
                except json.JSONDecodeError:
                    existing_data = []
        
        while True:
            if os.path.exists(csv_file_path):
                with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
                    reader = list(csv.DictReader(csv_file))
                    new_lines = len(reader)
                    
                    if new_lines > last_line_count:  # 새 라인이 추가되었을 경우
                        new_data = reader[last_line_count:]
                        existing_data.extend(new_data)
                        last_line_count = new_lines

                        # JS 파일에 업데이트
                        with open(json_file_path, mode='w', encoding='utf-8') as js_file:
                            js_file.write("var solarData = ")
                            js_file.write(json.dumps(existing_data, indent=2, ensure_ascii=False))
                            js_file.write("\n")  # 파일 끝에 개행 추가로 깨짐 방지

                        print(f"✅ {len(new_data)} new records added to {json_file_path}")
            
            # 10초마다 파일을 상위 폴더로 복사
            time.sleep(10)
            if os.path.exists(json_file_path):
                shutil.copy(json_file_path, backup_path)
                print(f"📂 {json_file_path} copied to {backup_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    csv_file = "korea_solar_data.csv"  # API 스크립트에서 추가하는 CSV 파일
    json_file = "solar-data.js"  # JSON 데이터를 JS 파일로 저장
    backup_file = "../solar-data.js"  # 상위 폴더로 복사
    
    csv_to_json(csv_file, json_file, backup_file)

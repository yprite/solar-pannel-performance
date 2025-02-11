import requests
import json
import csv
import os
from time import sleep
import pandas as pd
import re

# NASA POWER API URL 템플릿
API_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&start=2023&end=2023&format=JSON"

# 파일 경로 설정
NEIGHBOURHOODS_FILE = "Korea_Localities"
FAILED_REQUESTS_FILE = "failed_requests"
CSV_FILE = "korea_solar_data.csv"
BATCH_SIZE = 50  # 데이터 저장 배치 크기

def load_existing_data(file_path):
    existing_locations = set()
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                match = re.match(r'"(.+)": \((\d+\.\d+), (\d+\.\d+)\)', line)
                if match:
                    name, lat, lon = match.groups()
                    existing_locations.add(name)
    return existing_locations

# 행정구역 데이터 검증 함수
def validate_neighbourhoods(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not re.match(r'".+": \(\d+\.\d+, \d+\.\d+\)', line):
                print(f"⚠️ 오류: {i}번째 줄의 형식이 잘못되었습니다: {line}")

# 행정구역 데이터를 파일에서 읽어오기
def load_neighbourhoods(file_path):
    locations = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                match = re.match(r'"(.+)": \((\d+\.\d+), (\d+\.\d+)\)', line)
                if match:
                    name, lat, lon = match.groups()
                    locations[name] = (float(lat), float(lon))
                else:
                    print(f"⚠️ 잘못된 데이터 무시: {line}")
    return locations

# 실패한 요청을 저장하는 함수
def save_failed_request(location, lat, lon):
    with open(FAILED_REQUESTS_FILE, "a", encoding="utf-8") as f:
        f.write(f'"{location}": ({lat}, {lon})\n')

# 파일 검증 실행
validate_neighbourhoods(NEIGHBOURHOODS_FILE)

# 대한민국 행정구역별 위도, 경도 데이터
korea_locations = load_neighbourhoods(NEIGHBOURHOODS_FILE)

# 기존 데이터 확인 (이미 처리된 지역 확인)
processed_locations = load_existing_data(CSV_FILE)
failed_requests = load_existing_data(FAILED_REQUESTS_FILE)

# 결과 저장할 리스트
data_list = []

# 새로운 데이터를 처리
for location, (lat, lon) in korea_locations.items():
    if location in processed_locations:
        print(f"🔄 {location} 이미 처리됨, 건너뜀.")
        continue  # 기존 데이터는 건너뛴다.

    if location in failed_requests:
        print(f"⚠️ {location} 이전에 실패한 요청, 재시도 중...")

    url = API_URL.format(lat=lat, lon=lon)
    print(f"🔍 요청 URL 확인: {url}")  # 요청 URL 출력해서 확인

    for attempt in range(3):  # 최대 3번 재시도
        response = requests.get(url)
        sleep(0.2)  # API 요청 제한 방지를 위한 딜레이

        if response.status_code == 200:
            data = response.json()
            allsky_data = data.get("properties", {}).get("parameter", {}).get("ALLSKY_SFC_SW_DWN", {})

            if allsky_data:
                # 1~12월 데이터만 저장
                filtered_data = {k: v for k, v in allsky_data.items() if k.isdigit() and int(k[-2:]) <= 12}

                row = {"Latitude": lat, "Longitude": lon, "Location": location}
                row.update(filtered_data)  # 월별 데이터 추가
                data_list.append(row)

                # 배치 크기만큼 데이터가 쌓이면 저장
                if len(data_list) >= BATCH_SIZE:
                    with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
                        fieldnames = ["Latitude", "Longitude", "Location"] + sorted(set().union(*[row.keys() for row in data_list]) - {"Latitude", "Longitude", "Location"})
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
                            writer.writeheader()  # 첫 실행 시 헤더 추가
                        writer.writerows(data_list)
                    print(f"✅ {len(data_list)}개 데이터 저장 완료.")
                    data_list = []  # 리스트 초기화
                break  # 성공하면 루프 종료
        else:
            print(f"❌ 요청 실패 ({attempt+1}/3): {location} (lat: {lat}, lon: {lon})")
            if attempt == 2:
                print(f"🚨 최종 실패: {location}, 재시도 목록에 추가됨.")
                save_failed_request(location, lat, lon)

# 남은 데이터 저장
if data_list:
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Latitude", "Longitude", "Location"] + sorted(set().union(*[row.keys() for row in data_list]) - {"Latitude", "Longitude", "Location"})
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
            writer.writeheader()  # 첫 실행 시 헤더 추가
        writer.writerows(data_list)
    print(f"✅ 최종 데이터 저장 완료: {len(data_list)}개 데이터 추가됨.")

print(f"🎯 모든 데이터 처리 완료! 저장된 파일: {CSV_FILE}")


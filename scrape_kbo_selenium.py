#!/usr/bin/env python3
"""
KBO 정규시즌 선수별 기록 수집 스크립트 (Selenium 사용)
- 타자 기록: Basic1 페이지
- 투수 기록: Basic1 페이지
- 연도: 2000-2025
- 전 팀 대상

팀 드롭다운을 선택하여 각 팀별 전체 선수 데이터 수집
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime

# KBO 팀 코드 (드롭다운 value)
TEAM_CODES = {
    'LG': 'LG 트윈스',
    'HH': '한화 이글스',
    'SK': 'SSG 랜더스',  # SSG는 SK 코드 사용
    'SS': '삼성 라이온즈',
    'NC': 'NC 다이노스',
    'KT': 'KT 위즈',
    'LT': '롯데 자이언츠',
    'HT': 'KIA 타이거즈',
    'OB': '두산 베어스',
    'WO': '키움 히어로즈',
}


def setup_driver():
    """Chrome WebDriver 설정"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def parse_table(html, year):
    """테이블에서 데이터 추출"""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='tData01')
    if not table:
        return []

    # 헤더 추출
    headers = []
    thead = table.find('thead')
    if thead:
        for th in thead.find_all('th'):
            headers.append(th.get_text(strip=True))

    # 데이터 추출
    players = []
    tbody = table.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 3:
                player_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        value = cell.get_text(strip=True)
                        # 선수명에서 링크의 playerId 추출
                        if headers[i] == '선수명':
                            link = cell.find('a')
                            if link and 'href' in link.attrs:
                                player_id_match = re.search(r'playerId=(\d+)', link['href'])
                                if player_id_match:
                                    player_data['playerId'] = player_id_match.group(1)
                        player_data[headers[i]] = value

                if player_data and player_data.get('선수명'):
                    player_data['year'] = year
                    players.append(player_data)

    return players


def collect_team_data(driver, base_url, year, team_code, team_name):
    """특정 팀의 데이터 수집"""
    all_players = []

    try:
        # 페이지 로드
        url = f'{base_url}?years={year}'
        driver.get(url)

        # 페이지 로드 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tData01'))
        )
        time.sleep(1)

        # 팀 선택 드롭다운 찾기
        team_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'cphContents_cphContents_cphContents_ddlTeam_ddlTeam'))
        )

        # 팀 선택
        select = Select(team_dropdown)
        select.select_by_value(team_code)

        # AJAX 응답 대기
        time.sleep(2)

        # 테이블 데이터 추출
        html = driver.page_source
        players = parse_table(html, year)

        if players:
            for p in players:
                p['teamCode'] = team_code
            all_players.extend(players)

        return all_players

    except Exception as e:
        print(f"      오류: {e}")
        return []


def collect_year_all_teams(driver, base_url, year, team_codes):
    """특정 연도의 모든 팀 데이터 수집"""
    all_data = []

    for team_code, team_name in team_codes.items():
        try:
            players = collect_team_data(driver, base_url, year, team_code, team_name)
            if players:
                all_data.extend(players)
                print(f"    {team_name}: {len(players)}명")
            time.sleep(0.5)
        except Exception as e:
            print(f"    {team_name} 오류: {e}")

    return all_data


def main():
    years = list(range(2000, 2026))  # 2000-2025
    team_codes = TEAM_CODES

    all_hitter_data = []
    all_pitcher_data = []

    print("=" * 60)
    print("KBO 선수 기록 수집 시작 (Selenium)")
    print(f"연도 범위: {years[0]} - {years[-1]}")
    print(f"팀 수: {len(team_codes)}")
    print("=" * 60)

    # WebDriver 초기화
    print("\nWebDriver 초기화 중...")
    driver = setup_driver()
    print("WebDriver 준비 완료")

    try:
        # 타자 기록 수집
        hitter_url = 'https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx'
        print("\n[1/2] 타자 기록 수집 중...")

        for year in years:
            print(f"\n{year}년 타자 기록:")
            year_data = collect_year_all_teams(driver, hitter_url, year, team_codes)
            all_hitter_data.extend(year_data)
            print(f"  → 총 {len(year_data)}명")

        # 투수 기록 수집
        pitcher_url = 'https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx'
        print("\n[2/2] 투수 기록 수집 중...")

        for year in years:
            print(f"\n{year}년 투수 기록:")
            year_data = collect_year_all_teams(driver, pitcher_url, year, team_codes)
            all_pitcher_data.extend(year_data)
            print(f"  → 총 {len(year_data)}명")

    finally:
        driver.quit()

    # JSON 파일로 저장
    print("\n" + "=" * 60)
    print("데이터 저장 중...")

    hitter_filename = 'kbo_hitter_stats_2000_2025.json'
    pitcher_filename = 'kbo_pitcher_stats_2000_2025.json'

    with open(hitter_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'description': 'KBO 정규시즌 타자 기록 (2000-2025)',
                'source': 'https://www.koreabaseball.com',
                'collected_at': datetime.now().isoformat(),
                'total_records': len(all_hitter_data)
            },
            'data': all_hitter_data
        }, f, ensure_ascii=False, indent=2)

    with open(pitcher_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'description': 'KBO 정규시즌 투수 기록 (2000-2025)',
                'source': 'https://www.koreabaseball.com',
                'collected_at': datetime.now().isoformat(),
                'total_records': len(all_pitcher_data)
            },
            'data': all_pitcher_data
        }, f, ensure_ascii=False, indent=2)

    print(f"\n타자 기록: {hitter_filename} ({len(all_hitter_data)}건)")
    print(f"투수 기록: {pitcher_filename} ({len(all_pitcher_data)}건)")
    print("\n수집 완료!")


if __name__ == '__main__':
    main()

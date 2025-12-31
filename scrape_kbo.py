#!/usr/bin/env python3
"""
KBO 정규시즌 선수별 기록 수집 스크립트
- 타자 기록: 팀별 전체 선수
- 투수 기록: 팀별 전체 선수
- 연도: 2000-2025
- 전 팀 대상 (현대 유니콘스, 해태 타이거즈 등 과거 팀 포함)

Playwright를 사용하여 JavaScript 렌더링 지원
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime


def parse_table(html, year, team_code, team_name):
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
                    player_data['teamCode'] = team_code
                    player_data['teamName'] = team_name
                    players.append(player_data)

    return players


def get_total_pages(html):
    """전체 페이지 수 확인"""
    soup = BeautifulSoup(html, 'html.parser')
    pager = soup.find('div', class_='paging')
    if not pager:
        return 1

    max_page = 1
    for link in pager.find_all('a'):
        link_id = link.get('id', '')
        match = re.search(r'btnNo(\d+)', link_id)
        if match:
            page_num = int(match.group(1))
            max_page = max(max_page, page_num)

    return max_page


def get_teams_for_year(page):
    """현재 연도의 팀 목록 가져오기"""
    teams = []
    options = page.locator('select[name*="ddlTeam"] option').all()
    for opt in options:
        value = opt.get_attribute('value')
        text = opt.text_content().strip()
        if value:  # 빈 값(팀 선택) 제외
            teams.append((value, text))
    return teams


def collect_team_data(page, year, team_code, team_name, max_retries=5):
    """특정 팀의 전체 선수 데이터 수집 (재시도 로직 포함)"""

    for attempt in range(max_retries):
        all_players = []
        try:
            # 팀 선택
            page.select_option('select[name*="ddlTeam"]', team_code)
            time.sleep(3)  # 대기 시간 증가 (2->3초)
            page.wait_for_selector('table.tData01', timeout=60000)
            time.sleep(2)  # 추가 대기 (1->2초)

            # 첫 페이지 데이터 추출
            html = page.content()
            page_players = parse_table(html, year, team_code, team_name)
            if page_players:
                all_players.extend(page_players)

            # 페이지 수 확인
            total_pages = get_total_pages(html)

            # 2페이지 이상 있으면 추가 수집
            if total_pages > 1:
                for page_num in range(2, total_pages + 1):
                    try:
                        btn_selector = f'a[id*="btnNo{page_num}"]'
                        if page.locator(btn_selector).count() > 0:
                            page.click(btn_selector)
                            time.sleep(1)
                            page.wait_for_selector('table.tData01', timeout=30000)

                            html = page.content()
                            page_players = parse_table(html, year, team_code, team_name)
                            if not page_players:
                                break
                            all_players.extend(page_players)
                        else:
                            break
                    except Exception as e:
                        print(f" [페이지 {page_num} 오류: {e}]", end='')
                        break

            # 데이터가 있으면 성공
            if all_players:
                return all_players

            # 데이터가 없으면 재시도
            if attempt < max_retries - 1:
                print(f" [재시도 {attempt+1}]", end='')
                time.sleep(2)

        except Exception as e:
            if attempt < max_retries - 1:
                print(f" [오류, 재시도: {e}]", end='')
                time.sleep(2)
            else:
                print(f" [오류: {e}]", end='')

    return all_players


def collect_year_data(page, url, year):
    """특정 연도의 모든 팀 데이터 수집 (각 팀마다 페이지 새로 로드)"""
    all_players = []

    try:
        # 먼저 팀 목록 가져오기
        page.goto(url, timeout=60000)
        page.wait_for_selector('table.tData01', timeout=30000)
        page.select_option('select[name*="ddlSeason"]', str(year))
        time.sleep(2)
        page.wait_for_selector('table.tData01', timeout=30000)
        teams = get_teams_for_year(page)

        # 각 팀마다 페이지 새로 로드해서 수집
        for team_code, team_name in teams:
            # 페이지 새로 로드
            page.goto(url, timeout=60000)
            page.wait_for_selector('table.tData01', timeout=30000)

            # 연도 선택
            page.select_option('select[name*="ddlSeason"]', str(year))
            time.sleep(2)
            page.wait_for_selector('table.tData01', timeout=30000)

            # 팀 데이터 수집
            team_players = collect_team_data(page, year, team_code, team_name)
            all_players.extend(team_players)
            print(f" {team_name}:{len(team_players)}", end='')

        return all_players

    except Exception as e:
        print(f" [오류: {e}]", end='')
        return all_players


def main():
    years = list(range(2025, 1999, -1))  # 2025-2000

    all_hitter_data = []
    all_pitcher_data = []

    print("=" * 60)
    print("KBO 선수 기록 수집 시작 (팀별 전체 선수)")
    print(f"연도 범위: {years[0]} - {years[-1]}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 타자 기록 수집
        hitter_url = 'https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx'
        print("\n[1/2] 타자 기록 수집 중...")

        for year in years:
            print(f"\n{year}년:", end='')
            year_data = collect_year_data(page, hitter_url, year)
            all_hitter_data.extend(year_data)
            print(f" → 총 {len(year_data)}명")

        # 투수 기록 수집
        pitcher_url = 'https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx'
        print("\n[2/2] 투수 기록 수집 중...")

        for year in years:
            print(f"\n{year}년:", end='')
            year_data = collect_year_data(page, pitcher_url, year)
            all_pitcher_data.extend(year_data)
            print(f" → 총 {len(year_data)}명")

        browser.close()

    # JSON 파일로 저장
    print("\n" + "=" * 60)
    print("데이터 저장 중...")

    hitter_filename = 'kbo_hitter_stats_2000_2025.json'
    pitcher_filename = 'kbo_pitcher_stats_2000_2025.json'

    with open(hitter_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'description': 'KBO 정규시즌 타자 기록 (2000-2025) - 팀별 전체 선수',
                'source': 'https://www.koreabaseball.com',
                'collected_at': datetime.now().isoformat(),
                'total_records': len(all_hitter_data),
            },
            'data': all_hitter_data
        }, f, ensure_ascii=False, indent=2)

    with open(pitcher_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'description': 'KBO 정규시즌 투수 기록 (2000-2025) - 팀별 전체 선수',
                'source': 'https://www.koreabaseball.com',
                'collected_at': datetime.now().isoformat(),
                'total_records': len(all_pitcher_data),
            },
            'data': all_pitcher_data
        }, f, ensure_ascii=False, indent=2)

    print(f"\n타자 기록: {hitter_filename} ({len(all_hitter_data)}건)")
    print(f"투수 기록: {pitcher_filename} ({len(all_pitcher_data)}건)")
    print("\n수집 완료!")


if __name__ == '__main__':
    main()

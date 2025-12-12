#!/usr/bin/env python3
"""
KBO 정규시즌 선수별 기록 수집 스크립트
- 타자 기록: Basic1 페이지
- 투수 기록: Basic1 페이지
- 연도: 2000-2025
- 전 팀 대상

각 연도별로 전체 데이터를 페이징하여 수집
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from urllib.parse import urlencode

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.koreabaseball.com/',
}


def get_viewstate_regex(html):
    """정규식으로 ASP.NET ViewState 값 추출"""
    viewstate_match = re.search(r'id="__VIEWSTATE"[^>]*value="([^"]*)"', html)
    viewstate_gen_match = re.search(r'id="__VIEWSTATEGENERATOR"[^>]*value="([^"]*)"', html)
    event_validation_match = re.search(r'id="__EVENTVALIDATION"[^>]*value="([^"]*)"', html)

    return {
        '__VIEWSTATE': viewstate_match.group(1) if viewstate_match else '',
        '__VIEWSTATEGENERATOR': viewstate_gen_match.group(1) if viewstate_gen_match else '',
        '__EVENTVALIDATION': event_validation_match.group(1) if event_validation_match else '',
    }


def parse_table(soup, year):
    """테이블에서 데이터 추출"""
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


def get_total_pages(soup):
    """전체 페이지 수 확인"""
    # 페이저에서 마지막 페이지 번호 찾기
    pager = soup.find('div', class_='paging')
    if pager:
        # 페이지 링크들 찾기
        page_links = pager.find_all('a')
        max_page = 1
        for link in page_links:
            text = link.get_text(strip=True)
            if text.isdigit():
                max_page = max(max_page, int(text))
        return max_page
    return 1


def collect_year_data(base_url, year, session):
    """특정 연도의 전체 데이터 수집 (모든 페이지)"""
    all_players = []

    try:
        # 첫 페이지 로드
        url = f'{base_url}?years={year}'
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # 첫 페이지 데이터 추출
        page_players = parse_table(soup, year)
        if page_players:
            all_players.extend(page_players)

        # ViewState 추출
        viewstate = get_viewstate_regex(html)

        # 페이지 수 확인 및 나머지 페이지 수집
        page = 2
        max_pages = 50  # 최대 페이지 수 제한

        while page <= max_pages:
            try:
                # POST로 다음 페이지 요청
                post_data = {
                    '__EVENTTARGET': f'ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ucPager$btnNo{page}',
                    '__EVENTARGUMENT': '',
                    '__LASTFOCUS': '',
                    '__VIEWSTATE': viewstate['__VIEWSTATE'],
                    '__VIEWSTATEGENERATOR': viewstate['__VIEWSTATEGENERATOR'],
                    '__EVENTVALIDATION': viewstate['__EVENTVALIDATION'],
                    'ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSeason$ddlSeason': str(year),
                    'ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSeries$ddlSeries': '0',
                    'ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlTeam$ddlTeam': '',
                    'ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlPos$ddlPos': '',
                    'ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSituation$ddlSituation': '',
                    'ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSituationDetail$ddlSituationDetail': '',
                }

                post_headers = HEADERS.copy()
                post_headers['Content-Type'] = 'application/x-www-form-urlencoded'

                response = session.post(url, data=post_data, headers=post_headers, timeout=30)
                response.raise_for_status()

                html = response.text
                soup = BeautifulSoup(html, 'html.parser')

                page_players = parse_table(soup, year)
                if not page_players:
                    break

                all_players.extend(page_players)
                viewstate = get_viewstate_regex(html)

                page += 1
                time.sleep(0.3)

            except Exception as e:
                # 더 이상 페이지가 없으면 종료
                break

        return all_players

    except Exception as e:
        print(f"    오류: {e}")
        return all_players


def main():
    years = list(range(2000, 2026))  # 2000-2025

    all_hitter_data = []
    all_pitcher_data = []

    session = requests.Session()

    print("=" * 60)
    print("KBO 선수 기록 수집 시작")
    print(f"연도 범위: {years[0]} - {years[-1]}")
    print("=" * 60)

    # 타자 기록 수집
    hitter_url = 'https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx'
    print("\n[1/2] 타자 기록 수집 중...")

    for year in years:
        print(f"\n{year}년 타자 기록 수집 중...", end=' ')
        year_data = collect_year_data(hitter_url, year, session)
        all_hitter_data.extend(year_data)

        # 팀별 통계
        teams = {}
        for p in year_data:
            team = p.get('팀명', 'Unknown')
            teams[team] = teams.get(team, 0) + 1

        print(f"총 {len(year_data)}명")
        for team, count in sorted(teams.items()):
            print(f"    {team}: {count}명")

        time.sleep(0.5)

    # 투수 기록 수집
    pitcher_url = 'https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx'
    print("\n[2/2] 투수 기록 수집 중...")

    for year in years:
        print(f"\n{year}년 투수 기록 수집 중...", end=' ')
        year_data = collect_year_data(pitcher_url, year, session)
        all_pitcher_data.extend(year_data)

        # 팀별 통계
        teams = {}
        for p in year_data:
            team = p.get('팀명', 'Unknown')
            teams[team] = teams.get(team, 0) + 1

        print(f"총 {len(year_data)}명")
        for team, count in sorted(teams.items()):
            print(f"    {team}: {count}명")

        time.sleep(0.5)

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

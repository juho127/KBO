# KBO 선수 기록 수집기

KBO(한국프로야구) 정규시즌 선수별 기록을 수집하는 Python 스크립트입니다.

## 📊 수집 데이터

- **타자 기록**: 2000-2025년 정규시즌 전체 팀 타자 통계
- **투수 기록**: 2000-2025년 정규시즌 전체 팀 투수 통계
- **데이터 출처**: [KBO 공식 홈페이지](https://www.koreabaseball.com)

## 📁 파일 구조

```
kbo/
├── scrape_kbo.py                      # 메인 스크래핑 스크립트 (requests 기반)
├── scrape_kbo_playwright.py           # Playwright 기반 대체 스크립트
├── scrape_kbo_selenium.py             # Selenium 기반 대체 스크립트
├── kbo_hitter_stats_2000_2025.json    # 타자 기록 (JSON)
├── kbo_hitter_stats_2000_2025.xlsx    # 타자 기록 (Excel)
├── kbo_pitcher_stats_2000_2025.json   # 투수 기록 (JSON)
└── kbo_pitcher_stats_2000_2025.xlsx   # 투수 기록 (Excel)
```

## 🛠 설치 및 실행

### 필수 패키지

```bash
pip install requests beautifulsoup4 pandas openpyxl
```

### 실행

```bash
python scrape_kbo.py
```

## 📈 데이터 필드

### 타자 기록
| 필드 | 설명 |
|------|------|
| year | 시즌 연도 |
| teamCode | 팀 코드 |
| 팀명 | 팀 이름 |
| 선수명 | 선수 이름 |
| AVG | 타율 |
| G | 경기 수 |
| PA | 타석 |
| AB | 타수 |
| R | 득점 |
| H | 안타 |
| 2B | 2루타 |
| 3B | 3루타 |
| HR | 홈런 |
| TB | 루타 |
| RBI | 타점 |
| SAC | 희생번트 |
| SF | 희생플라이 |

### 투수 기록
| 필드 | 설명 |
|------|------|
| year | 시즌 연도 |
| teamCode | 팀 코드 |
| 팀명 | 팀 이름 |
| 선수명 | 선수 이름 |
| ERA | 평균자책점 |
| G | 경기 수 |
| W | 승 |
| L | 패 |
| SV | 세이브 |
| HLD | 홀드 |
| WPCT | 승률 |
| IP | 이닝 |
| H | 피안타 |
| HR | 피홈런 |
| BB | 볼넷 |
| HBP | 사구 |
| SO | 삼진 |
| R | 실점 |
| ER | 자책점 |
| WHIP | WHIP |

## 📝 라이선스

이 프로젝트는 개인 학습 및 연구 목적으로 제작되었습니다. 데이터 저작권은 KBO에 있습니다.

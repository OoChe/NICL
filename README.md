# NICL (News Information Collection & Library)

네이버 뉴스 API와 구글 뉴스 웹 크롤링을 통합한 뉴스 수집 시스템

## 기능

- 네이버 뉴스 API를 통한 뉴스 수집
- 구글 뉴스 웹 크롤링
- 키워드 기반 뉴스 검색
- 다중 키워드 일괄 수집
- 섹션별 뉴스 수집
- SQLite 데이터베이스 자동 저장
- 중복 뉴스 자동 필터링

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/OoChe/NICL.git
cd NICL
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 설정

`.env` 파일을 생성하고 네이버 API 키를 설정합니다:

```env
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

## 사용 방법

### 기본 사용법

#### 1. 키워드로 뉴스 수집 (API + 크롤링)

```bash
python main.py --keyword "인공지능" --count 20
```

#### 2. API만 사용

```bash
python main.py --keyword "ChatGPT" --count 30 --api-only
```

#### 3. 크롤링만 사용

```bash
python main.py --keyword "ChatGPT" --count 30 --crawl-only
```

### 고급 사용법

#### 다중 키워드 수집

```bash
python main.py --keywords "정치" "경제" "사회" --count 10
```

#### 섹션별 뉴스 수집

```bash
python main.py --section politics --count 30
```

사용 가능한 섹션:
- `politics` - 정치
- `economy` - 경제
- `society` - 사회
- `culture` - 문화
- `world` - 국제
- `it` - IT/과학

#### 인기 뉴스 수집

```bash
python main.py --trending --count 20
```

### 유틸리티 명령어

#### 데이터베이스 통계 확인

```bash
python main.py --stats
```

#### 설정 검증

```bash
python main.py --validate
```

## 명령어 옵션

| 옵션 | 단축 | 설명 |
|------|------|------|
| `--keyword` | `-k` | 검색할 키워드 |
| `--keywords` | `-ks` | 여러 키워드 (공백으로 구분) |
| `--count` | `-c` | 수집할 뉴스 개수 (기본: 50) |
| `--category` | | 뉴스 카테고리 |
| `--section` | | 네이버 뉴스 섹션 |
| `--trending` | `-t` | 인기 뉴스 수집 |
| `--stats` | `-s` | 데이터베이스 통계 확인 |
| `--validate` | `-v` | 설정 검증 |
| `--api-only` | | API만 사용 |
| `--crawl-only` | | 크롤링만 사용 |

## 출력 예시

```
============================================================
NICL (News Information Collection & Library)
네이버 뉴스 API + 웹 크롤링 통합 수집 시스템
============================================================
실행 시간: 2025-10-25 01:30:00
수집 방식: API + 크롤링

🔍 키워드 'ChatGPT' 뉴스 수집 중...
수집 목표: 20개
----------------------------------------
✅ 수집 완료!
📰 총 수집: 20개
   ├─ API: 10개
   └─ 크롤링: 10개
💾 저장됨: 18개
🔄 중복: 2개
⏱️ 실행 시간: 5.23초
```

## 데이터베이스

수집된 뉴스는 `data/nicl_news.db` SQLite 데이터베이스에 저장됩니다.

### 테이블 구조

- **news**: 수집된 뉴스 기사
- **collection_logs**: 수집 작업 로그

## 프로젝트 구조

```
NICL/
├── main.py                 # 메인 실행 파일
├── requirements.txt        # 패키지 의존성
├── .env                    # 환경 변수 (직접 생성)
├── data/
│   └── nicl_news.db       # SQLite 데이터베이스
├── src/
│   ├── api/
│   │   └── naver_news.py  # 네이버 API 클라이언트
│   ├── crawler/
│   │   └── news_crawler.py # 구글 뉴스 크롤러
│   ├── database/
│   │   └── manager.py     # 데이터베이스 매니저
│   └── utils/
│       └── config.py      # 설정 관리
└── logs/                   # 로그 파일
```

## 주의사항

- 네이버 API 사용 시 일일 호출 제한이 있습니다
- 크롤링 시 과도한 요청은 차단될 수 있으니 적절한 간격을 유지하세요
- `.env` 파일은 절대 Git에 커밋하지 마세요

## 라이선스

MIT License

## 기여

Issue 및 Pull Request는 언제든 환영합니다!
"""
NICL 프로젝트 - 데이터 조회 스크립트
수집된 뉴스 데이터를 확인하는 유틸리티
"""

import os
import sys
import sqlite3
from datetime import datetime

# 프로젝트 루트 경로
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 데이터베이스 경로
DB_PATH = os.path.join(project_root, 'data', 'nicl_news.db')

def connect_db():
    """데이터베이스 연결"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")
        print("먼저 뉴스를 수집해주세요.")
        return None
    
    return sqlite3.connect(DB_PATH)

def view_all_news(limit=10):
    """모든 뉴스 조회"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 최근 뉴스 조회
    cursor.execute("""
        SELECT id, title, keyword, pub_date, created_at, source
        FROM news_articles
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    news_list = cursor.fetchall()
    
    print("=" * 80)
    print(f"📰 최근 수집된 뉴스 (최대 {limit}개)")
    print("=" * 80)
    
    if not news_list:
        print("수집된 뉴스가 없습니다.")
    else:
        for i, news in enumerate(news_list, 1):
            news_id, title, keyword, pub_date, created_at, source = news
            print(f"\n[{i}] ID: {news_id}")
            print(f"제목: {title}")
            print(f"키워드: {keyword}")
            print(f"발행일: {pub_date}")
            print(f"수집일: {created_at}")
            print(f"출처: {source}")
            print("-" * 80)
    
    conn.close()

def view_news_by_keyword(keyword):
    """키워드별 뉴스 조회"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, description, pub_date, link
        FROM news_articles
        WHERE keyword = ?
        ORDER BY created_at DESC
    """, (keyword,))
    
    news_list = cursor.fetchall()
    
    print("=" * 80)
    print(f"📰 '{keyword}' 키워드 뉴스 ({len(news_list)}개)")
    print("=" * 80)
    
    if not news_list:
        print(f"'{keyword}' 키워드로 수집된 뉴스가 없습니다.")
    else:
        for i, news in enumerate(news_list, 1):
            news_id, title, description, pub_date, link = news
            print(f"\n[{i}] ID: {news_id}")
            print(f"제목: {title}")
            print(f"요약: {description[:100]}..." if description else "요약: 없음")
            print(f"발행일: {pub_date}")
            print(f"링크: {link}")
            print("-" * 80)
    
    conn.close()

def view_statistics():
    """통계 조회"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 전체 통계
    cursor.execute("SELECT COUNT(*) FROM news_articles")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM news_articles WHERE is_duplicate = 1")
    duplicates = cursor.fetchone()[0]
    
    # 키워드별 통계
    cursor.execute("""
        SELECT keyword, COUNT(*) as count
        FROM news_articles
        WHERE is_duplicate = 0
        GROUP BY keyword
        ORDER BY count DESC
    """)
    keyword_stats = cursor.fetchall()
    
    # 날짜별 통계
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM news_articles
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 7
    """)
    date_stats = cursor.fetchall()
    
    print("=" * 80)
    print("📊 NICL 데이터베이스 통계")
    print("=" * 80)
    
    print(f"\n📰 전체 뉴스")
    print(f"  - 총 뉴스: {total:,}개")
    print(f"  - 고유 뉴스: {total - duplicates:,}개")
    print(f"  - 중복 뉴스: {duplicates:,}개")
    
    if keyword_stats:
        print(f"\n🔍 키워드별 통계 (중복 제외)")
        for keyword, count in keyword_stats:
            print(f"  - {keyword}: {count:,}개")
    
    if date_stats:
        print(f"\n📅 최근 7일 수집 현황")
        for date, count in date_stats:
            print(f"  - {date}: {count:,}개")
    
    conn.close()

def view_detailed_news(news_id):
    """특정 뉴스 상세 조회"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT *
        FROM news_articles
        WHERE id = ?
    """, (news_id,))
    
    news = cursor.fetchone()
    
    if not news:
        print(f"ID {news_id}인 뉴스를 찾을 수 없습니다.")
    else:
        columns = [desc[0] for desc in cursor.description]
        print("=" * 80)
        print(f"📰 뉴스 상세 정보 (ID: {news_id})")
        print("=" * 80)
        
        for col, val in zip(columns, news):
            print(f"{col}: {val}")
    
    conn.close()

def export_to_csv(filename='nicl_news_export.csv'):
    """CSV로 내보내기"""
    conn = connect_db()
    if not conn:
        return
    
    import csv
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, original_link, description, pub_date, keyword, category, created_at
        FROM news_articles
        WHERE is_duplicate = 0
        ORDER BY created_at DESC
    """)
    
    news_list = cursor.fetchall()
    
    if not news_list:
        print("내보낼 뉴스가 없습니다.")
        return
    
    # CSV 파일 생성
    csv_path = os.path.join(project_root, filename)
    
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # 헤더
        writer.writerow(['ID', '제목', '링크', '요약', '발행일', '키워드', '카테고리', '수집일'])
        
        # 데이터
        writer.writerows(news_list)
    
    print(f"✅ CSV 파일로 내보내기 완료: {csv_path}")
    print(f"총 {len(news_list):,}개의 뉴스 데이터")
    
    conn.close()

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NICL 데이터 조회')
    parser.add_argument('--all', '-a', action='store_true', help='모든 뉴스 조회')
    parser.add_argument('--limit', '-l', type=int, default=10, help='조회할 뉴스 개수')
    parser.add_argument('--keyword', '-k', type=str, help='키워드별 뉴스 조회')
    parser.add_argument('--stats', '-s', action='store_true', help='통계 조회')
    parser.add_argument('--detail', '-d', type=int, help='뉴스 상세 조회 (ID)')
    parser.add_argument('--export', '-e', action='store_true', help='CSV로 내보내기')
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        # 기본: 통계 보기
        view_statistics()
    elif args.all:
        view_all_news(args.limit)
    elif args.keyword:
        view_news_by_keyword(args.keyword)
    elif args.stats:
        view_statistics()
    elif args.detail:
        view_detailed_news(args.detail)
    elif args.export:
        export_to_csv()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
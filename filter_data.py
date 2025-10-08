"""
NICL 프로젝트 - 데이터 필터링 스크립트
제목에 키워드가 없는 뉴스를 정리
"""

import os
import sys
import sqlite3

# 프로젝트 루트 경로
project_root = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(project_root, 'data', 'nicl_news.db')

def filter_irrelevant_news(delete=False):
    """
    제목이나 요약에 키워드가 없는 뉴스 찾기 및 정리
    
    Args:
        delete: True이면 삭제, False이면 표시만
    """
    if not os.path.exists(DB_PATH):
        print(f"❌ 데이터베이스를 찾을 수 없습니다: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 모든 뉴스 조회
    cursor.execute("""
        SELECT id, title, description, keyword
        FROM news_articles
        WHERE is_duplicate = 0
    """)
    
    all_news = cursor.fetchall()
    irrelevant_news = []
    
    print("=" * 80)
    print("🔍 키워드 포함 여부 검사 중...")
    print("=" * 80)
    
    for news_id, title, description, keyword in all_news:
        title_lower = title.lower() if title else ""
        description_lower = description.lower() if description else ""
        keyword_lower = keyword.lower() if keyword else ""
        
        # 제목이나 요약에 키워드가 없으면
        if keyword_lower and keyword_lower not in title_lower and keyword_lower not in description_lower:
            irrelevant_news.append((news_id, title, keyword))
    
    print(f"\n📊 검사 결과:")
    print(f"전체 뉴스: {len(all_news)}개")
    print(f"키워드 미포함 뉴스: {len(irrelevant_news)}개")
    
    if irrelevant_news:
        print(f"\n❌ 키워드가 포함되지 않은 뉴스 목록:")
        print("-" * 80)
        
        for i, (news_id, title, keyword) in enumerate(irrelevant_news[:20], 1):
            print(f"{i}. [ID:{news_id}] {title[:60]}...")
            print(f"   키워드: '{keyword}'")
        
        if len(irrelevant_news) > 20:
            print(f"\n... 외 {len(irrelevant_news) - 20}개 더")
        
        if delete:
            # 삭제 확인
            print(f"\n⚠️  {len(irrelevant_news)}개의 뉴스를 삭제하시겠습니까?")
            confirm = input("삭제하려면 'YES' 입력: ")
            
            if confirm == "YES":
                # 삭제 실행
                ids_to_delete = [str(news_id) for news_id, _, _ in irrelevant_news]
                placeholders = ','.join(['?'] * len(ids_to_delete))
                
                cursor.execute(f"""
                    DELETE FROM news_articles
                    WHERE id IN ({placeholders})
                """, ids_to_delete)
                
                conn.commit()
                print(f"✅ {len(irrelevant_news)}개의 뉴스가 삭제되었습니다.")
            else:
                print("❌ 삭제가 취소되었습니다.")
        else:
            print("\n💡 삭제하려면 --delete 옵션을 추가하세요:")
            print("   python filter_data.py --delete")
    else:
        print("\n✅ 모든 뉴스가 키워드를 포함하고 있습니다!")
    
    conn.close()

def show_keyword_coverage():
    """키워드별 매칭률 통계"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 데이터베이스를 찾을 수 없습니다: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT keyword, COUNT(*) as total
        FROM news_articles
        WHERE is_duplicate = 0
        GROUP BY keyword
    """)
    
    keywords = cursor.fetchall()
    
    print("=" * 80)
    print("📊 키워드별 매칭 통계")
    print("=" * 80)
    
    for keyword, total in keywords:
        # 제목에 키워드 포함된 뉴스
        cursor.execute("""
            SELECT COUNT(*)
            FROM news_articles
            WHERE keyword = ? AND LOWER(title) LIKE ?
        """, (keyword, f'%{keyword.lower()}%'))
        
        title_match = cursor.fetchone()[0]
        
        # 요약에 키워드 포함된 뉴스
        cursor.execute("""
            SELECT COUNT(*)
            FROM news_articles
            WHERE keyword = ? AND LOWER(description) LIKE ?
        """, (keyword, f'%{keyword.lower()}%'))
        
        desc_match = cursor.fetchone()[0]
        
        # 둘 다 포함 안 된 뉴스
        not_match = total - max(title_match, desc_match)
        
        print(f"\n키워드: '{keyword}'")
        print(f"  총 뉴스: {total}개")
        print(f"  제목 매칭: {title_match}개 ({title_match/total*100:.1f}%)")
        print(f"  요약 매칭: {desc_match}개 ({desc_match/total*100:.1f}%)")
        print(f"  미매칭: {not_match}개 ({not_match/total*100:.1f}%)")
    
    conn.close()

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NICL 데이터 필터링')
    parser.add_argument('--delete', '-d', action='store_true', 
                       help='키워드 미포함 뉴스 삭제')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='키워드 매칭 통계')
    
    args = parser.parse_args()
    
    if args.stats:
        show_keyword_coverage()
    else:
        filter_irrelevant_news(delete=args.delete)

if __name__ == "__main__":
    main()
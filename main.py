"""
NICL 프로젝트 - 메인 실행 파일
News Information Collection & Library
"""

import os
import sys
import argparse
from datetime import datetime

# 디버그용 출력 (문제 해결 시 제거 가능)
print("=" * 60)
print("NICL 프로젝트 초기화 중...")
print("현재 작업 디렉토리:", os.getcwd())

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
print("프로젝트 루트:", project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print("✅ Python 경로에 프로젝트 루트 추가됨")

try:
    from src.news_collector import NewsCollector
    print("✅ NewsCollector 모듈 로드 성공")
except ImportError as e:
    print(f"❌ NewsCollector 모듈 로드 실패: {e}")
    print("\n문제 해결 방법:")
    print("1. 모든 파일이 올바른 위치에 있는지 확인")
    print("2. src 폴더 내 __init__.py 파일들 확인")
    print("3. pip install -r requirements.txt 실행")
    sys.exit(1)

print("=" * 60)
print()

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='NICL 뉴스 수집 시스템')
    parser.add_argument('--keyword', '-k', type=str, help='검색할 키워드')
    parser.add_argument('--keywords', '-ks', nargs='+', help='여러 키워드 (공백으로 구분)')
    parser.add_argument('--count', '-c', type=int, default=50, help='수집할 뉴스 개수 (기본: 50)')
    parser.add_argument('--category', type=str, help='뉴스 카테고리')
    parser.add_argument('--trending', '-t', action='store_true', help='인기 뉴스 수집')
    parser.add_argument('--stats', '-s', action='store_true', help='데이터베이스 통계 확인')
    parser.add_argument('--validate', '-v', action='store_true', help='설정 검증')
    
    args = parser.parse_args()
    
    # 인수가 없으면 도움말 출력
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # 뉴스 수집기 초기화
    try:
        with NewsCollector() as collector:
            print("=" * 60)
            print("NICL (News Information Collection & Library)")
            print("네이버 뉴스 API 기반 뉴스 수집 시스템")
            print("=" * 60)
            print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # 설정 검증
            if args.validate:
                print("🔍 설정 검증 중...")
                if collector.validate_setup():
                    print("✅ 모든 설정이 올바르게 구성되었습니다.")
                else:
                    print("❌ 설정에 문제가 있습니다. 로그를 확인해주세요.")
                return
            
            # 데이터베이스 통계
            if args.stats:
                print("📊 데이터베이스 통계")
                print("-" * 30)
                stats = collector.get_database_statistics()
                
                print(f"총 뉴스 기사: {stats.get('total_articles', 0):,}개")
                print(f"고유 뉴스: {stats.get('unique_articles', 0):,}개")
                print(f"중복 뉴스: {stats.get('total_duplicates', 0):,}개")
                print()
                return
            
            # 인기 뉴스 수집
            if args.trending:
                print("🔥 인기 뉴스 수집 중...")
                news_list = collector.get_trending_news(limit=args.count)
                
                if news_list:
                    print(f"✅ {len(news_list)}개의 인기 뉴스를 수집했습니다.")
                    for i, news in enumerate(news_list[:5], 1):
                        print(f"{i}. {news.title[:50]}...")
                else:
                    print("❌ 인기 뉴스를 수집하지 못했습니다.")
                return
            
            # 단일 키워드 수집
            if args.keyword:
                print(f"🔍 키워드 '{args.keyword}' 뉴스 수집 중...")
                print(f"수집 목표: {args.count}개")
                if args.category:
                    print(f"카테고리: {args.category}")
                print("-" * 40)
                
                result = collector.collect_news_by_keyword(
                    keyword=args.keyword,
                    max_count=args.count,
                    category=args.category
                )
                
                if result['success']:
                    print("✅ 수집 완료!")
                    print(f"📰 총 수집: {result['collected']}개")
                    print(f"💾 저장됨: {result['saved']}개")
                    print(f"🔄 중복: {result['duplicates']}개")
                    print(f"⏱️ 실행 시간: {result['execution_time']:.2f}초")
                else:
                    print("❌ 수집 실패!")
                    if 'error' in result:
                        print(f"오류: {result['error']}")
                
                return
            
            # 다중 키워드 수집
            if args.keywords:
                print(f"🔍 다중 키워드 뉴스 수집 중...")
                print(f"키워드: {', '.join(args.keywords)}")
                print(f"키워드당 수집 목표: {args.count}개")
                print("-" * 40)
                
                results = collector.collect_news_by_keywords(
                    keywords=args.keywords,
                    max_count_per_keyword=args.count
                )
                
                # 결과 요약
                total_collected = sum(r['collected'] for r in results)
                total_saved = sum(r['saved'] for r in results)
                total_duplicates = sum(r['duplicates'] for r in results)
                success_count = sum(1 for r in results if r['success'])
                
                print("\n📊 수집 결과 요약")
                print("-" * 30)
                print(f"처리된 키워드: {len(args.keywords)}개")
                print(f"성공한 키워드: {success_count}개")
                print(f"총 수집: {total_collected}개")
                print(f"총 저장: {total_saved}개")
                print(f"총 중복: {total_duplicates}개")
                
                print("\n📝 키워드별 상세 결과")
                print("-" * 40)
                for result in results:
                    status = "✅" if result['success'] else "❌"
                    print(f"{status} {result['keyword']}: "
                          f"수집={result['collected']}, 저장={result['saved']}, "
                          f"중복={result['duplicates']}")
                
                return
            
            # 기본 도움말
            print("사용 예시:")
            print("python main.py --keyword '인공지능' --count 100")
            print("python main.py --keywords '정치' '경제' '사회' --count 50")
            print("python main.py --trending --count 30")
            print("python main.py --stats")
            print("python main.py --validate")
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
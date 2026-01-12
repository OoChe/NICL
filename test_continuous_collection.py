"""
NICL 1시간 연속 최신 뉴스 수집 테스트 스크립트
기존 main.py를 수정하지 않고 독립적으로 실행되는 테스트 프로그램
키워드 없이 최신 뉴스만 수집 (API + 웹 크롤링)
"""

import os
import sys
import time
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.news_collector import NewsCollector

def continuous_collection(duration_hours=1):
    """
    지정된 시간 동안 지속적으로 최신 뉴스 수집 (키워드 없음)

    전략: 첫 사이클 대량 수집 + 이후 5분 간격 증분 수집
    - 1차 사이클: 200개 대량 수집 (즉시 실행)
    - 2차 이후: 50개 증분 수집 (5분 간격)

    Args:
        duration_hours: 수집 지속 시간 (시간 단위)
    """
    print("=" * 60)
    print("NICL 연속 최신 뉴스 수집 테스트 (최적화 전략)")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"수집 지속 시간: {duration_hours}시간")
    print(f"수집 방식: 네이버 API + 웹 크롤링 (최신 뉴스)")
    print(f"수집 전략:")
    print(f"  - 1차 사이클: 200개 대량 수집 (즉시)")
    print(f"  - 2차 이후: 50개 증분 수집 (5분 간격)")
    print("=" * 60)
    print()

    start_time = time.time()
    end_time = start_time + (duration_hours * 3600)  # 1시간 = 3600초

    cycle_count = 0
    total_collected = 0
    total_saved = 0
    total_duplicates = 0
    total_api_count = 0
    total_crawl_count = 0

    try:
        with NewsCollector() as collector:
            while time.time() < end_time:
                cycle_count += 1
                cycle_start = time.time()

                elapsed_minutes = (time.time() - start_time) / 60
                remaining_minutes = (end_time - time.time()) / 60

                # 사이클별 수집 전략 결정
                if cycle_count == 1:
                    max_count = 200  # 1차: 대량 수집
                    wait_before = 0  # 즉시 실행
                    strategy = "대량 수집"
                else:
                    max_count = 50   # 2차 이후: 증분 수집
                    wait_before = 300  # 5분 대기
                    strategy = "증분 수집"

                print(f"\n{'='*60}")
                print(f"🔄 수집 사이클 #{cycle_count} ({strategy})")
                print(f"⏱️  경과 시간: {elapsed_minutes:.1f}분 | 남은 시간: {remaining_minutes:.1f}분")
                print(f"📊 목표 수집량: {max_count}개")
                print(f"{'='*60}")

                # 대기 시간 처리 (1차 사이클 제외)
                if cycle_count > 1:
                    print(f"\n⏳ 다음 사이클까지 {wait_before}초 ({wait_before//60}분) 대기...")
                    time.sleep(wait_before)

                # 최신 뉴스 수집 (키워드 없음, API + 크롤링)
                print(f"\n📰 최신 뉴스 수집 중...")
                print("-" * 40)

                result = collector.collect_latest_news(
                    max_count=max_count,  # 사이클별 차등 수집
                    use_api=True,
                    use_crawling=True
                )

                if result['success']:
                    total_collected += result['collected']
                    total_saved += result['saved']
                    total_duplicates += result['duplicates']
                    total_api_count += result.get('api_count', 0)
                    total_crawl_count += result.get('crawl_count', 0)

                    print(f"✅ 수집: {result['collected']}개 "
                          f"(API: {result.get('api_count', 0)}, "
                          f"크롤링: {result.get('crawl_count', 0)})")
                    print(f"💾 저장: {result['saved']}개 | 🔄 중복: {result['duplicates']}개")
                else:
                    print(f"❌ 수집 실패: {result.get('error', '알 수 없는 오류')}")

                # 사이클 통계
                cycle_time = time.time() - cycle_start
                print(f"\n📊 사이클 #{cycle_count} 완료 (소요 시간: {cycle_time:.1f}초)")
                print(f"📈 누적 통계:")
                print(f"   총 수집: {total_collected}개 (API: {total_api_count}, 크롤링: {total_crawl_count})")
                print(f"   총 저장: {total_saved}개")
                print(f"   총 중복: {total_duplicates}개")

                # 남은 시간 확인 및 다음 사이클 판단
                if time.time() >= end_time:
                    break

                # 다음 사이클이 5분 이내에 시작되지 않으면 종료
                if cycle_count > 1:  # 2차 이후만 체크
                    remaining_time = end_time - time.time()
                    if remaining_time < 300:  # 5분 미만 남음
                        print(f"\n⏹️  남은 시간({remaining_time:.1f}초)이 다음 사이클 대기 시간(300초)보다 짧아 종료합니다.")
                        break

            # 최종 통계
            total_time = time.time() - start_time

            print("\n" + "=" * 60)
            print("🎉 연속 최신 뉴스 수집 완료!")
            print("=" * 60)
            print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"총 실행 시간: {total_time/60:.1f}분 ({total_time:.0f}초)")
            print(f"총 사이클 수: {cycle_count}회")
            print(f"\n📊 최종 통계:")
            print(f"  총 수집: {total_collected}개")
            print(f"    ├─ API: {total_api_count}개")
            print(f"    └─ 크롤링: {total_crawl_count}개")
            print(f"  총 저장: {total_saved}개")
            print(f"  총 중복: {total_duplicates}개")
            print(f"  중복률: {(total_duplicates/total_collected*100):.1f}%" if total_collected > 0 else "  중복률: 0.0%")

            # 데이터베이스 통계
            db_stats = collector.get_database_statistics()
            print(f"\n💾 데이터베이스 현황:")
            print(f"  전체 기사: {db_stats.get('total_articles', 0):,}개")
            print(f"  고유 기사: {db_stats.get('unique_articles', 0):,}개")
            print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
        total_time = time.time() - start_time
        print(f"실행 시간: {total_time/60:.1f}분")
        print(f"수집 사이클: {cycle_count}회")
        print(f"누적 통계:")
        print(f"  수집={total_collected}개 (API:{total_api_count}, 크롤링:{total_crawl_count})")
        print(f"  저장={total_saved}개, 중복={total_duplicates}개")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 NICL 연속 최신 뉴스 수집 시작...\n")
    # 연속 수집 테스트 시간
    continuous_collection(duration_hours=3)
    print("\n✅ 프로그램 종료\n")

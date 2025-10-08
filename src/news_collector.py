"""
NICL 프로젝트 - 메인 뉴스 수집기
네이버 API와 데이터베이스를 연동한 뉴스 수집 메인 클래스
"""

import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.api.naver_news import NaverNewsAPI, NaverNewsSearchParams
from src.database.manager import DatabaseManager
from src.utils.config import config

class NewsCollector:
    """NICL 메인 뉴스 수집기"""
    
    def __init__(self):
        """뉴스 수집기 초기화"""
        # 로깅 설정
        self.logger = config.setup_logging()
        
        # 설정 로드
        self.naver_config = config.naver_api
        self.db_config = config.database
        
        # API 클라이언트 초기화
        self.naver_api = NaverNewsAPI(
            client_id=self.naver_config.client_id,
            client_secret=self.naver_config.client_secret,
            base_url=self.naver_config.base_url
        )
        
        # 데이터베이스 매니저 초기화
        self.db_manager = DatabaseManager(
            db_path=config.get_full_path(self.db_config.path)
        )
        
        self.logger.info("NICL 뉴스 수집기 초기화 완료")
    
    def collect_news_by_keyword(self, keyword: str, max_count: int = 100, 
                               category: str = None) -> Dict[str, Any]:
        """
        키워드로 뉴스 수집 및 데이터베이스 저장
        
        Args:
            keyword: 검색 키워드
            max_count: 수집할 최대 뉴스 개수
            category: 뉴스 카테고리
            
        Returns:
            수집 결과 통계
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"뉴스 수집 시작: 키워드='{keyword}', 최대={max_count}개")
            
            # 네이버 API로 뉴스 수집
            news_data = self.naver_api.collect_news_by_keyword(
                keyword=keyword,
                max_count=max_count,
                category=category
            )
            
            if not news_data:
                self.logger.warning(f"키워드 '{keyword}'로 수집된 뉴스가 없습니다.")
                return {
                    'success': False,
                    'keyword': keyword,
                    'collected': 0,
                    'saved': 0,
                    'duplicates': 0,
                    'execution_time': time.time() - start_time
                }
            
            # 데이터베이스에 배치 저장
            save_result = self.db_manager.save_news_batch(news_data)
            
            execution_time = time.time() - start_time
            
            # 수집 로그 저장
            log_data = {
                'source': 'naver_api',
                'keyword': keyword,
                'total_collected': save_result['saved'],
                'duplicates_found': save_result['duplicates'],
                'success': True,
                'execution_time': int(execution_time)
            }
            self.db_manager.log_collection(log_data)
            
            result = {
                'success': True,
                'keyword': keyword,
                'collected': len(news_data),
                'saved': save_result['saved'],
                'duplicates': save_result['duplicates'],
                'execution_time': execution_time
            }
            
            self.logger.info(
                f"뉴스 수집 완료: 키워드='{keyword}', "
                f"수집={result['collected']}개, 저장={result['saved']}개, "
                f"중복={result['duplicates']}개, 시간={execution_time:.2f}초"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"뉴스 수집 중 오류 발생: {e}")
            
            # 에러 로그 저장
            log_data = {
                'source': 'naver_api',
                'keyword': keyword,
                'total_collected': 0,
                'duplicates_found': 0,
                'success': False,
                'error_message': str(e),
                'execution_time': int(execution_time)
            }
            self.db_manager.log_collection(log_data)
            
            return {
                'success': False,
                'keyword': keyword,
                'collected': 0,
                'saved': 0,
                'duplicates': 0,
                'error': str(e),
                'execution_time': execution_time
            }
    
    def collect_news_by_keywords(self, keywords: List[str], max_count_per_keyword: int = 50) -> List[Dict[str, Any]]:
        """
        여러 키워드로 뉴스 수집
        
        Args:
            keywords: 검색 키워드 리스트
            max_count_per_keyword: 키워드당 최대 수집 개수
            
        Returns:
            키워드별 수집 결과 리스트
        """
        results = []
        total_start_time = time.time()
        
        self.logger.info(f"다중 키워드 뉴스 수집 시작: {len(keywords)}개 키워드")
        
        for i, keyword in enumerate(keywords, 1):
            self.logger.info(f"진행률: {i}/{len(keywords)} - '{keyword}' 수집 중...")
            
            result = self.collect_news_by_keyword(
                keyword=keyword,
                max_count=max_count_per_keyword
            )
            results.append(result)
            
            # API 호출 간격 조절
            if i < len(keywords):
                time.sleep(self.naver_config.request_delay)
        
        total_time = time.time() - total_start_time
        
        # 전체 통계 계산
        total_collected = sum(r['collected'] for r in results)
        total_saved = sum(r['saved'] for r in results)
        total_duplicates = sum(r['duplicates'] for r in results)
        
        self.logger.info(
            f"다중 키워드 수집 완료: {len(keywords)}개 키워드, "
            f"총 수집={total_collected}개, 저장={total_saved}개, "
            f"중복={total_duplicates}개, 총 시간={total_time:.2f}초"
        )
        
        return results
    
    def get_trending_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        인기 키워드로 최신 뉴스 수집
        
        Args:
            limit: 수집할 뉴스 개수
            
        Returns:
            최신 뉴스 리스트
        """
        trending_keywords = self.naver_api.get_trending_keywords()
        
        if not trending_keywords:
            self.logger.warning("인기 키워드를 가져올 수 없습니다.")
            return []
        
        # 첫 번째 인기 키워드로 뉴스 수집
        keyword = trending_keywords[0]
        result = self.collect_news_by_keyword(keyword, max_count=limit)
        
        if result['success']:
            return self.db_manager.get_recent_news(limit)
        else:
            return []
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """데이터베이스 통계 조회"""
        return self.db_manager.get_statistics()
    
    def validate_setup(self) -> bool:
        """설정 및 연결 상태 검증"""
        try:
            # API 자격증명 검증
            if not self.naver_api.validate_api_credentials():
                self.logger.error("네이버 API 자격증명이 유효하지 않습니다.")
                return False
            
            # 데이터베이스 연결 확인
            stats = self.db_manager.get_statistics()
            if stats is None:
                self.logger.error("데이터베이스 연결에 실패했습니다.")
                return False
            
            self.logger.info("NICL 설정 검증 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"설정 검증 중 오류: {e}")
            return False
    
    def close(self):
        """리소스 정리"""
        try:
            if hasattr(self, 'naver_api'):
                self.naver_api.close()
            
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
            
            self.logger.info("NICL 뉴스 수집기 리소스 정리 완료")
            
        except Exception as e:
            self.logger.error(f"리소스 정리 중 오류: {e}")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()
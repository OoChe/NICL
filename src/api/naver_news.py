"""
NICL 프로젝트 - 네이버 뉴스 API 클라이언트
네이버 뉴스 검색 API를 통한 뉴스 수집
"""

import os
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re
from urllib.parse import quote

@dataclass
class NaverNewsSearchParams:
    """네이버 뉴스 검색 파라미터"""
    query: str                    # 검색어
    display: int = 10            # 검색 결과 개수 (1~100)
    start: int = 1               # 검색 시작 위치 (1~1000)
    sort: str = 'date'           # 정렬 방식 (date:날짜순, sim:정확도순)

class NaverNewsAPI:
    """네이버 뉴스 API 클라이언트"""
    
    def __init__(self, client_id: str, client_secret: str, base_url: str = None):
        """
        네이버 뉴스 API 클라이언트 초기화
        
        Args:
            client_id: 네이버 API 클라이언트 ID
            client_secret: 네이버 API 클라이언트 시크릿
            base_url: API 기본 URL
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url or "https://openapi.naver.com/v1/search/news.json"
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # 헤더 설정
        self.session.headers.update({
            'X-Naver-Client-Id': self.client_id,
            'X-Naver-Client-Secret': self.client_secret,
            'User-Agent': 'NICL-NewsCollector/1.0'
        })
        
        self.logger.info("네이버 뉴스 API 클라이언트 초기화 완료")
    
    def search_news(self, params: NaverNewsSearchParams) -> Dict[str, Any]:
        """
        네이버 뉴스 검색
        
        Args:
            params: 검색 파라미터
            
        Returns:
            API 응답 데이터
        """
        try:
            # 검색어 URL 인코딩
            encoded_query = quote(params.query)
            
            # 요청 파라미터 구성
            request_params = {
                'query': encoded_query,
                'display': min(params.display, 100),  # 최대 100개
                'start': max(1, min(params.start, 1000)),  # 1~1000
                'sort': params.sort
            }
            
            self.logger.info(f"네이버 뉴스 검색 시작: '{params.query}' (display={params.display}, start={params.start})")
            
            # API 요청
            response = self.session.get(self.base_url, params=request_params, timeout=30)
            response.raise_for_status()
            
            # JSON 응답 파싱
            data = response.json()
            
            self.logger.info(f"검색 완료: {data.get('total', 0)}개 중 {len(data.get('items', []))}개 수집")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"네이버 API 요청 실패: {e}")
            return {'items': [], 'total': 0, 'start': 1, 'display': 0}
        except Exception as e:
            self.logger.error(f"네이버 뉴스 검색 중 오류: {e}")
            return {'items': [], 'total': 0, 'start': 1, 'display': 0}
    
    def collect_news_by_keyword(self, keyword: str, max_count: int = 100, 
                               category: str = None) -> List[Dict[str, Any]]:
        """
        키워드로 뉴스 수집
        
        Args:
            keyword: 검색 키워드
            max_count: 수집할 최대 뉴스 개수
            category: 뉴스 카테고리 (선택)
            
        Returns:
            수집된 뉴스 데이터 리스트
        """
        collected_news = []
        total_collected = 0
        current_start = 1
        
        self.logger.info(f"키워드 '{keyword}' 뉴스 수집 시작 (최대 {max_count}개)")
        
        while total_collected < max_count:
            # 한 번에 가져올 개수 계산
            display_count = min(100, max_count - total_collected)
            
            # 검색 파라미터 설정
            params = NaverNewsSearchParams(
                query=keyword,
                display=display_count,
                start=current_start,
                sort='date'
            )
            
            # 뉴스 검색
            result = self.search_news(params)
            items = result.get('items', [])
            
            if not items:
                self.logger.info("더 이상 검색 결과가 없습니다.")
                break
            
            # 뉴스 데이터 처리
            for item in items:
                processed_news = self._process_news_item(item, keyword, category)
                if processed_news:
                    collected_news.append(processed_news)
                    total_collected += 1
            
            # 다음 페이지 준비
            current_start += display_count
            
            # API 호출 제한 고려 (1초 대기)
            time.sleep(1.0)
            
            # 검색 한계 확인 (네이버 API는 1000개까지만 지원)
            if current_start > 1000:
                self.logger.warning("네이버 API 검색 한계에 도달했습니다 (1000개)")
                break
        
        self.logger.info(f"키워드 '{keyword}' 수집 완료: {len(collected_news)}개")
        return collected_news
    
    def _process_news_item(self, item: Dict[str, Any], keyword: str, 
                          category: str = None) -> Optional[Dict[str, Any]]:
        """
        네이버 API 응답 아이템을 내부 데이터 형식으로 변환
        제목 또는 본문(description)에 키워드가 포함된 뉴스만 반환
        
        Args:
            item: 네이버 API 응답 아이템
            keyword: 검색 키워드
            category: 카테고리
            
        Returns:
            처리된 뉴스 데이터 또는 None
        """
        try:
            # HTML 태그 제거
            title = self._clean_html_tags(item.get('title', ''))
            description = self._clean_html_tags(item.get('description', ''))
            
            # 빈 제목 필터링
            if not title.strip():
                self.logger.debug("빈 제목으로 필터링됨")
                return None
            
            # 키워드 필터링: 제목 또는 본문에 키워드가 있어야 함
            if keyword:
                keyword_lower = keyword.lower()
                title_lower = title.lower()
                description_lower = description.lower() if description else ""
                
                # 제목과 본문 모두에 키워드가 없으면 필터링
                if keyword_lower not in title_lower and keyword_lower not in description_lower:
                    self.logger.debug(f"키워드 미포함으로 필터링: {title[:50]}...")
                    return None
                
                self.logger.debug(f"키워드 매칭 성공: {title[:50]}...")
            
            return {
                'title': title,
                'original_link': item.get('originallink', ''),
                'link': item.get('link', ''),
                'description': description,
                'pub_date': item.get('pubDate', ''),
                'source': 'naver_api',
                'keyword': keyword,
                'category': category or 'general'
            }
            
        except Exception as e:
            self.logger.error(f"뉴스 아이템 처리 중 오류: {e}")
            return None
    
    def _clean_html_tags(self, text: str) -> str:
        """HTML 태그 및 특수문자 정리"""
        if not text:
            return ""
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # HTML 엔티티 변환
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_trending_keywords(self) -> List[str]:
        """
        인기 검색어 추천 (기본 키워드 리스트 반환)
        실제 구현 시에는 별도 API나 크롤링으로 대체 가능
        """
        default_keywords = [
            '정치', '경제', '사회', '문화', '국제', '스포츠',
            'IT', '과학', '건강', '교육', '환경', '부동산'
        ]
        
        return default_keywords
    
    def validate_api_credentials(self) -> bool:
        """API 자격증명 유효성 검사"""
        try:
            params = NaverNewsSearchParams(query='테스트', display=1)
            result = self.search_news(params)
            return 'items' in result
            
        except Exception as e:
            self.logger.error(f"API 자격증명 검증 실패: {e}")
            return False
    
    def close(self):
        """세션 종료"""
        if self.session:
            self.session.close()
            self.logger.info("네이버 API 세션 종료")
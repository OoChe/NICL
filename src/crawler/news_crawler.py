"""
NICL 프로젝트 - 웹 크롤링 모듈
구글 뉴스를 크롤링하여 뉴스 수집
"""

import time
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

class NewsWebCrawler:
    """구글 뉴스 웹 크롤러"""
    
    def __init__(self, delay: float = 2.0):
        """
        웹 크롤러 초기화
        
        Args:
            delay: 요청 간 대기 시간 (초)
        """
        self.delay = delay
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # User-Agent 설정
        try:
            ua = UserAgent()
            self.session.headers.update({
                'User-Agent': ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            })
        except Exception as e:
            self.logger.warning(f"UserAgent 설정 실패, 기본값 사용: {e}")
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
        
        self.logger.info("구글 뉴스 웹 크롤러 초기화 완료")
    
    def collect_latest_news(self, max_count: int = 30, language: str = 'ko') -> List[Dict[str, Any]]:
        """
        구글 뉴스 메인 페이지에서 최신 뉴스 수집

        Args:
            max_count: 수집할 최대 뉴스 개수
            language: 언어 코드 (ko: 한국어, en: 영어)

        Returns:
            수집된 뉴스 데이터 리스트
        """
        collected_news = []

        # 구글 뉴스 메인 페이지 URL (한국)
        base_url = "https://news.google.com/"

        self.logger.info(f"구글 뉴스 최신 뉴스 크롤링 시작: 목표={max_count}개")

        try:
            params = {
                'hl': language,
                'gl': 'KR',
                'ceid': 'KR:ko'
            }

            self.logger.info("구글 뉴스 메인 페이지 접속 중...")

            response = self.session.get(base_url, params=params, timeout=30)
            response.raise_for_status()

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'lxml')

            # 뉴스 아이템 추출 (키워드 필터링 없음)
            news_items = self._parse_google_news_results(soup, keyword=None)

            if not news_items:
                self.logger.warning("구글 뉴스에서 최신 뉴스를 찾을 수 없습니다.")
            else:
                collected_news.extend(news_items[:max_count])
                self.logger.info(f"구글 뉴스 최신 뉴스 수집 완료: {len(collected_news)}개")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"구글 뉴스 크롤링 실패: {e}")
        except Exception as e:
            self.logger.error(f"구글 뉴스 처리 중 오류: {e}")

        result = collected_news[:max_count]
        self.logger.info(f"크롤링 완료: 총 {len(result)}개 수집")

        return result

    def search_naver_news(self, keyword: str, max_count: int = 30) -> List[Dict[str, Any]]:
        """
        구글 뉴스 검색 (메서드명은 호환성을 위해 유지)

        Args:
            keyword: 검색 키워드
            max_count: 수집할 최대 뉴스 개수

        Returns:
            수집된 뉴스 데이터 리스트
        """
        return self.search_google_news(keyword, max_count)
    
    def search_google_news(self, keyword: str, max_count: int = 30, language: str = 'ko') -> List[Dict[str, Any]]:
        """
        구글 뉴스 검색 결과 크롤링
        
        Args:
            keyword: 검색 키워드
            max_count: 수집할 최대 뉴스 개수
            language: 언어 코드 (ko: 한국어, en: 영어)
            
        Returns:
            수집된 뉴스 데이터 리스트
        """
        collected_news = []
        
        # 구글 뉴스 검색 URL
        base_url = "https://news.google.com/search"
        
        self.logger.info(f"구글 뉴스 크롤링 시작: 키워드='{keyword}', 목표={max_count}개")
        
        try:
            # 한국 뉴스로 제한
            params = {
                'q': keyword,
                'hl': language,
                'gl': 'KR',
                'ceid': 'KR:ko'
            }
            
            self.logger.info(f"구글 뉴스 검색 중... (키워드: {keyword})")
            
            response = self.session.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 뉴스 아이템 추출
            news_items = self._parse_google_news_results(soup, keyword)
            
            if not news_items:
                self.logger.warning(f"구글 뉴스에서 '{keyword}' 검색 결과를 찾을 수 없습니다.")
            else:
                collected_news.extend(news_items[:max_count])
                self.logger.info(f"구글 뉴스 수집 완료: {len(collected_news)}개")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"구글 뉴스 크롤링 실패: {e}")
        except Exception as e:
            self.logger.error(f"구글 뉴스 처리 중 오류: {e}")
        
        result = collected_news[:max_count]
        self.logger.info(f"크롤링 완료: 총 {len(result)}개 수집")
        
        return result
    
    def _parse_google_news_results(self, soup: BeautifulSoup, keyword: str) -> List[Dict[str, Any]]:
        """
        구글 뉴스 검색 결과에서 뉴스 데이터 추출

        Args:
            soup: BeautifulSoup 객체
            keyword: 검색 키워드

        Returns:
            뉴스 데이터 리스트
        """
        news_list = []

        # 구글 뉴스 아티클 선택자 (여러 선택자 시도)
        article_selectors = [
            'article',                    # 표준 article 태그
            'div.xrnccd',                 # 구글 뉴스 카드
            'c-wiz > div > article',      # 중첩된 article
            'div[jsname]',                # JS 컴포넌트
        ]

        articles = []
        for selector in article_selectors:
            articles = soup.select(selector)
            if articles:
                self.logger.info(f"선택자 '{selector}'로 {len(articles)}개 발견")
                break

        if not articles:
            # 대체 방법: 구글 뉴스 링크만 찾기
            self.logger.warning("article 선택자로 뉴스를 찾지 못했습니다. 링크 기반 추출 시도...")
            all_links = soup.select('a[href*="./articles/"]')

            if not all_links:
                all_links = soup.select('a')

            self.logger.info(f"총 {len(all_links)}개의 링크 발견")

            seen_titles = set()
            for link in all_links:
                try:
                    href = link.get('href', '')
                    if not href or not ('./articles/' in href or 'articles/' in href):
                        continue

                    title = link.get_text(strip=True)
                    if not title or len(title) < 10 or title in seen_titles:
                        continue

                    # 키워드 필터링 (키워드가 있을 때만)
                    if keyword and keyword.lower() not in title.lower():
                        continue

                    seen_titles.add(title)

                    # 링크 정규화
                    if href.startswith('./'):
                        href = 'https://news.google.com' + href[1:]
                    elif not href.startswith('http'):
                        href = 'https://news.google.com' + href

                    news_list.append({
                        'title': title,
                        'original_link': href,
                        'link': href,
                        'description': '',
                        'pub_date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900'),
                        'source': 'google_crawling',
                        'keyword': keyword or 'latest',
                        'category': 'general',
                        'press': 'Google News'
                    })

                except Exception as e:
                    self.logger.debug(f"링크 처리 오류: {e}")
                    continue

            self.logger.info(f"링크 기반 추출로 {len(news_list)}개 수집")
            return news_list

        # article 태그로 추출
        for article in articles:
            try:
                news_data = self._extract_google_news_data(article, keyword)
                if news_data:
                    news_list.append(news_data)
            except Exception as e:
                self.logger.debug(f"뉴스 아이템 파싱 오류: {e}")
                continue

        return news_list
    
    def _extract_google_news_data(self, article, keyword: str) -> Optional[Dict[str, Any]]:
        """
        구글 뉴스 개별 아티클에서 데이터 추출

        Args:
            article: BeautifulSoup 아티클 요소
            keyword: 검색 키워드

        Returns:
            뉴스 데이터 딕셔너리
        """
        try:
            # 제목 및 링크 - 다양한 선택자 시도
            title_elem = None
            title_selectors = [
                'a.gPFEn',           # 2025년 구글 뉴스 선택자
                'a.JtKRv',           # 이전 선택자
                'a.DY5T1d',          # 또 다른 선택자
                'h3 a',              # h3 내부 링크
                'h4 a',              # h4 내부 링크
                'a[href*="./articles/"]',  # articles 링크
            ]

            for selector in title_selectors:
                title_elem = article.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    break

            if not title_elem:
                # 모든 링크 중에서 articles 링크 찾기
                all_links = article.select('a')
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if ('./articles/' in href or 'articles/' in href) and text and len(text) > 10:
                        title_elem = link
                        break

            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            # 구글 뉴스 링크 처리
            link = title_elem.get('href', '')
            if link.startswith('./'):
                link = 'https://news.google.com' + link[1:]
            elif not link.startswith('http'):
                link = 'https://news.google.com' + link

            # 빈 제목이나 링크 필터링
            if not title or not link or len(title) < 10:
                return None

            # 키워드 필터링 (키워드가 있을 때만, 제목에 포함되어야 함)
            if keyword and keyword.lower() not in title.lower():
                return None

            # 언론사 정보
            press = "Google News"
            press_selectors = [
                'div.vr1PYe',
                'span.vr1PYe',
                'a.wEwyrc',
                'div[data-n-tid]',   # 새로운 선택자
            ]

            for selector in press_selectors:
                press_elem = article.select_one(selector)
                if press_elem:
                    press_text = press_elem.get_text(strip=True)
                    if press_text:
                        press = press_text
                        break

            # 발행 시간
            time_elem = article.select_one('time')
            pub_date_text = time_elem.get('datetime', '') if time_elem else ''

            if not pub_date_text:
                time_selectors = ['div.SVJrMe', 'span.SVJrMe', 'time', 'div.UOVeFe']
                for selector in time_selectors:
                    time_text_elem = article.select_one(selector)
                    if time_text_elem:
                        pub_date_text = time_text_elem.get_text(strip=True)
                        if pub_date_text:
                            break

            # 현재 시간을 기본값으로
            if not pub_date_text:
                pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900')
            else:
                pub_date = pub_date_text

            # 요약 (구글 뉴스는 요약이 제한적)
            desc_selectors = ['div.GI74Re', 'div.Rai5ob', 'div.xBbh9']
            description = ""

            for selector in desc_selectors:
                desc_elem = article.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if description:
                        break

            return {
                'title': title,
                'original_link': link,
                'link': link,
                'description': description,
                'pub_date': pub_date,
                'source': 'google_crawling',
                'keyword': keyword or 'latest',
                'category': 'general',
                'press': press
            }

        except Exception as e:
            self.logger.debug(f"구글 뉴스 데이터 추출 오류: {e}")
            return None
    
    def crawl_naver_news_main(self, section: str = 'politics', max_count: int = 20) -> List[Dict[str, Any]]:
        """
        구글 뉴스 토픽별 수집 (메서드명은 호환성을 위해 유지)
        
        Args:
            section: 뉴스 섹션
            max_count: 수집할 최대 뉴스 개수
            
        Returns:
            수집된 뉴스 데이터 리스트
        """
        # 섹션을 한글 키워드로 변환
        section_keywords = {
            'politics': '정치',
            'economy': '경제',
            'society': '사회',
            'culture': '문화',
            'world': '국제',
            'it': 'IT'
        }
        
        keyword = section_keywords.get(section, '뉴스')
        return self.search_google_news(keyword, max_count)
    
    def search_google_news_by_topic(self, topic: str = 'WORLD', max_count: int = 20) -> List[Dict[str, Any]]:
        """
        구글 뉴스 토픽별 크롤링
        
        Args:
            topic: 토픽 (WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH)
            max_count: 수집할 최대 뉴스 개수
            
        Returns:
            수집된 뉴스 데이터 리스트
        """
        collected_news = []
        
        # 구글 뉴스 토픽 URL
        topic_url = f"https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR%3Ako"
        
        # 토픽별 URL (한국 뉴스)
        topic_urls = {
            'WORLD': 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtdHZHZ0pMVWlnQVAB',
            'NATION': 'https://news.google.com/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRGs0TVRZM0VnSnJieWdBUAE',
            'BUSINESS': 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB',
            'TECHNOLOGY': 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtdHZHZ0pMVWlnQVAB',
            'ENTERTAINMENT': 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtdHZHZ0pMVWlnQVAB',
            'SPORTS': 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtdHZHZ0pMVWlnQVAB',
            'SCIENCE': 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtdHZHZ0pMVWlnQVAB',
            'HEALTH': 'https://news.google.com/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtdHZLQUFQAQ'
        }
        
        url = topic_urls.get(topic.upper(), topic_urls['WORLD'])
        
        self.logger.info(f"구글 뉴스 토픽 크롤링: {topic}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 뉴스 추출
            news_items = self._parse_google_news_results(soup, topic)
            
            collected_news.extend(news_items[:max_count])
            self.logger.info(f"토픽별 수집 완료: {len(collected_news)}개")
            
        except Exception as e:
            self.logger.error(f"토픽별 크롤링 실패: {e}")
        
        return collected_news
    
    def get_article_content(self, url: str) -> Optional[str]:
        """
        뉴스 기사 본문 추출 (선택적 기능)
        
        Args:
            url: 뉴스 기사 URL
            
        Returns:
            기사 본문 텍스트
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 일반적인 뉴스 본문 선택자
            content_selectors = [
                'article',
                'div.article-body',
                'div.article-content',
                'div.news-content',
                'div.story-body'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 스크립트 및 불필요한 태그 제거
                    for tag in content_elem.select('script, style, aside, nav'):
                        tag.decompose()
                    
                    return content_elem.get_text(strip=True)
            
            return None
            
        except Exception as e:
            self.logger.error(f"본문 추출 실패 ({url}): {e}")
            return None
    
    def close(self):
        """세션 종료"""
        if self.session:
            self.session.close()
            self.logger.info("웹 크롤러 세션 종료")
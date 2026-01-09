"""
NICL 프로젝트 - 데이터베이스 매니저
SQLite 데이터베이스 연결 및 관리
"""

import os
import logging
import time
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

from src.models.news import Base, NewsArticle, CollectionLog

class DatabaseManager:
    """NICL 프로젝트 데이터베이스 매니저"""
    
    def __init__(self, db_path: str):
        """
        데이터베이스 매니저 초기화
        
        Args:
            db_path: SQLite 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        self.logger = logging.getLogger(__name__)
        
        self._setup_database()
    
    def _setup_database(self):
        """데이터베이스 초기 설정"""
        try:
            # 데이터베이스 디렉토리 생성
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            # SQLite 엔진 생성
            self.engine = create_engine(
                f'sqlite:///{self.db_path}',
                echo=False,  # SQL 쿼리 로그 출력 여부
                pool_recycle=3600,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30  # 30초 타임아웃 (엣지 케이스 9)
                }
            )

            # 세션 팩토리 생성
            self.SessionLocal = sessionmaker(bind=self.engine)

            # 테이블 생성
            Base.metadata.create_all(bind=self.engine)

            self.logger.info(f"데이터베이스 연결 성공: {self.db_path}")

        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """데이터베이스 세션 컨텍스트 매니저"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"데이터베이스 세션 에러: {e}")
            raise
        finally:
            session.close()
    
    def save_news_article(self, article_data: Dict[str, Any]) -> Optional[NewsArticle]:
        """
        뉴스 기사 저장
        
        Args:
            article_data: 뉴스 기사 데이터 딕셔너리
            
        Returns:
            저장된 NewsArticle 객체 또는 None
        """
        try:
            with self.get_session() as session:
                # 중복 확인 (원본 링크 기준)
                existing = session.query(NewsArticle).filter_by(
                    original_link=article_data.get('original_link')
                ).first()
                
                if existing:
                    self.logger.debug(f"중복 뉴스 발견: {article_data.get('title', '')[:50]}")
                    existing.is_duplicate = True
                    session.commit()
                    return None
                
                # 새 뉴스 기사 생성
                article = NewsArticle(
                    title=article_data.get('title', ''),
                    original_link=article_data.get('original_link', ''),
                    link=article_data.get('link', ''),
                    description=article_data.get('description', ''),
                    pub_date=article_data.get('pub_date', ''),
                    source=article_data.get('source', 'naver_api'),
                    keyword=article_data.get('keyword', ''),
                    category=article_data.get('category', '')
                )
                
                session.add(article)
                session.flush()  # ID 생성을 위해 flush
                
                self.logger.debug(f"뉴스 저장 성공: {article.id}")
                return article
                
        except SQLAlchemyError as e:
            self.logger.error(f"뉴스 저장 실패: {e}")
            return None
    
    def save_news_batch(self, articles_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        뉴스 기사 배치 저장
        
        Args:
            articles_data: 뉴스 기사 데이터 리스트
            
        Returns:
            저장 결과 통계
        """
        saved_count = 0
        duplicate_count = 0
        
        try:
            with self.get_session() as session:
                for article_data in articles_data:
                    # 중복 확인
                    existing = session.query(NewsArticle).filter_by(
                        original_link=article_data.get('original_link')
                    ).first()
                    
                    if existing:
                        duplicate_count += 1
                        continue
                    
                    # 새 뉴스 기사 생성
                    article = NewsArticle(
                        title=article_data.get('title', ''),
                        original_link=article_data.get('original_link', ''),
                        link=article_data.get('link', ''),
                        description=article_data.get('description', ''),
                        pub_date=article_data.get('pub_date', ''),
                        source=article_data.get('source', 'naver_api'),
                        keyword=article_data.get('keyword', ''),
                        category=article_data.get('category', '')
                    )
                    
                    session.add(article)
                    saved_count += 1
                
                session.commit()
                
        except SQLAlchemyError as e:
            self.logger.error(f"배치 저장 실패: {e}")
            
        return {
            'saved': saved_count,
            'duplicates': duplicate_count,
            'total_processed': len(articles_data)
        }
    
    def get_recent_news(self, limit: int = 10) -> List[NewsArticle]:
        """최근 뉴스 조회"""
        try:
            with self.get_session() as session:
                return session.query(NewsArticle)\
                    .order_by(desc(NewsArticle.created_at))\
                    .limit(limit)\
                    .all()
        except SQLAlchemyError as e:
            self.logger.error(f"뉴스 조회 실패: {e}")
            return []
    
    def log_collection(self, log_data: Dict[str, Any]) -> None:
        """수집 로그 저장"""
        try:
            with self.get_session() as session:
                log_entry = CollectionLog(
                    source=log_data.get('source', ''),
                    keyword=log_data.get('keyword', ''),
                    total_collected=log_data.get('total_collected', 0),
                    duplicates_found=log_data.get('duplicates_found', 0),
                    success=log_data.get('success', True),
                    error_message=log_data.get('error_message', ''),
                    execution_time=log_data.get('execution_time', 0)
                )
                
                session.add(log_entry)
                session.commit()
                
        except SQLAlchemyError as e:
            self.logger.error(f"로그 저장 실패: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """데이터베이스 통계 조회"""
        try:
            with self.get_session() as session:
                total_articles = session.query(NewsArticle).count()
                total_duplicates = session.query(NewsArticle)\
                    .filter(NewsArticle.is_duplicate == True).count()
                recent_collections = session.query(CollectionLog)\
                    .order_by(desc(CollectionLog.created_at))\
                    .limit(5)\
                    .all()
                
                return {
                    'total_articles': total_articles,
                    'total_duplicates': total_duplicates,
                    'unique_articles': total_articles - total_duplicates,
                    'recent_collections': [log.to_dict() if hasattr(log, 'to_dict') else str(log) for log in recent_collections]
                }
                
        except SQLAlchemyError as e:
            self.logger.error(f"통계 조회 실패: {e}")
            return {}
    
    def get_recent_links(self, minutes_ago: int = 2, max_records: int = 500) -> Set[str]:
        """
        최근 수집된 뉴스 링크 조회 (중복 방지용 캐시)

        Args:
            minutes_ago: 조회할 시간 범위 (분 단위, 기본 2분)
            max_records: 최대 레코드 수 제한 (메모리 보호, 엣지 케이스 4)

        Returns:
            original_link 집합 (Set)
        """
        max_retries = 3
        retry_delay = 1  # 초

        for attempt in range(max_retries):
            try:
                with self.get_session() as session:
                    cutoff_time = datetime.now() - timedelta(minutes=minutes_ago)

                    # 시간 기반 조회 (최근 N분)
                    articles = session.query(NewsArticle.original_link)\
                        .filter(NewsArticle.created_at >= cutoff_time)\
                        .limit(max_records)\
                        .all()

                    result = {article[0] for article in articles if article[0]}

                    self.logger.info(
                        f"캐시 조회 성공: {len(result)}개 링크 "
                        f"(최근 {minutes_ago}분, 최대 {max_records}개)"
                    )

                    return result

            except SQLAlchemyError as e:
                self.logger.warning(
                    f"캐시 조회 실패 (시도 {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    self.logger.error(
                        "캐시 조회 최종 실패 - 빈 캐시 반환 (중복 가능성 있음)"
                    )
                    return set()

            except Exception as e:
                self.logger.error(f"캐시 조회 중 예상치 못한 오류: {e}")
                return set()

        return set()

    def close(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("데이터베이스 연결 종료")
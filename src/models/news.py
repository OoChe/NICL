"""
NICL 프로젝트 - 뉴스 데이터 모델
SQLAlchemy를 사용한 뉴스 데이터 구조 정의
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

class NewsArticle(Base):
    """네이버 뉴스 API로 수집한 뉴스 기사 모델"""
    
    __tablename__ = 'news_articles'
    
    # 기본 필드
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 네이버 API 응답 데이터
    title = Column(String(500), nullable=False, comment='뉴스 제목')
    original_link = Column(Text, nullable=False, comment='원본 뉴스 링크')
    link = Column(Text, nullable=False, comment='네이버 뉴스 링크')
    description = Column(Text, comment='뉴스 요약')
    pub_date = Column(String(100), comment='발행일 (네이버 형식)')
    
    # 추가 메타데이터
    source = Column(String(100), default='naver_api', comment='수집 소스')
    keyword = Column(String(200), comment='검색 키워드')
    category = Column(String(50), comment='뉴스 카테고리')
    
    # 시스템 필드
    created_at = Column(DateTime, default=func.now(), comment='수집 시간')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_processed = Column(Boolean, default=False, comment='처리 완료 여부')
    is_duplicate = Column(Boolean, default=False, comment='중복 여부')
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"
    
    def to_dict(self) -> dict:
        """객체를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'title': self.title,
            'original_link': self.original_link,
            'link': self.link,
            'description': self.description,
            'pub_date': self.pub_date,
            'source': self.source,
            'keyword': self.keyword,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_processed': self.is_processed,
            'is_duplicate': self.is_duplicate
        }

class CollectionLog(Base):
    """뉴스 수집 로그 모델"""
    
    __tablename__ = 'collection_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, comment='수집 소스')
    keyword = Column(String(200), comment='검색 키워드')
    total_collected = Column(Integer, default=0, comment='수집된 뉴스 개수')
    duplicates_found = Column(Integer, default=0, comment='중복 발견 개수')
    success = Column(Boolean, default=True, comment='수집 성공 여부')
    error_message = Column(Text, comment='에러 메시지')
    execution_time = Column(Integer, comment='실행 시간 (초)')
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<CollectionLog(source='{self.source}', keyword='{self.keyword}', collected={self.total_collected})>"
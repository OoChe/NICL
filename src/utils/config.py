"""
NICL 프로젝트 - 설정 매니저
환경변수 및 설정 관리
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from dataclasses import dataclass

@dataclass
class NaverAPIConfig:
    """네이버 API 설정"""
    client_id: str
    client_secret: str
    base_url: str
    request_delay: float
    max_display: int

@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    path: str

@dataclass
class LogConfig:
    """로그 설정"""
    level: str
    file: str

class ConfigManager:
    """NICL 프로젝트 설정 매니저"""
    
    def __init__(self, env_file: str = '.env'):
        """
        설정 매니저 초기화
        
        Args:
            env_file: 환경변수 파일 경로
        """
        self.env_file = env_file
        self._load_environment()
        self._validate_config()
    
    def _load_environment(self):
        """환경변수 로드"""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            print(f"환경변수 파일 로드: {self.env_file}")
        else:
            print(f"환경변수 파일을 찾을 수 없습니다: {self.env_file}")
    
    def _validate_config(self):
        """필수 설정 검증"""
        required_vars = [
            'NAVER_CLIENT_ID',
            'NAVER_CLIENT_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
    
    @property
    def naver_api(self) -> NaverAPIConfig:
        """네이버 API 설정 반환"""
        return NaverAPIConfig(
            client_id=os.getenv('NAVER_CLIENT_ID'),
            client_secret=os.getenv('NAVER_CLIENT_SECRET'),
            base_url=os.getenv('NAVER_API_BASE_URL', 'https://openapi.naver.com/v1/search/news.json'),
            request_delay=float(os.getenv('REQUEST_DELAY', '1.0')),
            max_display=int(os.getenv('MAX_DISPLAY', '100'))
        )
    
    @property
    def database(self) -> DatabaseConfig:
        """데이터베이스 설정 반환"""
        return DatabaseConfig(
            path=os.getenv('DATABASE_PATH', 'data/nicl_news.db')
        )
    
    @property
    def log(self) -> LogConfig:
        """로그 설정 반환"""
        return LogConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            file=os.getenv('LOG_FILE', 'logs/nicl.log')
        )
    
    def get_project_root(self) -> str:
        """프로젝트 루트 디렉토리 반환"""
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def get_full_path(self, relative_path: str) -> str:
        """상대 경로를 절대 경로로 변환"""
        return os.path.join(self.get_project_root(), relative_path)
    
    def setup_logging(self):
        """로깅 설정"""
        log_config = self.log
        
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(self.get_full_path(log_config.file))
        os.makedirs(log_dir, exist_ok=True)
        
        # 로깅 설정
        logging.basicConfig(
            level=getattr(logging, log_config.level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.get_full_path(log_config.file), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger('NICL')

# 전역 설정 인스턴스
config = ConfigManager()
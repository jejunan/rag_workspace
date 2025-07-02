"""
Utils 패키지 - 파일 처리 및 텍스트 추출 유틸리티

이 패키지는 다양한 파일 형식(PDF, Word, PPT, CSV, HTML 등)에서
텍스트를 추출하는 기능을 제공합니다.
"""

# 환경 설정
import os
os.environ['USER_AGENT'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# 메인 함수들 import
from .text_processor import (
    to_text_data, 
    to_text_data_sync,
    extract_text_only,
    to_text_data_with_metadata,
    batch_process_files,
    batch_process_with_progress,
    smart_batch_processing,
    get_file_info
)
from .file_detector import extract_file_type
from .html_extractor import extract_html_content
from .encoding_utils import detect_and_decode, fix_encoding_issues

# 버전 정보
__version__ = "1.0.0"
__author__ = "RAG Workspace Team"

# 외부에서 사용할 수 있는 함수들
__all__ = [
    # 기본 텍스트 추출 함수들
    'to_text_data',
    'to_text_data_sync', 
    'extract_text_only',
    'to_text_data_with_metadata',
    
    # 일괄 처리 함수들
    'batch_process_files',
    'batch_process_with_progress',
    'smart_batch_processing',
    
    # 유틸리티 함수들
    'extract_file_type',
    'extract_html_content',
    'detect_and_decode',
    'fix_encoding_issues',
    'get_file_info'
]
"""
파일 타입 감지 모듈

파일 경로나 URL을 분석하여 파일 타입을 식별하는 기능을 제공합니다.
확장자, MIME 타입, 파일 시그니처를 통해 정확한 파일 타입을 판단합니다.
"""

import os
import mimetypes
from urllib.parse import urlparse


def extract_file_type(file_input: str) -> str:
    """
    파일 경로나 URL을 입력받아 파일 타입을 반환하는 함수.
    
    Args:
        file_input (str): 파일 경로 또는 URL
        
    Returns:
        str: 'pdf', 'word', 'url', 'ppt', 'csv', 'txt', 'excel' 중 하나, 또는 'unknown'
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
    """
    
    # URL인지 먼저 확인
    if _is_url(file_input):
        return 'url'
    
    # 파일이 존재하는지 확인
    if not os.path.exists(file_input):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_input}")
    
    # 확장자 기반 확인
    file_extension = os.path.splitext(file_input)[1].lower()
    extension_map = {
        '.pdf': 'pdf',
        '.doc': 'word',
        '.docx': 'word',
        '.ppt': 'ppt',
        '.pptx': 'ppt',
        '.csv': 'csv',
        '.txt': 'txt',
        '.xlsx': 'excel',
        '.xls': 'excel'
    }
    
    if file_extension in extension_map:
        return extension_map[file_extension]
    
    # MIME 타입으로 확인 (내장 mimetypes 모듈 사용)
    try:
        mime_type, _ = mimetypes.guess_type(file_input)
        if mime_type:
            mime_map = {
                'application/pdf': 'pdf',
                'application/msword': 'word',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'word',
                'application/vnd.ms-powerpoint': 'ppt',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'ppt',
                'text/csv': 'csv',
                'application/csv': 'csv',
                'text/plain': 'txt',
                'application/vnd.ms-excel': 'excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'excel'
            }
            
            if mime_type in mime_map:
                return mime_map[mime_type]
    
    except Exception as e:
        print(f"MIME 타입 확인 중 오류 발생: {e}")
    
    # 파일 시그니처로 확인 (바이너리 헤더 확인)
    try:
        file_type = _check_file_signature(file_input)
        if file_type != 'unknown':
            return file_type
    except Exception as e:
        print(f"파일 시그니처 확인 중 오류 발생: {e}")
    
    return 'unknown'


def _check_file_signature(file_path: str) -> str:
    """
    파일의 바이너리 시그니처를 확인하여 타입을 판단
    
    Args:
        file_path (str): 파일 경로
        
    Returns:
        str: 감지된 파일 타입 또는 'unknown'
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            
        # PDF 파일 시그니처: %PDF
        if header.startswith(b'%PDF'):
            return 'pdf'
            
        # ZIP 기반 파일들 (docx, pptx, xlsx 등)
        if header.startswith(b'PK\x03\x04'):
            # ZIP 파일이지만 Office 문서일 수 있음
            # 확장자로 다시 확인
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.docx']:
                return 'word'
            elif ext in ['.pptx']:
                return 'ppt'
            elif ext in ['.xlsx']:
                return 'excel'
                
        # 구 버전 MS Office 파일 시그니처
        if header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.doc']:
                return 'word'
            elif ext in ['.ppt']:
                return 'ppt'
            elif ext in ['.xls']:
                return 'excel'
        
    except Exception:
        pass
    
    return 'unknown'


def _is_url(string: str) -> bool:
    """
    문자열이 URL인지 확인하는 헬퍼 함수
    
    Args:
        string (str): 확인할 문자열
        
    Returns:
        bool: URL이면 True, 아니면 False
    """
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except:
        return False


# 지원하는 파일 형식 상수
SUPPORTED_FILE_TYPES = ['pdf', 'word', 'ppt', 'csv', 'txt', 'excel', 'url']

# 파일 확장자 매핑
FILE_EXTENSIONS = {
    'pdf': ['.pdf'],
    'word': ['.doc', '.docx'], 
    'ppt': ['.ppt', '.pptx'],
    'csv': ['.csv'],
    'txt': ['.txt'],
    'excel': ['.xls', '.xlsx']
}
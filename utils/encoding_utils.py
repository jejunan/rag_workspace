"""
인코딩 처리 유틸리티 모듈

다양한 인코딩 문제를 해결하고 텍스트를 올바르게 디코딩하는 기능을 제공합니다.
웹 크롤링이나 파일 처리 시 발생하는 인코딩 문제를 자동으로 감지하고 해결합니다.
"""

import re
import chardet
from typing import Optional, Union
import requests


def detect_and_decode(response: requests.Response, forced_encoding: Optional[str] = None) -> str:
    """
    HTTP 응답에서 올바른 인코딩을 감지하고 디코딩
    
    Args:
        response (requests.Response): HTTP 응답 객체
        forced_encoding (str, optional): 강제할 인코딩. 기본값은 None
        
    Returns:
        str: 디코딩된 텍스트
    """
    if forced_encoding:
        try:
            return response.content.decode(forced_encoding, errors='ignore')
        except:
            pass
    
    # 1. HTTP 헤더에서 charset 확인
    content_type = response.headers.get('content-type', '')
    charset_match = re.search(r'charset=([^;\s]+)', content_type, re.I)
    if charset_match:
        try:
            encoding = charset_match.group(1).strip('\'"')
            return response.content.decode(encoding, errors='ignore')
        except:
            pass
    
    # 2. HTML meta 태그에서 charset 확인
    try:
        partial_content = response.content[:2048].decode('utf-8', errors='ignore')
        meta_match = re.search(r'<meta[^>]*charset["\s]*=["\s]*([^">\s]+)', partial_content, re.I)
        if meta_match:
            encoding = meta_match.group(1).strip('\'"')
            return response.content.decode(encoding, errors='ignore')
    except:
        pass
    
    # 3. chardet 라이브러리로 자동 감지
    try:
        detected = chardet.detect(response.content)
        if detected['confidence'] > 0.7:
            encoding = detected['encoding']
            return response.content.decode(encoding, errors='ignore')
    except:
        pass
    
    # 4. 일반적인 인코딩들 시도
    common_encodings = ['utf-8', 'euc-kr', 'cp949', 'iso-8859-1', 'latin1']
    for encoding in common_encodings:
        try:
            return response.content.decode(encoding, errors='ignore')
        except:
            continue
    
    # 5. 최후의 수단: utf-8로 강제 디코딩
    return response.content.decode('utf-8', errors='ignore')


def fix_encoding_issues(text: str) -> str:
    """
    인코딩 문제로 깨진 텍스트 복구 시도
    
    Args:
        text (str): 복구할 텍스트
        
    Returns:
        str: 복구된 텍스트
    """
    if not text:
        return text
    
    # 한글 깨짐 패턴 복구
    fixes = [
        # EUC-KR을 UTF-8로 잘못 디코딩한 경우
        (r'Ã¡', 'ㅏ'), (r'Ã¢', 'ㅑ'), (r'Ã£', 'ㅓ'), (r'Ã¤', 'ㅕ'),
        (r'Ã¥', 'ㅗ'), (r'Ã¦', 'ㅛ'), (r'Ã§', 'ㅜ'), (r'Ã¨', 'ㅠ'),
        (r'Ã©', 'ㅡ'), (r'Ãª', 'ㅣ'), (r'Ã«', 'ㅢ'),
        
        # CP949 관련 복구
        (r'\?{2,}', ''),  # 연속된 물음표 제거
        (r'â', '-'),      # 대시 복구
        (r'â¢', '•'),     # 불릿 포인트 복구
        (r'â', '"'),      # 따옴표 복구
        (r'â', '"'),
        (r'â', '''),
        (r'â', '''),
    ]
    
    for pattern, replacement in fixes:
        text = re.sub(pattern, replacement, text)
    
    return text


def detect_file_encoding(file_path: str) -> str:
    """
    파일의 인코딩을 감지하는 함수
    
    Args:
        file_path (str): 파일 경로
        
    Returns:
        str: 감지된 인코딩 이름
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        detected = chardet.detect(raw_data)
        return detected.get('encoding', 'utf-8')
    except:
        return 'utf-8'


def try_multiple_encodings(content_bytes: bytes) -> tuple[str, str]:
    """
    여러 인코딩을 시도하여 올바른 텍스트 찾기
    
    Args:
        content_bytes (bytes): 디코딩할 바이트 데이터
        
    Returns:
        tuple[str, str]: (디코딩된 텍스트, 사용된 인코딩)
    """
    encodings = [
        'utf-8', 'euc-kr', 'cp949', 'iso-8859-1', 
        'latin1', 'ascii', 'utf-16', 'gb2312', 'big5'
    ]
    
    for encoding in encodings:
        try:
            decoded = content_bytes.decode(encoding)
            # 한글이 포함되어 있고 깨지지 않았는지 확인
            if any('가' <= char <= '힣' for char in decoded) or not re.search(r'[^\x00-\x7F]{3,}', decoded):
                return decoded, encoding
        except (UnicodeDecodeError, IndexError):
            continue
    
    # 모든 인코딩 실패시 utf-8로 강제 디코딩
    return content_bytes.decode('utf-8', errors='ignore'), 'utf-8'


def safe_decode_text(data: Union[bytes, str], encoding: Optional[str] = None) -> str:
    """
    안전하게 텍스트를 디코딩하는 함수
    
    Args:
        data (Union[bytes, str]): 디코딩할 데이터
        encoding (str, optional): 사용할 인코딩
        
    Returns:
        str: 디코딩된 텍스트
    """
    if isinstance(data, str):
        return fix_encoding_issues(data)
    
    if encoding:
        try:
            return data.decode(encoding, errors='ignore')
        except:
            pass
    
    # chardet으로 인코딩 감지 시도
    try:
        detected = chardet.detect(data)
        if detected['confidence'] > 0.7:
            encoding = detected['encoding']
            return data.decode(encoding, errors='ignore')
    except:
        pass
    
    # 최후의 수단으로 UTF-8 디코딩
    return data.decode('utf-8', errors='ignore')


# 상수들
COMMON_ENCODINGS = ['utf-8', 'euc-kr', 'cp949', 'iso-8859-1', 'latin1', 'ascii']
KOREAN_ENCODINGS = ['utf-8', 'euc-kr', 'cp949']
MINIMUM_CONFIDENCE = 0.7
"""
텍스트 처리 모듈

다양한 파일 형식에서 텍스트를 추출하고 변환하는 메인 기능을 제공합니다.
PDF, Word, PPT, CSV, Excel, 텍스트 파일, URL 등을 처리할 수 있습니다.
"""

import pandas as pd
import chardet
import os
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_community.document_loaders import UnstructuredPowerPointLoader
from langchain_community.document_loaders import CSVLoader

from .file_detector import extract_file_type
from .html_extractor import extract_html_content
from .encoding_utils import fix_encoding_issues


async def to_text_data(file_path: str, include_metadata: bool = False):
    """
    파일을 텍스트 데이터로 변환하는 비동기 함수
    
    Args:
        file_path (str): 파일 경로 또는 URL
        include_metadata (bool): 메타데이터 포함 여부
        
    Returns:
        str or dict: include_metadata=False시 텍스트, True시 메타데이터 포함 딕셔너리
        
    Raises:
        ValueError: 지원하지 않는 파일 형식인 경우
        FileNotFoundError: 파일을 찾을 수 없는 경우
    """
    try:
        file_type = extract_file_type(file_path)
        
        if file_type == 'pdf':
            text = await _process_pdf_async(file_path)
        elif file_type == 'word':
            text = await _process_word_async(file_path)
        elif file_type == 'ppt':
            text = await _process_ppt_async(file_path)
        elif file_type == 'csv':
            text = await _process_csv_async(file_path)
        elif file_type == 'txt':
            text = await _process_txt_async(file_path)
        elif file_type == 'excel':
            text = await _process_excel_async(file_path)
        elif file_type == 'url':
            text = await _process_url_async(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_type}")
        
        if include_metadata:
            return _create_metadata_response(file_path, text, file_type)
        else:
            return text
            
    except Exception as e:
        print(f"파일 처리 중 오류 발생: {e}")
        if include_metadata:
            return _create_error_response(file_path, str(e))
        else:
            raise


def to_text_data_sync(file_path: str, include_metadata: bool = False):
    """
    파일을 텍스트 데이터로 변환하는 동기 함수 (비동기가 필요없는 경우)
    
    Args:
        file_path (str): 파일 경로 또는 URL
        include_metadata (bool): 메타데이터 포함 여부
        
    Returns:
        str or dict: include_metadata=False시 텍스트, True시 메타데이터 포함 딕셔너리
        
    Raises:
        ValueError: 지원하지 않는 파일 형식인 경우
        FileNotFoundError: 파일을 찾을 수 없는 경우
    """
    try:
        file_type = extract_file_type(file_path)
        
        if file_type == 'pdf':
            text = _process_pdf_sync(file_path)
        elif file_type == 'word':
            text = _process_word_sync(file_path)
        elif file_type == 'ppt':
            text = _process_ppt_sync(file_path)
        elif file_type == 'csv':
            text = _process_csv_sync(file_path)
        elif file_type == 'txt':
            text = _process_txt_sync(file_path)
        elif file_type == 'excel':
            text = _process_excel_sync(file_path)
        elif file_type == 'url':
            text = _process_url_sync(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_type}")
        
        if include_metadata:
            return _create_metadata_response(file_path, text, file_type)
        else:
            return text
            
    except Exception as e:
        print(f"파일 처리 중 오류 발생: {e}")
        if include_metadata:
            return _create_error_response(file_path, str(e))
        else:
            raise


def extract_text_only(file_path: str) -> str:
    """
    텍스트만 추출하는 간단한 함수 (메타데이터 없음)
    
    Args:
        file_path (str): 파일 경로 또는 URL
        
    Returns:
        str: 추출된 텍스트
    """
    return to_text_data_sync(file_path, include_metadata=False)


def to_text_data_with_metadata(file_path: str) -> dict:
    """
    메타데이터와 함께 텍스트를 추출하는 함수
    
    Args:
        file_path (str): 파일 경로 또는 URL
        
    Returns:
        dict: 메타데이터가 포함된 결과
    """
    return to_text_data_sync(file_path, include_metadata=True)


def _create_metadata_response(file_path: str, text: str, file_type: str) -> dict:
    """메타데이터가 포함된 응답 생성"""
    return {
        'file_path': file_path,
        'text': text,
        'file_type': file_type,
        'char_count': len(text),
        'word_count': len(text.split()) if text else 0,
        'line_count': len(text.split('\n')) if text else 0,
        'processed_at': datetime.now().isoformat(),
        'success': True,
        'error': None
    }


def _create_error_response(file_path: str, error_msg: str) -> dict:
    """오류 응답 생성"""
    return {
        'file_path': file_path,
        'text': '',
        'file_type': 'unknown',
        'char_count': 0,
        'word_count': 0,
        'line_count': 0,
        'processed_at': datetime.now().isoformat(),
        'success': False,
        'error': error_msg
    }


# 비동기 처리 함수들
async def _process_pdf_async(file_path: str) -> str:
    """PDF 파일을 비동기로 처리"""
    loader = PyPDFLoader(file_path)
    pages = []
    async for page in loader.alazy_load():
        pages.append(page.page_content)
    return "\n".join(pages)


async def _process_word_async(file_path: str) -> str:
    """Word 파일을 비동기로 처리"""
    loader = UnstructuredWordDocumentLoader(
        file_path=file_path,
        mode="elements",
        strategy="fast",
    )
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


async def _process_ppt_async(file_path: str) -> str:
    """PowerPoint 파일을 비동기로 처리"""
    loader = UnstructuredPowerPointLoader(
        file_path=file_path,
        mode="elements",
        strategy="fast",
    )
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


async def _process_csv_async(file_path: str) -> str:
    """CSV 파일을 비동기로 처리"""
    loader = CSVLoader(file_path=file_path)
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


async def _process_txt_async(file_path: str) -> str:
    """텍스트 파일을 비동기로 처리"""
    return _process_txt_sync(file_path)


async def _process_excel_async(file_path: str) -> str:
    """Excel 파일을 비동기로 처리"""
    return _process_excel_sync(file_path)


async def _process_url_async(file_path: str) -> str:
    """URL을 비동기로 처리"""
    return extract_html_content(file_path)


# 동기 처리 함수들
def _process_pdf_sync(file_path: str) -> str:
    """PDF 파일을 동기로 처리"""
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


def _process_word_sync(file_path: str) -> str:
    """Word 파일을 동기로 처리"""
    loader = UnstructuredWordDocumentLoader(
        file_path=file_path,
        mode="elements",
        strategy="fast",
    )
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


def _process_ppt_sync(file_path: str) -> str:
    """PowerPoint 파일을 동기로 처리"""
    loader = UnstructuredPowerPointLoader(
        file_path=file_path,
        mode="elements",
        strategy="fast",
    )
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


def _process_csv_sync(file_path: str) -> str:
    """CSV 파일을 동기로 처리"""
    loader = CSVLoader(file_path=file_path)
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


def _process_txt_sync(file_path: str) -> str:
    """텍스트 파일을 동기로 처리 (인코딩 감지 포함)"""
    try:
        # 먼저 UTF-8로 시도
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except UnicodeDecodeError:
        # UTF-8 실패시 인코딩 감지
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')
        text = raw_data.decode(encoding, errors='ignore')
    
    # 인코딩 문제 수정
    return fix_encoding_issues(text)


def _process_excel_sync(file_path: str) -> str:
    """Excel 파일을 동기로 처리"""
    df = pd.read_excel(file_path)
    return df.to_string(index=False)


def _process_url_sync(file_path: str) -> str:
    """URL을 동기로 처리"""
    return extract_html_content(file_path)


# 일괄 처리 및 유틸리티 함수들
def batch_process_files(file_paths: list, use_async: bool = False, include_metadata: bool = True) -> dict:
    """
    여러 파일을 일괄 처리
    
    Args:
        file_paths (list): 처리할 파일 경로 리스트
        use_async (bool): 비동기 처리 여부
        include_metadata (bool): 메타데이터 포함 여부
        
    Returns:
        dict: {파일_경로: 결과} 형태의 딕셔너리
    """
    results = {}
    
    for file_path in file_paths:
        try:
            if use_async:
                # 비동기 처리는 별도의 이벤트 루프에서 실행해야 함
                import asyncio
                result = asyncio.run(to_text_data(file_path, include_metadata))
            else:
                result = to_text_data_sync(file_path, include_metadata)
            
            results[file_path] = result
            
        except Exception as e:
            print(f"{file_path} 처리 실패: {e}")
            if include_metadata:
                results[file_path] = _create_error_response(file_path, str(e))
            else:
                results[file_path] = ""
    
    return results


def batch_process_with_progress(file_paths: list, callback=None) -> dict:
    """
    진행 상황을 보여주면서 일괄 처리
    
    Args:
        file_paths (list): 처리할 파일 경로 리스트
        callback (function): 진행 상황 콜백 함수
        
    Returns:
        dict: 처리 결과
    """
    results = {}
    total = len(file_paths)
    
    for i, file_path in enumerate(file_paths, 1):
        try:
            result = to_text_data_sync(file_path, include_metadata=True)
            results[file_path] = result
            
            # 진행 상황 출력
            if callback:
                callback(i, total, file_path, True)
            else:
                print(f"진행률: {i}/{total} - 완료: {file_path}")
                
        except Exception as e:
            results[file_path] = _create_error_response(file_path, str(e))
            
            if callback:
                callback(i, total, file_path, False, str(e))
            else:
                print(f"진행률: {i}/{total} - 실패: {file_path} ({e})")
    
    return results


def smart_batch_processing(file_paths: list) -> dict:
    """
    파일 타입에 따른 스마트 일괄 처리
    
    Args:
        file_paths (list): 처리할 파일 경로 리스트
        
    Returns:
        dict: 처리 결과와 통계
    """
    results = {}
    stats = {
        'total': len(file_paths),
        'success': 0,
        'failed': 0,
        'by_type': {}
    }
    
    for file_path in file_paths:
        try:
            result = to_text_data_sync(file_path, include_metadata=True)
            results[file_path] = result
            
            # 통계 업데이트
            stats['success'] += 1
            file_type = result.get('file_type', 'unknown')
            stats['by_type'][file_type] = stats['by_type'].get(file_type, 0) + 1
            
            # 파일 타입별 후처리
            text = result['text']
            if file_type == 'pdf':
                # PDF 특수 문자 정리
                text = _clean_pdf_artifacts(text)
            elif file_type == 'url':
                # HTML 노이즈 제거
                text = _remove_html_noise(text)
            
            result['text'] = text
            
        except Exception as e:
            results[file_path] = _create_error_response(file_path, str(e))
            stats['failed'] += 1
    
    return {
        'results': results,
        'statistics': stats
    }


def _clean_pdf_artifacts(text: str) -> str:
    """PDF 특유의 아티팩트 정리"""
    # PDF에서 자주 나타나는 불필요한 문자 제거
    import re
    text = re.sub(r'\f', '', text)  # 폼피드 문자 제거
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)  # 하이픈으로 나뉜 단어 합치기
    return text


def _remove_html_noise(text: str) -> str:
    """HTML에서 추출한 텍스트의 노이즈 제거"""
    import re
    # 연속된 공백 제거
    text = re.sub(r'\s+', ' ', text)
    # 불필요한 줄바꿈 정리
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


# 유틸리티 함수들
def get_supported_file_types() -> list:
    """
    지원하는 파일 형식 목록을 반환
    
    Returns:
        list: 지원하는 파일 형식 리스트
    """
    return ['pdf', 'word', 'ppt', 'csv', 'txt', 'excel', 'url']


def validate_file_path(file_path: str) -> bool:
    """
    파일 경로나 URL이 유효한지 확인
    
    Args:
        file_path (str): 확인할 파일 경로 또는 URL
        
    Returns:
        bool: 유효하면 True, 아니면 False
    """
    try:
        file_type = extract_file_type(file_path)
        return file_type in get_supported_file_types()
    except:
        return False


def get_file_info(file_path: str) -> dict:
    """
    파일 정보를 가져오는 함수
    
    Args:
        file_path (str): 파일 경로
        
    Returns:
        dict: 파일 정보
    """
    try:
        file_type = extract_file_type(file_path)
        
        if file_type == 'url':
            return {
                'file_path': file_path,
                'file_type': file_type,
                'file_size': None,
                'exists': True,
                'is_url': True
            }
        else:
            return {
                'file_path': file_path,
                'file_type': file_type,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else None,
                'exists': os.path.exists(file_path),
                'is_url': False
            }
    except Exception as e:
        return {
            'file_path': file_path,
            'file_type': 'unknown',
            'file_size': None,
            'exists': False,
            'is_url': False,
            'error': str(e)
        }


# 상수들
SUPPORTED_FORMATS = {
    'pdf': 'Portable Document Format',
    'word': 'Microsoft Word Document',
    'ppt': 'Microsoft PowerPoint Presentation',
    'csv': 'Comma-Separated Values',
    'txt': 'Plain Text File',
    'excel': 'Microsoft Excel Spreadsheet',
    'url': 'Web URL'
}

LOADER_SETTINGS = {
    'word': {'mode': 'elements', 'strategy': 'fast'},
    'ppt': {'mode': 'elements', 'strategy': 'fast'}
}
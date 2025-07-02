"""
HTML 콘텐츠 추출 모듈

웹페이지에서 본문 내용을 추출하는 기능을 제공합니다.
readability 알고리즘을 사용하여 광고, 메뉴 등을 제거하고 순수한 본문만 추출합니다.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Tuple
from .encoding_utils import detect_and_decode, fix_encoding_issues


def extract_html_content(url: str, encoding: Optional[str] = None) -> str:
    """
    URL에서 스마트 추출 방법으로 본문 내용을 추출하는 함수 (readability 알고리즘 유사)
    
    Args:
        url (str): 추출할 웹페이지 URL
        encoding (str, optional): 강제할 인코딩
        
    Returns:
        str: 추출된 본문 텍스트
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # Session 사용으로 쿠키 및 연결 관리
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=20, allow_redirects=True)
        response.raise_for_status()
        
        # 더 정교한 인코딩 감지
        html_content = detect_and_decode(response, encoding)
        
    except requests.RequestException as e:
        print(f"URL 요청 실패: {e}")
        return ""
    
    # 여러 파서 시도
    parsers = ['html.parser', 'lxml', 'html5lib']
    soup = None
    
    for parser in parsers:
        try:
            soup = BeautifulSoup(html_content, parser)
            break
        except:
            continue
    
    if not soup:
        print("HTML 파싱 실패")
        return ""
    
    # 불필요한 태그들 제거
    _remove_unwanted_elements(soup)
    
    # 각 요소의 점수 계산 (readability 알고리즘)
    scored_elements = _score_content_elements(soup)
    
    # 상위 요소들의 텍스트 합치기
    main_texts = _extract_top_content(scored_elements)
    
    # 텍스트 정리 및 인코딩 문제 해결
    result_text = clean_extracted_text('\n\n'.join(main_texts))
    return fix_encoding_issues(result_text)


def _remove_unwanted_elements(soup: BeautifulSoup) -> None:
    """
    불필요한 HTML 요소들을 제거하는 함수
    
    Args:
        soup (BeautifulSoup): BeautifulSoup 객체
    """
    # 불필요한 태그들 제거
    remove_tags = [
        'script', 'style', 'nav', 'header', 'footer', 'aside',
        'iframe', 'noscript', 'form', 'button', 'input',
        'select', 'textarea', 'option', 'meta', 'link',
        'advertisement', 'ads', 'popup', 'modal'
    ]
    
    for tag in remove_tags:
        for element in soup.find_all(tag):
            element.decompose()
    
    # 클래스나 ID로 불필요한 요소 제거
    unwanted_patterns = [
        'nav', 'menu', 'sidebar', 'footer', 'header', 'ad',
        'advertisement', 'banner', 'popup', 'modal', 'comment',
        'social', 'share', 'related', 'recommend', 'widget'
    ]
    
    for pattern in unwanted_patterns:
        # 클래스명에 패턴이 포함된 요소 제거
        for element in soup.find_all(class_=re.compile(pattern, re.I)):
            element.decompose()
        # ID에 패턴이 포함된 요소 제거
        for element in soup.find_all(id=re.compile(pattern, re.I)):
            element.decompose()


def _score_content_elements(soup: BeautifulSoup) -> List[Tuple[float, object, str]]:
    """
    각 요소의 본문 가능성 점수를 계산하는 함수
    
    Args:
        soup (BeautifulSoup): BeautifulSoup 객체
        
    Returns:
        List[Tuple[float, object, str]]: (점수, 요소, 텍스트) 튜플 리스트
    """
    scored_elements = []
    
    for element in soup.find_all(['p', 'div', 'article', 'section']):
        text = element.get_text(strip=True)
        if not text:
            continue
            
        score = calculate_content_score(element, text)
        if score > 0:
            scored_elements.append((score, element, text))
    
    # 점수순으로 정렬
    scored_elements.sort(key=lambda x: x[0], reverse=True)
    return scored_elements


def _extract_top_content(scored_elements: List[Tuple[float, object, str]], max_length: int = 3000) -> List[str]:
    """
    상위 점수 요소들의 텍스트를 추출하는 함수
    
    Args:
        scored_elements (List[Tuple[float, object, str]]): 점수가 매겨진 요소들
        max_length (int): 최대 텍스트 길이
        
    Returns:
        List[str]: 추출된 텍스트 리스트
    """
    main_texts = []
    total_length = 0
    
    for score, element, text in scored_elements:
        if total_length > max_length:  # 충분한 텍스트가 모이면 중단
            break
        main_texts.append(text)
        total_length += len(text)
    
    return main_texts


def calculate_content_score(element, text: str) -> float:
    """
    요소의 본문 가능성 점수 계산 (readability 알고리즘)
    
    Args:
        element: BeautifulSoup 요소
        text (str): 요소의 텍스트 내용
        
    Returns:
        float: 본문 가능성 점수
    """
    score = 0.0
    
    # 텍스트 길이에 따른 점수
    text_length = len(text)
    if text_length > 50:
        score += min(text_length / 100, 5)
    
    # 문장 부호가 많으면 본문일 가능성 증가
    punctuation_count = len(re.findall(r'[.!?]', text))
    score += punctuation_count * 0.5
    
    # 클래스명이나 ID로 점수 조정
    class_names = ' '.join(element.get('class', []))
    id_name = element.get('id', '')
    
    # 본문을 나타내는 키워드
    content_keywords = ['content', 'article', 'post', 'main', 'body', 'text', 'story']
    for keyword in content_keywords:
        if keyword in class_names.lower() or keyword in id_name.lower():
            score += 2
    
    # 불필요한 요소를 나타내는 키워드
    unwanted_keywords = ['nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'comment', 'widget']
    for keyword in unwanted_keywords:
        if keyword in class_names.lower() or keyword in id_name.lower():
            score -= 3
    
    # 링크가 많으면 메뉴나 네비게이션일 가능성
    links = element.find_all('a')
    if len(links) > text_length / 100:  # 텍스트 대비 링크가 많으면
        score -= 2
    
    return max(0, score)


def clean_extracted_text(text: str) -> str:
    """
    추출된 텍스트 정리
    
    Args:
        text (str): 정리할 텍스트
        
    Returns:
        str: 정리된 텍스트
    """
    if not text:
        return ""
    
    # 연속된 공백과 줄바꿈 정리
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    # 너무 짧은 줄 제거 (광고나 메뉴 항목일 가능성)
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if len(line) > 10 or (len(line) > 0 and line.endswith(('.', '!', '?', ':', ';'))):
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def extract_from_body(soup: BeautifulSoup) -> str:
    """
    body 전체에서 텍스트 추출 (마지막 수단)
    
    Args:
        soup (BeautifulSoup): BeautifulSoup 객체
        
    Returns:
        str: 추출된 텍스트
    """
    body = soup.find('body')
    if body:
        return body.get_text(separator='\n', strip=True)
    else:
        return soup.get_text(separator='\n', strip=True)


def extract_by_common_selectors(soup: BeautifulSoup) -> str:
    """
    일반적인 본문 선택자들을 시도하여 내용 추출
    
    Args:
        soup (BeautifulSoup): BeautifulSoup 객체
        
    Returns:
        str: 추출된 텍스트
    """
    # 본문을 나타내는 일반적인 선택자들
    content_selectors = [
        'article',
        '.content', '.main-content', '.post-content', '.entry-content',
        '.article-content', '.story-content', '.text-content',
        '#content', '#main-content', '#post-content', '#article-content',
        'main', '.main', '#main',
        '.post-body', '.entry-body', '.article-body',
        '.news-content', '.blog-content'
    ]
    
    for selector in content_selectors:
        try:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator='\n', strip=True)
                if len(text) > 100:  # 충분한 길이의 텍스트가 있으면 반환
                    return text
        except:
            continue
    
    return ""


def extract_basic_content(url: str) -> str:
    """
    기본적인 방법으로 웹페이지 콘텐츠 추출 (fallback 용도)
    
    Args:
        url (str): 웹페이지 URL
        
    Returns:
        str: 추출된 텍스트
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 기본적인 불필요 요소 제거
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        # 일반적인 선택자로 본문 찾기
        content = extract_by_common_selectors(soup)
        
        if not content:
            content = extract_from_body(soup)
        
        return clean_extracted_text(content)
        
    except Exception as e:
        print(f"기본 콘텐츠 추출 실패: {e}")
        return ""


# 상수들
DEFAULT_MAX_CONTENT_LENGTH = 3000
MIN_TEXT_LENGTH_FOR_CONTENT = 10
CONTENT_KEYWORDS = ['content', 'article', 'post', 'main', 'body', 'text', 'story']
UNWANTED_KEYWORDS = ['nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'comment', 'widget']
CONTENT_SELECTORS = [
    'article',
    '.content', '.main-content', '.post-content', '.entry-content',
    '.article-content', '.story-content', '.text-content',
    '#content', '#main-content', '#post-content', '#article-content',
    'main', '.main', '#main',
    '.post-body', '.entry-body', '.article-body',
    '.news-content', '.blog-content'
]
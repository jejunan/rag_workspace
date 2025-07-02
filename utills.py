# import os
# import mimetypes
# import pandas as pd
# import asyncio
# import re
# import requests
# import chardet

# from urllib.parse import urlparse
# from bs4 import BeautifulSoup
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_community.document_loaders import UnstructuredWordDocumentLoader
# from langchain_community.document_loaders import UnstructuredPowerPointLoader
# from langchain_community.document_loaders import CSVLoader

# # USER_AGENT 설정 (경고 메시지 방지)
# os.environ['USER_AGENT'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# def extract_file_type(file_input):
#     """
#     파일 경로나 URL을 입력받아 파일 타입을 반환하는 함수.
    
#     Args:
#         file_input (str): 파일 경로 또는 URL
        
#     Returns:
#         str: 'pdf', 'word', 'url', 'ppt', 'csv' 중 하나, 또는 'unknown'
#     """
    
#     # URL인지 먼저 확인
#     if _is_url(file_input):
#         return 'url'
    
#     # 파일이 존재하는지 확인
#     if not os.path.exists(file_input):
#         raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_input}")
    
#     # 확장자 기반 확인
#     file_extension = os.path.splitext(file_input)[1].lower()
#     extension_map = {
#         '.pdf': 'pdf',
#         '.doc': 'word',
#         '.docx': 'word',
#         '.ppt': 'ppt',
#         '.pptx': 'ppt',
#         '.csv': 'csv',
#         '.txt': 'txt',  # 추가
#         '.xlsx': 'excel',  # 추가
#         '.xls': 'excel'    # 추가
#     }
    
#     if file_extension in extension_map:
#         return extension_map[file_extension]
    
#     # MIME 타입으로 확인 (내장 mimetypes 모듈 사용)
#     try:
#         mime_type, _ = mimetypes.guess_type(file_input)
#         if mime_type:
#             mime_map = {
#                 'application/pdf': 'pdf',
#                 'application/msword': 'word',
#                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'word',
#                 'application/vnd.ms-powerpoint': 'ppt',
#                 'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'ppt',
#                 'text/csv': 'csv',
#                 'application/csv': 'csv',
#                 'text/plain': 'txt',
#                 'application/vnd.ms-excel': 'excel',
#                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'excel'
#             }
            
#             if mime_type in mime_map:
#                 return mime_map[mime_type]
    
#     except Exception as e:
#         print(f"MIME 타입 확인 중 오류 발생: {e}")
    
#     # 파일 시그니처로 확인 (바이너리 헤더 확인)
#     try:
#         file_type = _check_file_signature(file_input)
#         if file_type != 'unknown':
#             return file_type
#     except Exception as e:
#         print(f"파일 시그니처 확인 중 오류 발생: {e}")
    
#     return 'unknown'

# # 인코딩 문제 해결을 위한 함수들
# def detect_and_decode(response, forced_encoding=None):
#     """
#     HTTP 응답에서 올바른 인코딩을 감지하고 디코딩
#     """
#     if forced_encoding:
#         try:
#             return response.content.decode(forced_encoding, errors='ignore')
#         except:
#             pass
    
#     # 1. HTTP 헤더에서 charset 확인
#     content_type = response.headers.get('content-type', '')
#     charset_match = re.search(r'charset=([^;\s]+)', content_type, re.I)
#     if charset_match:
#         try:
#             encoding = charset_match.group(1).strip('\'"')
#             return response.content.decode(encoding, errors='ignore')
#         except:
#             pass
    
#     # 2. HTML meta 태그에서 charset 확인
#     try:
#         partial_content = response.content[:2048].decode('utf-8', errors='ignore')
#         meta_match = re.search(r'<meta[^>]*charset["\s]*=["\s]*([^">\s]+)', partial_content, re.I)
#         if meta_match:
#             encoding = meta_match.group(1).strip('\'"')
#             return response.content.decode(encoding, errors='ignore')
#     except:
#         pass
    
#     # 3. chardet 라이브러리로 자동 감지
#     try:
#         detected = chardet.detect(response.content)
#         if detected['confidence'] > 0.7:
#             encoding = detected['encoding']
#             return response.content.decode(encoding, errors='ignore')
#     except:
#         pass
    
#     # 4. 일반적인 인코딩들 시도
#     common_encodings = ['utf-8', 'euc-kr', 'cp949', 'iso-8859-1', 'latin1']
#     for encoding in common_encodings:
#         try:
#             return response.content.decode(encoding, errors='ignore')
#         except:
#             continue
    
#     # 5. 최후의 수단: utf-8로 강제 디코딩
#     return response.content.decode('utf-8', errors='ignore')

# def fix_encoding_issues(text):
#     """
#     인코딩 문제로 깨진 텍스트 복구 시도
#     """
#     if not text:
#         return text
    
#     # 한글 깨짐 패턴 복구
#     fixes = [
#         # EUC-KR을 UTF-8로 잘못 디코딩한 경우
#         (r'Ã¡', 'ㅏ'), (r'Ã¢', 'ㅑ'), (r'Ã£', 'ㅓ'), (r'Ã¤', 'ㅕ'),
#         (r'Ã¥', 'ㅗ'), (r'Ã¦', 'ㅛ'), (r'Ã§', 'ㅜ'), (r'Ã¨', 'ㅠ'),
#         (r'Ã©', 'ㅡ'), (r'Ãª', 'ㅣ'), (r'Ã«', 'ㅢ'),
        
#         # CP949 관련 복구
#         (r'\?{2,}', ''),  # 연속된 물음표 제거
#         (r'â', '-'),      # 대시 복구
#         (r'â¢', '•'),     # 불릿 포인트 복구
#         (r'â', '"'),      # 따옴표 복구
#         (r'â', '"'),
#         (r'â', '''),
#         (r'â', '''),
#     ]
    
#     for pattern, replacement in fixes:
#         text = re.sub(pattern, replacement, text)
    
#     return text

# def extract_html_content(url, encoding=None):
#     """
#     URL에서 스마트 추출 방법으로 본문 내용을 추출하는 함수 (readability 알고리즘 유사)
#     """
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#         'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
#         'Accept-Encoding': 'gzip, deflate, br',
#         'Cache-Control': 'no-cache',
#         'Connection': 'keep-alive',
#         'DNT': '1',
#         'Pragma': 'no-cache',
#         'Sec-Fetch-Dest': 'document',
#         'Sec-Fetch-Mode': 'navigate',
#         'Sec-Fetch-Site': 'none',
#         'Upgrade-Insecure-Requests': '1'
#     }
    
#     try:
#         # Session 사용으로 쿠키 및 연결 관리
#         session = requests.Session()
#         session.headers.update(headers)
        
#         response = session.get(url, timeout=20, allow_redirects=True)
#         response.raise_for_status()
        
#         # 더 정교한 인코딩 감지
#         html_content = detect_and_decode(response, encoding)
        
#     except requests.RequestException as e:
#         print(f"URL 요청 실패: {e}")
#         return ""
    
#     # 여러 파서 시도
#     parsers = ['html.parser', 'lxml', 'html5lib']
#     soup = None
    
#     for parser in parsers:
#         try:
#             soup = BeautifulSoup(html_content, parser)
#             break
#         except:
#             continue
    
#     if not soup:
#         print("HTML 파싱 실패")
#         return ""
    
#     # 불필요한 태그들 제거
#     remove_tags = [
#         'script', 'style', 'nav', 'header', 'footer', 'aside',
#         'iframe', 'noscript', 'form', 'button', 'input',
#         'select', 'textarea', 'option', 'meta', 'link',
#         'advertisement', 'ads', 'popup', 'modal'
#     ]
    
#     for tag in remove_tags:
#         for element in soup.find_all(tag):
#             element.decompose()
    
#     # 클래스나 ID로 불필요한 요소 제거
#     unwanted_patterns = [
#         'nav', 'menu', 'sidebar', 'footer', 'header', 'ad',
#         'advertisement', 'banner', 'popup', 'modal', 'comment',
#         'social', 'share', 'related', 'recommend', 'widget'
#     ]
    
#     for pattern in unwanted_patterns:
#         # 클래스명에 패턴이 포함된 요소 제거
#         for element in soup.find_all(class_=re.compile(pattern, re.I)):
#             element.decompose()
#         # ID에 패턴이 포함된 요소 제거
#         for element in soup.find_all(id=re.compile(pattern, re.I)):
#             element.decompose()
    
#     # 각 요소의 점수 계산 (readability 알고리즘)
#     scored_elements = []
    
#     for element in soup.find_all(['p', 'div', 'article', 'section']):
#         text = element.get_text(strip=True)
#         if not text:
#             continue
            
#         score = calculate_content_score(element, text)
#         if score > 0:
#             scored_elements.append((score, element, text))
    
#     # 점수순으로 정렬
#     scored_elements.sort(key=lambda x: x[0], reverse=True)
    
#     # 상위 요소들의 텍스트 합치기
#     main_texts = []
#     total_length = 0
    
#     for score, element, text in scored_elements:
#         if total_length > 3000:  # 충분한 텍스트가 모이면 중단
#             break
#         main_texts.append(text)
#         total_length += len(text)
    
#     # 텍스트 정리 및 인코딩 문제 해결
#     result_text = clean_extracted_text('\n\n'.join(main_texts))
#     return fix_encoding_issues(result_text)

# def calculate_content_score(element, text):
#     """
#     요소의 본문 가능성 점수 계산 (readability 알고리즘)
#     """
#     score = 0
    
#     # 텍스트 길이에 따른 점수
#     text_length = len(text)
#     if text_length > 50:
#         score += min(text_length / 100, 5)
    
#     # 문장 부호가 많으면 본문일 가능성 증가
#     punctuation_count = len(re.findall(r'[.!?]', text))
#     score += punctuation_count * 0.5
    
#     # 클래스명이나 ID로 점수 조정
#     class_names = ' '.join(element.get('class', []))
#     id_name = element.get('id', '')
    
#     # 본문을 나타내는 키워드
#     content_keywords = ['content', 'article', 'post', 'main', 'body', 'text', 'story']
#     for keyword in content_keywords:
#         if keyword in class_names.lower() or keyword in id_name.lower():
#             score += 2
    
#     # 불필요한 요소를 나타내는 키워드
#     unwanted_keywords = ['nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'comment', 'widget']
#     for keyword in unwanted_keywords:
#         if keyword in class_names.lower() or keyword in id_name.lower():
#             score -= 3
    
#     # 링크가 많으면 메뉴나 네비게이션일 가능성
#     links = element.find_all('a')
#     if len(links) > text_length / 100:  # 텍스트 대비 링크가 많으면
#         score -= 2
    
#     return max(0, score)

# def clean_extracted_text(text):
#     """
#     추출된 텍스트 정리
#     """
#     if not text:
#         return ""
    
#     # 연속된 공백과 줄바꿈 정리
#     text = re.sub(r'\n\s*\n', '\n\n', text)
#     text = re.sub(r' +', ' ', text)
#     text = re.sub(r'\t+', ' ', text)
    
#     # 앞뒤 공백 제거
#     text = text.strip()
    
#     # 너무 짧은 줄 제거 (광고나 메뉴 항목일 가능성)
#     lines = text.split('\n')
#     filtered_lines = []
    
#     for line in lines:
#         line = line.strip()
#         if len(line) > 10 or (len(line) > 0 and line.endswith(('.', '!', '?', ':', ';'))):
#             filtered_lines.append(line)
    
#     return '\n'.join(filtered_lines)

# def extract_from_body(soup):
#     """
#     body 전체에서 텍스트 추출 (마지막 수단)
#     """
#     body = soup.find('body')
#     if body:
#         return body.get_text(separator='\n', strip=True)
#     else:
#         return soup.get_text(separator='\n', strip=True)

# def extract_by_common_selectors(soup):
#     """
#     일반적인 본문 선택자들을 시도하여 내용 추출
#     """
#     # 본문을 나타내는 일반적인 선택자들
#     content_selectors = [
#         'article',
#         '.content', '.main-content', '.post-content', '.entry-content',
#         '.article-content', '.story-content', '.text-content',
#         '#content', '#main-content', '#post-content', '#article-content',
#         'main', '.main', '#main',
#         '.post-body', '.entry-body', '.article-body',
#         '.news-content', '.blog-content'
#     ]
    
#     for selector in content_selectors:
#         try:
#             element = soup.select_one(selector)
#             if element:
#                 text = element.get_text(separator='\n', strip=True)
#                 if len(text) > 100:  # 충분한 길이의 텍스트가 있으면 반환
#                     return text
#         except:
#             continue
    
#     return ""

# def _check_file_signature(file_path):
#     """
#     파일의 바이너리 시그니처를 확인하여 타입을 판단
#     """
#     try:
#         with open(file_path, 'rb') as f:
#             header = f.read(8)
            
#         # PDF 파일 시그니처: %PDF
#         if header.startswith(b'%PDF'):
#             return 'pdf'
            
#         # ZIP 기반 파일들 (docx, pptx, xlsx 등)
#         if header.startswith(b'PK\x03\x04'):
#             # ZIP 파일이지만 Office 문서일 수 있음
#             # 확장자로 다시 확인
#             ext = os.path.splitext(file_path)[1].lower()
#             if ext in ['.docx']:
#                 return 'word'
#             elif ext in ['.pptx']:
#                 return 'ppt'
#             elif ext in ['.xlsx']:
#                 return 'excel'
                
#         # 구 버전 MS Office 파일 시그니처
#         if header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
#             ext = os.path.splitext(file_path)[1].lower()
#             if ext in ['.doc']:
#                 return 'word'
#             elif ext in ['.ppt']:
#                 return 'ppt'
#             elif ext in ['.xls']:
#                 return 'excel'
        
#     except Exception:
#         pass
    
#     return 'unknown'

# def _is_url(string):
#     """
#     문자열이 URL인지 확인하는 헬퍼 함수
#     """
#     try:
#         result = urlparse(string)
#         return all([result.scheme, result.netloc])
#     except:
#         return False

# async def to_text_data(file_path: str):
#     """
#     파일을 텍스트 데이터로 변환하는 비동기 함수
    
#     Args:
#         file_path (str): 파일 경로 또는 URL
        
#     Returns:
#         str: 추출된 텍스트 데이터
#     """
#     try:
#         file_type = extract_file_type(file_path)
        
#         if file_type == 'pdf':
#             loader = PyPDFLoader(file_path)
#             pages = []
#             async for page in loader.alazy_load():
#                 pages.append(page.page_content)  # 수정: page_content 추출
#             text = "\n".join(pages)
#             return text
            
#         elif file_type == 'word':
#             loader = UnstructuredWordDocumentLoader(
#                 file_path=file_path,
#                 mode="elements",
#                 strategy="fast",
#             )
#             docs = loader.load()
#             text = "\n".join([doc.page_content for doc in docs])
#             return text
            
#         elif file_type == 'ppt':
#             loader = UnstructuredPowerPointLoader(
#                 file_path=file_path,
#                 mode="elements",
#                 strategy="fast",
#             )
#             docs = loader.load()
#             text = "\n".join([doc.page_content for doc in docs])
#             return text
            
#         elif file_type == 'csv':
#             # CSV 파일 처리 추가
#             loader = CSVLoader(file_path=file_path)
#             docs = loader.load()
#             text = "\n".join([doc.page_content for doc in docs])
#             return text
            
#         elif file_type == 'txt':
#             # 텍스트 파일 처리 (인코딩 감지 추가)
#             try:
#                 # 먼저 UTF-8로 시도
#                 with open(file_path, 'r', encoding='utf-8') as f:
#                     text = f.read()
#             except UnicodeDecodeError:
#                 # UTF-8 실패시 인코딩 감지
#                 with open(file_path, 'rb') as f:
#                     raw_data = f.read()
#                 detected = chardet.detect(raw_data)
#                 encoding = detected.get('encoding', 'utf-8')
#                 text = raw_data.decode(encoding, errors='ignore')
            
#             # 인코딩 문제 수정
#             text = fix_encoding_issues(text)
#             return text
            
#         elif file_type == 'excel':
#             # Excel 파일 처리 추가
#             df = pd.read_excel(file_path)
#             text = df.to_string(index=False)
#             return text
            
#         elif file_type == 'url':
#             # 스마트 추출 방법 사용 (readability 알고리즘)
#             text = extract_html_content(file_path)
#             return text
            
#         else:
#             raise ValueError(f"지원하지 않는 파일 형식입니다: {file_type}")
            
#     except Exception as e:
#         print(f"파일 처리 중 오류 발생: {e}")
#         raise

# def to_text_data_sync(file_path: str):
#     """
#     파일을 텍스트 데이터로 변환하는 동기 함수 (비동기가 필요없는 경우)
    
#     Args:
#         file_path (str): 파일 경로 또는 URL
        
#     Returns:
#         str: 추출된 텍스트 데이터
#     """
#     try:
#         file_type = extract_file_type(file_path)
        
#         if file_type == 'pdf':
#             loader = PyPDFLoader(file_path)
#             docs = loader.load()
#             text = "\n".join([doc.page_content for doc in docs])
#             return text
            
#         elif file_type == 'word':
#             loader = UnstructuredWordDocumentLoader(
#                 file_path=file_path,
#                 mode="elements",
#                 strategy="fast",
#             )
#             docs = loader.load()
#             text = "\n".join([doc.page_content for doc in docs])
#             return text
            
#         elif file_type == 'ppt':
#             loader = UnstructuredPowerPointLoader(
#                 file_path=file_path,
#                 mode="elements",
#                 strategy="fast",
#             )
#             docs = loader.load()
#             text = "\n".join([doc.page_content for doc in docs])
#             return text
            
#         elif file_type == 'csv':
#             loader = CSVLoader(file_path=file_path)
#             docs = loader.load()
#             text = "\n".join([doc.page_content for doc in docs])
#             return text
            
#         elif file_type == 'txt':
#             # 텍스트 파일 처리 (인코딩 감지 추가)
#             try:
#                 with open(file_path, 'r', encoding='utf-8') as f:
#                     text = f.read()
#             except UnicodeDecodeError:
#                 with open(file_path, 'rb') as f:
#                     raw_data = f.read()
#                 detected = chardet.detect(raw_data)
#                 encoding = detected.get('encoding', 'utf-8')
#                 text = raw_data.decode(encoding, errors='ignore')
            
#             text = fix_encoding_issues(text)
#             return text
            
#         elif file_type == 'excel':
#             df = pd.read_excel(file_path)
#             text = df.to_string(index=False)
#             return text
            
#         elif file_type == 'url':
#             # 개선된 HTML 콘텐츠 추출 사용
#             text = extract_html_content(file_path)
#             return text
            
#         else:
#             raise ValueError(f"지원하지 않는 파일 형식입니다: {file_type}")
            
#     except Exception as e:
#         print(f"파일 처리 중 오류 발생: {e}")
#         raise




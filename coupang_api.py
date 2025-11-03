"""
쿠팡 파트너스 API 호출 전담 모듈
HMAC 서명 기반 인증을 사용하여 쿠팡 파트너스 API를 호출합니다.
"""
import requests
import os
import hmac
import hashlib
import urllib.parse
import datetime


# 환경 변수에서 API 키 가져오기
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

# 쿠팡 파트너스 API 베이스 URL
BASE_URL = 'https://api-gateway.coupang.com'


def generate_hmac(method, path, query=''):
    """
    HMAC 서명을 생성합니다.
    쿠팡 파트너스 API 공식 문서에 따라 HMAC-SHA256 서명을 생성합니다.
    
    Args:
        method (str): HTTP 메서드 (예: 'GET', 'POST')
        path (str): 요청 경로 (예: '/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink/goldbox')
        query (str): 쿼리 문자열 (없을 경우 빈 문자열)
    
    Returns:
        str: Authorization 헤더에 사용할 서명 문자열
    """
    try:
        # 타임스탬프 생성 (밀리초 단위)
        timestamp = str(int(datetime.datetime.utcnow().timestamp() * 1000))
        
        # 서명 메시지 생성: timestamp + method + path + query
        message = f'{timestamp}{method}{path}{query}'
        
        # HMAC-SHA256 서명 생성
        signature = hmac.new(
            SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Authorization 헤더 형식: CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp}, signature={signature}
        auth_header = f'CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp}, signature={signature}'
        
        return auth_header
    
    except Exception as e:
        print(f'HMAC 서명 생성 중 오류 발생: {e}')
        raise


def get_goldbox_products():
    """
    골드박스 상품 목록을 조회하는 API를 호출합니다.
    
    API 엔드포인트: GET /v2/providers/affiliate_open_api/apis/openapi/v1/deeplink/goldbox
    
    Returns:
        list: 상품 목록의 JSON 리스트. 오류 발생 시 빈 리스트 반환.
    """
    try:
        if not ACCESS_KEY or not SECRET_KEY:
            print('경고: 쿠팡 API 키가 설정되지 않았습니다.')
            return []
        
        method = 'GET'
        path = '/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink/goldbox'
        query = ''
        
        # HMAC 서명 생성
        auth_header = generate_hmac(method, path, query)
        
        # API 요청 URL 구성
        url = f'{BASE_URL}{path}'
        
        # 요청 헤더 설정
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json;charset=UTF-8'
        }
        
        # API 요청 실행
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # JSON 응답 파싱
        result = response.json()
        
        # 응답 구조에 따라 데이터 추출 (실제 응답 구조에 맞게 수정 필요)
        if isinstance(result, dict):
            # 일반적인 응답 구조: {'data': {...}, 'products': [...]}
            if 'data' in result:
                if isinstance(result['data'], dict) and 'products' in result['data']:
                    return result['data']['products']
                elif isinstance(result['data'], list):
                    return result['data']
            elif 'products' in result:
                return result['products']
            elif 'rCode' in result and result.get('rCode') == '0':
                # 성공 응답이지만 상품 리스트가 다른 키에 있을 수 있음
                return result.get('data', [])
        elif isinstance(result, list):
            return result
        
        return []
    
    except requests.exceptions.RequestException as e:
        print(f'골드박스 상품 조회 API 호출 실패: {e}')
        if hasattr(e.response, 'text'):
            print(f'응답 내용: {e.response.text}')
        return []
    
    except Exception as e:
        print(f'골드박스 상품 조회 중 예상치 못한 오류 발생: {e}')
        import traceback
        traceback.print_exc()
        return []


def get_bestseller_products(category_id):
    """
    특정 카테고리의 베스트셀러 상품 목록을 조회하는 API를 호출합니다.
    
    API 엔드포인트: GET /v2/providers/affiliate_open_api/apis/openapi/v1/products/best-categories/{categoryId}
    
    Args:
        category_id (str): 조회할 카테고리의 ID
    
    Returns:
        list: 상품 목록의 JSON 리스트. 오류 발생 시 빈 리스트 반환.
    """
    try:
        if not ACCESS_KEY or not SECRET_KEY:
            print('경고: 쿠팡 API 키가 설정되지 않았습니다.')
            return []
        
        if not category_id:
            print('경고: 카테고리 ID가 제공되지 않았습니다.')
            return []
        
        method = 'GET'
        path = f'/v2/providers/affiliate_open_api/apis/openapi/v1/products/best-categories/{category_id}'
        query = ''
        
        # HMAC 서명 생성
        auth_header = generate_hmac(method, path, query)
        
        # API 요청 URL 구성
        url = f'{BASE_URL}{path}'
        
        # 요청 헤더 설정
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json;charset=UTF-8'
        }
        
        # API 요청 실행
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # JSON 응답 파싱
        result = response.json()
        
        # 응답 구조에 따라 데이터 추출 (실제 응답 구조에 맞게 수정 필요)
        if isinstance(result, dict):
            # 일반적인 응답 구조: {'data': {...}, 'products': [...]}
            if 'data' in result:
                if isinstance(result['data'], dict) and 'products' in result['data']:
                    return result['data']['products']
                elif isinstance(result['data'], list):
                    return result['data']
            elif 'products' in result:
                return result['products']
            elif 'rCode' in result and result.get('rCode') == '0':
                # 성공 응답이지만 상품 리스트가 다른 키에 있을 수 있음
                return result.get('data', [])
        elif isinstance(result, list):
            return result
        
        return []
    
    except requests.exceptions.RequestException as e:
        print(f'베스트셀러 상품 조회 API 호출 실패 (카테고리 ID: {category_id}): {e}')
        if hasattr(e, 'response') and e.response is not None:
            print(f'응답 내용: {e.response.text}')
        return []
    
    except Exception as e:
        print(f'베스트셀러 상품 조회 중 예상치 못한 오류 발생 (카테고리 ID: {category_id}): {e}')
        import traceback
        traceback.print_exc()
        return []


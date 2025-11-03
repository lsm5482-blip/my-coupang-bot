"""
쿠팡 파트너스 API 호출 전담 모듈 (v2)
HMAC 서명 기반 인증을 사용하여 쿠팡 파트너스 API v2를 호출합니다.
"""
import requests
import os
import hmac
import hashlib
import json
import datetime


# 환경 변수에서 API 키 가져오기
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
CHANNEL_ID = os.environ.get('COUPANG_CHANNEL_ID')

# 쿠팡 파트너스 API 베이스 URL
BASE_URL = 'https://api-gateway.coupang.com'


def generate_hmac(method, path, body=''):
    """
    HMAC 서명을 생성합니다.
    쿠팡 파트너스 API v2 공식 문서에 따라 HMAC-SHA256 서명을 생성합니다.
    POST 요청 시 JSON body를 포함하여 서명을 생성합니다.
    
    Args:
        method (str): HTTP 메서드 (예: 'GET', 'POST')
        path (str): 요청 경로 (예: '/v2/providers/affiliate_open_api/apis/openapi/v2/products/reco')
        body (str): JSON body 문자열 (POST 요청 시 사용, 없을 경우 빈 문자열)
    
    Returns:
        tuple: (Authorization 헤더 문자열, 타임스탬프)
    """
    try:
        # 타임스탬프 생성 (밀리초 단위)
        timestamp = str(int(datetime.datetime.utcnow().timestamp() * 1000))
        
        # 서명 메시지 생성: timestamp + method + path + body
        # v2 API는 POST 방식이며 JSON body를 포함하여 서명 생성
        message = f'{timestamp}{method}{path}{body}'
        
        # HMAC-SHA256 서명 생성
        signature = hmac.new(
            SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Authorization 헤더 형식: CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp}, signature={signature}
        auth_header = f'CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp}, signature={signature}'
        
        return auth_header, timestamp
    
    except Exception as e:
        print(f'HMAC 서명 생성 중 오류 발생: {e}')
        raise


def get_recommended_products():
    """
    추천 상품 목록을 조회하는 API를 호출합니다.
    쿠팡 파트너스 API v2의 reco 엔드포인트를 POST 방식으로 호출합니다.
    
    API 엔드포인트: POST /v2/providers/affiliate_open_api/apis/openapi/v2/products/reco
    
    Returns:
        list: 상품 목록의 JSON 리스트. 오류 발생 시 빈 리스트 반환.
    """
    try:
        if not ACCESS_KEY or not SECRET_KEY:
            print('경고: 쿠팡 API 키가 설정되지 않았습니다.')
            return []
        
        method = 'POST'
        path = '/v2/providers/affiliate_open_api/apis/openapi/v2/products/reco'
        
        # 필수 JSON body 구성 (v2 API 파라미터 예제)
        request_body = {
            'device': {
                'id': 'TEMP_DEVICE_ID',
                'lmt': 0
            },
            'imp': {
                'imageSize': '200x200'
            },
            'user': {
                'puid': 'TEMP_USER_ID'
            },
            'affiliate': {
                'subId': CHANNEL_ID
            }
        }
        
        # JSON body를 문자열로 변환 (서명 생성용)
        body_str = json.dumps(request_body, separators=(',', ':'), ensure_ascii=False)
        
        # HMAC 서명 생성 (POST 요청이므로 body 포함)
        auth_header, timestamp = generate_hmac(method, path, body_str)
        
        # API 요청 URL 구성
        url = f'{BASE_URL}{path}'
        
        # 요청 헤더 설정
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json;charset=UTF-8'
        }
        
        # POST 요청 실행
        response = requests.post(url, headers=headers, json=request_body, timeout=30)
        response.raise_for_status()
        
        # JSON 응답 파싱
        result = response.json()
        
        # 응답 구조에 따라 데이터 추출
        if isinstance(result, dict):
            # 일반적인 응답 구조: {'data': [...], 'rCode': '0', ...}
            if 'data' in result:
                data = result['data']
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    # data가 딕셔너리인 경우, products 키가 있을 수 있음
                    if 'products' in data:
                        return data['products']
                    elif 'items' in data:
                        return data['items']
            elif 'rCode' in result and result.get('rCode') == '0':
                # 성공 응답이지만 상품 리스트가 다른 키에 있을 수 있음
                return result.get('data', [])
        elif isinstance(result, list):
            return result
        
        return []
    
    except requests.exceptions.RequestException as e:
        print(f'추천 상품 조회 API 호출 실패: {e}')
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f'응답 내용: {e.response.text}')
            except:
                pass
        return []
    
    except Exception as e:
        print(f'추천 상품 조회 중 예상치 못한 오류 발생: {e}')
        import traceback
        traceback.print_exc()
        return []

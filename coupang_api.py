from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
import requests
import json
import time
import hmac
import hashlib
import sys

class CoupangApiHandler:
    """
    쿠팡 파트너스 v1 API 핸들러
    'GET' 방식 + 'Query Parameter'를 포함하는 HMAC 서명 구현
    """

    def __init__(self):
        try:
            self.access_key = os.environ['COUPANG_ACCESS_KEY']
            self.secret_key = os.environ['COUPANG_SECRET_KEY']
            self.channel_id = os.environ['COUPANG_CHANNEL_ID']
        except KeyError as e:
            print(f"❌ 치명적 오류: GitHub Secrets에 {e}가 설정되지 않았습니다.", file=sys.stderr)
            sys.exit(1)

        self.base_url = "https://api-gateway.coupang.com"
        print("🔑 쿠팡 v1 API 핸들러 초기화 완료 (GET + Query HMAC 기준)")
    
    def _generate_hmac(self, method, path, query):
        """GET 방식 HMAC 서명 생성 (Query 포함)"""
        os.environ['TZ'] = 'GMT+0'
        datetime_gmt = time.strftime('%y%m%d', time.gmtime()) + 'T' + time.strftime('%H%M%S', time.gmtime()) + 'Z'
        
        # GET 방식은 'path'와 'query'를 모두 서명에 포함해야 함
        message = datetime_gmt + method + path + query
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return (
            f"CEA algorithm=HmacSHA256, "
            f"access-key={self.access_key}, "
            f"signed-date={datetime_gmt}, "
            f"signature={signature}"
        )

    def _request_api(self, method, path, query):
        """API 요청 공통 로직"""
        try:
            authorization = self._generate_hmac(method, path, query)
            headers = {"Authorization": authorization}
            url = f"{self.base_url}{path}?{query}"

            print(f"🚀 {method} API 호출 시작 (Path: {path})")
            print(f"   Query: {query}")
            
            response = requests.get(url, headers=headers)
            response.raise_for_status() # 200번대가 아니면 오류 발생
            
            result_json = response.json()
            print("✅ API 호출 성공! 상품 데이터를 반환합니다.")
            
            # v1 API는 응답 구조가 'data' 키 안에 상품 리스트가 있음
            return result_json.get('data', [])

        except requests.exceptions.RequestException as e:
            print(f"❌ API 호출 실패: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"    - 상태 코드: {e.response.status_code}", file=sys.stderr)
                print(f"    - 응답 내용: {e.response.text}", file=sys.stderr)
            return [] # 실패 시 빈 리스트 반환
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}", file=sys.stderr)
            return []

    def get_goldbox_products(self):
        """v1 골드박스 API 호출"""
        METHOD = "GET"
        PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
        QUERY = f"subId={self.channel_id}" # subId 쿼리 추가
        
        return self._request_api(METHOD, PATH, QUERY)
    
    def get_bestseller_products(self, category_id="1001"):
        """v1 베스트셀러 API 호출 (카테고리 ID 1001 = 패션의류/잡화)"""
        METHOD = "GET"
        PATH = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/bestcategories/{category_id}"
        QUERY = f"subId={self.channel_id}" # subId 쿼리 추가
        
        return self._request_api(METHOD, PATH, QUERY)
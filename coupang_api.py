import requests
import json
import time
import hmac
import hashlib
import os
import sys # 오류 출력을 위해 추가

class CoupangApiHandler:
    """
    쿠팡 파트 K너스 Reco API (v2) 핸들러
    'POST' 방식 + 'JSON Body'를 포함하는 HMAC 서명 구현
    """

    def __init__(self):
        try:
            self.access_key = os.environ['COUPANG_ACCESS_KEY']
            self.secret_key = os.environ['COUPANG_SECRET_KEY']
            self.channel_id = os.environ['COUPANG_CHANNEL_ID']
        except KeyError as e:
            print(f"❌ 치명적 오류: GitHub Secrets에 {e}가 설정되지 않았습니다.", file=sys.stderr)
            sys.exit(1) # Secrets 없이는 실행 불가능하므로 종료

        self.base_url = "https://api-gateway.coupang.com"
        print("🔑 쿠팡 Reco API 핸들러 초기화 완료 (POST + Body HMAC 기준)")

    def get_recommended_products(self):
        """
        Reco API (v2)를 호출하여 추천 상품 목록을 가져옵니다.
        'POST' + 'Body' HMAC 서명 로직을 100% 준수합니다.
        """
        METHOD = "POST"
        PATH = "/v2/providers/affiliate_open_api/apis/openapi/v2/products/reco"
        
        try:
            # 1. GMT 날짜시간 생성
            os.environ['TZ'] = 'GMT+0'
            datetime_gmt = time.strftime('%y%m%d', time.gmtime()) + 'T' + time.strftime('%H%M%S', time.gmtime()) + 'Z'
            
            # 2. POST Body (JSON) 구성
            body = {
                "device": { "id": "TEMP_DEVICE_ID", "lmt": 0 },
                "imp": { "imageSize": "200x200" },
                "user": { "puid": "TEMP_USER_ID" },
                "affiliate": { "subId": self.channel_id }
            }
            
            # 3. ★★★ HMAC 서명 생성 (가장 중요) ★★★
            # 'reco' API는 'body'를 공백 없이 JSON 문자열로 만들어 서명에 포함해야 함
            body_json_string = json.dumps(body, separators=(',', ':'))
            message = datetime_gmt + METHOD + PATH + body_json_string
            
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # 4. Authorization 헤더 완성
            authorization = (
                f"CEA algorithm=HmacSHA256, "
                f"access-key={self.access_key}, "
                f"signed-date={datetime_gmt}, "
                f"signature={signature}"
            )
            
            # 5. API 요청 구성
            url = self.base_url + PATH
            headers = {
                "Authorization": authorization,
                "Content-Type": "application/json;charset=UTF-8"
            }
            
            print(f"🚀 Reco API 호출 시작 (Path: {PATH})")
            print(f"   Sub-ID: {self.channel_id}")
            
            # 6. API 호출
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status() # 200번대가 아니면 오류 발생
            
            result_json = response.json()
            
            print("✅ Reco API 호출 성공! 상품 데이터를 반환합니다.")
            return result_json.get('data', []) # 상품 리스트 반환

        except requests.exceptions.RequestException as e:
            print(f"❌ API 호출 실패: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"    - 상태 코드: {e.response.status_code}", file=sys.stderr)
                print(f"    - 응답 내용: {e.response.text}", file=sys.stderr)
            return [] # 실패 시 빈 리스트 반환
            
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}", file=sys.stderr)
            return [] # 실패 시 빈 리스트 반환

# --- 아래 코드는 GitHub Actions에서는 실행되지 않지만,
# --- main.py와 make_html.py가 사용할 클래스를 정의합니다.
# --- (이 파일 자체는 클래스 정의 파일입니다)
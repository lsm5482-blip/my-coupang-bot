"""
쿠팡 파트너스 자동화 딜 사이트 생성기
골드박스와 카테고리별 베스트셀러 상품을 조회하여 index.html 생성
"""
import hashlib
import hmac
import base64
import json
import time
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional
import requests
from config import (
    COUPANG_ACCESS_KEY,
    COUPANG_SECRET_KEY,
    COUPANG_API_BASE_URL,
    REQUEST_TIMEOUT,
    CATEGORIES
)


class CoupangAPI:
    """쿠팡 파트너스 API 클라이언트"""
    
    def __init__(self, access_key: str, secret_key: str):
        if not access_key or not secret_key:
            raise ValueError("쿠팡 API 키가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = COUPANG_API_BASE_URL
    
    def _generate_signature(self, method: str, path: str, query_string: str, timestamp: str) -> str:
        """HMAC-SHA256 서명 생성"""
        message = f"{method}{path}{query_string}{timestamp}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """API 요청 실행"""
        method = 'GET'
        path = endpoint
        query_string = urllib.parse.urlencode(params or {}, doseq=True)
        timestamp = str(int(time.time() * 1000))
        
        signature = self._generate_signature(method, path, query_string, timestamp)
        
        headers = {
            'Authorization': f'CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={timestamp}, signature={signature}',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        
        url = f"{self.base_url}{endpoint}"
        if query_string:
            url += f"?{query_string}"
        
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API 요청 실패: {e}")
            return {}
    
    def get_goldbox_products(self, limit: int = 50) -> List[Dict]:
        """골드박스 상품 조회"""
        # 참고: 실제 쿠팡 API 엔드포인트는 공식 문서 확인 필요
        # 여기서는 일반적인 구조로 작성
        params = {
            'subId': '',  # 서브 ID (선택사항)
            'limit': limit
        }
        # 실제 엔드포인트는 쿠팡 파트너스 API 문서 확인 필요
        # 예시: '/v2/providers/affiliate_open_api/apis/openapi/products/goldbox'
        result = self._make_request('/v2/providers/affiliate_open_api/apis/openapi/products/goldbox', params)
        
        if result.get('data'):
            return result['data'].get('products', [])
        return []
    
    def get_category_bestsellers(self, category_id: str, limit: int = 20) -> List[Dict]:
        """카테고리별 베스트셀러 조회"""
        params = {
            'categoryId': category_id,
            'subId': '',
            'limit': limit
        }
        # 실제 엔드포인트는 쿠팡 파트너스 API 문서 확인 필요
        # 예시: '/v2/providers/affiliate_open_api/apis/openapi/products/bestcategory'
        result = self._make_request('/v2/providers/affiliate_open_api/apis/openapi/products/bestcategory', params)
        
        if result.get('data'):
            return result['data'].get('products', [])
        return []


class HTMLGenerator:
    """HTML 파일 생성기"""
    
    @staticmethod
    def escape_html(text: str) -> str:
        """HTML 이스케이프"""
        if not text:
            return ''
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
    
    @staticmethod
    def format_price(price: int) -> str:
        """가격 포맷팅"""
        return f"{price:,}원"
    
    @staticmethod
    def generate_product_card(product: Dict) -> str:
        """상품 카드 HTML 생성"""
        product_id = product.get('productId', '')
        product_name = HTMLGenerator.escape_html(product.get('productName', '상품명 없음'))
        product_price = product.get('productPrice', 0)
        discount_rate = product.get('discountRate', 0)
        product_image = product.get('productImage', '')
        product_url = product.get('productUrl', '')
        category_name = product.get('categoryName', '')
        
        # 할인 전 가격 계산
        original_price = int(product_price / (1 - discount_rate / 100)) if discount_rate > 0 else product_price
        
        card_html = f"""
        <div class="product-card">
            <div class="product-badge">{category_name}</div>
            <a href="{product_url}" target="_blank" rel="nofollow" class="product-link">
                <div class="product-image-wrapper">
                    <img src="{product_image}" alt="{product_name}" loading="lazy" onerror="this.src='https://via.placeholder.com/300?text=이미지+없음'">
                    {f'<span class="discount-badge">{discount_rate}%</span>' if discount_rate > 0 else ''}
                </div>
                <div class="product-info">
                    <h3 class="product-title">{product_name}</h3>
                    <div class="product-price">
                        {f'<span class="original-price">{HTMLGenerator.format_price(original_price)}</span>' if discount_rate > 0 else ''}
                        <span class="current-price">{HTMLGenerator.format_price(product_price)}</span>
                    </div>
                </div>
            </a>
        </div>
        """
        return card_html
    
    @staticmethod
    def generate_html(goldbox_products: List[Dict], category_products: Dict[str, List[Dict]]) -> str:
        """전체 HTML 생성"""
        current_time = datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')
        
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="쿠팡 파트너스 골드박스 & 카테고리별 베스트셀러 상품을 실시간으로 확인하세요!">
    <title>쿠팡 파트너스 딜 사이트 - 골드박스 & 베스트셀러</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .update-time {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-top: 10px;
        }}
        
        .section {{
            padding: 40px 20px;
        }}
        
        .section-title {{
            font-size: 2em;
            color: #333;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #ff6b6b;
        }}
        
        .products-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }}
        
        .product-card {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
        }}
        
        .product-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }}
        
        .product-link {{
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        
        .product-image-wrapper {{
            position: relative;
            width: 100%;
            padding-top: 100%;
            overflow: hidden;
            background: #f5f5f5;
        }}
        
        .product-image-wrapper img {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .discount-badge {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #ff6b6b;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .product-badge {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            z-index: 1;
        }}
        
        .product-info {{
            padding: 15px;
        }}
        
        .product-title {{
            font-size: 1em;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.4;
            height: 2.8em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}
        
        .product-price {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .original-price {{
            color: #999;
            text-decoration: line-through;
            font-size: 0.9em;
        }}
        
        .current-price {{
            color: #ff6b6b;
            font-weight: bold;
            font-size: 1.2em;
        }}
        
        .category-section {{
            margin-top: 50px;
        }}
        
        footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8em;
            }}
            
            .products-grid {{
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 15px;
            }}
            
            .section {{
                padding: 20px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏆 쿠팡 파트너스 딜 사이트</h1>
            <p>골드박스 & 카테고리별 베스트셀러를 한눈에!</p>
            <div class="update-time">마지막 업데이트: {current_time}</div>
        </header>
        
        <div class="section">
            <h2 class="section-title">✨ 골드박스 특가</h2>
            <div class="products-grid">
"""
        
        # 골드박스 상품 추가
        if goldbox_products:
            for product in goldbox_products:
                html += HTMLGenerator.generate_product_card(product)
        else:
            html += '<p style="text-align: center; padding: 40px; color: #999;">골드박스 상품을 불러오는 중...</p>'
        
        html += """
            </div>
        </div>
"""
        
        # 카테고리별 베스트셀러 추가
        for category_name, products in category_products.items():
            if products:
                html += f"""
        <div class="section category-section">
            <h2 class="section-title">🔥 {category_name} 베스트셀러</h2>
            <div class="products-grid">
"""
                for product in products:
                    html += HTMLGenerator.generate_product_card(product)
                
                html += """
            </div>
        </div>
"""
        
        html += f"""
        <footer>
            <p>이 사이트는 쿠팡 파트너스 활동을 통해 일정 수수료를 받을 수 있습니다.</p>
            <p>© {datetime.now().year} 쿠팡 파트너스 딜 사이트 | 자동 업데이트 시스템</p>
        </footer>
    </div>
</body>
</html>
"""
        return html


def main():
    """메인 실행 함수"""
    print("쿠팡 파트너스 딜 사이트 생성 시작...")
    
    try:
        # API 클라이언트 초기화
        api = CoupangAPI(COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY)
        
        # 골드박스 상품 조회
        print("골드박스 상품 조회 중...")
        goldbox_products = api.get_goldbox_products(limit=50)
        print(f"골드박스 상품 {len(goldbox_products)}개 조회 완료")
        
        # 카테고리별 베스트셀러 조회
        print("카테고리별 베스트셀러 조회 중...")
        category_products = {}
        for category_name, category_id in CATEGORIES.items():
            products = api.get_category_bestsellers(category_id, limit=20)
            if products:
                category_products[category_name] = products
                print(f"{category_name}: {len(products)}개 상품 조회 완료")
        
        # HTML 생성
        print("HTML 생성 중...")
        html_content = HTMLGenerator.generate_html(goldbox_products, category_products)
        
        # index.html 저장
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✅ index.html 생성 완료!")
        print(f"골드박스: {len(goldbox_products)}개, 카테고리별: {sum(len(p) for p in category_products.values())}개")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        # 오류 발생 시에도 기본 HTML 생성
        error_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>오류 발생</title>
</head>
<body>
    <h1>데이터를 불러오는 중 오류가 발생했습니다.</h1>
    <p>{str(e)}</p>
    <p>잠시 후 다시 시도해주세요.</p>
</body>
</html>"""
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(error_html)


if __name__ == '__main__':
    main()


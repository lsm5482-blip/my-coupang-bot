"""
쿠팡 파트너스 딜 사이트 HTML 생성 스크립트
coupang_api.py 모듈을 사용하여 상품 데이터를 가져와 index.html을 생성합니다.
"""
import os
from datetime import datetime
import coupang_api


def escape_html(text):
    """
    HTML 특수문자를 이스케이프합니다.
    
    Args:
        text (str): 이스케이프할 텍스트
    
    Returns:
        str: 이스케이프된 텍스트
    """
    if not text:
        return ''
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def format_price(price):
    """
    가격을 포맷팅합니다.
    
    Args:
        price (int or str): 가격
    
    Returns:
        str: 포맷팅된 가격 문자열 (예: "10,000원")
    """
    try:
        price_int = int(price)
        return f"{price_int:,}원"
    except (ValueError, TypeError):
        return "가격 정보 없음"


def generate_product_card(product):
    """
    상품 데이터를 HTML 카드 문자열로 변환합니다.
    상품 이미지, 상품명, 가격을 포함하며 전체가 파트너스 링크로 감싸집니다.
    
    Args:
        product (dict): 상품 정보 딕셔너리
    
    Returns:
        str: HTML 카드 문자열
    """
    # 상품 데이터 추출 (쿠팡 API 응답 구조에 따라 키명이 다를 수 있음)
    product_name = escape_html(product.get('productName') or product.get('title') or '상품명 없음')
    product_price = product.get('productPrice') or product.get('price') or product.get('salePrice') or 0
    product_image = product.get('productImage') or product.get('imageUrl') or product.get('image') or ''
    product_url = product.get('productUrl') or product.get('link') or product.get('url') or '#'
    discount_rate = product.get('discountRate') or product.get('discount') or 0
    category_name = escape_html(product.get('categoryName') or product.get('category') or '')
    
    # 할인 전 가격 계산 (할인율이 있는 경우)
    try:
        discount_rate_float = float(discount_rate)
        if discount_rate_float > 0 and discount_rate_float < 100:
            original_price = int(float(product_price) / (1 - discount_rate_float / 100))
        else:
            original_price = None
    except (ValueError, TypeError, ZeroDivisionError):
        original_price = None
    
    # HTML 카드 생성
    card_html = f'''
        <div class="product-card">
'''
    
    # 카테고리 배지 (있는 경우)
    if category_name:
        card_html += f'            <div class="product-badge">{category_name}</div>\n'
    
    # 파트너스 링크로 전체 카드 감싸기
    card_html += f'''            <a href="{product_url}" target="_blank" rel="nofollow" class="product-link">
                <div class="product-image-wrapper">
                    <img src="{product_image}" alt="{product_name}" loading="lazy" onerror="this.src='https://via.placeholder.com/300?text=이미지+없음'">
'''
    
    # 할인 배지 (있는 경우)
    if discount_rate and float(discount_rate) > 0:
        card_html += f'                    <span class="discount-badge">{int(discount_rate)}%</span>\n'
    
    card_html += f'''                </div>
                <div class="product-info">
                    <h3 class="product-title">{product_name}</h3>
                    <div class="product-price">
'''
    
    # 할인 전 가격 (있는 경우)
    if original_price:
        card_html += f'                        <span class="original-price">{format_price(original_price)}</span>\n'
    
    # 현재 가격
    card_html += f'                        <span class="current-price">{format_price(product_price)}</span>\n'
    
    card_html += '''                    </div>
                </div>
            </a>
        </div>
'''
    
    return card_html


def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("쿠팡 파트너스 딜 사이트 HTML 생성 시작")
    print("=" * 50)
    
    try:
        # 1. 골드박스 상품 조회
        print("\n[1/4] 골드박스 상품 조회 중...")
        goldbox_products = coupang_api.get_goldbox_products()
        print(f"✓ 골드박스 상품 {len(goldbox_products)}개 조회 완료")
        
        # 2. 베스트셀러 상품 조회 (카테고리 ID: 1001)
        print("\n[2/4] 베스트셀러 상품 조회 중...")
        bestseller_products = coupang_api.get_bestseller_products(category_id='1001')
        print(f"✓ 베스트셀러 상품 {len(bestseller_products)}개 조회 완료")
        
        # 3. HTML 카드 생성
        print("\n[3/4] HTML 카드 생성 중...")
        
        # 골드박스 카드 생성
        goldbox_cards_html = ''
        if goldbox_products:
            for product in goldbox_products:
                goldbox_cards_html += generate_product_card(product)
        else:
            goldbox_cards_html = '<p style="text-align: center; padding: 40px; color: #999;">골드박스 상품을 불러오는 중...</p>'
        
        # 베스트셀러 카드 생성
        bestseller_cards_html = ''
        if bestseller_products:
            for product in bestseller_products:
                bestseller_cards_html += generate_product_card(product)
        else:
            bestseller_cards_html = '<p style="text-align: center; padding: 40px; color: #999;">베스트셀러 상품을 불러오는 중...</p>'
        
        print(f"✓ 골드박스 카드 {len(goldbox_products)}개, 베스트셀러 카드 {len(bestseller_products)}개 생성 완료")
        
        # 4. template.html 읽기
        print("\n[4/4] HTML 템플릿 로드 및 치환 중...")
        template_path = 'template.html'
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
        
        # 5. 치환 작업
        current_time = datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')
        final_html = (html_template
                     .replace('%%UPDATE_TIME%%', current_time)
                     .replace('%%GOLDBOX_CARDS%%', goldbox_cards_html)
                     .replace('%%BESTSELLER_CARDS%%', bestseller_cards_html))
        
        # 6. docs 폴더 생성 (없는 경우)
        docs_dir = './docs'
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            print(f"✓ docs 폴더 생성 완료")
        
        # 7. index.html 저장
        output_path = './docs/index.html'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        print(f"\n✅ HTML 생성 완료!")
        print(f"   저장 경로: {output_path}")
        print(f"   골드박스: {len(goldbox_products)}개")
        print(f"   베스트셀러: {len(bestseller_products)}개")
        print(f"   업데이트 시간: {current_time}")
        print("=" * 50)
        
    except FileNotFoundError as e:
        print(f"\n❌ 파일 오류: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())


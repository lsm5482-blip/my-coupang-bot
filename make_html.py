import os
import datetime
import sys
from coupang_api import CoupangApiHandler # v1 핸들러 임포트

def create_product_card(item):
    """쿠팡 API 응답(item)으로 HTML 카드 1개를 생성"""
    
    # v1 API 응답 필드명 (productUrl, productImage, productName, productPrice)
    product_url = item.get('productUrl', '#')
    product_image = item.get('productImage', '')
    product_name = item.get('productName', '상품명 없음')
    product_price = item.get('productPrice', 0)
    
    # 가격 포맷팅 (예: 10000 -> 10,000)
    try:
        price_formatted = f"{int(product_price):,}"
    except ValueError:
        price_formatted = product_price

    return f"""
    <div class="product-card">
        <a href="{product_url}" target="_blank" rel="noopener sponsored">
            <img src="{product_image}" alt="{product_name}" loading="lazy">
            <div class="product-info">
                <div class="product-name">{product_name}</div>
                <div class="product-price">{price_formatted}원</div>
            </div>
        </a>
    </div>
    """

def main():
    print("============================================")
    print("쿠팡 파트너스 v1 딜 사이트 HTML 생성 시작")
    print("============================================")
    
    try:
        # 1. API 핸들러 초기화
        print("[1/3] 쿠팡 API 핸들러 초기화...")
        api_handler = CoupangApiHandler()
        
        # 2. 상품 데이터 조회
        print("[2/3] 상품 데이터 조회 시작...")
        
        # 골드박스 상품 조회
        print("  - 골드박스 상품 조회 중...")
        goldbox_items = api_handler.get_goldbox_products()
        
        # 베스트셀러 상품 조회 (카테고리 1001 = 패션)
        print("  - 베스트셀러(1001) 상품 조회 중...")
        bestseller_items = api_handler.get_bestseller_products(category_id="1001")
        
        if not goldbox_items and not bestseller_items:
            print("❌ 골드박스와 베스트셀러 상품을 모두 불러오지 못했습니다. API 로그를 확인하세요.")
            # 실패해도 빈 페이지만 만들도록 스크립트를 중단하지는 않습니다.
        
        # 3. HTML 카드 생성
        print("[3/3] HTML 코드 생성 중...")
        goldbox_html = "".join([create_product_card(item) for item in goldbox_items])
        bestseller_html = "".join([create_product_card(item) for item in bestseller_items])
        
        if not goldbox_html:
            goldbox_html = "<p>오늘의 골드박스 상품을 불러오는 데 실패했습니다.</p>"
            
        if not bestseller_html:
            bestseller_html = "<p>오늘의 베스트셀러 상품을 불러오는 데 실패했습니다.</p>"

        # 4. 템플릿 파일 읽기
        with open('template.html', 'r', encoding='utf-8') as f:
            template = f.read()

        # 5. 템플릿에 데이터 치환
        now = datetime.datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
        output_html = template.replace("%%UPDATE_TIME%%", f"{now} 기준")
        output_html = output_html.replace("%%GOLDBOX_CARDS%%", goldbox_html)
        output_html = output_html.replace("%%BESTSELLER_CARDS%%", bestseller_html)

        # 6. 최종 index.html 파일 저장
        output_dir = './docs'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, 'index.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
            
        print("============================================")
        print(f"✅ HTML 생성 완료!")
        print(f"   저장 경로: {output_path}")
        print(f"   업데이트 시간: {now}")
        print("============================================")

    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
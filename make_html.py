from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
from datetime import datetime, timedelta
import sys
from coupang_api import CoupangApiHandler # v1 핸들러 임포트

def create_product_card(item):
    """쿠팡 API 응답(item)으로 HTML 카드 1개를 생성"""
    
    # 기획전 API 응답 필드명
    product_url = item.get('productUrl', '#')
    product_image = item.get('productImage', '')
    product_name = item.get('productName', '상품명 없음')
    original_price = item.get('originalPrice', 0)
    sale_price = item.get('salePrice', 0)
    discount_rate = item.get('discountRate', 0)
    
    # 가격 포맷팅 (천 단위 콤마)
    try:
        original_price_formatted = f"{int(original_price):,}"
        sale_price_formatted = f"{int(sale_price):,}"
    except (ValueError, TypeError):
        original_price_formatted = str(original_price)
        sale_price_formatted = str(sale_price)

    # 할인율 배지 생성
    discount_badge = ''
    if discount_rate > 0:
        discount_badge = f'<span class="discount-badge">{int(discount_rate)}% OFF</span>'

    return f"""
    <div class="product-card">
        {discount_badge}
        <a href="{product_url}" target="_blank" rel="noopener sponsored">
            <img src="{product_image}" alt="{product_name}" loading="lazy">
            <div class="product-info">
                <div class="product-name">{product_name}</div>
                <div class="product-price-container">
                    {f'<span class="original-price">{original_price_formatted}원</span>' if original_price > 0 else ''}
                    <span class="sale-price">{sale_price_formatted}원</span>
                </div>
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
        print("[1/4] 쿠팡 API 핸들러 초기화...")
        api_handler = CoupangApiHandler()
        
        # 2. 카테고리 설정
        CATEGORIES_TO_DISPLAY = {
            '가전디지털': '1016',
            '헬스/건강식품': '1024',
            '여성패션': '1001'
        }
        
        # 3. 상품 데이터 조회
        print("[2/4] 상품 데이터 조회 시작...")
        
        # 기획전 목록 조회
        print("  - 기획전 목록 조회 중...")
        event_list = api_handler.get_special_event_list()
        
        if not event_list:
            print("❌ 기획전 목록을 불러오지 못했습니다.")
            event_items = []
        else:
            # 첫 번째 기획전 ID 가져오기
            event_id = None
            if isinstance(event_list, list) and len(event_list) > 0:
                event_id = event_list[0].get('eventId') or event_list[0].get('id')
            elif isinstance(event_list, dict):
                # data 안에 리스트가 있을 수 있음
                data = event_list.get('data', [])
                if isinstance(data, list) and len(data) > 0:
                    event_id = data[0].get('eventId') or data[0].get('id')
            
            if event_id:
                print(f"  - 기획전 ID: {event_id} 상품 조회 중...")
                event_items = api_handler.get_special_event_products(event_id)
            else:
                print("❌ 기획전 ID를 찾을 수 없습니다.")
                event_items = []
        
        # 상품 데이터 처리: 할인율 계산 및 필터링
        processed_items = []
        for item in event_items:
            original_price = item.get('originalPrice', 0)
            sale_price = item.get('salePrice', 0)
            
            # originalPrice가 0이거나 salePrice보다 낮으면 제외
            if original_price <= 0 or original_price < sale_price:
                continue
            
            # 할인율 계산
            discount_rate = round(((original_price - sale_price) / original_price) * 100)
            item['discountRate'] = discount_rate
            item['originalPrice'] = original_price
            item['salePrice'] = sale_price
            processed_items.append(item)
        
        # 할인율이 높은 순으로 정렬
        processed_items.sort(key=lambda x: x.get('discountRate', 0), reverse=True)
        
        if not processed_items:
            print("❌ 처리된 기획전 상품이 없습니다.")
        
        # 카테고리별 베스트셀러 상품 조회
        category_data = {}
        for category_name, category_id in CATEGORIES_TO_DISPLAY.items():
            print(f"  - 베스트셀러({category_name}, {category_id}) 상품 조회 중...")
            items = api_handler.get_bestseller_products(category_id=category_id)
            category_data[category_name] = items
        
        if not processed_items and not any(category_data.values()):
            print("❌ 기획전과 베스트셀러 상품을 모두 불러오지 못했습니다. API 로그를 확인하세요.")
        
        # 4. HTML 카드 생성
        print("[3/4] HTML 코드 생성 중...")
        event_html = "".join([create_product_card(item) for item in processed_items])
        
        if not event_html:
            event_html = "<p>오늘의 기획전 상품을 불러오는 데 실패했습니다.</p>"
        
        # 카테고리별 HTML 카드 생성
        category_htmls = {}
        for category_name, items in category_data.items():
            category_html = "".join([create_product_card(item) for item in items])
            if not category_html:
                category_html = f"<p>{category_name} 카테고리의 베스트셀러 상품을 불러오는 데 실패했습니다.</p>"
            category_htmls[category_name] = category_html

        # 5. 템플릿 파일 읽기
        with open('template.html', 'r', encoding='utf-8') as f:
            template = f.read()

        # 6. 메인 콘텐츠 HTML 생성
        print("[4/4] HTML 구조 생성 중...")
        main_content_html = f"""
        <div class="special-event-section">
            <h2 class="section-title">✨ 기획전 특가</h2>
            <div class="grid-container">
                {event_html}
            </div>
        </div>
"""
        
        # 카테고리별 섹션 추가
        for category_name in CATEGORIES_TO_DISPLAY.keys():
            category_html = category_htmls.get(category_name, "<p>상품을 불러오는 데 실패했습니다.</p>")
            main_content_html += f"""
        <div class="category-section">
            <h2 class="section-title" style="margin-top: 40px;">🔥 {category_name} 베스트셀러</h2>
            <div class="grid-container">
                {category_html}
            </div>
        </div>
"""

        # 7. 템플릿에 데이터 치환
        now = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y년 %m월 %d일 %H시 %M분")
        output_html = template.replace("%%UPDATE_TIME%%", f"{now} 기준")
        output_html = output_html.replace("%%MAIN_CONTENT%%", main_content_html)

        # 8. 최종 index.html 파일 저장
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
from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
from datetime import datetime, timedelta
import sys
import time
import json
import requests
from coupang_api import CoupangApiHandler # v1 핸들러 임포트

# 가격 기록 DB 파일
DB_FILE = 'price_history.json'

def load_price_db():
    """가격 기록 DB 로드"""
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_price_db(db):
    """가격 기록 DB 저장"""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def create_product_card(item, is_all_time_low=False):
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
    
    # 역대 최저가 배지 생성
    all_time_low_badge = ''
    if is_all_time_low:
        all_time_low_badge = '<span class="badge-all-time-low">🔥 역대 최저가!</span>'

    return f"""
    <div class="product-card">
        {discount_badge}
        {all_time_low_badge}
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

def process_products(product_list, db=None):
    """상품 리스트를 처리하여 할인율 계산 및 필터링, 역대 최저가 기록"""
    if db is None:
        db = {}
    
    processed_items = []
    for item in product_list:
        # API 응답 필드명이 다를 수 있으므로 여러 필드명 시도
        original_price = item.get('originalPrice', 0) or item.get('productPrice', 0) or 0
        sale_price = item.get('salePrice', 0) or item.get('productPrice', 0) or 0
        
        # 숫자로 변환 시도
        try:
            original_price = float(original_price) if original_price else 0
            sale_price = float(sale_price) if sale_price else 0
        except (ValueError, TypeError):
            original_price = 0
            sale_price = 0
        
        # originalPrice가 0이거나 salePrice보다 낮으면 제외
        # 단, originalPrice가 없고 salePrice만 있는 경우는 허용 (할인율 계산 없이)
        if original_price <= 0:
            # originalPrice가 없으면 salePrice를 originalPrice로 사용
            if sale_price > 0:
                original_price = sale_price
            else:
                continue
        
        if original_price < sale_price:
            continue
        
        # 할인율 계산
        discount_rate = round(((original_price - sale_price) / original_price) * 100)
        item['discountRate'] = discount_rate
        item['originalPrice'] = original_price
        item['salePrice'] = sale_price
        
        # 역대 최저가 기록 및 비교
        product_id = str(item.get('productId', ''))
        current_price = sale_price
        is_all_time_low = False
        
        if product_id:
            if product_id not in db:
                # 처음 보는 상품이면
                db[product_id] = {'history': [current_price]}
                is_all_time_low = True  # 첫 가격이 역대 최저가
            else:
                # 기록이 있는 상품이면
                all_time_low_price = min(db[product_id]['history'])
                if current_price < all_time_low_price:
                    # 기록 갱신 시
                    is_all_time_low = True
                db[product_id]['history'].append(current_price)  # 현재 가격을 기록에 추가
        
        item['isAllTimeLow'] = is_all_time_low
        processed_items.append(item)
    
    # 할인율이 높은 순으로 정렬
    processed_items.sort(key=lambda x: x.get('discountRate', 0), reverse=True)
    return processed_items

def main():
    print("============================================")
    print("쿠팡 파트너스 다중 페이지 딜 사이트 HTML 생성 시작")
    print("============================================")
    
    try:
        # 0. 가격 기록 DB 로드
        print("[0/7] 가격 기록 DB 로드...")
        db = load_price_db()
        print(f"  ✓ {len(db)}개 상품의 가격 기록을 불러왔습니다.")
        
        # 1. 기본 템플릿 로드
        print("[1/7] 기본 템플릿 로드...")
        with open('template.html', 'r', encoding='utf-8') as f:
            base_template = f.read()
        
        # 2. API 핸들러 초기화
        print("[2/7] 쿠팡 API 핸들러 초기화...")
        api_handler = CoupangApiHandler()
        
        # 3. 카테고리 맵 정의
        ALL_CATEGORIES = {
            '1016': ('가전/디지털', 'digital'),
            '1024': ('헬스/건강식품', 'health'),
            '1001': ('여성패션', 'womens-fashion'),
            '1002': ('남성패션', 'mens-fashion'),
            '1003': ('화장품', 'beauty'),
            '1004': ('식품', 'food'),
            '1005': ('생활용품', 'home'),
            '1006': ('도서', 'books'),
            '1007': ('스포츠', 'sports'),
            '1008': ('완구', 'toys'),
            '1009': ('반려동물', 'pets'),
            '1010': ('출산/유아동', 'baby'),
            '1011': ('식물', 'plants'),
            '1012': ('자동차', 'automotive'),
            '1013': ('기타', 'others')
        }
        
        TOP_CATEGORIES = {
            '1016': ('가전/디지털', 'digital'),
            '1024': ('헬스/건강식품', 'health'),
            '1001': ('여성패션', 'womens-fashion'),
            '1003': ('화장품', 'beauty'),
            '1004': ('식품', 'food')
        }
        
        # 4. 변수 초기화
        main_page_sections_html = ""
        category_hub_html = ""
        
        # 골드박스 및 베스트셀러 HTML (메인 페이지용)
        goldbox_html = ""
        bestseller_html = ""
        
        # 5. 골드박스 상품 조회
        print("[3/6] 골드박스 상품 조회...")
        try:
            print("  - 골드박스 상품 조회 중...")
            
            METHOD = "GET"
            PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
            QUERY = f"subId={api_handler.channel_id}"
            
            authorization = api_handler._generate_hmac(METHOD, PATH, QUERY)
            headers = {"Authorization": authorization}
            url = f"{api_handler.base_url}{PATH}?{QUERY}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            product_list = response.json().get('data', [])
            
            # API 호출 직후 1초 대기
            time.sleep(1)
            
            processed_items = process_products(product_list, db)
            goldbox_html = "".join([create_product_card(item, item.get('isAllTimeLow', False)) for item in processed_items])
            print(f"  ✓ 골드박스 상품 {len(processed_items)}개 처리 완료")
        
        except Exception as e:
            print(f"  ❌ 골드박스 상품 조회 실패: {e}")
        
        # 6. 베스트셀러 상품 조회 (메인 페이지용)
        print("[4/6] 베스트셀러 상품 조회...")
        try:
            # TOP 5 카테고리 중 첫 번째 카테고리로 베스트셀러 조회
            first_top_category_id = list(TOP_CATEGORIES.keys())[0]
            category_name = TOP_CATEGORIES[first_top_category_id][0]
            
            print(f"  - 베스트셀러({category_name}, {first_top_category_id}) 상품 조회 중...")
            items = api_handler.get_bestseller_products(category_id=first_top_category_id)
            
            # API 호출 직후 1초 대기
            time.sleep(1)
            
            if items:
                # 베스트셀러는 가격 기록 없이 처리 (간단히)
                bestseller_html = "".join([create_product_card(item, False) for item in items[:10]])
                print(f"  ✓ 베스트셀러 상품 {len(items)}개 처리 완료")
        except Exception as e:
            print(f"  ❌ 베스트셀러 상품 조회 실패: {e}")
        
        # 7. 메인 루프 (15개 카테고리 전체 반복)
        print("[5/6] 카테고리별 상세 페이지 생성...")
        output_dir = './docs'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for category_id, (category_name, category_slug) in ALL_CATEGORIES.items():
            try:
                print(f"  - {category_name} ({category_id}) 처리 중...")
                
                # API 호출 전 2초 대기 (API 안정성을 위해, 504 에러 방지)
                time.sleep(2)
                
                # API 호출: bestcategories (재시도 로직 포함)
                METHOD = "GET"
                PATH = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/bestcategories/{category_id}"
                QUERY = f"subId={api_handler.channel_id}"
                
                authorization = api_handler._generate_hmac(METHOD, PATH, QUERY)
                headers = {"Authorization": authorization}
                url = f"{api_handler.base_url}{PATH}?{QUERY}"
                
                # 504 에러 재시도 로직 (최대 3회)
                max_retries = 3
                retry_count = 0
                response = None
                
                while retry_count < max_retries:
                    try:
                        response = requests.get(url, headers=headers, timeout=30)
                        response.raise_for_status()
                        break  # 성공하면 루프 탈출
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 504 and retry_count < max_retries - 1:
                            retry_count += 1
                            wait_time = (retry_count * 2) + 2  # 2초, 4초, 6초...
                            print(f"    ⚠ 504 Gateway Timeout 발생. {wait_time}초 후 재시도 ({retry_count}/{max_retries-1})...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise  # 다른 에러이거나 재시도 횟수 초과
                    except requests.exceptions.Timeout:
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            wait_time = (retry_count * 2) + 2
                            print(f"    ⚠ Timeout 발생. {wait_time}초 후 재시도 ({retry_count}/{max_retries-1})...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise
                
                result_json = response.json()
                product_list = result_json.get('data', [])
                
                # 디버깅: API 응답 확인
                print(f"    📊 API 응답: 총 {len(product_list)}개 상품 수신")
                if len(product_list) > 0:
                    sample_item = product_list[0]
                    print(f"    📋 샘플 상품 필드: {list(sample_item.keys())}")
                    print(f"    💰 샘플 가격 정보: originalPrice={sample_item.get('originalPrice', 'N/A')}, salePrice={sample_item.get('salePrice', 'N/A')}, productPrice={sample_item.get('productPrice', 'N/A')}")
                
                # API 호출 직후 2초 대기 (서버 부하 방지)
                time.sleep(2)
                
                # 상품 처리
                processed_items = process_products(product_list, db)
                
                print(f"    📦 필터링 후: {len(processed_items)}개 상품")
                
                if not processed_items:
                    print(f"    ⚠ {category_name} 상품이 없습니다. (필터링 조건: originalPrice > 0 && originalPrice >= salePrice)")
                    continue
                
                # (A) 전체 상품 HTML
                all_products_html = "".join([create_product_card(item, item.get('isAllTimeLow', False)) for item in processed_items])
                
                # (B) 미리보기 HTML (상위 5개)
                preview_products_html = "".join([create_product_card(item, item.get('isAllTimeLow', False)) for item in processed_items[:5]])
                
                # 작업 1: 상세 페이지 저장
                page_html = base_template.replace("%%PAGE_TITLE%%", f"{category_name} 핫딜")
                page_html = page_html.replace("%%UPDATE_TIME%%", f"{(datetime.utcnow() + timedelta(hours=9)).strftime('%Y년 %m월 %d일 %H시 %M분')} 기준")
                page_html = page_html.replace("%%GOLDBOX_CARDS%%", "")
                page_html = page_html.replace("%%RECOMMENDATION_CARDS%%", "")
                page_html = page_html.replace("%%MAIN_CONTENT%%", f"""
        <div class="category-detail-section">
            <h2 class="section-title">{category_name} 핫딜</h2>
            <div class="grid-container">
                {all_products_html}
            </div>
        </div>
""")
                
                category_file_path = os.path.join(output_dir, f"{category_slug}.html")
                with open(category_file_path, 'w', encoding='utf-8') as f:
                    f.write(page_html)
                
                print(f"    ✓ {category_slug}.html 저장 완료 ({len(processed_items)}개 상품)")
                
                # 작업 2: 허브 페이지 링크 누적
                category_hub_html += f'<a href="{category_slug}.html" class="category-link">{category_name}</a>\n        '
                
                # 작업 3: 메인 페이지 섹션 누적 (TOP 5만)
                if category_id in TOP_CATEGORIES:
                    main_page_sections_html += f"""
        <div class="category-section">
            <h2 class="section-title" style="margin-top: 40px;">🔥 {category_name} 핫딜</h2>
            <div class="grid-container">
                {preview_products_html}
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <a href="{category_slug}.html" style="display: inline-block; padding: 10px 20px; background-color: #FF416C; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">더보기 →</a>
            </div>
        </div>
"""
                    print(f"    ✓ 메인 페이지 섹션 추가 완료")
            
            except Exception as e:
                print(f"    ❌ {category_name} 처리 실패: {e}")
                continue
        
        # 8. 최종 2개 페이지 저장
        print("[6/6] 최종 페이지 저장...")
        now = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y년 %m월 %d일 %H시 %M분")
        
        # (1) 허브 페이지: category.html
        hub_html = base_template.replace("%%PAGE_TITLE%%", "카테고리 전체보기")
        hub_html = hub_html.replace("%%UPDATE_TIME%%", f"{now} 기준")
        hub_html = hub_html.replace("%%GOLDBOX_CARDS%%", "")
        hub_html = hub_html.replace("%%RECOMMENDATION_CARDS%%", "")
        
        # 카테고리 링크 스타일 추가
        category_hub_content = f"""
        <div class="category-hub-section">
            <h2 class="section-title">전체 카테고리</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px;">
                {category_hub_html}
            </div>
        </div>
"""
        hub_html = hub_html.replace("%%MAIN_CONTENT%%", category_hub_content)
        
        hub_file_path = os.path.join(output_dir, 'category.html')
        with open(hub_file_path, 'w', encoding='utf-8') as f:
            f.write(hub_html)
        print(f"  ✓ category.html 저장 완료")
        
        # (2) 메인 페이지: index.html
        main_content = ""
        
        # 골드박스 섹션
        if goldbox_html:
            main_content += f"""
        <div class="goldbox-section">
            <h2 class="section-title">✨ 골드박스 특가</h2>
            <div class="grid-container">
                {goldbox_html}
            </div>
        </div>
"""
        
        # 베스트셀러 섹션
        if bestseller_html:
            main_content += f"""
        <div class="bestseller-section">
            <h2 class="section-title" style="margin-top: 40px;">🔥 베스트셀러</h2>
            <div class="grid-container">
                {bestseller_html}
            </div>
        </div>
"""
        
        # TOP 5 카테고리 섹션
        main_content += main_page_sections_html
        
        main_html = base_template.replace("%%PAGE_TITLE%%", "쿠팡 실시간 핫딜")
        main_html = main_html.replace("%%UPDATE_TIME%%", f"{now} 기준")
        main_html = main_html.replace("%%GOLDBOX_CARDS%%", "")
        main_html = main_html.replace("%%RECOMMENDATION_CARDS%%", "")
        main_html = main_html.replace("%%MAIN_CONTENT%%", main_content)
        
        main_file_path = os.path.join(output_dir, 'index.html')
        with open(main_file_path, 'w', encoding='utf-8') as f:
            f.write(main_html)
        print(f"  ✓ index.html 저장 완료")
        
        # 9. 가격 기록 DB 저장
        print("[7/7] 가격 기록 DB 저장...")
        save_price_db(db)
        print(f"  ✓ {len(db)}개 상품의 가격 기록을 저장했습니다.")
        
        print("============================================")
        print(f"✅ 모든 페이지 생성 완료!")
        print(f"   메인 페이지: {main_file_path}")
        print(f"   허브 페이지: {hub_file_path}")
        print(f"   업데이트 시간: {now}")
        print("============================================")

    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

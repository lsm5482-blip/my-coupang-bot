"""
쿠팡 파트너스 API 설정
GitHub Secrets에서 환경 변수로 주입됩니다.
"""
import os

# 쿠팡 파트너스 API 키 (GitHub Secrets에서 주입)
COUPANG_ACCESS_KEY = os.getenv('COUPANG_ACCESS_KEY', '')
COUPANG_SECRET_KEY = os.getenv('COUPANG_SECRET_KEY', '')

# 쿠팡 파트너스 API 엔드포인트
COUPANG_API_BASE_URL = 'https://api-gateway.coupang.com'

# API 호출 설정
REQUEST_TIMEOUT = 30

# 카테고리 설정 (쿠팡 카테고리 ID)
CATEGORIES = {
    '전자기기': '1001',
    '패션': '1002',
    '화장품': '1003',
    '식품': '1004',
    '생활용품': '1005',
    '도서': '1006',
    '스포츠': '1007',
    '완구': '1008',
}


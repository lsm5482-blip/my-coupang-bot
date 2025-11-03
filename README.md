# 🏆 쿠팡 파트너스 100% 자동화 딜 사이트

쿠팡 API를 이용해 '골드박스'와 '카테고리별 베스트셀러' 상품 정보를 1시간마다 자동으로 가져와 GitHub Pages로 무료 호스팅하는 프로젝트입니다.

## 📋 프로젝트 개요

- **목표**: 쿠팡 파트너스 상품을 자동으로 수집하여 정적 HTML 사이트 생성
- **자동화**: GitHub Actions를 통한 1시간마다 자동 업데이트
- **호스팅**: GitHub Pages (무료 정적 호스팅)
- **기술 스택**: Python, GitHub Actions, GitHub Pages

## 🚀 시작하기

### 1. 저장소 준비

1. 이 저장소를 포크하거나 클론합니다
2. GitHub Settings > Pages에서 `gh-pages` 브랜치를 소스로 설정합니다

### 2. 쿠팡 파트너스 API 키 설정

1. [쿠팡 파트너스](https://partners.coupang.com/)에서 API 키를 발급받습니다
2. GitHub 저장소의 **Settings > Secrets and variables > Actions**로 이동
3. 다음 Secrets를 추가합니다:
   - `COUPANG_ACCESS_KEY`: 쿠팡 파트너스 Access Key
   - `COUPANG_SECRET_KEY`: 쿠팡 파트너스 Secret Key

### 3. GitHub Actions 활성화

1. 저장소의 **Actions** 탭으로 이동
2. 워크플로우가 활성화되어 있는지 확인
3. `workflow_dispatch`를 통해 수동으로 실행하여 테스트 가능

## 📁 프로젝트 구조

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions 워크플로우
├── main.py                      # 메인 스크립트 (API 호출 및 HTML 생성)
├── config.py                    # 설정 파일
├── requirements.txt             # Python 패키지 의존성
├── .gitignore                   # Git 제외 파일
└── README.md                    # 프로젝트 문서
```

## 🔧 작동 방식

1. **GitHub Actions 스케줄러**: 매시간 자동으로 워크플로우 실행
2. **Python 스크립트**: 쿠팡 API를 호출하여 상품 데이터 수집
   - 골드박스 상품 조회
   - 카테고리별 베스트셀러 조회
3. **HTML 생성**: 수집한 데이터를 기반으로 `index.html` 전체를 새로 생성
4. **GitHub Pages 배포**: 생성된 HTML을 `gh-pages` 브랜치에 자동 배포

## 🎨 주요 기능

- ✨ **골드박스 특가**: 쿠팡 골드박스 상품 자동 수집
- 🔥 **카테고리별 베스트셀러**: 전자기기, 패션, 화장품 등 카테고리별 인기 상품
- 📱 **반응형 디자인**: 모바일과 데스크톱에서 모두 최적화
- ⏰ **자동 업데이트**: 1시간마다 최신 상품 정보로 자동 갱신
- 🎯 **SEO 최적화**: 메타 태그 및 시맨틱 HTML 구조

## ⚙️ 설정 변경

`config.py`에서 다음 설정을 변경할 수 있습니다:

- 카테고리 추가/수정
- API 타임아웃 설정
- 상품 개수 제한 조정

## 📝 주의사항

1. **API 엔드포인트**: 실제 쿠팡 파트너스 API 엔드포인트는 공식 문서를 참고하여 수정이 필요할 수 있습니다.
2. **API 키 보안**: 절대 코드에 API 키를 직접 작성하지 마세요. GitHub Secrets를 반드시 사용하세요.
3. **API 제한**: 쿠팡 API의 호출 제한을 확인하고 필요시 조정하세요.

## 🔍 트러블슈팅

### API 호출 실패
- GitHub Secrets에 API 키가 제대로 설정되었는지 확인
- 쿠팡 파트너스 API 엔드포인트 URL 확인
- API 키 권한 확인

### GitHub Pages가 업데이트되지 않음
- GitHub Actions 실행 로그 확인
- `gh-pages` 브랜치가 생성되었는지 확인
- GitHub Pages 설정 확인

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요!

---

**면책 조항**: 이 프로젝트는 쿠팡 파트너스와 공식적으로 연관되어 있지 않습니다. 쿠팡 파트너스 API의 최신 문서를 참고하여 구현을 완료해주세요.
테스트

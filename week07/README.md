# Python을 통한 REST API 호출 및 데이터 분석

## 1. Python REST API 호출 기초 (`requests`)

* **HTTP 요청 및 응답 처리 흐름**
  1. `requests.get(url, params=...)`: 대상 엔드포인트에 GET 요청 전송 및 Query Parameter 전달
  2. `response.status_code` / `response.headers`: HTTP 상태 코드(예: `200 OK`) 및 응답 데이터 형식(`application/json`) 확인
  3. `response.json()`: JSON 형식의 응답 본문을 Python `dict` 또는 `list` 객체로 디코딩

* **JSON 데이터의 테이블화 (`pd.json_normalize`)**
  * API로부터 반환된 딕셔너리 리스트(`list[dict]`) 및 중첩 JSON 구조를 평탄화(Flatten)하여 분석 가능한 Pandas `DataFrame` 컬럼 형태로 변환
  * 단건 조회(`/breweries/{id}`)처럼 응답이 단일 `dict`인 경우 리스트(`[one]`)로 감싸서 `pd.json_normalize()` 적용

---

## 2. 쿼리 파라미터 및 엔드포인트 활용 (Open Brewery DB)

* **쿼리 파라미터(`params`) 기반 필터링**
  * `per_page`, `page`: 페이지당 반환 데이터 개수 및 페이지 번호 제어
  * `by_city`, `by_country`: 도시명(공백은 `_` 처리) 및 국가명 기준 조건 필터링
  * `by_type`: 양조장 유형(`micro`, `nano`, `regional`, `brewpub` 등)별 조회

* **주요 API 엔드포인트 패턴**
  * **목록 조회**: `GET /v1/breweries`
  * **키워드 검색**: `GET /v1/breweries/search?query=...` (부분 일치 및 대소문자 무시 검색)
  * **랜덤 데이터 조회**: `GET /v1/breweries/random` (`size` 파라미터 유무에 따라 단일 `dict` 또는 `list` 반환)
  * **상세 단건 조회**: `GET /v1/breweries/{id}` (Path Parameter를 이용한 특정 리소스 식별)

---

## 3. 실전 API 연동 및 Pandas 데이터 분석 (TMDb Movie Analysis)

* **API 키 인증 및 데이터 수집**
  * TMDb(The Movie Database) 개발자 계정 발급 후 `api_key` 파라미터를 포함하여 `discover/movie` 엔드포인트 호출
  * 응답 JSON의 `"results"` 키 값을 추출해 `pd.json_normalize()`로 영화 데이터프레임 생성

* **Pandas 기반 영화 데이터 탐색적 분석(EDA) 5가지 주제**
  1. **출시 연도별 영화 개수**: `pd.to_datetime(df['release_date']).dt.year`로 연도 추출 후 `value_counts().sort_index()` 집계
  2. **평점 구간별 분포**: `pd.cut()`을 활용해 `vote_average`를 1점 단위 구간(`0~1` ~ `9~10`)으로 범주화하여 분포 확인
  3. **원어(`original_language`)별 영화 개수**: 언어 코드별 빈도수(`value_counts()`) 집계
  4. **인기도(`popularity`) Top 10 영화**: `nlargest(10, 'popularity')`를 통한 상위 인기작 추출 및 순위 재정렬
  5. **출시 월별 영화 개수**: `dt.month` 추출을 통한 월별 개봉 영화 수 추이 파악

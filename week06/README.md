# Python을 통한 데이터베이스 연동 및 데이터 처리

## 1. Python DB 연동 구조 및 드라이버

* **핵심 객체 및 프로세스**
  * **Connection**: Python 애플리케이션과 데이터베이스 서버 간의 연결 통로 생성 (`connect()`)
  * **Cursor**: SQL 쿼리문을 실행하고 반환된 결과 집합을 임시 저장하는 메모리 공간
  * **실행 흐름**: `Connection 생성` $\rightarrow$ `Cursor 생성` $\rightarrow$ `execute()` 쿼리 실행 $\rightarrow$ `fetchone()` / `fetchall()` 결과 조회 (단, 한 번 fetch한 결과는 재조회 불가) $\rightarrow$ `commit()` 변경 사항 물리적 반영 $\rightarrow$ `close()` 자원 해제

* **DBMS별 전용 드라이버 및 통합 엔진**
  * **SQLite**: `sqlite3` (별도 서버 없이 로컬 파일 기반 동작, Python 기본 내장)
  * **MySQL / MariaDB**: `pymysql` (Docker 컨테이너 등으로 구동된 DB 서버와 호스트·포트·계정 정보로 연동)
  * **PostgreSQL**: `psycopg2`
  * **Oracle / MSSQL**: `oracledb` / `pymssql`
  * **SQLAlchemy**: 다양한 RDBMS를 동일한 코드 인터페이스(`create_engine`)로 연결하는 통합 DB 엔진

---

## 2. 리소스 관리 (`Connection Pool` & `with` 문)

* **Connection Pool (커넥션 풀)**
  * 일정 개수의 Connection 객체를 미리 생성해 풀(Pool)에 보관한 뒤, 요청 시 대여하고 작업 완료 후 반납받는 구조
  * 풀이 크면 대기 시간이 줄어드는 대신 메모리 점유율이 높아지고, 풀이 작으면 메모리를 아끼는 대신 대기 시간이 증가함

* **`with` 문을 활용한 안전한 자원 반납**
  * DB 작업 중 예외가 발생하거나 `close()` 호출을 누락할 경우 발생하는 커넥션 고갈 방지
  * `with` 블록 종료 시 `Cursor`와 `Connection` 자원을 자동으로 해제하여 안정적인 리소스 관리 보장

---

## 3. SQLAlchemy 연동 및 Pandas 데이터 처리

* **SQLAlchemy 연결 문자열 (Connection URL)**
  * 형식: `{dialect}+{driver}://{user}:{password}@{host}:{port}/{database}`
  * **SQLite**: `sqlite:///pokemon.db`
  * **MySQL**: `mysql+pymysql://practice:123456@localhost:3300/docker_mysql`
  * 쿼리 실행 시 `text()` 구문으로 SQL 문을 감싸서 안전하게 실행

* **Pandas와 RDBMS 간 데이터 입출력**
  * **DataFrame $\rightarrow$ DB 테이블 저장 (`to_sql`)**
    * CSV(`pokemon.csv`, `trainer.csv`, `battle.csv`) 등을 읽어 DB 테이블로 일괄 적재
    * 주요 옵션: `if_exists='replace'`(기존 테이블 덮어쓰기), `index=False`(인덱스 제외), `dtype={...}`(SQLAlchemy 타입 모듈을 활용한 컬럼별 데이터 타입 명시)
  * **DB 테이블 $\rightarrow$ DataFrame 조회 (`read_sql_table` / `read_sql`)**
    * `pd.read_sql_table('테이블명', con=engine)`: 테이블 전체 데이터를 DataFrame으로 로드
    * `pd.read_sql('SELECT ...', con=engine)`: 집계(`GROUP BY`), 정렬(`ORDER BY`) 등 SQL 쿼리 실행 결과를 직접 DataFrame으로 변환

## 1. DB 연동 기본 매커니즘
* **Connection**: Python 애플리케이션과 DB 서버 간의 통신 통로 형성
* **Cursor**: DB 내부에서 SQL 구문을 실행하고 결과 집합을 가리키는 매개체 역할
* **통신 프로세스**:
  1. `execute()`: DB 서버로 SQL 명령어 전달 및 실행
  2. `fetchone()` / `fetchall()`: 실행 결과를 Python 내부로 전달(Fetch)
  3. `commit()`: DML(INSERT, UPDATE, DELETE) 변경 사항을 DB에 최종 반영
  4. `close()`: 사용 완료 후 Connection 및 Cursor 자원 해제

## 2. DB별 드라이버(Driver) 분리
* DBMS 종류별 통신 규격이 상이하여 개별 라이브러리 사용 필요
  * **SQLite**: `sqlite3` (Python 기본 내장)
  * **MySQL**: `pymysql`
  * **PostgreSQL**: `psycopg2`
* **SQLAlchemy**: 각 DB 드라이버(Dialect)를 통합하여 동일한 인터페이스로 연결 관리하는 DB 엔진

## 3. 리소스 관리 (`with` 문)
* DB Connection 및 Cursor 사용 후 자원 미반환으로 인한 커넥션 고갈 방지 필요
* `with` 구문 활용을 통한 자동 자원 해제(Close) 및 안전한 예외 처리 보장

## 4. 데이터 분석 라이브러리 연동
* DB 연결 객체(SQLAlchemy Engine)를 매개로 SQL 실행 결과를 Pandas DataFrame 구조로 직접 변환 및 활용

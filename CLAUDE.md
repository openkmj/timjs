# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TimJS Backend는 FastAPI 기반의 이벤트 및 미디어 관리 API입니다. 팀 단위로 이벤트를 생성하고, 이벤트에 사진/동영상을 업로드하며, 팀원들과 공유할 수 있는 기능을 제공합니다.

## Development Commands

### 의존성 설치

```bash
uv sync
```

### 개발 서버 실행

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --forwarded-allow-ips='*' --proxy-headers
```

### 린팅 및 포맷팅

```bash
# 자동 수정 포함
uv run ruff check --fix .

# 검사만
uv run ruff check .
```

### 데이터베이스 초기화

```bash
uv run python init_db.py
```

### 테스트 실행

```bash
# 모든 테스트 실행
uv run pytest

# 특정 파일 테스트
uv run pytest tests/test_middlewares.py

# 특정 마커의 테스트만 실행
uv run pytest -m unit
uv run pytest -m api
uv run pytest -m db
```

## Architecture

### 핵심 아키텍처 패턴

1. **인증 시스템**: API 키 기반의 Bearer 토큰 인증

   - `app/middlewares/auth.py`의 `AuthContext`를 통해 현재 사용자 정보 주입
   - 모든 API 엔드포인트는 `user: AuthContext` 파라미터로 인증된 사용자 접근

2. **데이터베이스 세션 관리**: FastAPI Depends를 통한 자동 세션 관리

   - `app/middlewares/db.py`의 `DBContext`를 통해 DB 세션 주입
   - 모든 엔드포인트는 `db: DBContext` 파라미터로 DB 접근

3. **팀 기반 멀티테넌시**: 모든 데이터는 팀 단위로 격리

   - User, Event는 `team_id` 외래키를 통해 Team과 연결
   - 사용자는 자신의 팀 데이터만 조회/수정 가능

4. **미디어 업로드 플로우**: S3 Presigned URL을 통한 클라이언트 직접 업로드

   - 단계 1: 클라이언트가 Presigned URL 요청
   - 단계 2: 클라이언트가 S3에 직접 업로드
   - 단계 3: 클라이언트가 업로드 완료 확인 요청으로 DB 레코드 생성

5. **관리자 패널**: SQLAdmin 기반의 세션 인증 관리자 대시보드
   - 경로: `/timjs/admin`
   - 별도의 세션 기반 인증 (API 키 인증과 독립적)

### 디렉토리 구조

```
app/
├── routers/          # API 엔드포인트 정의
│   ├── events.py     # 이벤트 CRUD API
│   ├── media.py      # 미디어 업로드/조회 API
│   └── users.py      # 사용자 프로필 API
├── middlewares/      # 의존성 주입 컴포넌트
│   ├── auth.py       # API 키 인증
│   └── db.py         # DB 세션 관리
├── db/               # 데이터베이스 레이어
│   ├── models.py     # SQLAlchemy 모델
│   ├── query.py      # DB 쿼리 함수
│   └── connection.py # DB 엔진 설정
├── utils/            # 유틸리티 함수
│   ├── config.py     # 환경 변수 설정
│   ├── s3.py         # S3 업로드 로직
│   └── push_notification.py  # Expo 푸시 알림
├── admin.py          # SQLAdmin 설정
├── schemas.py        # Pydantic 스키마
└── main.py           # FastAPI 앱 진입점
```

### 데이터 모델 관계

```
Team (팀)
├── users (1:N) → User (사용자)
│   └── media (1:N) → Media (미디어)
└── events (1:N) → Event (이벤트)
    └── media (1:N) → Media (미디어)
```

- **Team**: 스토리지 할당량 관리 (`storage_limit`, `storage_used`)
- **User**: API 키로 인증, Expo 푸시 토큰 저장
- **Event**: nanoid로 생성된 고유 `s3_key` 사용 (S3 폴더 경로)
- **Media**: 원본 이미지/동영상과 썸네일 URL 모두 저장

### 환경 변수 설정

`.env` 파일 필수 항목 (`.env.example` 참고):

- `DATABASE_URL`: SQLite 경로 (기본값: `sqlite:////data/timjs.db`)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: S3 업로드용
- `S3_BUCKET_NAME`: S3 버킷 이름
- `ADMIN_SECRET_KEY`: 관리자 세션 암호화 키
- `ADMIN_PASSWORD`: 관리자 로그인 비밀번호

## Testing

- **pytest 설정**: `pytest.ini`에 정의된 마커 사용

  - `@pytest.mark.unit`: 단위 테스트
  - `@pytest.mark.api`: API 엔드포인트 테스트
  - `@pytest.mark.db`: 데이터베이스 테스트

- **테스트 픽스처** (`tests/conftest.py`):

  - `test_db`: 인메모리 SQLite DB 세션
  - `client`: FastAPI TestClient (DB 의존성 오버라이드 포함)
  - `sample_team`, `sample_user`, `sample_event`, `sample_media`: 테스트 데이터
  - `auth_headers`: Bearer 토큰 인증 헤더

- **테스트 작성 시**: 각 테스트는 독립적인 인메모리 DB 사용 (`scope="function"`)

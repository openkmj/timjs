# TimJS Backend

Event and media management API built with FastAPI.

## 기술 스택

- **FastAPI** - Modern async web framework
- **SQLite** - Lightweight database (easily switchable to PostgreSQL)
- **AWS S3** - Media storage with presigned URLs
- **SQLAlchemy** - ORM with async support
- **uv** - Fast Python package manager

## API 엔드포인트

### 인증

모든 요청에 `Authorization: Bearer <api-key>` 헤더 필수

### 사용자

- `GET /users/me` - 내 정보 조회

### 이벤트

- `GET /events` - 이벤트 목록 조회
  - Query params: `skip`, `limit`, `tag` (선택)
- `POST /events` - 이벤트 생성
- `PUT /events/{id}` - 이벤트 수정
- `DELETE /events/{id}` - 이벤트 삭제

### 미디어

- `POST /media/presigned-url` - S3 직접 업로드를 위한 presigned URL 생성
- `POST /media/confirm-upload` - 업로드 완료 확인 및 메타데이터 저장
- `GET /media` - 미디어 피드 조회
  - Query params: `cursor` (무한 스크롤용), `limit`
- `GET /media/{id}` - 미디어 상세 조회
- `DELETE /media/{id}` - 미디어 삭제 (본인 것만)

## 데이터베이스 스키마

### users

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    expo_push_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### events

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    date TIMESTAMP NOT NULL,
    location TEXT,
    tags TEXT, -- JSON array
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### media

```sql
CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    event_id INTEGER REFERENCES events(id),
    user_id INTEGER REFERENCES users(id),
    s3_key TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    file_metadata TEXT, -- JSON (width, height, duration 등)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 환경 변수

`.env.example` 파일 참고:

```env
# Database
DATABASE_URL=sqlite:///./timjs.db

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=timjs-media
```

## 설치 및 실행

### 1. 의존성 설치

```bash
uv sync
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 설정값 입력
```

### 3. 데이터베이스 초기화

```bash
uv run python init_db.py
# 테스트 사용자 3명이 자동 생성됨 (API 키는 콘솔에 출력)
```

### 4. 서버 실행

```bash
uv run uvicorn app.main:app --reload --port 8000
```

### 5. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 사용 예시

### 이벤트 생성

```bash
curl -X POST \
  -H "Authorization: Bearer test-api-key-1" \
  -H "Content-Type: application/json" \
  -d '{"title": "팀 회식", "date": "2024-01-20T18:00:00", "tags": ["회식", "저녁"]}' \
  http://localhost:8000/api/events
```

### 미디어 업로드 (Presigned URL 방식)

```bash
# 1. Presigned URL 요청
curl -X POST \
  -H "Authorization: Bearer test-api-key-1" \
  -H "Content-Type: application/json" \
  -d '{"file_name": "photo.jpg", "content_type": "image/jpeg"}' \
  http://localhost:8000/api/media/presigned-url

# 2. S3에 직접 업로드 (반환된 URL과 fields 사용)

# 3. 업로드 확인
curl -X POST \
  -H "Authorization: Bearer test-api-key-1" \
  -H "Content-Type: application/json" \
  -d '{"key": "media/xxx.jpg", "file_size": 1024000}' \
  http://localhost:8000/api/media/confirm-upload
```

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py           # FastAPI 앱 진입점
│   ├── config.py         # 환경 변수 설정
│   ├── database.py       # 데이터베이스 연결
│   ├── models.py         # SQLAlchemy 모델
│   ├── schemas.py        # Pydantic 스키마
│   ├── auth.py           # Bearer 토큰 인증
│   ├── routers/
│   │   ├── events.py     # 이벤트 API
│   │   └── media.py      # 미디어 API
│   └── utils/
│       ├── logger.py     # 로깅 설정
│       └── s3.py         # S3 presigned URL 생성
├── init_db.py            # DB 초기화 및 테스트 데이터
├── pyproject.toml        # 프로젝트 의존성 (uv)
├── uv.lock               # 의존성 lock 파일
├── .env.example          # 환경 변수 예시
└── README.md
```

## 개발 도구

### 코드 품질 검사

```bash
# Linting
uv run ruff check .

# 자동 수정
uv run ruff check --fix .
```

## 라이선스

MIT

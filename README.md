# Jira Clone API - FastAPI + PostgreSQL + WebSocket


## 1. Cài đặt

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 2. Chạy PostgreSQL bằng Docker

```bash
docker compose up -d
```

## 3. Tạo file .env

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
copy .env.example .env
```

Nếu máy bạn bị đụng PostgreSQL cổng 5432, đổi `docker-compose.yml` sang `5433:5432`, rồi sửa `.env` thành:

```env
DATABASE_URL=postgresql+asyncpg://jira_user:jira_password@127.0.0.1:5433/jira_clone
```

## 4. Chạy API

```bash
uvicorn app.main:app --reload
```

Mở Swagger:

```text
http://127.0.0.1:8000/docs
```

## 5. Flow test nhanh

### Register

POST `/auth/register`

```json
{
  "full_name": "Admin User",
  "email": "admin@gmail.com",
  "password": "123456"
}
```

### Login

POST `/auth/login` dạng form-data hoặc dùng nút Authorize trong Swagger:

```text
username=admin@gmail.com
password=123456
```

### Create project

POST `/projects`

```json
{
  "name": "Demo Jira",
  "key": "DEMO",
  "description": "Project test"
}
```

Sau khi tạo project, hệ thống tự tạo 4 cột: TO DO, IN PROGRESS, REVIEW, DONE.

### Create issue

POST `/projects/1/issues`

```json
{
  "column_id": 1,
  "title": "Create login page",
  "description": "Build login UI and call API",
  "issue_type": "TASK",
  "priority": "HIGH"
}
```

### Move issue

PATCH `/projects/1/issues/1/move`

```json
{
  "column_id": 2,
  "position": 0
}
```

### Create comment

POST `/issues/1/comments`

```json
{
  "body": "I am working on this task."
}
```

## 6. Notification API

Các thông báo được lưu vào bảng `notifications` và bắn realtime event `notification.created` qua WebSocket.

### Lấy danh sách thông báo

GET `/notifications`

Query hỗ trợ:

```text
unread_only=false
limit=30
```

### Đếm thông báo chưa đọc

GET `/notifications/unread-count`

Response:

```json
{
  "unread_count": 3
}
```

### Đánh dấu đã đọc một thông báo

PATCH `/notifications/{notification_id}/read`

### Đánh dấu tất cả đã đọc

PATCH `/notifications/read-all`

### Xóa thông báo

DELETE `/notifications/{notification_id}`

## 7. WebSocket realtime

Frontend connect:

```js
const token = "YOUR_JWT_TOKEN";
const socket = new WebSocket(`ws://127.0.0.1:8000/ws/projects/1?token=${token}`);

socket.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};

socket.onopen = () => {
  socket.send(JSON.stringify({ event: "ping" }));
};
```





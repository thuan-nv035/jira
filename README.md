# Jira Clone Frontend

Frontend Vue 3 + Vite + Tailwind CSS + WebSocket cho backend Jira Clone FastAPI.

## Chức năng

- Register / Login JWT
- Dashboard danh sách project
- Tạo project mới
- Board Kanban theo project
- Tạo issue/task/bug/story
- Kéo thả issue giữa các column
- Xem / sửa / xóa issue
- Comment trong issue
- Add member vào project
- Chuông thông báo realtime
- Đọc / đánh dấu tất cả đã đọc / xóa thông báo
- Realtime WebSocket theo project

## Cài đặt

```bash
cd jira_clone_fe
npm install
```

Tạo file `.env` từ `.env.example`:

```bash
copy .env.example .env
```

Nội dung mặc định:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

## Chạy frontend

Backend FastAPI cần chạy trước:

```bash
uvicorn app.main:app --reload
```

Sau đó chạy frontend:

```bash
npm run dev
```

Mở trình duyệt:

```txt
http://127.0.0.1:5173

## Luồng test nhanh

1. Vào `/register`, tạo tài khoản A.
2. Tạo project mới.
3. Tạo tài khoản B.
4. Đăng nhập A, thêm B vào project.
5. Đăng nhập B, vào project để thấy chuông thông báo.
6. Tạo issue, kéo issue, comment issue để test realtime notification.

## Ghi chú kết nối WebSocket

Frontend sẽ tự connect tới:

```txt
ws://127.0.0.1:8000/ws/projects/{project_id}?token=JWT_TOKEN
```

Khi backend bắn các event như `issue.created`, `issue.updated`, `issue.moved`, `comment.created`, `notification.created`, frontend tự refresh board và chuông thông báo.

## Nếu bị lỗi CORS

Mở file `.env` của backend FastAPI và thêm:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Sau đó restart backend.

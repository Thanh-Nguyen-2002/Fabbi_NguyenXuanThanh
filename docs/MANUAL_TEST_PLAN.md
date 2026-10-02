# Manual Test Plan: Authentication, Todo CRUD, Authorization & Caching Regression

## 1. Scope & Objective

- **Mục tiêu kiểm thử**: Xác thực toàn bộ luồng chức năng chính của ứng dụng Todo và kiểm tra hồi quy (regression) các lỗi bảo mật đã biết. Đảm bảo không có lỗ hổng phân quyền và cache hoạt động đúng theo thiết kế.
- **Phạm vi kiểm thử**: Authentication (register/login), Authorization (cross-user access), Todo CRUD, Cache Invalidation, JWT Token Security.

---

## 2. Test Environment & Prerequisites

- **Base URL Backend**: `http://localhost:8000`
- **Base URL Frontend**: `http://localhost:3000`
- **Tools**: Postman / curl / Browser DevTools
- **Pre-seeded Test Accounts**:
  - Account 1 (User A): `user_a@test.com` / `Password@123`
  - Account 2 (User B): `user_b@test.com` / `Password@123`
- **Prerequisites**:
  - Docker services đang chạy (`docker compose up -d`)
  - DB đã migrate xong (`alembic upgrade head`)
  - Redis đang running và reachable

---

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status (Pass/Fail) |
|---|---|---|---|---|---|---|---|
| TC-01 | Auth – Register | Đăng ký tài khoản mới thành công | Chưa tồn tại email trong DB | 1. POST `/auth/register` với `email`, `password` hợp lệ | HTTP 201, trả về user info (không trả về password). DB có record mới. | High / Blocker | |
| TC-02 | Auth – Register | Đăng ký với email đã tồn tại | Email đã được đăng ký | 1. POST `/auth/register` với email đã có | HTTP 409 Conflict, message `"Email already registered"` | Medium / Major | |
| TC-03 | Auth – Login | Login thành công với thông tin đúng | User A đã đăng ký | 1. POST `/auth/login` với email/password đúng<br>2. Lưu `access_token` | HTTP 200, trả về `access_token` và `token_type: "bearer"` | High / Blocker | |
| TC-04 | Auth – Login | Login thất bại với password sai (tránh User Enumeration) | User A đã đăng ký | 1. POST `/auth/login` với email đúng, password sai | HTTP 401, message chung **"Invalid email or password"** (không tiết lộ email có tồn tại hay không) | High / Security | |
| TC-05 | Auth – Login | Login thất bại với email không tồn tại | Không có pre-condition | 1. POST `/auth/login` với email chưa đăng ký, password bất kỳ | HTTP 401, message **"Invalid email or password"** (cùng message với TC-04) | Medium / Security | |
| TC-06 | Auth – Login | Login thất bại với các trường bị bỏ trống | Không có pre-condition | 1. POST `/auth/login` với body `{}` (không có email, password) | HTTP 422 Unprocessable Entity, liệt kê các field bị thiếu | Medium / Major | |
| TC-07 | Authorization | User A không thể **sửa** Todo của User B | User A & B đã login; User B đã tạo Todo ID X | 1. User B tạo todo (lấy ID X)<br>2. User A gọi `PUT /todos/{X}` với token của A | HTTP 403 Forbidden **hoặc** 404 Not Found (không để lộ sự tồn tại của resource) | High / Critical | |
| TC-08 | Authorization | User A không thể **xóa** Todo của User B | User A & B đã login; User B đã tạo Todo ID Y | 1. User B tạo todo (lấy ID Y)<br>2. User A gọi `DELETE /todos/{Y}` với token của A | HTTP 403 Forbidden **hoặc** 404 Not Found | High / Critical | |
| TC-09 | Todo CRUD – Create | Tạo Todo mới thành công | User A đã login | 1. POST `/todos` với `{ "title": "Buy groceries" }`<br>2. Lưu `id` trả về | HTTP 201, trả về `{ "id": "...", "title": "Buy groceries", "completed": false }` | High / Blocker | |
| TC-10 | Todo CRUD – Read | Lấy danh sách Todos chỉ của mình | User A & B đều đã tạo todos | 1. User A gọi `GET /todos` với token của A | HTTP 200, danh sách **chỉ chứa todos của User A**, không lộ todos của User B | High / Critical | |
| TC-11 | Todo CRUD – Update Title | Cập nhật title của Todo | User A đã login và có Todo ID Z | 1. PUT `/todos/{Z}` với `{ "title": "New Title" }` | HTTP 200, response `title` = `"New Title"`. `GET /todos/{Z}` sau đó cũng trả về title mới | Medium / Major | |
| TC-12 | Todo CRUD – Toggle Completed | Đổi trạng thái completed=true về completed=false | Todo ID Z đang `completed: true` | 1. PUT `/todos/{Z}` với `{ "completed": false }`<br>2. Refresh / gọi lại `GET /todos/{Z}` | HTTP 200; `GET /todos/{Z}` trả về `completed: false` (không bị rollback về true) | Medium / Major | |
| TC-13 | Todo CRUD – Delete | Xóa Todo thành công | User A có Todo ID W | 1. DELETE `/todos/{W}` với token của A<br>2. Gọi `GET /todos/{W}` | DELETE → HTTP 200/204.<br>GET sau đó → HTTP 404 Not Found | High / Major | |
| TC-14 | Cache – Create | Tạo Todo mới phải invalidate cache list | Cache list của User A đang active | 1. `GET /todos` (cache được tạo)<br>2. `POST /todos` với title mới<br>3. `GET /todos` lần 2 | Lần 3 phải trả về danh sách **bao gồm todo vừa tạo**, không phải cache cũ | Medium / Major | |
| TC-15 | Cache – Update | Cập nhật Todo phải invalidate cache | Todo đã được cache sau GET | 1. `GET /todos/{id}` (cache item)<br>2. `PUT /todos/{id}` với title mới<br>3. `GET /todos/{id}` lần 2 | Lần 3 trả về **title mới**, không nhận dữ liệu cũ từ cache | Medium / Major | |
| TC-16 | Cache – Delete | Xóa Todo phải invalidate cache | Todo đã được cache | 1. `GET /todos` (cache list)<br>2. `DELETE /todos/{id}`<br>3. `GET /todos` lần 2 | Lần 3 **không còn chứa** todo đã xóa trong danh sách | Medium / Major | |
| TC-17 | Token Security | Expired token bị từ chối | Có JWT token đã hết hạn (quá `ACCESS_TOKEN_EXPIRE_MINUTES`) | 1. Dùng expired token gọi `GET /todos` | HTTP 401 Unauthorized, message `"Token has expired"` hoặc `"Could not validate credentials"` | High / Security | |
| TC-18 | Token Security | Tampered token bị từ chối | Có JWT token hợp lệ | 1. Lấy token hợp lệ<br>2. Sửa 1 ký tự bất kỳ trong phần payload (base64 decode → modify → encode)<br>3. Gọi `GET /todos` với token đã sửa | HTTP 401 Unauthorized, chữ ký JWT không hợp lệ | High / Security | |

---

## 4. Defect Tracking & Known Limitations

- **Known Limitation**: Test TC-17 (expired token) yêu cầu chờ hoặc mock time; trong môi trường test có thể set `ACCESS_TOKEN_EXPIRE_MINUTES=1` để rút ngắn thời gian.
- **Known Limitation**: Cache tests (TC-14 đến TC-16) có thể bị flaky nếu TTL Redis quá ngắn hoặc Redis bị flush giữa chừng. Đảm bảo Redis không bị restart trong quá trình test.
- **Ghi chú bảo mật**: TC-04 và TC-05 phải trả về **cùng một message lỗi và cùng HTTP status** để tránh user enumeration attack. Nếu response khác nhau → đánh dấu **FAIL Critical**.
- **Chưa cover**: Rate limiting trên endpoint `/auth/login` (sẽ bổ sung khi tính năng được triển khai), Todo Sharing scenarios (xem `TODO_SHARING_SPEC.md`).

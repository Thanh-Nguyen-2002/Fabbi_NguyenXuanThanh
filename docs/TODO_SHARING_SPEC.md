# Technical Specification: Todo Sharing

> Template dành cho phần Requirement Analysis & Spec Writing.

## 1. Overview & Objective

- **Feature Summary**: Cho phép chủ sở hữu (Owner) của một Todo chia sẻ nó với người dùng khác trong hệ thống theo hai mức quyền: chỉ xem (Viewer) hoặc chỉnh sửa (Editor).
- **Problem Statement**: Hiện tại mỗi Todo chỉ có thể được truy cập bởi người tạo ra nó. Điều này hạn chế khả năng cộng tác – ví dụ, chia sẻ danh sách việc cần làm với đồng nghiệp hoặc bạn bè. Tính năng Todo Sharing giải quyết vấn đề này bằng cách cung cấp cơ chế phân quyền rõ ràng.
- **Target Audience / Roles**:
  - **Owner**: Người tạo ra Todo, có toàn quyền CRUD và quản lý chia sẻ.
  - **Editor**: Người được Owner cấp quyền, có thể đọc và cập nhật nội dung Todo.
  - **Viewer**: Người được Owner cấp quyền, chỉ có thể đọc Todo.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Owner chia sẻ Todo với người dùng khác

- **As a** Todo Owner
- **I want to** chia sẻ một Todo của tôi với người dùng khác theo quyền Viewer hoặc Editor
- **So that** họ có thể xem hoặc cộng tác chỉnh sửa Todo đó
- **Acceptance Criteria**:
  - [ ] Owner gọi `POST /todos/{todo_id}/shares` với `shared_with_user_id` và `permission` hợp lệ → trả về `201 Created` kèm thông tin share record.
  - [ ] Hệ thống từ chối nếu `shared_with_user_id` trùng với `owner_id` → `400 Bad Request` với message `"Cannot share a todo with yourself"`.
  - [ ] Hệ thống từ chối nếu đã tồn tại share record active giữa cùng `todo_id` và `shared_with_user_id` → `409 Conflict` với message `"Todo already shared with this user"`.
  - [ ] Chỉ Owner của Todo mới được gọi endpoint này; người khác nhận `403 Forbidden`.
  - [ ] `permission` phải là `"viewer"` hoặc `"editor"`; giá trị khác → `422 Unprocessable Entity`.

### User Story 2: Owner thu hồi quyền chia sẻ (Revoke)

- **As a** Todo Owner
- **I want to** thu hồi quyền truy cập của một người dùng đã được chia sẻ
- **So that** họ không còn có thể xem hoặc chỉnh sửa Todo của tôi nữa
- **Acceptance Criteria**:
  - [ ] Owner gọi `DELETE /todos/{todo_id}/shares/{share_id}` → `200 OK` (hoặc `204 No Content`), trường `revoked_at` được ghi nhận timestamp.
  - [ ] Sau khi revoke, người dùng bị thu hồi gọi bất kỳ API nào liên quan đến Todo đó → nhận `403 Forbidden` hoặc Todo không còn xuất hiện trong `GET /shared-todos`.
  - [ ] Cache Redis liên quan (`shared:user:{shared_with_user_id}:*`) bị invalidate ngay lập tức sau khi revoke thành công.
  - [ ] Revoke một `share_id` không tồn tại hoặc không thuộc `todo_id` → `404 Not Found`.
  - [ ] Chỉ Owner mới được revoke; người khác nhận `403 Forbidden`.

### User Story 3: Viewer xem Todo được chia sẻ

- **As a** Viewer (người được chia sẻ với quyền `viewer`)
- **I want to** xem danh sách và nội dung chi tiết của các Todo được chia sẻ với tôi
- **So that** tôi có thể nắm bắt thông tin mà không lo bị thay đổi ngoài ý muốn
- **Acceptance Criteria**:
  - [ ] Viewer gọi `GET /shared-todos` → nhận danh sách tất cả todos đang được chia sẻ với mình (chỉ các share chưa bị revoke).
  - [ ] Viewer **không thể** gọi `PUT /todos/{todo_id}` để cập nhật → nhận `403 Forbidden`.
  - [ ] Viewer **không thể** gọi `DELETE /todos/{todo_id}` → nhận `403 Forbidden`.
  - [ ] Viewer **không thể** gọi `POST /todos/{todo_id}/shares` để chia sẻ tiếp → nhận `403 Forbidden`.

### User Story 4: Editor chỉnh sửa Todo được chia sẻ

- **As an** Editor (người được chia sẻ với quyền `editor`)
- **I want to** cập nhật nội dung của Todo được chia sẻ với tôi
- **So that** tôi có thể cộng tác với Owner trong việc quản lý công việc
- **Acceptance Criteria**:
  - [ ] Editor gọi `PUT /todos/{todo_id}` với body hợp lệ → `200 OK`, nội dung Todo được cập nhật.
  - [ ] Sau khi Editor update, cache `todos:user:{owner_id}:*` và `shared:user:{editor_id}:*` bị invalidate ngay lập tức.
  - [ ] Editor **không thể** xóa Todo (`DELETE /todos/{todo_id}`) → `403 Forbidden`.
  - [ ] Editor **không thể** quản lý share (gọi các endpoint `/shares`) → `403 Forbidden`.

---

## 3. Scope

### In-Scope
- Tạo share record giữa Owner và một người dùng cụ thể (1-to-1 sharing).
- Hai mức quyền: `viewer` (chỉ đọc) và `editor` (đọc + cập nhật).
- Owner xem danh sách tất cả người được share của một Todo.
- Owner thu hồi quyền chia sẻ (soft-delete bằng `revoked_at`).
- Người được chia sẻ xem danh sách Todos được share với mình.
- Invalidate Redis cache khi có thay đổi quyền hoặc nội dung.
- Validation đầy đủ: self-share, duplicate share, permission enum.

### Out-of-Scope
- Chia sẻ theo nhóm (group sharing) hoặc theo team/organization.
- Chia sẻ công khai (public link / anyone with link).
- Người được share chia sẻ tiếp cho người khác (re-share).
- Thông báo email / push notification khi được share.
- Lịch sử chỉnh sửa (audit log / version history).
- Quyền `admin` hoặc quyền xóa Todo cho collaborator.
- UI/Frontend implementation (spec này chỉ bao gồm backend API).

---

## 4. Database Design

### Bảng mới: `todo_shares`

```sql
CREATE TABLE todo_shares (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    todo_id             UUID NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
    owner_id            UUID NOT NULL REFERENCES users(id),
    shared_with_user_id UUID NOT NULL REFERENCES users(id),
    permission          VARCHAR(10) NOT NULL CHECK (permission IN ('viewer', 'editor')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at          TIMESTAMPTZ NULL,

    -- Constraints
    CONSTRAINT uq_todo_shares_todo_user UNIQUE (todo_id, shared_with_user_id),
    CONSTRAINT chk_no_self_share CHECK (owner_id != shared_with_user_id)
);
```

> **Lưu ý**: `UNIQUE(todo_id, shared_with_user_id)` đảm bảo mỗi cặp (todo, user) chỉ có một share record. Khi Owner muốn thay đổi permission, thực hiện UPDATE thay vì INSERT mới.

### Constraints & Indexes

| Constraint / Index | Loại | Cột | Mục đích |
|---|---|---|---|
| `pk_todo_shares` | PRIMARY KEY | `id` | Định danh duy nhất |
| `uq_todo_shares_todo_user` | UNIQUE | `(todo_id, shared_with_user_id)` | Ngăn duplicate share |
| `chk_no_self_share` | CHECK | `owner_id != shared_with_user_id` | Ngăn tự chia sẻ cho chính mình |
| `fk_todo_shares_todo` | FOREIGN KEY | `todo_id → todos.id` | Cascade delete khi Todo bị xóa |
| `fk_todo_shares_owner` | FOREIGN KEY | `owner_id → users.id` | Liên kết owner |
| `fk_todo_shares_shared_with` | FOREIGN KEY | `shared_with_user_id → users.id` | Liên kết người được share |
| `idx_todo_shares_todo_id` | INDEX | `(todo_id)` | Query shares của một Todo |
| `idx_todo_shares_shared_with_user_id` | INDEX | `(shared_with_user_id)` | Query todos được share với user |
| `idx_todo_shares_owner_id` | INDEX | `(owner_id)` | Query todos mà user đã share |

```sql
CREATE INDEX idx_todo_shares_todo_id             ON todo_shares(todo_id);
CREATE INDEX idx_todo_shares_shared_with_user_id ON todo_shares(shared_with_user_id);
CREATE INDEX idx_todo_shares_owner_id            ON todo_shares(owner_id);
```

---

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required | Role Allowed |
|---|---|---|---|---|
| POST | `/todos/{todo_id}/shares` | Tạo share mới cho Todo | Yes (JWT) | Owner only |
| GET | `/todos/{todo_id}/shares` | List tất cả shares của Todo | Yes (JWT) | Owner only |
| DELETE | `/todos/{todo_id}/shares/{share_id}` | Thu hồi quyền chia sẻ | Yes (JWT) | Owner only |
| GET | `/shared-todos` | Xem danh sách Todos được share với mình | Yes (JWT) | Any authenticated user |

---

### POST `/todos/{todo_id}/shares`

**Request Body** (JSON):
```json
{
  "shared_with_user_id": "uuid-of-target-user",
  "permission": "viewer"
}
```

**Validation**:
- `shared_with_user_id`: required, valid UUID, must exist in `users` table.
- `permission`: required, enum `["viewer", "editor"]`.

**Responses**:
| Status | Description | Body |
|---|---|---|
| 201 | Share tạo thành công | `{ "id": "...", "todo_id": "...", "shared_with_user_id": "...", "permission": "viewer", "created_at": "..." }` |
| 400 | Tự share cho chính mình | `{ "detail": "Cannot share a todo with yourself" }` |
| 403 | Không phải Owner | `{ "detail": "Forbidden" }` |
| 404 | Todo không tìm thấy | `{ "detail": "Todo not found" }` |
| 409 | Đã tồn tại share với user này | `{ "detail": "Todo already shared with this user" }` |
| 422 | Validation error (permission sai) | FastAPI default validation error |

---

### GET `/todos/{todo_id}/shares`

**Query Parameters**: Không có (có thể thêm `?active_only=true` trong tương lai).

**Responses**:
| Status | Description | Body |
|---|---|---|
| 200 | Danh sách shares | `[ { "id": "...", "shared_with_user_id": "...", "permission": "...", "created_at": "...", "revoked_at": null } ]` |
| 403 | Không phải Owner | `{ "detail": "Forbidden" }` |
| 404 | Todo không tìm thấy | `{ "detail": "Todo not found" }` |

---

### DELETE `/todos/{todo_id}/shares/{share_id}`

**Path Parameters**: `todo_id` (UUID), `share_id` (UUID).

**Responses**:
| Status | Description | Body |
|---|---|---|
| 200 | Revoke thành công | `{ "message": "Share revoked successfully", "revoked_at": "2026-10-02T07:00:00Z" }` |
| 403 | Không phải Owner | `{ "detail": "Forbidden" }` |
| 404 | Share không tồn tại hoặc không thuộc todo này | `{ "detail": "Share not found" }` |

---

### GET `/shared-todos`

**Query Parameters**:
- `skip` (int, default `0`): Offset phân trang.
- `limit` (int, default `20`, max `100`): Số lượng kết quả.

**Responses**:
| Status | Description | Body |
|---|---|---|
| 200 | Danh sách todos được share | `[ { "todo": { "id": "...", "title": "...", "completed": false }, "permission": "viewer", "shared_by": "owner@email.com", "created_at": "..." } ]` |
| 401 | Chưa xác thực | `{ "detail": "Not authenticated" }` |

---

## 6. Business Logic & Security Considerations

### Authorization & Permission Matrix

| Hành động | Owner | Editor | Viewer | Unauthenticated |
|---|---|---|---|---|
| `GET /todos/{id}` (của owner) | ✅ | ✅ | ✅ | ❌ |
| `PUT /todos/{id}` | ✅ | ✅ | ❌ (403) | ❌ |
| `DELETE /todos/{id}` | ✅ | ❌ (403) | ❌ (403) | ❌ |
| `POST /todos/{id}/shares` | ✅ | ❌ (403) | ❌ (403) | ❌ |
| `GET /todos/{id}/shares` | ✅ | ❌ (403) | ❌ (403) | ❌ |
| `DELETE /todos/{id}/shares/{sid}` | ✅ | ❌ (403) | ❌ (403) | ❌ |
| `GET /shared-todos` | ✅ | ✅ | ✅ | ❌ |

> **Quy tắc re-share**: Người được chia sẻ (dù là Editor hay Viewer) **không được phép** chia sẻ tiếp Todo đó cho người khác. Chỉ Owner mới có quyền quản lý danh sách shares.

### Edge Cases & Race Conditions

| Edge Case | Hành vi mong đợi |
|---|---|
| **Tự share cho chính mình** (`owner_id == shared_with_user_id`) | Reject ngay tại tầng validation, trả về `400 Bad Request`. |
| **Duplicate invite** (share đã tồn tại cho cùng user) | Kiểm tra DB trước INSERT; nếu đã có record (dù active hay revoked), trả về `409 Conflict`. Nếu muốn đổi permission, Owner dùng endpoint UPDATE riêng (future scope). |
| **Concurrent revoke** (Owner revoke trong lúc Editor đang gửi PUT) | Dùng DB transaction; Editor sẽ thất bại với `403 Forbidden` sau khi middleware kiểm tra `revoked_at IS NULL`. |
| **Todo bị xóa khi có active shares** | `ON DELETE CASCADE` trên `todo_id` FK tự động xóa tất cả share records. |
| **`shared_with_user_id` không tồn tại** | Trả về `404 Not Found` với message `"User not found"`. |
| **Share ID không thuộc todo_id tương ứng** | Query với `WHERE id = share_id AND todo_id = todo_id`; nếu không khớp → `404 Not Found`. |

### Authorization Flow (middleware/dependency)

```
Request → JWT Decode → Get current_user
         ↓
Fetch todo by todo_id (must exist → 404)
         ↓
         ├─ current_user.id == todo.owner_id → Role: OWNER → proceed
         │
         └─ Query todo_shares WHERE todo_id AND shared_with_user_id = current_user.id AND revoked_at IS NULL
                    ├─ Found, permission='editor' → Role: EDITOR → proceed
                    ├─ Found, permission='viewer' → Role: VIEWER → proceed
                    └─ Not found → 403 Forbidden
```

---

## 7. Caching & Invalidation Strategy

### Cache Key Patterns

| Cache Key | Nội dung | TTL |
|---|---|---|
| `todos:user:{owner_id}:list` | Danh sách todos của owner | 300s |
| `todos:user:{owner_id}:todo:{todo_id}` | Chi tiết một todo của owner | 300s |
| `shared:user:{user_id}:list` | Danh sách todos được share với user | 300s |
| `shared:user:{user_id}:todo:{todo_id}` | Chi tiết todo được share với user | 300s |

### Invalidation Triggers

| Sự kiện | Cache bị invalidate |
|---|---|
| **Owner tạo/sửa/xóa Todo** | `todos:user:{owner_id}:*` |
| **Editor cập nhật Todo** | `todos:user:{owner_id}:*` và `shared:user:{editor_id}:*` |
| **Owner tạo share mới** | `shared:user:{shared_with_user_id}:*` |
| **Owner revoke share** | `shared:user:{revoked_user_id}:*` — **invalidate ngay lập tức** |
| **Todo bị xóa (cascade)** | `todos:user:{owner_id}:*` và `shared:user:{*}:todo:{todo_id}` cho tất cả người được share |

### Implementation Notes

- Sử dụng Redis `SCAN` với pattern `shared:user:{user_id}:*` để invalidate toàn bộ cache của user khi revoke.
- **Không dùng** `KEYS` trong production (blocking operation).
- Khi revoke: thực hiện invalidate cache **trong cùng transaction logic** (sau khi DB commit thành công) để tránh stale data.
- Nên dùng Redis Pipeline để batch delete nhiều keys cùng lúc.

```python
# Pseudocode invalidation on revoke
async def revoke_share(share_id: UUID, current_user: User):
    share = await db.get_share(share_id)  # fetch before delete
    await db.revoke_share(share_id)       # set revoked_at = now()
    
    # Invalidate cache immediately after DB commit
    pattern = f"shared:user:{share.shared_with_user_id}:*"
    keys = await redis.scan_iter(pattern)
    if keys:
        await redis.delete(*keys)
```

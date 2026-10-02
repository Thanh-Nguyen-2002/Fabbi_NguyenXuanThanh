import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from app.services.todo_service import (
    create_todo,
    delete_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300  # 5 minutes


from datetime import date
from typing import Optional

def _cache_key(user_id: uuid.UUID, page: int, size: int, status: Optional[bool] = None, tag_id: Optional[uuid.UUID] = None, keyword: Optional[str] = None, date_from: Optional[date] = None, date_to: Optional[date] = None) -> str:
    """Generate a user-scoped cache key including all filters."""
    return f"todos:user:{user_id}:page:{page}:size:{size}:status:{status}:tag:{tag_id}:kw:{keyword}:from:{date_from}:to:{date_to}"

async def _invalidate_user_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    """Delete all cached todo-list pages for this user via pattern scan."""
    pattern = f"todos:user:{user_id}:*"
    cursor = 0
    while True:
        cursor, keys = await redis.client.scan(cursor, match=pattern, count=100)
        for key in keys:
            await redis.delete(key)
        if cursor == 0:
            break


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    status: Optional[bool] = Query(None),
    tag_id: Optional[uuid.UUID] = Query(None),
    keyword: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos."""
    skip = (page - 1) * size

    cache_key = _cache_key(current_user.id, page, size, status, tag_id, keyword, date_from, date_to)

    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    todos, total = await get_todos(db, user_id=current_user.id, skip=skip, limit=size, status=status, tag_id=tag_id, keyword=keyword, date_from=date_from, date_to=date_to)

    items = [
        TodoResponse(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            completed=todo.completed,
            user_id=todo.user_id,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            tags=[{"id": t.id, "user_id": t.user_id, "name": t.name, "color": t.color, "created_at": t.created_at, "updated_at": t.updated_at} for t in todo.tags],
        )
        for todo in todos
    ]

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )

    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)

    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Create a new todo item."""
    todo = await create_todo(db, todo_data, current_user.id)

    # B5 FIX: Invalidate cache after creating a new todo
    await _invalidate_user_cache(redis, current_user.id)

    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        tags=[],
    )


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # B3 FIX: Ensure the todo belongs to the current user
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo",
        )

    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # B3 FIX: Ownership check before updating
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this todo",
        )

    # B4 FIX: Use model_dump(exclude_unset=True) so only provided fields are updated.
    # This prevents partial updates from erasing description, and allows
    # setting completed=False (the old code only ever set completed=True).
    update_data = todo_data.model_dump(exclude_unset=True)

    updated_todo = await update_todo(db, todo, update_data)

    # Invalidate cache after update
    await _invalidate_user_cache(redis, current_user.id)

    return updated_todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    # B3 FIX: Ownership check before deleting
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this todo",
        )

    await delete_todo(db, todo)

    # B6 FIX: Invalidate cache after deleting
    await _invalidate_user_cache(redis, current_user.id)

    return None

from app.models.tag import Tag
from app.models.todo_tag import TodoTag
from sqlalchemy import select
from pydantic import BaseModel

class TagAddRequest(BaseModel):
    tag_id: uuid.UUID

class BulkStatusRequest(BaseModel):
    todo_ids: list[uuid.UUID]
    completed: bool

@router.post("/{todo_id}/tags", status_code=status.HTTP_201_CREATED)
async def add_tag_to_todo(
    todo_id: uuid.UUID,
    req: TagAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")
        
    tag = await db.execute(select(Tag).where(Tag.id == req.tag_id, Tag.user_id == current_user.id))
    if not tag.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tag not found")
        
    try:
        todo_tag = TodoTag(todo_id=todo_id, tag_id=req.tag_id)
        db.add(todo_tag)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Tag already added")
        
    await _invalidate_user_cache(redis, current_user.id)
    return {"message": "Tag added"}

@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_todo(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")
        
    stmt = select(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id)
    result = await db.execute(stmt)
    todo_tag = result.scalar_one_or_none()
    if not todo_tag:
        raise HTTPException(status_code=404, detail="Tag not found on todo")
        
    await db.delete(todo_tag)
    await db.commit()
    await _invalidate_user_cache(redis, current_user.id)
    return None

@router.patch("/bulk-status", status_code=status.HTTP_200_OK)
async def bulk_update_status(
    req: BulkStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    from app.models.todo import Todo
    stmt = select(Todo).where(Todo.id.in_(req.todo_ids), Todo.user_id == current_user.id)
    result = await db.execute(stmt)
    todos = result.scalars().all()
    
    for todo in todos:
        todo.completed = req.completed
        
    await db.commit()
    await _invalidate_user_cache(redis, current_user.id)
    return {"message": f"Updated {len(todos)} todos"}

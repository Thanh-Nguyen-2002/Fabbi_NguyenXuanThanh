import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc

from app.api.deps import get_current_user, get_db, get_redis
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.core.redis import RedisClient

async def _invalidate_user_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    pattern = f"todos:user:{user_id}:*"
    cursor = 0
    while True:
        cursor, keys = await redis.client.scan(cursor, match=pattern, count=100)
        for key in keys:
            await redis.delete(key)
        if cursor == 0:
            break

router = APIRouter()

@router.get("/", response_model=list[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve all tags for current user."""
    stmt = select(Tag).where(Tag.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: RedisClient = Depends(get_redis),
) -> Any:
    """Create new tag."""
    tag = Tag(name=tag_in.name, color=tag_in.color, user_id=current_user.id)
    db.add(tag)
    try:
        await db.commit()
        await db.refresh(tag)
        await _invalidate_user_cache(redis, current_user.id)
        return tag
    except exc.IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )

@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get tag by ID."""
    stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    tag_in: TagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: RedisClient = Depends(get_redis),
) -> Any:
    """Update tag."""
    stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    update_data = tag_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)
    
    try:
        await db.commit()
        await db.refresh(tag)
        await _invalidate_user_cache(redis, current_user.id)
        return tag
    except exc.IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: RedisClient = Depends(get_redis),
) -> None:
    """Delete tag."""
    stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    await db.delete(tag)
    await db.commit()
    await _invalidate_user_cache(redis, current_user.id)

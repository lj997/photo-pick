"""
连拍分组服务

基于拍摄时间的聚类算法：相邻照片拍摄间隔小于阈值（默认2秒）
则归为同一组。2张及以上的组才会被创建。
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models import Photo, Group, GroupMember, gen_uuid
from app.config import settings


async def detect_groups(db: AsyncSession, session_id: str) -> int:
    # Remove existing auto groups
    existing = await db.execute(
        select(Group).where(Group.session_id == session_id, Group.group_type.in_(["burst", "similar"]))
    )
    for g in existing.scalars().all():
        await db.delete(g)
    await db.flush()

    # Fetch photos ordered by taken_at
    result = await db.execute(
        select(Photo)
        .where(Photo.session_id == session_id, Photo.taken_at.isnot(None))
        .order_by(Photo.taken_at)
    )
    photos = result.scalars().all()

    if not photos:
        await db.commit()
        return 0

    # Time-based clustering
    threshold = settings.grouping_time_threshold_seconds
    groups_created = 0
    current_group: list[Photo] = [photos[0]]

    for i in range(1, len(photos)):
        prev = photos[i - 1]
        curr = photos[i]

        if prev.taken_at and curr.taken_at:
            diff = (curr.taken_at - prev.taken_at).total_seconds()
            if diff <= threshold:
                current_group.append(curr)
            else:
                if len(current_group) >= 2:
                    await _create_group(db, session_id, current_group, groups_created + 1)
                    groups_created += 1
                current_group = [curr]
        else:
            if len(current_group) >= 2:
                await _create_group(db, session_id, current_group, groups_created + 1)
                groups_created += 1
            current_group = [curr]

    # Handle last group
    if len(current_group) >= 2:
        await _create_group(db, session_id, current_group, groups_created + 1)
        groups_created += 1

    await db.commit()
    return groups_created


async def _create_group(db: AsyncSession, session_id: str, photos: list[Photo], num: int):
    group = Group(
        id=gen_uuid(),
        session_id=session_id,
        name=f"Burst #{num}",
        group_type="burst",
    )
    db.add(group)
    await db.flush()

    for idx, photo in enumerate(photos):
        member = GroupMember(
            group_id=group.id,
            photo_id=photo.id,
            position=idx,
        )
        db.add(member)

"""
内容标签分组服务

根据照片的 AI 标签自动创建内容分组，同一标签下的照片归为一组。
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.models import Photo, PhotoTag, Group, GroupMember, gen_uuid


async def detect_content_groups(db: AsyncSession, session_id: str) -> int:
    """根据内容标签自动创建分组，返回创建的分组数量"""
    # 删除旧的内容标签分组
    existing = await db.execute(
        select(Group).where(Group.session_id == session_id, Group.group_type == "content_tag")
    )
    for g in existing.scalars().all():
        await db.delete(g)
    await db.flush()

    # 查询每个标签维度下照片数 >= 2 的标签
    result = await db.execute(
        select(PhotoTag.dimension, PhotoTag.tag_value, func.count(PhotoTag.photo_id.distinct()).label("cnt"))
        .join(Photo, Photo.id == PhotoTag.photo_id)
        .where(Photo.session_id == session_id)
        .group_by(PhotoTag.dimension, PhotoTag.tag_value)
        .having(func.count(PhotoTag.photo_id.distinct()) >= 2)
        .order_by(PhotoTag.dimension, func.count(PhotoTag.photo_id.distinct()).desc())
    )
    tag_groups = result.all()

    groups_created = 0

    dimension_labels = {
        "scene": "场景",
        "people": "人物",
        "setting": "环境",
        "composition": "构图",
    }

    for dimension, tag_value, count in tag_groups:
        # 获取该标签下的所有照片
        photos_result = await db.execute(
            select(Photo.id)
            .join(PhotoTag, PhotoTag.photo_id == Photo.id)
            .where(
                Photo.session_id == session_id,
                PhotoTag.dimension == dimension,
                PhotoTag.tag_value == tag_value,
            )
            .order_by(Photo.sort_order)
        )
        photo_ids = [row[0] for row in photos_result.all()]

        if len(photo_ids) < 2:
            continue

        dim_label = dimension_labels.get(dimension, dimension)
        group = Group(
            id=gen_uuid(),
            session_id=session_id,
            name=f"{dim_label}: {tag_value}",
            group_type="content_tag",
        )
        db.add(group)
        await db.flush()

        for idx, photo_id in enumerate(photo_ids):
            member = GroupMember(
                group_id=group.id,
                photo_id=photo_id,
                position=idx,
            )
            db.add(member)

        groups_created += 1

    await db.commit()
    return groups_created

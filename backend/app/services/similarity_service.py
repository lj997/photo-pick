"""
图片相似度分组服务

使用感知哈希（pHash）计算图片指纹，通过 Union-Find 聚类
将 hamming 距离小于阈值的照片归为同一相似组。
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import imagehash
from PIL import Image
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Photo, Group, GroupMember, gen_uuid
from app.services.ws_manager import ws_manager


_hash_executor = ThreadPoolExecutor(max_workers=settings.thumbnail_workers)


def _compute_phash(thumb_path: str) -> str:
    img = Image.open(thumb_path)
    h = imagehash.phash(img)
    return str(h)


async def compute_hashes(db: AsyncSession, session_id: str) -> int:
    """计算会话中缺少 phash 的照片的感知哈希值"""
    result = await db.execute(
        select(Photo).where(
            Photo.session_id == session_id,
            Photo.phash.is_(None),
            Photo.thumb_sm_ready == True,
        )
    )
    photos = result.scalars().all()

    if not photos:
        return 0

    total = len(photos)
    loop = asyncio.get_event_loop()

    for idx, photo in enumerate(photos):
        thumb_path = settings.cache_dir / f"{photo.id}_sm.jpg"
        if not Path(thumb_path).exists():
            continue

        try:
            hash_str = await loop.run_in_executor(
                _hash_executor, _compute_phash, str(thumb_path)
            )
            photo.phash = hash_str
        except Exception:
            continue

        if (idx + 1) % 10 == 0 or idx == total - 1:
            await ws_manager.broadcast(session_id, "similarity_progress", {
                "total": total,
                "processed": idx + 1,
            })

    await db.commit()
    return total


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1


async def detect_similar_groups(db: AsyncSession, session_id: str, threshold: int = None) -> int:
    """基于 pHash hamming 距离聚类相似照片"""
    if threshold is None:
        threshold = settings.similarity_hash_threshold

    # 清除旧的相似分组
    existing = await db.execute(
        select(Group).where(Group.session_id == session_id, Group.group_type == "similar")
    )
    for g in existing.scalars().all():
        await db.delete(g)
    await db.flush()

    # 加载所有有 phash 的照片
    result = await db.execute(
        select(Photo).where(
            Photo.session_id == session_id,
            Photo.phash.isnot(None),
        ).order_by(Photo.sort_order)
    )
    photos = result.scalars().all()

    if len(photos) < 2:
        await db.commit()
        return 0

    # 两两比较 hamming 距离，Union-Find 聚类
    n = len(photos)
    hashes = [imagehash.hex_to_hash(p.phash) for p in photos]
    uf = UnionFind(n)

    for i in range(n):
        for j in range(i + 1, n):
            distance = hashes[i] - hashes[j]
            if distance <= threshold:
                uf.union(i, j)

    # 收集聚类结果
    clusters: dict[int, list[int]] = {}
    for i in range(n):
        root = uf.find(i)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(i)

    # 创建分组（仅 2+ 成员的聚类）
    groups_created = 0
    for indices in clusters.values():
        if len(indices) < 2:
            continue

        groups_created += 1
        group = Group(
            id=gen_uuid(),
            session_id=session_id,
            name=f"相似组 #{groups_created}",
            group_type="similar",
        )
        db.add(group)
        await db.flush()

        for pos, idx in enumerate(indices):
            member = GroupMember(
                group_id=group.id,
                photo_id=photos[idx].id,
                position=pos,
            )
            db.add(member)

    await db.commit()
    return groups_created

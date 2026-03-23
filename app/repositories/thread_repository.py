import base64
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import nullslast
from app.entities.thread_entity import ThreadEntity


def get_threads(
    db: Session,
    org_id: int,
    user_id: Optional[int] = None,
    chatbot_id: Optional[int] = None,
    cursor: Optional[str] = None,
    limit: int = 20,
) -> list[ThreadEntity]:
    query = select(ThreadEntity).where(ThreadEntity.org_id == org_id)

    if user_id is not None:
        query = query.where(ThreadEntity.user_id == user_id)
    if chatbot_id is not None:
        query = query.where(ThreadEntity.chatbot_id == chatbot_id)

    if cursor:
        try:
            decoded = base64.b64decode(cursor).decode("utf-8")
            cursor_lma_str, cursor_id_str = decoded.split("|", 1)
            cursor_id = uuid.UUID(cursor_id_str)
            cursor_lma = datetime.fromisoformat(cursor_lma_str) if cursor_lma_str else None

            if cursor_lma is not None:
                query = query.where(
                    or_(
                        ThreadEntity.last_message_at < cursor_lma,
                        and_(
                            ThreadEntity.last_message_at == cursor_lma,
                            ThreadEntity.id < cursor_id,
                        ),
                        ThreadEntity.last_message_at.is_(None),
                    )
                )
            else:
                query = query.where(
                    and_(
                        ThreadEntity.last_message_at.is_(None),
                        ThreadEntity.id < cursor_id,
                    )
                )
        except Exception:
            pass

    query = query.order_by(
        nullslast(desc(ThreadEntity.last_message_at)),
        desc(ThreadEntity.id),
    ).limit(limit)

    return list(db.execute(query).scalars().all())


def get_thread_by_id(db: Session, thread_id: uuid.UUID) -> ThreadEntity | None:
    return db.execute(
        select(ThreadEntity).where(ThreadEntity.id == thread_id)
    ).scalar_one_or_none()


def update_thread_stats(db: Session, thread_id: uuid.UUID, message_count_increment: int = 1) -> None:
    thread = db.execute(
        select(ThreadEntity).where(ThreadEntity.id == thread_id)
    ).scalar_one_or_none()
    if thread:
        thread.message_count += message_count_increment
        thread.last_message_at = datetime.now(timezone.utc)
        db.commit()


def create_thread(
    db: Session,
    wren_thread_id: str,
    org_id: int,
    user_id: int,
    chatbot_id: int,
    title: str,
) -> ThreadEntity:
    thread = ThreadEntity(
        wren_thread_id=wren_thread_id,
        org_id=org_id,
        user_id=user_id,
        chatbot_id=chatbot_id,
        title=title,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread

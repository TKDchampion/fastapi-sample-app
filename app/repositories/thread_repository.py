import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.thread_entity import ThreadEntity


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

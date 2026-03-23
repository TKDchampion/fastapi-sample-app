import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.entities.message_entity import MessageEntity, MessageRole, MessageContentType, MessageStatus


def get_next_seq(db: Session, thread_id: uuid.UUID) -> int:
    result = db.execute(
        select(func.coalesce(func.max(MessageEntity.seq), 0)).where(
            MessageEntity.thread_id == thread_id
        )
    ).scalar()
    return result + 1


def get_message_by_thread_and_id(
    db: Session, thread_id: uuid.UUID, message_id: uuid.UUID
) -> MessageEntity | None:
    return db.execute(
        select(MessageEntity).where(
            MessageEntity.thread_id == thread_id,
            MessageEntity.id == message_id,
        )
    ).scalar_one_or_none()


def create_message(
    db: Session,
    thread_id: uuid.UUID,
    seq: int,
    role: MessageRole,
    content_type: MessageContentType,
    content_text: str | None,
    content_json: dict | None,
    status: MessageStatus,
    parent_message_id: uuid.UUID | None = None,
) -> MessageEntity:
    message = MessageEntity(
        thread_id=thread_id,
        seq=seq,
        role=role,
        content_type=content_type,
        content_text=content_text,
        content_json=content_json,
        status=status,
        parent_message_id=parent_message_id,
    )
    db.add(message)
    db.flush()
    db.refresh(message)
    return message

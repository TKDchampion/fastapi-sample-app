from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.chatbot_entity import ChatbotEntity


def get_chatbot_by_org_id(db: Session, org_id: int) -> ChatbotEntity | None:
    return db.execute(
        select(ChatbotEntity).where(ChatbotEntity.org_id == org_id)
    ).scalar_one_or_none()


def upsert_chatbot(
    db: Session,
    org_id: int,
    name: str,
    wren_project_id: str,
    wren_key: str,
) -> tuple[ChatbotEntity, bool]:
    """
    建立或更新 chatbot 記錄。
    回傳 (chatbot, is_new)，is_new=False 代表覆蓋既有記錄。
    """
    existing = get_chatbot_by_org_id(db, org_id)
    if existing:
        existing.name = name
        existing.wren_project_id = wren_project_id
        existing.wren_key = wren_key
        db.flush()
        return existing, False

    chatbot = ChatbotEntity(
        org_id=org_id,
        name=name,
        wren_project_id=wren_project_id,
        wren_key=wren_key,
    )
    db.add(chatbot)
    db.flush()
    return chatbot, True


def update_wren_models(db: Session, chatbot_id: int, models: List[str]) -> None:
    chatbot = db.execute(
        select(ChatbotEntity).where(ChatbotEntity.id == chatbot_id)
    ).scalar_one()
    chatbot.wren_models = models
    db.flush()

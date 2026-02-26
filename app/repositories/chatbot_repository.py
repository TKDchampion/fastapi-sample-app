from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.chatbot_entity import ChatbotEntity


def get_chatbot_by_org_id(db: Session, org_id: int) -> ChatbotEntity | None:
    return db.execute(
        select(ChatbotEntity).where(ChatbotEntity.org_id == org_id)
    ).scalar_one_or_none()
